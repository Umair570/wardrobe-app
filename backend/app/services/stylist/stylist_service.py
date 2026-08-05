import logging
import httpx

from app.core.config import settings
from app.services.stylist.schemas import WardrobeItem, StylistResponse, OutfitRecommendation
from app.services.stylist.prompt_builder import build_system_prompt

logger = logging.getLogger(__name__)

async def generate_outfit_recommendation(
    query: str, 
    retrieved_items: list[WardrobeItem], 
    weather_context: str | None = None,
    chat_history: list[dict] | None = None
) -> StylistResponse:
    """
    Calls the Groq LLM (or fallback) to generate a structured outfit recommendation.
    """
    provider = getattr(settings, "llm_provider", "groq").lower()
    if provider == "openrouter":
        api_key = getattr(settings, "openrouter_api_key", None)
        base_url = "https://openrouter.ai/api/v1/chat/completions"
        model = getattr(settings, "llm_model", "openai/gpt-3.5-turbo")
    else:
        api_key = settings.groq_api_key
        base_url = "https://api.groq.com/openai/v1/chat/completions"
        model = settings.groq_model
        
    if not api_key or api_key == "YOUR_GROQ_API_KEY":
        logger.warning(f"{provider} API key not configured. Using local fallback logic.")
        return _local_fallback(query, retrieved_items)

    system_prompt = build_system_prompt(retrieved_items, weather_context)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    if provider == "openrouter":
        headers["HTTP-Referer"] = "http://localhost:3000"
        headers["X-Title"] = "Wardrobe Stylist AI"

    messages = [{"role": "system", "content": system_prompt}]
    
    if chat_history:
        for msg in chat_history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
            
    messages.append({"role": "user", "content": query})

    payload = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                base_url,
                headers=headers,
                json=payload,
                timeout=15.0
            )
            response.raise_for_status()
            data = response.json()
            
            content_str = data["choices"][0]["message"]["content"]
            
            # Use Pydantic to validate the JSON string directly
            return StylistResponse.model_validate_json(content_str)
            
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return _local_fallback(query, retrieved_items, error_msg=f"Groq API error: {e}")

def _local_fallback(query: str, items: list[WardrobeItem], error_msg: str = "") -> StylistResponse:
    """
    Simple keyword-based fallback if LLM is unavailable.
    Returns the first matching items based on basic types.
    """
    outfit = OutfitRecommendation()
    message = "Here is a fallback recommendation based on your wardrobe."
    if error_msg:
        message += f" ({error_msg})"

    # Simple heuristic to pick items
    for item in items:
        cat = (item.category or "").lower()
        typ = (item.type or "").lower()
        
        if not outfit.top_id and (cat == "upper_body" or "shirt" in typ or "top" in typ):
            outfit.top_id = item.id
        elif not outfit.bottom_id and (cat == "lower_body" or "pant" in typ or "jean" in typ or "short" in typ):
            outfit.bottom_id = item.id
        elif not outfit.outerwear_id and ("jacket" in typ or "coat" in typ or "hoodie" in typ):
            outfit.outerwear_id = item.id
        elif not outfit.shoes_id and ("shoe" in typ or "sneaker" in typ or "boot" in typ):
            outfit.shoes_id = item.id

    return StylistResponse(
        message=message,
        outfit=outfit
    )
