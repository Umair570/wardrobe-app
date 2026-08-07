import topKnit from "@/assets/items/top-cream-knit.png";
import bottomTrousers from "@/assets/items/bottom-black-trousers.png";
import shoesLoafers from "@/assets/items/shoes-black-loafers.png";
import outerCoat from "@/assets/items/outer-green-coat.png";
import type { WardrobeItem } from "@/lib/types";

export const demoWardrobe: WardrobeItem[] = [
  {
    id: "top-1",
    name: "Ribbed Cashmere Knit",
    category: "top",
    original_url: topKnit,
    cutout_url: topKnit,
    color: "Cream",
    season: "Autumn / Winter",
    tags: ["Knitwear", "Minimal", "Layering"],
  },
  {
    id: "top-2",
    name: "Poplin Overshirt",
    category: "top",
    original_url: topKnit,
    cutout_url: topKnit,
    color: "Ivory",
    season: "All season",
    tags: ["Cotton", "Relaxed"],
  },
  {
    id: "bottom-1",
    name: "Pleated Wide Trouser",
    category: "bottom",
    original_url: bottomTrousers,
    cutout_url: bottomTrousers,
    color: "Black",
    season: "All season",
    tags: ["Tailored", "Evening"],
  },
  {
    id: "bottom-2",
    name: "Straight Wool Pant",
    category: "bottom",
    original_url: bottomTrousers,
    cutout_url: bottomTrousers,
    color: "Charcoal",
    season: "Winter",
    tags: ["Wool", "Office"],
  },
  {
    id: "shoes-1",
    name: "Polished Penny Loafer",
    category: "shoes",
    original_url: shoesLoafers,
    cutout_url: shoesLoafers,
    color: "Black",
    season: "All season",
    tags: ["Leather", "Formal"],
  },
  {
    id: "outer-1",
    name: "Forest Wool Overcoat",
    category: "outerwear",
    original_url: outerCoat,
    cutout_url: outerCoat,
    color: "Forest Green",
    season: "Winter",
    tags: ["Statement", "Wool", "Longline"],
  },
];