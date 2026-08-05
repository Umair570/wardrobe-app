import logging
import httpx
from typing import Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

async def extract_location_intent(query: str) -> Optional[str]:
    """
    Uses LLM to extract explicit cities from the prompt.
    Returns the city name if found, otherwise None.
    """
    api_key = settings.active_llm_api_key
    base_url = settings.active_llm_base_url
    model = settings.active_llm_model

    if not api_key or api_key == "YOUR_GROQ_API_KEY":
        return None
        
    prompt = f"""Extract the explicit city or destination mentioned in the following user prompt.
If the user mentions a location (e.g. "I'm going to London" -> "London", "Miami beach" -> "Miami"), return ONLY the city name string.
If no explicit location is mentioned, return exactly the word NULL.
Do not output anything else.

User Prompt: "{query}"
Target City:"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    if settings.llm_provider.lower() == "openrouter":
        headers["HTTP-Referer"] = "http://localhost:3000"
        headers["X-Title"] = "Wardrobe Stylist AI"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 15,
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(base_url, headers=headers, json=payload, timeout=5.0)
            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"].strip()
            
        if content.upper() == "NULL" or not content:
            return None
        return content
    except Exception as e:
        logger.warning("[weather_service] Failed to extract location intent: %s", e)
        return None

async def fetch_lat_lon_for_city(city: str) -> Tuple[Optional[float], Optional[float]]:
    """Uses Open-Meteo Geocoding to get latitude and longitude for a city."""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(url)
            res.raise_for_status()
            data = res.json()
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                return result.get("latitude"), result.get("longitude")
    except Exception as e:
        logger.warning("[weather_service] Geocoding failed for %s: %s", city, e)
    return None, None

async def fetch_weather_context(
    query: str, 
    browser_lat: Optional[float] = None, 
    browser_lon: Optional[float] = None
) -> Optional[str]:
    """
    1. Check if the user explicitly mentions a city using LLM intent extraction.
    2. If yes, get the coordinates for that city.
    3. If no, fallback to the provided browser coordinates.
    4. Fetch live weather from Open-Meteo and return a formatted string.
    """
    target_lat = browser_lat
    target_lon = browser_lon
    target_city = "your location"
    
    # 1. Intent extraction override
    explicit_city = await extract_location_intent(query)
    if explicit_city:
        lat, lon = await fetch_lat_lon_for_city(explicit_city)
        if lat is not None and lon is not None:
            target_lat = lat
            target_lon = lon
            target_city = explicit_city

    # 2. Require coordinates
    if target_lat is None or target_lon is None:
        logger.info("[weather_service] No target coordinates available. Skipping weather context.")
        return None

    # 3. Fetch Weather from Open-Meteo
    # WMO Weather interpretation codes: https://open-meteo.com/en/docs
    weather_codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        95: "Thunderstorm"
    }

    url = f"https://api.open-meteo.com/v1/forecast?latitude={target_lat}&longitude={target_lon}&current_weather=true&temperature_unit=fahrenheit"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(url)
            res.raise_for_status()
            data = res.json()
            
            if "current_weather" in data:
                cw = data["current_weather"]
                temp = cw.get("temperature")
                code = cw.get("weathercode", -1)
                condition = weather_codes.get(code, "Unknown")
                
                context = f"Weather in {target_city}: {temp}°F, {condition}."
                logger.info("[weather_service] Successfully resolved weather context: %s", context)
                return context
    except Exception as e:
        logger.warning("[weather_service] Weather API fetch failed: %s", e)
        
    return None
