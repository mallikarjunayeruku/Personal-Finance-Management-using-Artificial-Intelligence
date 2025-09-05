// src/lib/api.ts
import { API_BASE } from "../config";

const ACCESS_KEY = "lp_token";
const REFRESH_KEY = "lp_refresh";

// Use undefined (not null) for “no token” to play nicely with Headers
export function getToken(): string | undefined {
  return localStorage.getItem(ACCESS_KEY) ?? undefined;
}
export function getRefresh(): string | undefined {
  return localStorage.getItem(REFRESH_KEY) ?? undefined;
}
export function setToken(access: string, refresh?: string) {
  localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}
export function clearToken() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function refreshAccessToken(): Promise<string> {
  const refresh = getRefresh();
  if (!refresh) {
    clearToken();
    throw new Error("Session expired, please log in again");
  }
  const res = await fetch(`${API_BASE}/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) {
    clearToken();
    throw new Error("Session expired, please log in again");
  }
  const data = await res.json();
  if (!data?.access) throw new Error("Invalid refresh response");
  setToken(data.access, refresh);
  return data.access;
}

export async function api(path: string, init: RequestInit = {}) {
  // small helper that adds headers each time we call it
  const run = async (access?: string): Promise<Response> => {
    const headers = new Headers(init.headers || {});
    // only set content-type when sending a body (won’t break GET with no body)
    if (init.body != null && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    if (access) headers.set("Authorization", `Bearer ${access}`);
    return fetch(`${API_BASE}${path}`, { ...init, headers });
  };

  let access = getToken();
  let res = await run(access);

  if (res.status === 401) {
    // Try refresh once, then retry original request
    access = await refreshAccessToken();
    res = await run(access);
  }

  const text = await res.text();
  let data: any;
  try { data = JSON.parse(text); } catch { data = text; }

  if (!res.ok) {
    const message = data?.detail || (typeof data === "string" ? data : JSON.stringify(data));
    throw new Error(message || `HTTP ${res.status}`);
  }
  return data;
}
