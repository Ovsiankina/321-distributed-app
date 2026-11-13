import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { TagFilter } from '../components/TagFilter'
import { VideoGrid } from '../components/VideoGrid'
import { api } from '../lib/api'
import type { Video } from '../lib/types'
import { filterVideosByTag, getAllTags } from '../lib/videoFilters'
import './LandingPage.css'

export function LandingPage() {
  const [params, setParams] = useSearchParams()
  const selectedTag = params.get('tag')
  const [featured, setFeatured] = useState<Video[]>([])
  const [videos, setVideos] = useState<Video[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api.featured(), api.videos()])
      .then(([featuredRes, videosRes]) => {
        setFeatured(featuredRes.items)
        setVideos(videosRes.items)
      })
      .catch((err: Error) => setError(err.message))
  }, [])

  function selectTag(tag: string | null) {
    setParams(tag ? { tag } : {}, { replace: true })
  }

  if (error) return <p className="error">{error}</p>
  if (videos === null) return <p className="muted">Chargement…</p>

  const sections = [
    { title: 'À la une', videos: filterVideosByTag(featured, selectedTag) },
    { title: 'Toutes les vidéos', videos: filterVideosByTag(videos, selectedTag) },
  ]

  return (
    <>
      <h1>Découvrir</h1>
      <p className="muted">Lecture sans compte.</p>
      <TagFilter tags={getAllTags(videos)} selectedTag={selectedTag} onSelectTag={selectTag} />
      {sections.map((section) => (
        <section key={section.title} className="landing-section">
          <h2>{section.title}</h2>
          {section.videos.length === 0 ? (
            <p className="muted">Aucune vidéo pour ce filtre.</p>
          ) : (
            <VideoGrid videos={section.videos} />
          )}
        </section>
      ))}
    </>
  )
}
