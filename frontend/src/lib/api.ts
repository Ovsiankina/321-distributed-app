import type { User, Video } from './types'

// Every route follows the Gateway contract (docs/api/gateway.openapi.yaml).

const TOKEN_KEY = 'stream321_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body) headers.set('Content-Type', 'application/json')
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(path, { ...init, headers })
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
  videos: () => request<{ items: Video[]; total: number }>('/api/catalog/videos'),
  featured: () => request<{ items: Video[] }>('/api/catalog/featured'),
  search: (q: string) =>
    request<{ items: Video[]; q: string }>(`/api/catalog/search?q=${encodeURIComponent(q)}`),
  video: (id: string) => request<Video>(`/api/catalog/videos/${encodeURIComponent(id)}`),
  login: (email: string, password: string) =>
    request<TokenResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string) =>
    request<TokenResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<User>('/api/auth/me'),
  favorites: () => request<{ video_ids: string[]; videos: Video[] }>('/api/auth/favorites'),
  addFavorite: (id: string) =>
    request<{ ok: boolean; video_id: string }>(`/api/auth/favorites/${encodeURIComponent(id)}`, {
      method: 'POST',
    }),
  removeFavorite: (id: string) =>
    request<void>(`/api/auth/favorites/${encodeURIComponent(id)}`, { method: 'DELETE' }),
}

export function streamUrl(videoId: string, quality: string): string {
  return `/api/stream/${encodeURIComponent(videoId)}?quality=${encodeURIComponent(quality)}`
}
