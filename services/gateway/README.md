# Microservice API Gateway

Point d'entrée public (E0-04 / E0-05). Les clients n'appellent pas les autres microservices directement.

Contrat : [`docs/API_GATEWAY.md`](../../docs/API_GATEWAY.md), [`docs/api/gateway.openapi.yaml`](../../docs/api/gateway.openapi.yaml).

## Périmètre actuel (E0-05)

| Route | Comportement |
|-------|----------------|
| `GET /health` | `{"status":"ok","service":"gateway"}` |
| `GET /api/home` | Stub `{"sections":[]}` |
| `* /api/subtitles/*` | Proxy transparent vers `GATEWAY_SUBTITLES_URL` |
| Autre `/api/*` | **404** `Route inconnue` |

Auth, catalog, streaming (E1-05) : stories ultérieures.

## Port (E0-04)

| Environnement | URL |
|---------------|-----|
| Local (uvicorn) | `http://127.0.0.1:8000` |
| Docker (compose) | `http://127.0.0.1:${GATEWAY_PORT:-8000}` |

Référence microservices internes (non exposés au client) : catalog **8002**, upload **8003**, auth **8001** (prévu), subtitles **8004** (cible du proxy).

## Développement local

```bash
cd services/gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GATEWAY_SUBTITLES_URL=http://127.0.0.1:8004
uvicorn app.main:app --reload --port 8000
```

Tests :

```bash
pytest
```

## Docker

```bash
docker compose up --build
```

## Variables d'environnement

| Variable | Défaut | Rôle |
|----------|--------|------|
| `GATEWAY_PORT` | `8000` | Port d'écoute (E0-04) |
| `GATEWAY_SUBTITLES_URL` | `http://127.0.0.1:8004` | Base URL du service Subtitles |
| `GATEWAY_SUBTITLES_TIMEOUT_SECONDS` | `5.0` | Timeout HTTP vers Subtitles |
