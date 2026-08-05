import { apiFetch } from "./client";
import type { ChatMessage } from "@/types";

interface ChatResponse {
  reply: string;
  outfits?: Array<{
    title: string;
    rationale: string;
    top_id?: string | null;
    bottom_id?: string | null;
    outerwear_id?: string | null;
    shoes_id?: string | null;
  }>;
  outfit?: {
    top_id?: string | null;
    bottom_id?: string | null;
    outerwear_id?: string | null;
    shoes_id?: string | null;
  };
  session_id: string;
  weather?: {
    location: string;
    condition: string;
    temperature_c: number;
  } | null;
  items_retrieved?: number;
  tools_used?: string[];
}

/**
 * Send a message to the AI stylist (POST /chat).
 * Tracks session_id across turns for multi-turn conversation.
 */
export async function askStylist(
  query: string,
  sessionId?: string | null,
  latitude?: number,
  longitude?: number,
): Promise<ChatMessage> {
  const body: Record<string, unknown> = { message: query };
  if (sessionId) body.session_id = sessionId;
  if (latitude != null) body.latitude = latitude;
  if (longitude != null) body.longitude = longitude;

  const data = await apiFetch<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });

  return {
    id: crypto.randomUUID(),
    role: "assistant",
    text: data.reply,
    outfits: data.outfits,
    sessionId: data.session_id,
    look: data.outfit
      ? {
          top: data.outfit.top_id || "",
          bottom: data.outfit.bottom_id || "",
          shoes: data.outfit.shoes_id || "",
        }
      : undefined,
  };
}
