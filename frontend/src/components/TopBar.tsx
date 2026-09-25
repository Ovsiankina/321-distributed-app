import { Link } from 'react-router-dom'
import './TopBar.css'

function SearchIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="11" cy="11" r="7" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  )
}

function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 15V4" />
      <path d="M7.5 8.5 12 4l4.5 4.5" />
      <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
    </svg>
  )
}

function AccountIcon() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4 3.58-6 8-6s8 2 8 6" />
    </svg>
  )
}

export function TopBar() {
  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    // Search isn't wired to anything yet (see issue #6: "search bar (stub)"),
    // this just stops the browser from doing a full-page navigation on submit.
    event.preventDefault()
  }

  return (
    <header className="top-bar">
      <span className="top-bar-brand">321-app</span>
      <form className="top-bar-search-form" role="search" onSubmit={handleSearchSubmit}>
        <input className="top-bar-search" type="search" placeholder="Rechercher" />
        <button className="top-bar-search-submit" type="submit" aria-label="Rechercher">
          <SearchIcon />
        </button>
      </form>
      <nav className="top-bar-actions">
        <Link to="/upload" className="top-bar-icon-link" aria-label="Upload" title="Upload">
          <UploadIcon />
        </Link>
        <Link to="/account" className="top-bar-icon-link" aria-label="Compte" title="Compte">
          <AccountIcon />
        </Link>
      </nav>
    </header>
  )
}
