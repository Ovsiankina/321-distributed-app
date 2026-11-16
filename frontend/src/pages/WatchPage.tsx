import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { api, streamUrl } from '../lib/api'
import type { Video } from '../lib/types'
import './WatchPage.css'

export function WatchPage() {
  const { videoId } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const videoRef = useRef<HTMLVideoElement>(null)
  const resumeAt = useRef(0)
  const shouldPlay = useRef(true)
  const [video, setVideo] = useState<Video | null>(null)
  const [quality, setQuality] = useState('720p')
  const [favorite, setFavorite] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!videoId) return
    api
      .video(videoId)
      .then(setVideo)
      .catch((err: Error) => setError(err.message))
  }, [videoId])

  useEffect(() => {
    if (!user || !videoId) return
    api
      .favorites()
      .then((res) => setFavorite(res.video_ids.includes(videoId)))
      .catch(() => undefined)
  }, [user, videoId])

  function changeQuality(next: string) {
    const el = videoRef.current
    resumeAt.current = el?.currentTime ?? 0
    shouldPlay.current = el ? !el.paused : true
    setQuality(next)
  }

  function handleLoadedMetadata() {
    const el = videoRef.current
    if (!el) return
    el.currentTime = resumeAt.current
    if (shouldPlay.current) void el.play()
  }

  async function toggleFavorite() {
    if (!videoId) return
    if (!user) {
      navigate('/login')
      return
    }
    if (favorite) {
      await api.removeFavorite(videoId)
    } else {
      await api.addFavorite(videoId)
    }
    setFavorite(!favorite)
  }

  if (error) return <p className="error">{error}</p>
  if (!video || !videoId) return <p className="muted">Chargement…</p>

  return (
    <>
      <video
        ref={videoRef}
        className="watch-player"
        src={streamUrl(videoId, quality)}
        controls
        autoPlay
        onLoadedMetadata={handleLoadedMetadata}
      />
      <h1 className="watch-title">{video.title}</h1>
      <div className="watch-actions">
        <label>
          Qualité
          <select value={quality} onChange={(event) => changeQuality(event.target.value)}>
            {video.qualities.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={() => void toggleFavorite()}>
          {user ? (favorite ? 'Retirer des favoris' : 'Ajouter aux favoris') : 'Favori (compte requis)'}
        </button>
      </div>
      <p className="watch-description">{video.description}</p>
      <div className="watch-tags">
        {video.tags.map((tag) => (
          <Link key={tag} className="watch-tag" to={`/?tag=${encodeURIComponent(tag)}`}>
            {tag}
          </Link>
        ))}
      </div>
    </>
  )
}
