"""
Tests for region-scoped classification label banks.

Segmentation reports which body region each cutout came from, and the classifier
scores that cutout only against labels the region can plausibly contain. Without
the constraint, a shoe crop is scored against all ~157 labels and can land on
"blouse". These tests pin the scoping.

Run: pytest backend/tests/test_region_label_banks.py -v
"""

import sys
from pathlib import Path

import pytest

# ml/ lives at the repository root, beside backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.classification.model import (  # noqa: E402
    CATEGORY_LABELS,
    CATEGORY_MAP,
    labels_for_region,
)


class TestBankScoping:
    def test_every_region_is_narrower_than_the_full_bank(self):
        for region in ("top", "outerwear", "bottom", "shoes", "bag", "dress", "headwear"):
            assert len(labels_for_region(region)) < len(CATEGORY_LABELS)

    def test_unknown_and_flatlay_regions_get_the_full_bank(self):
        assert labels_for_region(None) == CATEGORY_LABELS
        assert labels_for_region("garment") == CATEGORY_LABELS
        assert labels_for_region("nonsense") == CATEGORY_LABELS

    @pytest.mark.parametrize(
        "region, expected, forbidden",
        [
            ("shoes",     "sneakers",  "blouse"),
            ("shoes",     "boots",     "jeans"),
            ("bottom",    "jeans",     "t-shirt"),
            ("top",       "t-shirt",   "jeans"),
            ("bag",       "handbag",   "sneakers"),
            ("headwear",  "beanie",    "trousers"),
            ("outerwear", "denim jacket", "sneakers"),
        ],
    )
    def test_region_contains_the_right_labels_only(self, region, expected, forbidden):
        bank = labels_for_region(region)
        assert expected in bank
        assert forbidden not in bank

    def test_dress_region_offers_dresses_and_traditional_wear(self):
        bank = labels_for_region("dress")
        assert "maxi dress" in bank
        assert "kurta" in bank
        assert "sneakers" not in bank

    def test_bottom_region_admits_dresses(self):
        # CLIPSeg reads a knee-length dress as the lower region; FashionCLIP is
        # then the one that settles "midi skirt vs shirt dress".
        bank = labels_for_region("bottom")
        assert "midi skirt" in bank
        assert "shirt dress" in bank


class TestBankIntegrity:
    def test_every_label_in_every_bank_is_a_real_label(self):
        for region in ("top", "outerwear", "bottom", "shoes", "bag", "dress"):
            for label in labels_for_region(region):
                assert label in CATEGORY_LABELS, f"{label!r} in {region} bank is not a known label"

    def test_no_bank_is_ever_empty(self):
        for region in ("top", "outerwear", "bottom", "shoes", "bag", "dress", "headwear",
                       "garment", None, "made-up"):
            assert labels_for_region(region), f"region {region!r} produced an empty bank"

    def test_every_category_label_maps_to_a_broad_category(self):
        missing = [lbl for lbl in CATEGORY_LABELS if lbl not in CATEGORY_MAP]
        assert not missing, f"labels with no CATEGORY_MAP entry: {missing}"

    def test_regions_partition_the_wearable_categories(self):
        # Every garment slot the visualiser renders must be reachable from a
        # region, or items of that kind could never be classified correctly.
        reachable = set()
        for region in ("top", "outerwear", "bottom", "shoes", "dress"):
            reachable |= {CATEGORY_MAP[lbl] for lbl in labels_for_region(region)}
        for essential in ("shirt", "pants", "shoes", "jacket", "dress", "skirt", "sweater"):
            assert essential in reachable
