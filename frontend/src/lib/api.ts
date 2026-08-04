import type { WardrobeItem } from "@/lib/types";
import { supabase } from "./supabase";

const BASE = import.meta.env['VITE_API_BASE_URL'] as string | undefined;

async function getAuthHeaders(): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession();
  if (data.session) {
    return {
      Authorization: `Bearer ${data.session.access_token}`,
    };
  }
  return {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!BASE) throw new Error("offline");

  const authHeaders = await getAuthHeaders();

  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
      ...(init?.headers ?? {})
    },
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Request failed: ${res.status} - ${errText}`);
  }
  return (await res.json()) as T;
}

/** GET /api/v1/wardrobe/ — fetches user's wardrobe from backend */
export async function fetchWardrobe(): Promise<WardrobeItem[]> {
  try {
    const data = await request<any[]>("/api/v1/wardrobe/");
    return data.map((item) => ({
      ...item,
      name: item.type || item.category || "Garment",
      original_url: item.image_url || item.source_image,
      cutout_url: item.segmentation_path || item.image_url,
    }));
  } catch (err) {
    console.error("Failed to fetch wardrobe:", err);
    return [];
  }
}

/** POST /api/v1/ingest — uploads a garment photo for background removal + embedding. */
export async function ingestGarment(file: File): Promise<{ ok: boolean }> {
  if (!BASE) {
    await new Promise((r) => setTimeout(r, 1400));
    return { ok: true };
  }

  const authHeaders = await getAuthHeaders();
  const body = new FormData();
  body.append("file", file);

  const res = await fetch(`${BASE}/api/v1/ingest/`, {
    method: "POST",
    body,
    headers: {
      ...authHeaders
    }
  });

  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);

  const data = await res.json();
  const jobId = data.job_id;

  if (jobId) {
    // Poll job status until done or failed (up to 180 seconds to allow ML models to download/run on CPU)
    for (let i = 0; i < 180; i++) {
      await new Promise((r) => setTimeout(r, 1000));
      try {
        const pollRes = await fetch(`${BASE}/api/v1/ingest/${jobId}`, {
          headers: { ...authHeaders }
        });
        if (pollRes.ok) {
          const pollData = await pollRes.json();
          if (pollData.status === "done") {
            return { ok: true };
          }
          if (pollData.status === "failed") {
            throw new Error(`Ingestion failed: ${pollData.error || "Unknown error"}`);
          }
        }
      } catch (err) {
        if (i === 179) throw err;
      }
    }
  }

  return { ok: true };
}

export interface ChatResponse {
  reply: string;
  outfit: {
    top_id: string | null;
    bottom_id: string | null;
    outerwear_id: string | null;
    shoes_id: string | null;
  };
  session_id?: string;
}

export interface ChatSession {
  session_id: string;
  title: string;
  updated_at: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  messages: Array<{
    id: string;
    role: string;
    content: string;
    outfit?: any;
  }>;
}

/** POST /api/v1/chat — AI stylist reply plus a suggested outfit. */
export async function askStylist(
  prompt: string,
  items: WardrobeItem[],
  session_id?: string
): Promise<ChatResponse> {
  try {
    return await request<ChatResponse>("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({ message: prompt, session_id }),
    });
  } catch (err) {
    console.error("Stylist API failed:", err);
    throw err;
  }
}

/** GET /api/v1/chat/sessions — fetch all user chat sessions */
export async function fetchSessions(): Promise<ChatSession[]> {
  try {
    return await request<ChatSession[]>("/api/v1/chat/sessions");
  } catch (err) {
    console.error("fetchSessions failed:", err);
    return [];
  }
}

/** GET /api/v1/chat/sessions/{id} — fetch chat history */
export async function fetchSessionHistory(session_id: string): Promise<ChatHistoryResponse | null> {
  try {
    return await request<ChatHistoryResponse>(`/api/v1/chat/sessions/${session_id}`);
  } catch (err) {
    console.error("fetchSessionHistory failed:", err);
    return null;
  }
}


export interface UserProfile {
  user_id: string;
  email?: string;
  display_name?: string;
  avatar_url?: string;
  body_photo_url?: string;
  updated_at?: string;
}

/** GET /api/v1/profile — fetch the current user's profile */
export async function fetchProfile(): Promise<UserProfile | null> {
  if (!BASE) return null;
  try {
    return await request<UserProfile>("/api/v1/profile/");
  } catch (err) {
    console.error("fetchProfile failed:", err);
    return null;
  }
}

/** POST /api/v1/profile/body-photo — upload user body photo for virtual try-on */
export async function uploadBodyPhoto(file: File, saveProfile: boolean = true): Promise<UserProfile> {
  if (!BASE) throw new Error("offline");
  const authHeaders = await getAuthHeaders();
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${BASE}/api/v1/profile/body-photo?save_profile=${saveProfile}`, {
    method: "POST",
    body,
    headers: { ...authHeaders },
  });
  if (!res.ok) throw new Error(`Body photo upload failed: ${res.status}`);
  return (await res.json()) as UserProfile;
}

/** DELETE /api/v1/profile/body-photo — remove user body photo */
export async function deleteBodyPhoto(): Promise<void> {
  await request("/api/v1/profile/body-photo", { method: "DELETE" });
}

/** POST /api/v1/visualization — Virtual Try-On generation */
export async function generateTryOn(itemIds: string[], userBodyPhotoUrl: string, mode = "ai"): Promise<{ ai_image_url: string }> {
  return await request<{ ai_image_url: string }>("/api/v1/visualization", {
    method: "POST",
    body: JSON.stringify({ item_ids: itemIds, user_body_photo_url: userBodyPhotoUrl, mode }),
  });
}