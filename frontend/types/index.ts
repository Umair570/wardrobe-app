export type Category =
  | "Top"
  | "Bottom"
  | "Outerwear"
  | "Shoes"
  | "Accessory"
  | "Dresses";

export interface ClothingItem {
  id: string;
  name: string;
  category: Category;
  colorHex: string;
  meta: string;
  imageUrl?: string;
  favorited?: boolean;
}

export interface OutfitRecommendation {
  id: string;
  title: string;
  match: number;
  hint?: string; // <-- Add the optional '?' mark here
}

export interface SavedLook {
  id: string;
  name: string;
  tag: "WEEKEND" | "WORK" | "EVENING";
  favorited?: boolean;
  images: string[];
}

export interface ActivityEvent {
  id: string;
  label: string;
  timestamp: string;
  kind: "add" | "query" | "favorite";
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  look?: { top: string; bottom: string; shoes: string };
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  stats: { itemsInCloset: number; looksSaved: number; stylistQueries: number };
  preferences: string[];
}
