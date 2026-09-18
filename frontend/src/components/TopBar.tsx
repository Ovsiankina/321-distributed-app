import { Link } from 'react-router-dom'
import './TopBar.css'

export function TopBar() {
  return (
    <header className="top-bar">
      <span className="top-bar-brand">321-app</span>
      <input className="top-bar-search" type="search" placeholder="Rechercher" />
      <nav className="top-bar-actions">
        <Link to="/upload">Upload</Link>
        <Link to="/account">Compte</Link>
      </nav>
    </header>
  )
}
