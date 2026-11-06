import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { api, streamUrl, subtitleUrl } from '../lib/api'
import { activeCue, parseSrt, type Cue } from '../lib/subtitles'
import type { Video } from '../lib/types'
import './WatchPage.css'

type SubtitleFormat = 'off' | 'vtt' | 'srt'

export function WatchPage() {
  const { videoId } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const videoRef = useRef<HTMLVideoElement>(null)
  const resumeAt = useRef(0)
  const shouldPlay = useRef(true)
  const [video, setVideo] = useState<Video | null>(null)
  const [quality, setQuality] = useState('720p')
  const [subtitleChoice, setSubtitleChoice] = useState<SubtitleFormat | null>(null)
  const [srt, setSrt] = useState<{ videoId: string; cues: Cue[] } | null>(null)
  const [overlay, setOverlay] = useState<Cue | null>(null)
  const [favorite, setFavorite] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Until the viewer picks one, use the first format the catalog lists for this video.
  const subtitleFormat = subtitleChoice ?? (video?.subtitle_formats[0] as SubtitleFormat | undefined) ?? 'off'

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

  useEffect(() => {
    if (!videoId || subtitleFormat !== 'srt') return
    fetch(subtitleUrl(videoId, 'fr', 'srt'))
      .then((res) => res.text())
      .then((raw) => setSrt({ videoId, cues: parseSrt(raw) }))
      .catch(() => setSrt(null))
  }, [videoId, subtitleFormat])

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

  function handleTimeUpdate() {
    if (subtitleFormat !== 'srt' || srt === null || srt.videoId !== videoId) return
    setOverlay(activeCue(srt.cues, videoRef.current?.currentTime ?? 0) ?? null)
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
      <div className="watch-player-wrap">
        <video
          ref={videoRef}
          className="watch-player"
          src={streamUrl(videoId, quality)}
          controls
          autoPlay
          crossOrigin="anonymous"
          onLoadedMetadata={handleLoadedMetadata}
          onTimeUpdate={handleTimeUpdate}
        >
          {subtitleFormat === 'vtt'
            ? video.subtitle_langs.map((lang) => (
                <track
                  key={lang}
                  kind="subtitles"
                  src={subtitleUrl(videoId, lang, 'vtt')}
                  srcLang={lang}
                  label={lang}
                  default
                />
              ))
            : null}
        </video>
        {subtitleFormat === 'srt' && overlay ? (
          <div className="watch-srt-overlay" style={overlay.color ? { color: overlay.color } : undefined}>
            {overlay.text}
          </div>
        ) : null}
      </div>
      <div className="watch-meta">
        <div>
          <h1>{video.title}</h1>
          <p className="watch-description">{video.description}</p>
          <div className="watch-tags">
            {video.tags.map((tag) => (
              <Link key={tag} className="watch-tag" to={`/?tag=${encodeURIComponent(tag)}`}>
                {tag}
              </Link>
            ))}
          </div>
        </div>
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
          <label>
            Sous-titres
            <select
              value={subtitleFormat}
              onChange={(event) => setSubtitleChoice(event.target.value as SubtitleFormat)}
            >
              <option value="off">Off</option>
              {video.subtitle_formats.map((format) => (
                <option key={format} value={format}>
                  {format.toUpperCase()}
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={() => void toggleFavorite()}>
            {user ? (favorite ? 'Retirer des favoris' : 'Ajouter aux favoris') : 'Favori (compte requis)'}
          </button>
        </div>
      </div>
    </>
  )
}
