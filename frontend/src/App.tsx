import { VideoGrid } from './components/VideoGrid'
import { videos } from './data/videos'

function App() {
  return (
    <main>
      <VideoGrid videos={videos} />
    </main>
  )
}

export default App
