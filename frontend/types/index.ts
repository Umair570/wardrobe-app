export type Category =
  | "Top"
  | "Bottom"
  | "Outerwear"
  | "Shoes"
  | "Accessory"
  | "Dresses"
  | string; // Backend may return other categories

/**
 * Matches backend WardrobeItemOut schema.
 * `name` and `meta` are derived on the frontend from backend fields.
 */
export interface ClothingItem {
  id: string;
  name: string;          // derived: type ?? category ?? "Garment"
  category: Category;
  colorHex: string;      // derived from `color` field
  meta: string;          // derived: "COLOR · STYLE · SEASON"
  imageUrl?: string;     // mapped from backend image_url or segmentation_path
  favorited?: boolean;

  // Raw backend fields kept for downstream use (try-on, visualization)
  type?: string | null;
  style?: string | null;
  season?: string | null;
  pattern?: string | null;
  color?: string | null;
  tags?: string[];
  segmentationPath?: string | null;
}

export interface OutfitRecommendation {
  id: string;
  title: string;
  match: number;
  hint?: string;
}

export interface SavedLook {
  id: string;
  name: string;
  tag: string;
  favorited?: boolean;
  images: string[];
  itemIds?: string[];
}

export interface ActivityEvent {
  id: string;
  label: string;
  timestamp: string;
  kind: "add" | "query" | "favorite" | "delete" | "tryon";
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  look?: { top: string; bottom: string; shoes: string };
  outfits?: OutfitOption[];
  sessionId?: string;
}

export interface OutfitOption {
  title: string;
  rationale: string;
  top_id?: string | null;
  bottom_id?: string | null;
  outerwear_id?: string | null;
  shoes_id?: string | null;
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  bodyPhotoUrl?: string;
  stats: { itemsInCloset: number; looksSaved: number; stylistQueries: number };
  preferences: string[];
}
