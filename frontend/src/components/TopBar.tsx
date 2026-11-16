import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
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
  const { user, ready, logout } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [toast, setToast] = useState<string | null>(null)

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const q = query.trim()
    if (q) navigate(`/search?q=${encodeURIComponent(q)}`)
  }

  function handleUpload() {
    setToast("L'upload n'est pas encore disponible (stub).")
    window.setTimeout(() => setToast(null), 2800)
  }

  return (
    <>
      <header className="top-bar">
        <Link to="/" className="top-bar-brand">
          <span className="top-bar-logo">S</span>
          Stream321
        </Link>
        <form className="top-bar-search-form" role="search" onSubmit={handleSearchSubmit}>
          <input
            className="top-bar-search"
            type="search"
            placeholder="Rechercher"
            aria-label="Rechercher"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button className="top-bar-search-submit" type="submit" aria-label="Rechercher">
            <SearchIcon />
          </button>
        </form>
        <nav className="top-bar-actions">
          <button type="button" className="top-bar-icon-link" aria-label="Upload" title="Upload" onClick={handleUpload}>
            <UploadIcon />
          </button>
          {user ? (
            <>
              <Link to="/favorites" className="top-bar-text-link">
                Favoris
              </Link>
              <span className="top-bar-email">{user.email}</span>
              <button type="button" className="top-bar-text-link" onClick={logout}>
                Déconnexion
              </button>
            </>
          ) : ready ? (
            <Link to="/login" className="top-bar-icon-link" aria-label="Compte" title="Compte">
              <AccountIcon />
            </Link>
          ) : null}
        </nav>
      </header>
      {/* Outside the header: its backdrop-filter would make it the toast's containing block. */}
      {toast ? <div className="top-bar-toast">{toast}</div> : null}
    </>
  )
}
