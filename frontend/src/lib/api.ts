import { demoWardrobe } from "@/data/wardrobe";
import type { ChatResponse, WardrobeItem } from "@/lib/types";
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
    console.error("Failed to fetch wardrobe, falling back to demo:", err);
    return demoWardrobe;
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
    // Poll job status until done or failed (up to 45 seconds)
    for (let i = 0; i < 45; i++) {
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
        if (i === 44) throw err;
      }
    }
  }

  return { ok: true };
}

/** POST /api/v1/chat — AI stylist reply plus a suggested outfit. */
export async function askStylist(prompt: string, items: WardrobeItem[]): Promise<ChatResponse> {
  try {
    return await request<ChatResponse>("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({ message: prompt }),
    });
  } catch (err) {
    console.error("Stylist API failed, falling back to mock:", err);
    await new Promise((r) => setTimeout(r, 1100));
    const pick = (c: string) => items.find((i) => i.category === c)?.id ?? null;
    return {
      reply: `Here's a look for "${prompt}": the cream knit softens the black tailoring, with the forest overcoat as the statement layer.`,
      outfit: {
        top_id: pick("top"),
        bottom_id: pick("bottom"),
        outerwear_id: pick("outerwear"),
        shoes_id: pick("shoes"),
      },
    };
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
export async function uploadBodyPhoto(file: File): Promise<UserProfile> {
  if (!BASE) throw new Error("offline");
  const authHeaders = await getAuthHeaders();
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${BASE}/api/v1/profile/body-photo`, {
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