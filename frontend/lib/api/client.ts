// Thin fetch wrapper. Swap NEXT_PUBLIC_API_BASE_URL to point at a real backend;
// every api/* module below falls back to local mock data when no base URL is set,
// so the app runs standalone during frontend development.
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  if (!BASE_URL) {
    throw new ApiError("NEXT_PUBLIC_API_BASE_URL not configured", 501);
  }
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    throw new ApiError(await res.text(), res.status);
  }
  return res.json() as Promise<T>;
}

export const USE_MOCKS = !BASE_URL;
