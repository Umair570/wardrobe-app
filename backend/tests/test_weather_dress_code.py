"""
Tests for the deterministic dressing-constraint layer.

`derive_dress_code` is what makes weather-aware styling precise rather than
vibes: it turns raw conditions into hard `require` / `avoid` lists before any
LLM sees them. These tests pin the rules that matter, especially the cases where
temperature and precipitation give contradictory advice.

Run: pytest backend/tests/test_weather_dress_code.py -v
"""

import pytest

from app.services.weather.weather_service import derive_dress_code

# WMO codes used below
CLEAR = 0
PARTLY_CLOUDY = 2
MODERATE_RAIN = 63
THUNDERSTORM = 95
HEAVY_SNOW = 75


def _joined(values: list[str]) -> str:
    return " | ".join(values).lower()


class TestTemperatureBands:
    @pytest.mark.parametrize(
        "feels_like, expected",
        [(-5, "freezing"), (5, "cold"), (14, "cool"), (20, "mild"), (28, "warm"), (38, "hot")],
    )
    def test_band_boundaries(self, feels_like, expected):
        assert derive_dress_code(feels_like, CLEAR, 5, 0).temperature_band == expected

    def test_hot_and_dry_forbids_outerwear(self):
        dc = derive_dress_code(38, CLEAR, 5, 0)
        assert "any outerwear" in dc.avoid
        assert dc.layers == 1

    def test_freezing_demands_layers(self):
        dc = derive_dress_code(-5, CLEAR, 5, 0)
        assert dc.layers >= 3
        assert "shorts" in dc.avoid


class TestPrecipitation:
    def test_rain_requires_waterproofing_and_bans_suede(self):
        dc = derive_dress_code(18, MODERATE_RAIN, 10, 100)
        assert "rain" in dc.precipitation
        assert "waterproof" in _joined(dc.require)
        assert "suede" in _joined(dc.avoid)
        assert "sandals and open footwear" in dc.avoid

    def test_snow_requires_grip(self):
        dc = derive_dress_code(-2, HEAVY_SNOW, 10, 100)
        assert "waterproof boots with deep tread" in dc.require
        assert "sneakers" in dc.avoid
        assert dc.layers >= 3

    def test_snow_does_not_duplicate_insulation_advice(self):
        # The freezing band already asks for insulation; the snow rule must add
        # waterproofing without repeating it as a near-identical entry.
        dc = derive_dress_code(-2, HEAVY_SNOW, 10, 100)
        assert len(dc.require) == len(set(dc.require))


class TestContradictionResolution:
    """Warm weather says 'no outerwear'; rain says 'wear a shell'. Rain wins,
    but only for a shell — not for a heavy coat."""

    def test_warm_rain_permits_a_shell(self):
        dc = derive_dress_code(31, MODERATE_RAIN, 12, 90)
        assert dc.temperature_band == "hot"
        assert "any outerwear" not in dc.avoid, "a waterproof layer must be allowed in warm rain"
        assert "waterproof" in _joined(dc.require)

    def test_warm_rain_still_bans_warm_layers(self):
        dc = derive_dress_code(31, MODERATE_RAIN, 12, 90)
        assert "insulating" in _joined(dc.avoid), (
            "dropping the outerwear ban outright would license a heavy coat in 31C"
        )

    def test_dry_but_rain_likely_is_also_resolved(self):
        dc = derive_dress_code(34, CLEAR, 5, 85)
        assert "precaution" in _joined(dc.require)
        assert "any outerwear" not in dc.avoid
        assert "insulating" in _joined(dc.avoid)

    def test_low_rain_chance_keeps_the_outerwear_ban(self):
        dc = derive_dress_code(34, CLEAR, 5, 10)
        assert "any outerwear" in dc.avoid
        assert "precaution" not in _joined(dc.require)

    def test_thunderstorm_is_treated_as_heavy_rain(self):
        dc = derive_dress_code(24, THUNDERSTORM, 15, 100)
        assert "fully waterproof" in _joined(dc.require)


class TestWindAndSwing:
    def test_strong_wind_adds_a_windproof_requirement(self):
        dc = derive_dress_code(12, PARTLY_CLOUDY, 45, 0)
        assert "a wind-resistant outer layer" in dc.require
        assert any("wind" in n.lower() for n in dc.notes)

    def test_calm_air_adds_nothing(self):
        dc = derive_dress_code(12, PARTLY_CLOUDY, 5, 0)
        assert "a wind-resistant outer layer" not in dc.require

    def test_large_dayn_night_swing_forces_layering(self):
        dc = derive_dress_code(28, CLEAR, 5, 0, daily_low_c=15)
        assert dc.layers >= 2
        assert any("later" in n.lower() for n in dc.notes)


class TestDeterminism:
    def test_same_conditions_give_identical_constraints(self):
        a = derive_dress_code(31, MODERATE_RAIN, 12, 90, daily_low_c=25)
        b = derive_dress_code(31, MODERATE_RAIN, 12, 90, daily_low_c=25)
        assert a == b

    def test_no_duplicate_entries(self):
        dc = derive_dress_code(31, MODERATE_RAIN, 45, 90, daily_low_c=20)
        assert len(dc.require) == len(set(dc.require))
        assert len(dc.avoid) == len(set(dc.avoid))

    def test_require_and_avoid_never_overlap(self):
        for feels in (-5, 5, 14, 20, 28, 38):
            for code in (CLEAR, PARTLY_CLOUDY, MODERATE_RAIN, THUNDERSTORM, HEAVY_SNOW):
                dc = derive_dress_code(feels, code, 10, 50)
                assert not set(dc.require) & set(dc.avoid), f"contradiction at {feels}C code={code}"
