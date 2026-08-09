import { supabase } from "./supabase";

const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { data } = (await supabase?.auth.getSession()) ?? { data: { session: null } };
  const headers = new Headers(init.headers);
  if (data.session?.access_token) headers.set("Authorization", `Bearer ${data.session.access_token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");

  const response = await fetch(`${apiUrl}/api/v1${path}`, { ...init, headers });
  if (!response.ok) {
    let message = "The request could not be completed.";
    try {
      const payload = (await response.json()) as { detail?: string | Array<{ msg: string }> };
      message = Array.isArray(payload.detail)
        ? payload.detail.map((item) => item.msg).join(" ")
        : payload.detail ?? message;
    } catch {
      // Preserve the fallback message for non-JSON gateway responses.
    }
    throw new ApiError(response.status, message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
