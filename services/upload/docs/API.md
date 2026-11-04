# API du microservice Upload

> **Statut : provisoire.** La route upload n'est pas encore stable dans
> [`docs/API_GATEWAY.md`](../../../docs/API_GATEWAY.md) ni dans
> [`docs/api/gateway.openapi.yaml`](../../../docs/api/gateway.openapi.yaml).
> Le chemin et le comportement ci-dessous servent au squelette et aux tests
> d'intégration (`tests/integration/test_upload_auth.py`). Ne pas les traiter
> comme contrat gateway tant que la section n'est pas marquée stable.

## Conventions alignées gateway

- Erreurs JSON : `{ "detail": "<message>" }`.
- JWT absent ou invalide : **401** avec `detail` = `Authentification requise`
  (même libellé que [`docs/API_GATEWAY.md`](../../../docs/API_GATEWAY.md)).

## Santé

### `GET /health`

Réponse `200` :

```json
{ "status": "ok", "service": "upload" }
```

## Upload (provisoire)

### `POST /api/upload/videos`

| Prérequis | Valeur |
|-----------|--------|
| Header | `Authorization: Bearer <JWT>` (même secret que le service auth : `UPLOAD_JWT_SECRET`) |
| Corps | `multipart/form-data`, champ fichier `file` |
| Catalog | Avant tout traitement : `GET {UPLOAD_CATALOG_URL}/health` doit répondre **200** avec `{"status":"ok","service":"catalog"}` |

| Code | Cas (squelette actuel) |
|------|-------------------------|
| 401 | Pas de JWT ou JWT invalide |
| 503 | Catalog injoignable, `/health` non 200, ou corps qui n'est pas un objet `{"status":"ok","service":"catalog"}` |
| 400 | Fichier manquant |
| 415 | `Content-Type` non vidéo |
| 501 | JWT valide, catalog ON, mais traitement upload non implémenté |
