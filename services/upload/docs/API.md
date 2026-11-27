# API du service média

Le service sert l'envoi et la lecture. La Gateway est le seul client public. Ce service lit `X-User-Id` et `X-Channel-Id`. Il ne vérifie pas le JWT et n'appelle pas le catalog.

## Santé

### `GET /health`

Réponse `200` : `{ "status": "ok", "service": "media" }`.

## Envoi

### `POST /api/upload/videos`

`multipart/form-data` : `file` (MP4), `title`, `description`, `tags` (liste séparée par des virgules).

| Code | Cas |
|------|-----|
| 202 | Fichier écrit, message `video.uploaded` publié. Corps `{ "video_id", "status": "processing" }`. |
| 400 | Titre vide ou fichier vide |
| 401 | `X-User-Id` absent |
| 403 | `X-Channel-Id` absent |
| 413 | Fichier au-dessus de `UPLOAD_MAX_BYTES` |
| 415 | Contenu autre que `video/mp4` |
| 422 | Fichier illisible, durée sous 1 s, ou miniature impossible |
| 503 | Broker injoignable. Le fichier est supprimé. |

## Lecture

### `GET` et `HEAD /api/stream/{video_id}`

| Code | Cas |
|------|-----|
| 200 | Fichier entier |
| 206 | Requête avec `Range` |
| 400 | `quality` autre que `360p` ou `720p` |
| 404 | Fichier absent |

`quality` est vérifié. Un seul MP4 existe par vidéo : la qualité ne change pas le fichier servi.

## Compensation

Un message `video.rejected` supprime `{video_id}.mp4`. Un second message pour le même fichier ne fait rien. Un `video_id` qui n'est pas un identifiant simple est ignoré.
