import { apiFetch, USE_MOCKS } from "./client";
import type { ChatMessage } from "@/types";

const REPLIES: Record<string, string> = {
  "rooftop dinner": "For a rooftop dinner, wear your Clay Linen Shirt with Sand Pleated Trousers and Canvas Court Sneakers.",
  "client meeting": "For a client meeting, your Charcoal Wool Skirt with Cream Silk Blouse and Brass Buckle Loafers reads sharp.",
  "rainy commute": "For a rainy commute, layer your Waxed Field Jacket over the Indigo Straight Denim with Canvas Court Sneakers.",
};

export async function askStylist(query: string): Promise<ChatMessage> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 900));
    const key = Object.keys(REPLIES).find((k) => query.toLowerCase().includes(k)) ?? "rooftop dinner";
    return {
      id: crypto.randomUUID(),
      role: "assistant",
      text: REPLIES[key],
      look: { top: "top", bottom: "bottom", shoes: "shoes" },
    };
  }
  return apiFetch<ChatMessage>("/stylist/ask", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}
