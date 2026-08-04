import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Category } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const SLOT_KEYWORDS = {
  outerwear: ["jacket", "coat", "outerwear", "blazer", "hoodie", "cardigan"],
  shoes: ["shoe", "boot", "sneaker", "heel", "footwear", "sandal", "loafer"],
  bottom: ["pant", "trouser", "short", "skirt", "jean", "bottom", "legging", "jogger", "culotte"],
  top: ["shirt", "top", "blouse", "t-shirt", "sweater", "dress"]
};

export function getSlot(i: any): Category {
  const text = `${i.category || ""} ${i.type || ""} ${(i.tags || []).join(" ")}`.toLowerCase();

  for (const [slot, keywords] of Object.entries(SLOT_KEYWORDS)) {
    if (keywords.some(kw => text.includes(kw))) {
      return slot as Category;
    }
  }

  return "top"; // Universal fallback
}
