import { TopBar } from '../components/TopBar'
import { VideoGrid } from '../components/VideoGrid'
import { videos } from '../data/videos'

export function LandingPage() {
  return (
    <main>
      <TopBar />
      <VideoGrid videos={videos} />
    </main>
  )
}
