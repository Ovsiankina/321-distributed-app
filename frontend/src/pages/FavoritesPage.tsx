import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { VideoGrid } from '../components/VideoGrid'
import { api } from '../lib/api'
import type { Video } from '../lib/types'

export function FavoritesPage() {
  const { user, ready } = useAuth()
  const [videos, setVideos] = useState<Video[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return
    api
      .favorites()
      .then((res) => setVideos(res.videos))
      .catch((err: Error) => setError(err.message))
  }, [user])

  if (!ready) return <p className="muted">Chargement…</p>
  if (!user) return <Navigate to="/login" replace />

  return (
    <>
      <h1>Favoris</h1>
      {error ? <p className="error">{error}</p> : null}
      {videos?.length === 0 ? <p className="muted">Aucun favori pour le moment.</p> : null}
      {videos ? <VideoGrid videos={videos} /> : null}
    </>
  )
}
