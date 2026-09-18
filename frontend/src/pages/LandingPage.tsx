import { useMemo, useState } from 'react'
import { TagFilter } from '../components/TagFilter'
import { TopBar } from '../components/TopBar'
import { VideoGrid } from '../components/VideoGrid'
import { videos } from '../data/videos'
import { filterVideosByTag, getAllTags } from '../lib/videoFilters'

export function LandingPage() {
  const [selectedTag, setSelectedTag] = useState<string | null>(null)
  const tags = useMemo(() => getAllTags(videos), [])
  const filteredVideos = useMemo(
    () => filterVideosByTag(videos, selectedTag),
    [selectedTag],
  )

  return (
    <main>
      <TopBar />
      <TagFilter tags={tags} selectedTag={selectedTag} onSelectTag={setSelectedTag} />
      <VideoGrid videos={filteredVideos} />
    </main>
  )
}
