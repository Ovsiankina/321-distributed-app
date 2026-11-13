import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { VideoGrid } from '../components/VideoGrid'
import { api } from '../lib/api'
import type { Video } from '../lib/types'

export function SearchPage() {
  const [params] = useSearchParams()
  const q = params.get('q') ?? ''
  // Results are keyed by query so a new search never shows the previous one's.
  const [result, setResult] = useState<{ q: string; items?: Video[]; error?: string } | null>(null)

  useEffect(() => {
    api
      .search(q)
      .then((res) => setResult({ q, items: res.items }))
      .catch((err: Error) => setResult({ q, error: err.message }))
  }, [q])

  const items = result?.q === q ? (result.items ?? null) : null
  const error = result?.q === q ? (result.error ?? null) : null

  return (
    <>
      <h1>Recherche</h1>
      <p className="muted">
        Résultats pour « {q} »{items ? ` (${items.length})` : ''}
      </p>
      {error ? <p className="error">{error}</p> : null}
      {!error && items === null ? <p className="muted">Chargement…</p> : null}
      {items?.length === 0 ? <p>Aucun résultat.</p> : null}
      {items ? <VideoGrid videos={items} /> : null}
    </>
  )
}
