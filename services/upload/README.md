# Microservice Upload

Réception et traitement des vidéos uploadées (squelette FastAPI). JWT obligatoire sur `POST /api/upload/videos`.

**Contrat gateway :** section Upload encore en _TODO_ dans [`docs/API_GATEWAY.md`](../../docs/API_GATEWAY.md). Voir [`docs/API.md`](docs/API.md) pour l'API provisoire du service. Questions ouvertes : [`docs/OPEN_QUESTIONS.md`](docs/OPEN_QUESTIONS.md).

## Prérequis

- Python 3.12

## Développement local

```bash
cd services/upload
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export UPLOAD_DATA_DIR=/tmp/upload-data
export UPLOAD_JWT_SECRET=dev-upload-jwt-secret   # aligner sur le service auth
export UPLOAD_CATALOG_URL=http://127.0.0.1:8002  # catalog doit répondre 200 sur /health
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
| `UPLOAD_JWT_SECRET` | `dev-upload-jwt-secret` | Secret HS256 partagé avec le service auth |
| `UPLOAD_JWT_ALGORITHM` | `HS256` | Algorithme JWT |
| `UPLOAD_CATALOG_URL` | `http://127.0.0.1:8002` | Base URL du microservice catalog (health avant upload) |
| `UPLOAD_CATALOG_TIMEOUT_SECONDS` | `3.0` | Timeout HTTP vers le catalog |

## Intégration multi-services

```bash
export INTEGRATION_CATALOG_URL=http://127.0.0.1:8002
export INTEGRATION_UPLOAD_URL=http://127.0.0.1:8003
export INTEGRATION_AUTH_URL=http://127.0.0.1:8001   # quand auth tourne
pytest ../../tests/integration/test_upload_auth.py -m integration -v
pytest ../../tests/integration/test_upload_catalog.py -m integration -v
```
