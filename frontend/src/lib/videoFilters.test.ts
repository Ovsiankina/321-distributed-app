import { describe, expect, it } from 'vitest'
import type { Video } from '../data/videos'
import { filterVideosByTag, getAllTags } from './videoFilters'

const videos: Video[] = [
  { id: '1', title: 'A', thumbnail: '', duration: '1:00', tags: ['tech', 'science'] },
  { id: '2', title: 'B', thumbnail: '', duration: '2:00', tags: ['musique'] },
  { id: '3', title: 'C', thumbnail: '', duration: '3:00', tags: ['tech'] },
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
