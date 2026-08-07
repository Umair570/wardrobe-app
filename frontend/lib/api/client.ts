import { supabase } from "@/lib/supabase";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

/**
 * Get the current Supabase access token for authenticated requests.
 */
async function getAuthToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

/**
 * Thin fetch wrapper that forwards the Supabase JWT to the backend.
 * For FormData bodies, the Content-Type header is omitted so the browser
 * sets the correct multipart boundary automatically.
 */
export async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  if (!BASE_URL) {
    throw new ApiError("NEXT_PUBLIC_API_BASE_URL not configured", 501);
  }

  const token = await getAuthToken();
  const headers: Record<string, string> = {};

  // Only set Content-Type for non-FormData bodies
  const isFormData = init?.body instanceof FormData;
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { ...headers, ...(init?.headers ?? {}) },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(text, res.status);
  }

  return res.json() as Promise<T>;
}
