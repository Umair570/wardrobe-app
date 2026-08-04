export type Category = "top" | "bottom" | "shoes" | "outerwear";

export interface WardrobeItem {
  id: string;
  name: string;
  category: Category;
  original_url: string;
  cutout_url: string;
  color: string;
  season: string;
  tags: string[];
}

export interface OutfitSelection {
  top_id: string | null;
  bottom_id: string | null;
  outerwear_id: string | null;
  shoes_id: string | null;
}

export interface ChatResponse {
  reply: string;
  outfit: OutfitSelection;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}