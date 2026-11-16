import { describe, expect, it } from 'vitest'
import type { Video } from './types'
import { filterVideosByTag, getAllTags } from './videoFilters'

function video(id: string, tags: string[]): Video {
  return {
    id,
    title: id,
    description: '',
    tags,
    duration_seconds: 60,
    thumbnail_url: '',
    qualities: [],
    featured: false,
    subtitle_langs: [],
    stream_modes: [],
    subtitle_formats: [],
  }
}

const videos: Video[] = [
  video('1', ['tech', 'science']),
  video('2', ['musique']),
  video('3', ['tech']),
]

describe('filterVideosByTag', () => {
  it('returns all videos when tag is null', () => {
    expect(filterVideosByTag(videos, null)).toEqual(videos)
  })

  it('returns only videos matching the given tag', () => {
    expect(filterVideosByTag(videos, 'tech')).toEqual([videos[0], videos[2]])
  })

  it('returns an empty array when no video matches the tag', () => {
    expect(filterVideosByTag(videos, 'inexistant')).toEqual([])
  })
})

describe('getAllTags', () => {
  it('returns the sorted list of unique tags across all videos', () => {
    expect(getAllTags(videos)).toEqual(['musique', 'science', 'tech'])
  })
})
