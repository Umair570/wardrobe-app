"""
Tests for the agent's final-answer validation.

The model is not trusted to place items correctly. `_build_response` re-derives
every slot from the item's own attributes and discards anything the tools never
returned, so a hallucinated or misplaced ID cannot reach the visualiser.

Run: pytest backend/tests/test_agent_validation.py -v
"""

import pytest

from app.services.agent.agent_service import _build_response, _fallback_response, _variety_shortfall
from app.services.agent.tools import ToolContext
from app.services.stylist.prompt_builder import slot_for_attributes


@pytest.fixture
def ctx():
    context = ToolContext(user_id="u1")
    context.remember([
        {"id": "tee",    "category": "shirt",  "type": "t-shirt"},
        {"id": "blouse", "category": "shirt",  "type": "blouse"},
        {"id": "jeans",  "category": "pants",  "type": "jeans"},
        {"id": "skirt",  "category": "skirt",  "type": "midi skirt"},
        {"id": "coat",   "category": "jacket", "type": "trench coat"},
        {"id": "boots",  "category": "shoes",  "type": "ankle boots"},
        {"id": "purse",  "category": "bag",    "type": "handbag"},
    ])
    return context


def _one(outfit: dict) -> dict:
    return {"message": "here you go", "outfits": [outfit]}


class TestSlotAssignment:
    @pytest.mark.parametrize(
        "category, type_, expected",
        [
            ("jacket", "trench coat", "outerwear"),
            ("shoes", "ankle boots", "shoes"),
            ("pants", "jeans", "bottom"),
            ("skirt", "midi skirt", "bottom"),
            ("shorts", "denim shorts", "bottom"),
            ("shirt", "blouse", "top"),
            ("sweater", "hoodie", "top"),
            ("dress", "maxi dress", "top"),
            ("bag", "handbag", "other"),
            ("accessory", "beanie", "other"),
        ],
    )
    def test_category_drives_slot(self, category, type_, expected):
        assert slot_for_attributes(category, type_) == expected

    def test_unknown_category_falls_back_to_type(self):
        assert slot_for_attributes(None, "denim jacket") == "outerwear"
        assert slot_for_attributes("", "chelsea boots") == "shoes"
        assert slot_for_attributes("", "chinos") == "bottom"


class TestBuildResponse:
    def test_well_formed_outfit_passes_through(self, ctx):
        r = _build_response(ctx, _one({
            "title": "Casual", "rationale": "why",
            "top_id": "tee", "bottom_id": "jeans",
            "outerwear_id": "coat", "shoes_id": "boots",
        }))
        o = r.outfits[0]
        assert (o.top_id, o.bottom_id, o.outerwear_id, o.shoes_id) == ("tee", "jeans", "coat", "boots")

    def test_hallucinated_id_is_dropped(self, ctx):
        r = _build_response(ctx, _one({"top_id": "does-not-exist", "bottom_id": "jeans"}))
        assert r.outfits[0].top_id is None
        assert r.outfits[0].bottom_id == "jeans"

    def test_skirt_in_top_slot_is_moved_to_bottom(self, ctx):
        # Observed with weaker models: a skirt handed back as `top_id` would be
        # rendered across the torso by the overlay.
        r = _build_response(ctx, _one({"top_id": "skirt", "shoes_id": "boots"}))
        o = r.outfits[0]
        assert o.top_id is None
        assert o.bottom_id == "skirt"
        assert o.shoes_id == "boots"

    def test_coat_in_top_slot_is_moved_to_outerwear(self, ctx):
        r = _build_response(ctx, _one({"top_id": "coat", "bottom_id": "jeans"}))
        assert r.outfits[0].top_id is None
        assert r.outfits[0].outerwear_id == "coat"

    def test_bag_is_rejected_from_every_outfit_slot(self, ctx):
        r = _build_response(ctx, _one({"top_id": "purse", "bottom_id": "jeans"}))
        o = r.outfits[0]
        assert "purse" not in o.item_ids()
        assert o.bottom_id == "jeans"

    def test_conflicting_items_keep_only_the_first(self, ctx):
        # Both resolve to `bottom`; the second has nowhere to go.
        r = _build_response(ctx, _one({"bottom_id": "jeans", "top_id": "skirt"}))
        assert r.outfits[0].bottom_id in ("jeans", "skirt")
        assert len(r.outfits[0].item_ids()) == 1

    def test_null_variants_are_treated_as_empty(self, ctx):
        r = _build_response(ctx, _one({
            "top_id": "tee", "bottom_id": None,
            "outerwear_id": "null", "shoes_id": "None",
        }))
        o = r.outfits[0]
        assert o.top_id == "tee"
        assert o.bottom_id is None and o.outerwear_id is None and o.shoes_id is None

    def test_capped_at_three_outfits(self, ctx):
        r = _build_response(ctx, {
            "message": "m",
            "outfits": [{"top_id": "tee"}, {"top_id": "blouse"}, {"bottom_id": "jeans"}, {"bottom_id": "skirt"}],
        })
        assert len(r.outfits) == 3

    def test_duplicate_outfits_are_collapsed_not_repeated(self, ctx):
        # Four raw entries but only two distinct garment combinations — three
        # near-identical shoe-swap "options" is not variety.
        r = _build_response(ctx, {
            "message": "m",
            "outfits": [{"top_id": "tee"}, {"top_id": "blouse"}, {"top_id": "tee"}, {"top_id": "blouse"}],
        })
        assert len(r.outfits) == 2

    def test_empty_outfit_is_not_returned(self, ctx):
        r = _build_response(ctx, _one({"top_id": "ghost", "bottom_id": "ghost2"}))
        assert r.outfits == []

    def test_message_is_always_preserved(self, ctx):
        r = _build_response(ctx, {"message": "Nothing suitable.", "outfits": []})
        assert r.message == "Nothing suitable."

    def test_primary_mirrors_first_outfit(self, ctx):
        r = _build_response(ctx, _one({"top_id": "tee", "bottom_id": "jeans"}))
        assert r.primary.top_id == "tee"
        assert r.primary.bottom_id == "jeans"

    def test_primary_is_empty_when_no_outfits(self, ctx):
        r = _build_response(ctx, {"message": "m", "outfits": []})
        assert r.primary.item_ids() == []


class TestVarietyShortfall:
    def test_flags_when_wardrobe_has_unused_alternatives(self, ctx):
        # ctx has 2 tops and 2 bottoms but only one outfit was produced.
        response = _build_response(ctx, _one({"top_id": "tee", "bottom_id": "jeans"}))
        assert _variety_shortfall(response, ctx) is not None

    def test_silent_when_three_distinct_outfits_exist(self, ctx):
        response = _build_response(ctx, {
            "message": "m",
            "outfits": [
                {"top_id": "tee", "bottom_id": "jeans"},
                {"top_id": "blouse", "bottom_id": "jeans"},
                {"top_id": "tee", "bottom_id": "skirt"},
            ],
        })
        assert _variety_shortfall(response, ctx) is None

    def test_silent_when_wardrobe_cannot_support_more(self):
        # Only one top and one bottom exist — nothing more to ask for.
        thin_ctx = ToolContext(user_id="u2")
        thin_ctx.remember([
            {"id": "tee", "category": "shirt", "type": "t-shirt"},
            {"id": "jeans", "category": "pants", "type": "jeans"},
        ])
        response = _build_response(thin_ctx, _one({"top_id": "tee", "bottom_id": "jeans"}))
        assert _variety_shortfall(response, thin_ctx) is None


class TestFallback:
    def test_fallback_assembles_from_retrieved_items(self, ctx):
        r = _fallback_response(ctx, "fallback message")
        assert r.message == "fallback message"
        assert r.outfits, "should build something from a stocked wardrobe"
        for o in r.outfits:
            assert o.item_ids()

    def test_fallback_respects_slots(self, ctx):
        for o in _fallback_response(ctx, "m").outfits:
            if o.bottom_id:
                assert slot_for_attributes(*_attrs(ctx, o.bottom_id)) == "bottom"
            if o.shoes_id:
                assert slot_for_attributes(*_attrs(ctx, o.shoes_id)) == "shoes"

    def test_fallback_with_nothing_retrieved(self):
        r = _fallback_response(ToolContext(user_id="u1"), "empty")
        assert r.outfits == []
        assert r.message == "empty"


def _attrs(ctx: ToolContext, item_id: str) -> tuple:
    item = ctx.seen_items[item_id]
    return item.get("category"), item.get("type")
