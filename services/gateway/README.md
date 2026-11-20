# Microservice API Gateway

Point d'entrée public (E0-04 / E0-05). Les clients n'appellent pas les autres microservices directement.

Contrat : [`docs/API_GATEWAY.md`](../../docs/API_GATEWAY.md), [`docs/api/gateway.openapi.yaml`](../../docs/api/gateway.openapi.yaml).

## Périmètre actuel

| Route | Comportement |
|-------|----------------|
| `GET /health` | `{"status":"ok","service":"gateway"}` |
| `GET /api/home` | Stub `{"sections":[]}` |
| `GET /api/catalog/*` | Proxy transparent vers `GATEWAY_CATALOG_URL` (E1-05 catalog) |
| `* /api/auth/*` | Proxy transparent vers `GATEWAY_AUTH_URL` (E1-05 auth) |
| `GET /api/stream/*` | Proxy transparent vers `GATEWAY_STREAMING_URL` (E1-05 streaming MP4) |
| `* /api/subtitles/*` | Proxy transparent vers `GATEWAY_SUBTITLES_URL` |
| Autre `/api/*` | **404** `Route inconnue` |

Upload (E1-05) : story ultérieure (`feat/gateway-proxy-upload`).

## Port (E0-04)

| Environnement | URL |
|---------------|-----|
| Local (uvicorn) | `http://127.0.0.1:8000` |
| Docker (compose) | `http://127.0.0.1:${GATEWAY_PORT:-8000}` |

Référence microservices internes (non exposés au client) : catalog **8002**, streaming **8003**, upload **8003** (service distinct, hors proxy gateway actuel), auth **8001**, subtitles **8004**.

## Développement local

```bash
cd services/gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GATEWAY_CATALOG_URL=http://127.0.0.1:8002
export GATEWAY_AUTH_URL=http://127.0.0.1:8001
export GATEWAY_STREAMING_URL=http://127.0.0.1:8003
export GATEWAY_SUBTITLES_URL=http://127.0.0.1:8004
uvicorn app.main:app --reload --port 8000
```

Tests :

```bash
pytest
```

### Smoke auth / streaming (POC Docker)

Les conteneurs `poc-gateway-auth-1` et `poc-gateway-streaming-1` n'exposent pas `8001`/`8003` sur l'hôte : utiliser leur IP bridge (ou publier les ports dans un compose local).

Avec le gateway sur `127.0.0.1:8000` et le catalog lab sur `8002` :

```bash
# terminal 1 : exporter GATEWAY_AUTH_URL / GATEWAY_STREAMING_URL (voir script)
./scripts/smoke_proxies_poc.sh
```

Le script résout les IP Docker, prend une `video_id` du catalog POC, attend **401** sur `GET /api/auth/me` (proxy OK) et **200** sur le streaming MP4.

## Docker

```bash
docker compose up --build
```

## Variables d'environnement

| Variable | Défaut | Rôle |
|----------|--------|------|
| `GATEWAY_PORT` | `8000` | Port d'écoute (E0-04) |
| `GATEWAY_CATALOG_URL` | `http://127.0.0.1:8002` | Base URL du service Catalog |
| `GATEWAY_CATALOG_TIMEOUT_SECONDS` | `5.0` | Timeout HTTP vers Catalog |
| `GATEWAY_AUTH_URL` | `http://127.0.0.1:8001` | Base URL du service Auth |
| `GATEWAY_AUTH_TIMEOUT_SECONDS` | `5.0` | Timeout HTTP vers Auth |
| `GATEWAY_STREAMING_URL` | `http://127.0.0.1:8003` | Base URL du service Streaming |
| `GATEWAY_STREAMING_TIMEOUT_SECONDS` | `30.0` | Timeout HTTP vers Streaming (fichiers plus longs) |
| `GATEWAY_SUBTITLES_URL` | `http://127.0.0.1:8004` | Base URL du service Subtitles |
| `GATEWAY_SUBTITLES_TIMEOUT_SECONDS` | `5.0` | Timeout HTTP vers Subtitles |
