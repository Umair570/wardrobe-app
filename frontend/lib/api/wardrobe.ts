import { apiFetch } from "./client";
import type { ClothingItem, OutfitRecommendation, ActivityEvent } from "@/types";

// ---------------------------------------------------------------------------
// Backend WardrobeItemOut shape (snake_case from FastAPI)
// ---------------------------------------------------------------------------
interface BackendItem {
  id: string;
  user_id?: string;
  category?: string | null;
  type?: string | null;
  style?: string | null;
  season?: string | null;
  pattern?: string | null;
  color?: string | null;
  tags?: string[];
  image_url?: string | null;
  segmentation_path?: string | null;
  area_ratio?: number | null;
  uploaded_at?: string | null;
}

// Simple name-safe colour map for colorHex
const COLOR_HEX_MAP: Record<string, string> = {
  red: "#C0392B", blue: "#2980B9", green: "#27AE60", black: "#1E1E1E",
  white: "#F4EFE4", navy: "#33415C", grey: "#7F8C8D", gray: "#7F8C8D",
  brown: "#8B4513", beige: "#D8CBA8", cream: "#F4EFE4", pink: "#E91E7B",
  orange: "#E67E22", yellow: "#F1C40F", purple: "#8E44AD", gold: "#C9A45C",
  tan: "#D2B48C", olive: "#3E4635", maroon: "#800000", indigo: "#33415C",
  charcoal: "#2A2A2A", sand: "#D8CBA8", clay: "#B5502F", khaki: "#C3B091",
};

function toColorHex(color?: string | null): string {
  if (!color) return "#7F8C8D";
  const lower = color.toLowerCase().trim();
  // Check for direct match
  if (COLOR_HEX_MAP[lower]) return COLOR_HEX_MAP[lower];
  // Check if color name appears as part of a compound like "dark blue"
  for (const [name, hex] of Object.entries(COLOR_HEX_MAP)) {
    if (lower.includes(name)) return hex;
  }
  // If it looks like a hex already
  if (lower.startsWith("#")) return lower;
  return "#7F8C8D";
}

function capitalize(s?: string | null): string {
  if (!s) return "";
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * Transform a backend WardrobeItemOut into the frontend ClothingItem shape.
 */
function backendToClothingItem(item: BackendItem): ClothingItem {
  const name = capitalize(item.type) || capitalize(item.category) || "Garment";
  const metaParts = [
    item.color?.toUpperCase(),
    item.style?.toUpperCase(),
    item.season?.toUpperCase(),
  ].filter(Boolean);

  return {
    id: item.id,
    name,
    category: capitalize(item.category) || "Top",
    colorHex: toColorHex(item.color),
    meta: metaParts.join(" · ") || "GARMENT",
    imageUrl: item.segmentation_path || item.image_url || undefined,
    type: item.type,
    style: item.style,
    season: item.season,
    pattern: item.pattern,
    color: item.color,
    tags: item.tags || [],
    segmentationPath: item.segmentation_path,
  };
}


export async function getClothingItems(): Promise<ClothingItem[]> {
  const data = await apiFetch<BackendItem[]>("/wardrobe/");
  return data.map(backendToClothingItem);
}

export async function getRecommendations(): Promise<OutfitRecommendation[]> {
  return apiFetch<OutfitRecommendation[]>("/wardrobe/recommendations");
}

export async function getActivity(): Promise<ActivityEvent[]> {
  return apiFetch<ActivityEvent[]>("/activity/");
}

export async function deleteItem(itemId: string): Promise<void> {
  await apiFetch(`/wardrobe/${itemId}`, { method: "DELETE" });
}

export async function uploadGarment(file: File): Promise<BackendItem[]> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<BackendItem[]>("/upload/", { method: "POST", body: form });
}

export async function getWardrobeStats(): Promise<{
  items_in_closet: number;
  looks_saved: number;
  stylist_queries: number;
}> {
  return apiFetch("/wardrobe/stats");
}
