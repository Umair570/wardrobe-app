import { apiFetch } from "./client";

interface ProfileOut {
  user_id: string;
  email?: string | null;
  display_name?: string | null;
  avatar_url?: string | null;
  body_photo_url?: string | null;
  updated_at?: string | null;
}

export async function getProfile(): Promise<ProfileOut> {
  return apiFetch<ProfileOut>("/profile/");
}

export async function uploadBodyPhoto(file: File): Promise<ProfileOut> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<ProfileOut>("/profile/body-photo", {
    method: "POST",
    body: form,
  });
}

export async function deleteBodyPhoto(): Promise<void> {
  await apiFetch("/profile/body-photo", { method: "DELETE" });
}
