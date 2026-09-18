import { Route, Routes } from 'react-router-dom'
import { AccountPage } from './pages/AccountPage'
import { LandingPage } from './pages/LandingPage'
import { UploadPage } from './pages/UploadPage'
import { WatchPage } from './pages/WatchPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/upload" element={<UploadPage />} />
      <Route path="/account" element={<AccountPage />} />
      <Route path="/watch/:videoId" element={<WatchPage />} />
    </Routes>
  )
}

export default App
