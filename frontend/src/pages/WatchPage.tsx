import { useParams } from 'react-router-dom'

export function WatchPage() {
  const { videoId } = useParams()
  return <main>Lecture de la vidéo {videoId} — bientôt disponible</main>
}
