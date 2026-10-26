# API du microservice Catalog

Ce service expose directement les chemins documentés pour le catalogue. La gateway les proxyfiera plus tard (`x-proxied-to: catalog`).

Référence normative : [`docs/api/gateway.openapi.yaml`](../../../docs/api/gateway.openapi.yaml) (schéma `Video`).

## Santé

### `GET /health`

Réponse `200` :

```json
{ "status": "ok", "service": "catalog" }
```

## Catalogue

### `GET /api/catalog/videos`

Liste complète, sans pagination.

Réponse `200` :

```json
{
  "items": [ { "...": "Video" } ],
  "total": 10
}
```

### `GET /api/catalog/featured`

Vidéos dont `featured` est vrai (défini dans `fixtures/featured.json`).

Réponse `200` : `{ "items": [ Video ] }`

### `GET /api/catalog/search`

| Paramètre | Type | Description |
|-----------|------|-------------|
| `q` | string | Mots-clés (titre, description, tags) |

- `q` vide ou blanc : `{ "items": [], "q": "<valeur reçue>" }`
- Sinon : recherche SQL `ILIKE` sur titre, description et tags.

Réponse `200` : `{ "items": [ Video ], "q": "<texte trimé>" }`

### `GET /api/catalog/videos/{video_id}`

Réponse `200` : objet `Video`.

Réponse `404` :

```json
{ "detail": "Vidéo introuvable" }
```

### `GET /api/catalog/videos/{video_id}/thumbnail`

Réponse `200` : corps binaire `image/jpeg`.

Réponse `404` : même `detail` que ci-dessus (vidéo inconnue ou fichier JPEG absent).

## Objet `Video` (résumé)

Champs obligatoires, sans propriétés additionnelles :

| Champ | Type |
|-------|------|
| `id` | string |
| `title` | string |
| `description` | string |
| `tags` | string[] |
| `duration_seconds` | integer ≥ 1 |
| `thumbnail_url` | string (chemin relatif gateway) |
| `qualities` | `360p` \| `720p` |
| `featured` | boolean |
| `subtitle_langs` | string[] |
| `stream_modes` | `mp4` \| `hls` |
| `subtitle_formats` | `srt` \| `vtt` (tableau ; le seed renvoie souvent `["srt"]` si des sous-titres existent sur disque) |

`thumbnail_url` est toujours `/api/catalog/videos/{id}/thumbnail`.
