import { Link } from 'react-router-dom'
import { formatDuration } from '../lib/formatDuration'
import type { Video } from '../lib/types'
import './VideoCard.css'

interface VideoCardProps {
  video: Video
}

export function VideoCard({ video }: VideoCardProps) {
  return (
    <Link to={`/watch/${video.id}`} className="video-card">
      <div className="video-card-thumbnail">
        <img src={video.thumbnail_url} alt="" width={480} height={270} loading="lazy" />
        <span className="video-card-duration">{formatDuration(video.duration_seconds)}</span>
      </div>
      <h3 className="video-card-title">{video.title}</h3>
      <p className="video-card-description">{video.description}</p>
      <div className="video-card-tags">
        {video.tags.map((tag) => (
          <span key={tag} className="video-card-tag">
            {tag}
          </span>
        ))}
      </div>
    </Link>
  )
}
