import type { Video } from '../data/videos'

export function filterVideosByTag(videos: Video[], tag: string | null): Video[] {
  if (!tag) return videos
  return videos.filter((video) => video.tags.includes(tag))
}

export function getAllTags(videos: Video[]): string[] {
  return Array.from(new Set(videos.flatMap((video) => video.tags))).sort()
}
