import type { User, Video } from './types'

// Contrat public : /api/v2 (docs/api/gateway.openapi.yaml). La Gateway retire /v2.
const API_BASE = '/api/v2'

const TOKEN_KEY = '321-distributed-app_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

let handleUnauthorized = () => {}

// Lets the auth context log out when the server rejects the stored token (expired after 1 h).
export function onUnauthorized(handler: () => void): void {
  handleUnauthorized = handler
}

// `authed` routes are the bearerAuth ones in the contract: only they carry the token, and only
// their 401 means a rejected session (login answers 401 for a wrong password).
async function request<T>(path: string, init: RequestInit = {}, authed = false): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body) headers.set('Content-Type', 'application/json')
  const token = authed ? getToken() : null
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(path, { ...init, headers })
  if (response.status === 401 && token) {
    setToken(null)
    handleUnauthorized()
  }
  if (response.status === 204) return undefined as T
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Erreur réseau')
  }
  return data as T
}

interface TokenResponse {
  token: string
  email: string
  expires_in_hours: number
}

export const api = {
  videos: () => request<{ items: Video[]; total: number }>(`${API_BASE}/catalog/videos`),
  featured: () => request<{ items: Video[] }>(`${API_BASE}/catalog/featured`),
  search: (q: string) =>
    request<{ items: Video[]; q: string }>(
      `${API_BASE}/catalog/search?q=${encodeURIComponent(q)}`,
    ),
  video: (id: string) =>
    request<Video>(`${API_BASE}/catalog/videos/${encodeURIComponent(id)}`),
  login: (email: string, password: string) =>
    request<TokenResponse>(`${API_BASE}/auth/login`, {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string) =>
    request<TokenResponse>(`${API_BASE}/auth/register`, {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<User>(`${API_BASE}/auth/me`, {}, true),
  favorites: () =>
    request<{
      video_ids: string[]
      videos: { id: string; title: string; channel_id: string }[]
    }>(`${API_BASE}/auth/favorites`, {}, true),
  addFavorite: (id: string) =>
    request<{ ok: boolean; video_id: string }>(
      `${API_BASE}/auth/favorites/${encodeURIComponent(id)}`,
      { method: 'POST' },
      true,
    ),
  removeFavorite: (id: string) =>
    request<void>(
      `${API_BASE}/auth/favorites/${encodeURIComponent(id)}`,
      { method: 'DELETE' },
      true,
    ),
}

export function streamUrl(videoId: string, quality: string): string {
  return `${API_BASE}/stream/${encodeURIComponent(videoId)}?quality=${encodeURIComponent(quality)}`
}
