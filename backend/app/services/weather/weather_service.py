"""
Weather & Location service.

Two responsibilities, kept deliberately separate:

  1. RESOLVE a location — from an explicit city name, from browser geolocation
     coordinates, or (last resort) from the caller's IP address.
  2. FETCH live conditions from Open-Meteo and turn them into *explicit dressing
     constraints*.

Step 2 matters more than it looks. Handing an LLM the string "88°F, Slight rain"
and hoping it reasons well is exactly how you get a suede loafer recommended in
a downpour. Instead `derive_dress_code()` converts the numbers into hard
requirements and prohibitions in plain Python, deterministically, and the model
receives those as constraints it must satisfy rather than facts it must
interpret.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
IP_LOOKUP_URL = "http://ip-api.com/json/"

# WMO weather interpretation codes → (human label, precipitation class)
# https://open-meteo.com/en/docs
WMO_CODES: dict[int, tuple[str, str]] = {
    0:  ("clear sky", "none"),
    1:  ("mainly clear", "none"),
    2:  ("partly cloudy", "none"),
    3:  ("overcast", "none"),
    45: ("foggy", "fog"),
    48: ("depositing rime fog", "fog"),
    51: ("light drizzle", "drizzle"),
    53: ("moderate drizzle", "drizzle"),
    55: ("dense drizzle", "drizzle"),
    56: ("light freezing drizzle", "freezing"),
    57: ("dense freezing drizzle", "freezing"),
    61: ("slight rain", "rain"),
    63: ("moderate rain", "rain"),
    65: ("heavy rain", "heavy_rain"),
    66: ("light freezing rain", "freezing"),
    67: ("heavy freezing rain", "freezing"),
    71: ("slight snow", "snow"),
    73: ("moderate snow", "snow"),
    75: ("heavy snow", "heavy_snow"),
    77: ("snow grains", "snow"),
    80: ("slight rain showers", "rain"),
    81: ("moderate rain showers", "rain"),
    82: ("violent rain showers", "heavy_rain"),
    85: ("slight snow showers", "snow"),
    86: ("heavy snow showers", "heavy_snow"),
    95: ("thunderstorm", "heavy_rain"),
    96: ("thunderstorm with slight hail", "heavy_rain"),
    99: ("thunderstorm with heavy hail", "heavy_rain"),
}


# ══════════════════════════════════════════════════════════════════════════════
# Data models
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ResolvedLocation:
    latitude: float
    longitude: float
    label: str
    source: str  # "explicit_city" | "browser_coords" | "ip_lookup"


@dataclass
class DressCode:
    """Explicit, machine-derived clothing constraints for a set of conditions."""
    temperature_band: str
    precipitation: str
    require: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    layers: int = 1
    notes: list[str] = field(default_factory=list)


@dataclass
class WeatherReport:
    location: str
    source: str
    temperature_c: float
    feels_like_c: float
    high_c: Optional[float]
    low_c: Optional[float]
    condition: str
    precipitation_chance: Optional[int]
    wind_kph: float
    humidity: Optional[int]
    dress_code: DressCode

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_prompt_block(self) -> str:
        """Render as the constraint block injected into the stylist's context."""
        dc = self.dress_code
        lines = [
            f"LIVE WEATHER — {self.location} (via {self.source})",
            f"  Now: {self.temperature_c:.0f}°C (feels like {self.feels_like_c:.0f}°C), {self.condition}",
        ]
        if self.high_c is not None and self.low_c is not None:
            lines.append(f"  Today: high {self.high_c:.0f}°C / low {self.low_c:.0f}°C")
        if self.precipitation_chance is not None:
            lines.append(f"  Chance of precipitation: {self.precipitation_chance}%")
        lines.append(f"  Wind: {self.wind_kph:.0f} km/h")
        lines.append("")
        lines.append("DERIVED DRESSING CONSTRAINTS (these are requirements, not suggestions):")
        lines.append(f"  Temperature band: {dc.temperature_band}")
        lines.append(f"  Precipitation: {dc.precipitation}")
        lines.append(f"  Recommended layers: {dc.layers}")
        if dc.require:
            lines.append("  MUST prioritise: " + "; ".join(dc.require))
        if dc.avoid:
            lines.append("  MUST NOT recommend: " + "; ".join(dc.avoid))
        for note in dc.notes:
            lines.append(f"  Note: {note}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# Location resolution
# ══════════════════════════════════════════════════════════════════════════════

async def geocode_city(city: str) -> Optional[ResolvedLocation]:
    """Look up coordinates for a city name via Open-Meteo geocoding."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(
                GEOCODE_URL,
                params={"name": city, "count": 1, "language": "en", "format": "json"},
            )
            res.raise_for_status()
            results = res.json().get("results") or []
    except Exception as e:
        logger.warning("[weather] Geocoding failed for %r: %s", city, e)
        return None

    if not results:
        logger.info("[weather] No geocoding match for %r", city)
        return None

    top = results[0]
    label_parts = [top.get("name"), top.get("admin1"), top.get("country")]
    label = ", ".join(p for p in label_parts if p)
    return ResolvedLocation(
        latitude=top["latitude"],
        longitude=top["longitude"],
        label=label or city,
        source="explicit_city",
    )


async def locate_by_ip() -> Optional[ResolvedLocation]:
    """Last-resort location lookup from the server's outbound IP."""
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(IP_LOOKUP_URL)
            res.raise_for_status()
            data = res.json()
    except Exception as e:
        logger.warning("[weather] IP geolocation failed: %s", e)
        return None

    if data.get("status") != "success":
        return None

    label = ", ".join(p for p in (data.get("city"), data.get("country")) if p)
    return ResolvedLocation(
        latitude=data["lat"],
        longitude=data["lon"],
        label=label or "your location",
        source="ip_lookup",
    )


async def resolve_location(
    city: Optional[str] = None,
    browser_lat: Optional[float] = None,
    browser_lon: Optional[float] = None,
) -> Optional[ResolvedLocation]:
    """
    Resolve a location, most-specific source first:
      explicit city → browser coordinates → IP lookup.
    """
    if city:
        located = await geocode_city(city)
        if located:
            return located
        logger.info("[weather] Falling through from unresolved city %r", city)

    if browser_lat is not None and browser_lon is not None:
        return ResolvedLocation(
            latitude=browser_lat,
            longitude=browser_lon,
            label="your location",
            source="browser_coords",
        )

    return await locate_by_ip()


# ══════════════════════════════════════════════════════════════════════════════
# Dress-code derivation — the precise reasoning layer
# ══════════════════════════════════════════════════════════════════════════════

def _temperature_band(feels_like_c: float) -> str:
    if feels_like_c < 0:
        return "freezing"
    if feels_like_c < 10:
        return "cold"
    if feels_like_c < 17:
        return "cool"
    if feels_like_c < 24:
        return "mild"
    if feels_like_c < 31:
        return "warm"
    return "hot"


# Per-band layering, requirements and prohibitions.
_BAND_RULES: dict[str, dict[str, Any]] = {
    "freezing": {
        "layers": 3,
        "require": ["heavy insulated outerwear", "long sleeves", "closed insulated footwear",
                    "thermal or knit accessories (scarf, beanie, gloves)"],
        "avoid": ["shorts", "sandals", "sleeveless tops", "lightweight single-layer outfits"],
    },
    "cold": {
        "layers": 3,
        "require": ["warm coat or puffer jacket", "long trousers", "closed footwear"],
        "avoid": ["shorts", "sandals", "tank tops", "linen or other thin summer fabrics"],
    },
    "cool": {
        "layers": 2,
        "require": ["a light jacket, cardigan or sweater as an outer layer", "long trousers"],
        "avoid": ["sleeveless tops on their own", "sandals"],
    },
    "mild": {
        "layers": 2,
        "require": ["a light top", "an optional light layer for the evening"],
        "avoid": ["heavy winter coats", "puffer jackets"],
    },
    "warm": {
        "layers": 1,
        "require": ["breathable short-sleeve or lightweight tops"],
        "avoid": ["heavy coats", "sweaters", "thick knitwear", "layered outerwear"],
    },
    "hot": {
        "layers": 1,
        "require": ["the lightest breathable fabrics available", "short sleeves or sleeveless",
                    "light colours"],
        "avoid": ["any outerwear", "sweaters", "hoodies", "dark heat-absorbing colours",
                  "denim jackets", "closed heavy boots"],
    },
}

# Precipitation overrides layer onto the temperature rules.
_PRECIP_RULES: dict[str, dict[str, Any]] = {
    "drizzle": {
        "require": ["a water-resistant outer layer"],
        "avoid": ["suede or untreated leather footwear"],
        "notes": ["Light precipitation — a compact water-resistant layer is enough."],
    },
    "rain": {
        "require": ["a waterproof jacket or raincoat", "closed water-resistant footwear"],
        "avoid": ["suede or untreated leather", "sandals and open footwear",
                  "long hems that drag on wet ground", "fabrics that stain when wet"],
        "notes": ["It is actively raining — waterproofing outranks style here."],
        "min_layers": 2,
    },
    "heavy_rain": {
        "require": ["a fully waterproof outer layer", "waterproof closed footwear",
                    "quick-drying fabrics"],
        "avoid": ["suede or untreated leather", "sandals and open footwear", "light colours that turn transparent when wet",
                  "delicate or dry-clean-only fabrics"],
        "notes": ["Heavy rain or thunderstorms — assume the wearer will get soaked without proper outerwear."],
        "min_layers": 2,
    },
    # The temperature band already demands insulation at these readings, so the
    # snow rules only add what snow specifically changes: waterproofing and grip.
    "snow": {
        "require": ["a waterproof shell over the insulation", "waterproof boots with grip"],
        "avoid": ["sneakers", "sandals", "thin soles", "cotton that stays wet"],
        "notes": ["Snow underfoot — traction and dry feet matter."],
        "min_layers": 3,
    },
    "heavy_snow": {
        "require": ["a fully waterproof shell over the insulation",
                    "waterproof boots with deep tread"],
        "avoid": ["sneakers", "sandals", "thin soles", "exposed skin"],
        "notes": ["Heavy snow — prioritise warmth and dryness over everything else."],
        "min_layers": 3,
    },
    "freezing": {
        "require": ["waterproof insulated outerwear", "boots with grip"],
        "avoid": ["smooth-soled shoes", "sandals"],
        "notes": ["Freezing precipitation means ice underfoot — grip is a safety issue."],
        "min_layers": 3,
    },
    "fog": {
        "require": ["a light outer layer against damp air"],
        "avoid": [],
        "notes": ["Fog carries damp that makes it feel colder than the reading."],
    },
    "none": {"require": [], "avoid": [], "notes": []},
}


def _swap_outerwear_ban(avoid: list[str]) -> list[str]:
    """
    Narrow a blanket outerwear ban down to a ban on *warm* outerwear.

    Warm weather says "no outerwear"; rain says "wear a shell". Deleting the ban
    outright resolves the contradiction but over-corrects — the model then reads
    a heavy charcoal cape as permitted in 36°C. Replacing it keeps the useful
    half of the rule: a shell is fine, insulation is not.
    """
    narrowed = [a for a in avoid if a not in ("any outerwear", "layered outerwear")]
    if len(narrowed) != len(avoid):
        narrowed.append(
            "any warm or insulating outer layer — only a lightweight "
            "water-resistant shell is acceptable, and none at all is better "
            "than a heavy one"
        )
    return narrowed


def derive_dress_code(
    feels_like_c: float,
    weather_code: int,
    wind_kph: float,
    precipitation_chance: Optional[int],
    daily_low_c: Optional[float] = None,
) -> DressCode:
    """
    Convert raw conditions into explicit clothing requirements and prohibitions.

    Deliberately deterministic: the same conditions always yield the same
    constraints, so the recommendation can be audited rather than guessed at.
    """
    band = _temperature_band(feels_like_c)
    condition_label, precip_class = WMO_CODES.get(weather_code, ("unknown conditions", "none"))

    band_rule = _BAND_RULES[band]
    require = list(band_rule["require"])
    avoid = list(band_rule["avoid"])
    layers = band_rule["layers"]
    notes: list[str] = []

    # ── Precipitation overrides ───────────────────────────────────────────────
    precip_rule = _PRECIP_RULES.get(precip_class, _PRECIP_RULES["none"])
    require += precip_rule["require"]
    avoid += precip_rule["avoid"]
    notes += precip_rule.get("notes", [])
    layers = max(layers, precip_rule.get("min_layers", 0))

    # Rain outranks the hot-weather "no outerwear" rule — a waterproof shell in
    # warm rain is correct, so drop the blanket prohibition rather than emit a
    # contradiction the model has to resolve on its own.
    if precip_class in ("drizzle", "rain", "heavy_rain"):
        avoid = _swap_outerwear_ban(avoid)
        notes.append(
            "Warm but wet: a light waterproof shell is required even though the "
            "temperature alone would not call for outerwear."
            if band in ("warm", "hot")
            else "Rain and cool air together — waterproof outer layer over insulation."
        )

    # ── Wind ──────────────────────────────────────────────────────────────────
    if wind_kph >= 35:
        require.append("a wind-resistant outer layer")
        avoid.append("loose flowing skirts, dresses or scarves that catch wind")
        notes.append(f"Strong wind ({wind_kph:.0f} km/h) makes it feel materially colder than {feels_like_c:.0f}°C.")
    elif wind_kph >= 20 and band in ("freezing", "cold", "cool"):
        require.append("a wind-resistant layer")

    # ── Rain that has not started yet ─────────────────────────────────────────
    if precip_class == "none" and precipitation_chance is not None and precipitation_chance >= 40:
        require.append("a packable water-resistant layer as a precaution")
        # Same contradiction as above: a hot day forbids outerwear outright, but
        # we just asked for a packable shell. The specific instruction wins.
        avoid = _swap_outerwear_ban(avoid)
        notes.append(f"{precipitation_chance}% chance of rain later today — carry a layer even though it is dry now.")

    # ── Day/night swing ───────────────────────────────────────────────────────
    if daily_low_c is not None and (feels_like_c - daily_low_c) >= 8:
        layers = max(layers, 2)
        notes.append(
            f"Temperature drops to {daily_low_c:.0f}°C later — layer so the outfit still works after dark."
        )

    # Preserve order while removing duplicates.
    require = list(dict.fromkeys(require))
    avoid = list(dict.fromkeys(avoid))

    return DressCode(
        temperature_band=band,
        precipitation=condition_label,
        require=require,
        avoid=avoid,
        layers=layers,
        notes=notes,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_weather(location: ResolvedLocation) -> Optional[WeatherReport]:
    """Fetch live conditions for a resolved location and derive its dress code."""
    params = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(FORECAST_URL, params=params)
            res.raise_for_status()
            data = res.json()
    except Exception as e:
        logger.warning("[weather] Forecast fetch failed for %s: %s", location.label, e)
        return None

    current = data.get("current") or {}
    daily = data.get("daily") or {}

    if "temperature_2m" not in current:
        logger.warning("[weather] Forecast response missing current conditions.")
        return None

    def _first(key: str) -> Optional[float]:
        values = daily.get(key) or []
        return values[0] if values else None

    temp = float(current["temperature_2m"])
    feels_like = float(current.get("apparent_temperature", temp))
    weather_code = int(current.get("weather_code", 0))
    wind = float(current.get("wind_speed_10m", 0.0))
    humidity = current.get("relative_humidity_2m")
    high = _first("temperature_2m_max")
    low = _first("temperature_2m_min")
    precip_chance = _first("precipitation_probability_max")

    condition_label = WMO_CODES.get(weather_code, ("unknown conditions", "none"))[0]

    report = WeatherReport(
        location=location.label,
        source=location.source,
        temperature_c=temp,
        feels_like_c=feels_like,
        high_c=high,
        low_c=low,
        condition=condition_label,
        precipitation_chance=int(precip_chance) if precip_chance is not None else None,
        wind_kph=wind,
        humidity=int(humidity) if humidity is not None else None,
        dress_code=derive_dress_code(
            feels_like_c=feels_like,
            weather_code=weather_code,
            wind_kph=wind,
            precipitation_chance=int(precip_chance) if precip_chance is not None else None,
            daily_low_c=low,
        ),
    )
    logger.info("[weather] %s: %.0f°C %s → band=%s precip=%s",
                report.location, report.temperature_c, report.condition,
                report.dress_code.temperature_band, report.dress_code.precipitation)
    return report


async def get_weather_report(
    city: Optional[str] = None,
    browser_lat: Optional[float] = None,
    browser_lon: Optional[float] = None,
) -> Optional[WeatherReport]:
    """Resolve a location and fetch its weather report in one call."""
    location = await resolve_location(city, browser_lat, browser_lon)
    if location is None:
        logger.info("[weather] Could not resolve any location.")
        return None
    return await fetch_weather(location)
