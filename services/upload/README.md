# Service Média (`services/upload`)

Même processus pour l'envoi et la lecture (port 8003). Le dossier garde le nom `upload` (voir `docs/ARCHITECTURE.md`). La Gateway vérifie le JWT et envoie `X-User-Id` et `X-Channel-Id`. Ce service ne parle pas au catalog : il publie `video.uploaded` sur `UPLOAD_AMQP_URL`.

## Prérequis

- Python 3.12

## Développement local

```bash
cd services/upload
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export UPLOAD_DATA_DIR=/tmp/media-videos
export UPLOAD_AMQP_URL=amqp://guest:guest@127.0.0.1:5672/
uvicorn app.main:app --reload --port 8003
```

Tests (de préférence avec le venv du service, pour éviter les plugins pytest globaux) :

```bash
source .venv/bin/activate
pytest
# ou : .venv/bin/pytest
```

## Docker

```bash
docker compose up --build
```

API sur le port **8003**.

## Variables d'environnement

| Variable | Défaut | Rôle |
|----------|--------|------|
| `UPLOAD_DATA_DIR` | `/data/upload/incoming` | Répertoire de dépôt des fichiers |
| `UPLOAD_JWT_PUBLIC_KEY` | **obligatoire** | Clé publique Ed25519 (PEM), paire du `AUTH_JWT_PRIVATE_KEY` du service auth |
| `UPLOAD_JWT_ISSUER` | `stream321-auth` | Claim `iss`, identique à auth |
| `UPLOAD_JWT_AUDIENCE` | `stream321-api` | Claim `aud`, identique à auth |
| `UPLOAD_CATALOG_URL` | `http://127.0.0.1:8002` | Base URL du microservice catalog (health avant upload) |
| `UPLOAD_CATALOG_TIMEOUT_SECONDS` | `3.0` | Timeout HTTP vers le catalog. Nombre strictement positif. Une valeur illisible empêche le démarrage. |

## Intégration multi-services

Catalog down → **503**, pas de buffer ; le client réessaie lorsque le catalog répond de nouveau sur `/health`.

```bash
export INTEGRATION_CATALOG_URL=http://127.0.0.1:8002
export INTEGRATION_UPLOAD_URL=http://127.0.0.1:8003
export INTEGRATION_AUTH_URL=http://127.0.0.1:8001   # quand auth tourne
pytest ../../tests/integration/test_upload_auth.py -m integration -v
pytest ../../tests/integration/test_upload_catalog.py -m integration -v
```
