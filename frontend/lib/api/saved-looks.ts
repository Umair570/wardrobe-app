import { apiFetch } from "./client";
import type { SavedLook } from "@/types";

interface BackendSavedLook {
  id: string;
  name: string;
  tag: string;
  item_ids?: string[];
  images?: string[];
  favorited?: boolean;
  created_at?: string;
}

function toSavedLook(doc: BackendSavedLook): SavedLook {
  return {
    id: doc.id,
    name: doc.name,
    tag: doc.tag,
    images: doc.images || [],
    favorited: doc.favorited || false,
    itemIds: doc.item_ids || [],
  };
}

export async function getSavedLooks(): Promise<SavedLook[]> {
  const data = await apiFetch<BackendSavedLook[]>("/saved-looks/");
  return data.map(toSavedLook);
}

export async function saveLook(
  name: string,
  tag: string,
  itemIds: string[],
): Promise<SavedLook> {
  const data = await apiFetch<BackendSavedLook>("/saved-looks/", {
    method: "POST",
    body: JSON.stringify({ name, tag, item_ids: itemIds }),
  });
  return toSavedLook(data);
}

export async function toggleLookFavorite(lookId: string): Promise<{ favorited: boolean }> {
  return apiFetch(`/saved-looks/${lookId}/favorite`, { method: "PATCH" });
}

export async function deleteSavedLook(lookId: string): Promise<void> {
  await apiFetch(`/saved-looks/${lookId}`, { method: "DELETE" });
}
