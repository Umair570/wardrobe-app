import { apiFetch, USE_MOCKS } from "./client";
import type { ClothingItem, OutfitRecommendation, SavedLook, ActivityEvent } from "@/types";

const MOCK_ITEMS: ClothingItem[] = [
  { id: "necklace", name: "Brass Chain Necklace", category: "Accessory", colorHex: "#C9A45C", meta: "BRASS · OS · ALL SEASON" },
  { id: "skirt", name: "Charcoal Wool Skirt", category: "Bottom", colorHex: "#2A2A2A", meta: "WOOL · S · AUTUMN" },
  { id: "sneakers", name: "Canvas Court Sneakers", category: "Shoes", colorHex: "#F1EEE7", meta: "CANVAS · 9 · SUMMER" },
  { id: "linenshirt", name: "Clay Linen Shirt", category: "Top", colorHex: "#B5502F", meta: "LINEN · M · SUMMER" },
  { id: "trouser", name: "Sand Pleated Trouser", category: "Bottom", colorHex: "#D8CBA8", meta: "COTTON TWILL · 31 · SPRING" },
  { id: "blouse", name: "Cream Silk Blouse", category: "Top", colorHex: "#F4EFE4", meta: "SILK · S · ALL SEASON" },
  { id: "denim", name: "Indigo Straight Denim", category: "Bottom", colorHex: "#33415C", meta: "SELVEDGE DENIM · 31 · ALL SEASON" },
  { id: "jacket", name: "Waxed Field Jacket", category: "Outerwear", colorHex: "#3E4635", meta: "WAXED COTTON · M · AUTUMN" },
];

const MOCK_RECS: OutfitRecommendation[] = [
  { id: "brunch", title: "Weekend brunch", match: 94 },
  { id: "meeting", title: "Client meeting", match: 89 },
  { id: "evening", title: "Evening out", match: 97 },
];

const MOCK_LOOKS: SavedLook[] = [
  { id: "weekend", name: "Weekend brunch", tag: "WEEKEND", favorited: true, images: [] },
  { id: "meeting", name: "Client meeting", tag: "WORK", images: [] },
  { id: "dinner", name: "Rooftop dinner", tag: "EVENING", favorited: true, images: [] },
  { id: "commute", name: "Rainy commute", tag: "WORK", images: [] },
  { id: "gallery", name: "Gallery opening", tag: "EVENING", images: [] },
  { id: "errands", name: "Saturday errands", tag: "WEEKEND", images: [] },
];

const MOCK_ACTIVITY: ActivityEvent[] = [
  { id: "1", label: "Added **Cashmere Sweater** to your closet", timestamp: "2h ago", kind: "add" },
  { id: "2", label: "Asked stylist for a **rooftop dinner** outfit", timestamp: "Yesterday", kind: "query" },
  { id: "3", label: "Favorited **Silk Slip Dress**", timestamp: "2 days ago", kind: "favorite" },
];

export async function getClothingItems(): Promise<ClothingItem[]> {
  if (USE_MOCKS) return MOCK_ITEMS;
  return apiFetch<ClothingItem[]>("/wardrobe/items");
}

export async function getRecommendations(): Promise<OutfitRecommendation[]> {
  if (USE_MOCKS) return MOCK_RECS;
  return apiFetch<OutfitRecommendation[]>("/wardrobe/recommendations");
}

export async function getSavedLooks(): Promise<SavedLook[]> {
  if (USE_MOCKS) return MOCK_LOOKS;
  return apiFetch<SavedLook[]>("/wardrobe/saved-looks");
}

export async function getActivity(): Promise<ActivityEvent[]> {
  if (USE_MOCKS) return MOCK_ACTIVITY;
  return apiFetch<ActivityEvent[]>("/wardrobe/activity");
}

export async function uploadGarment(file: File): Promise<{ ok: boolean; taggedName?: string }> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 800));
    return { ok: true, taggedName: "Navy Cotton Tee" };
  }
  const form = new FormData();
  form.append("file", file);
  return apiFetch("/wardrobe/upload", { method: "POST", body: form });
}
