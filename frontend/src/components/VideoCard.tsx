import { Link } from 'react-router-dom'
import type { Video } from '../data/videos'
import './VideoCard.css'

interface VideoCardProps {
  video: Video
}

export function VideoCard({ video }: VideoCardProps) {
  return (
    <Link to={`/watch/${video.id}`} className="video-card">
      <div className="video-card-thumbnail">
        <img src={video.thumbnail} alt="" width={480} height={270} loading="lazy" />
        <span className="video-card-duration">{video.duration}</span>
      </div>
      <h3 className="video-card-title">{video.title}</h3>
    </Link>
  )
}
