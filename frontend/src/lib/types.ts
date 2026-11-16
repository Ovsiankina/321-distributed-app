export interface Video {
  id: string
  title: string
  description: string
  tags: string[]
  duration_seconds: number
  thumbnail_url: string
  qualities: string[]
  featured: boolean
  subtitle_langs: string[]
  stream_modes: string[]
  subtitle_formats: string[]
}

export interface User {
  id: number
  email: string
}
