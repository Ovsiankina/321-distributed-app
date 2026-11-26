# Service Média (`services/upload`)

Même processus pour l'envoi et la lecture (port 8003). Le dossier garde le nom `upload` (voir `docs/ARCHITECTURE.md`). La Gateway vérifie le JWT et envoie `X-User-Id` et `X-Channel-Id`. Ce service ne parle pas au catalog : il publie `video.uploaded` sur `UPLOAD_AMQP_URL`, et il supprime le fichier quand il reçoit `video.rejected`.

## Prérequis

- Python 3.12

## Développement local

```bash
cd services/upload
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export UPLOAD_DATA_DIR=/tmp/media-videos
export UPLOAD_AMQP_URL=amqp://stream:stream@127.0.0.1:5672/
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
| `UPLOAD_DATA_DIR` | `/data/videos` | Fichiers `{video_id}.mp4` |
| `UPLOAD_AMQP_URL` | vide | Bus RabbitMQ. Vide : l'upload répond 503, le consumer `video.rejected` ne démarre pas. |
| `UPLOAD_MAX_BYTES` | 512 Mio | Taille maximale d'un envoi |

Miniatures du jeu de démonstration, une fois les MP4 copiés dans le volume :

```bash
python -m app.announce
```

La commande publie `video.uploaded` avec `origin=dataset`. Le catalog n'en retient que la miniature, pour les vidéos déjà présentes dans son fixture.

## Intégration multi-services

L'envoi ne dépend pas du catalog. Si le broker est arrêté, l'upload répond 503 et ne garde pas le fichier.

```bash
export INTEGRATION_UPLOAD_URL=http://127.0.0.1:8003
export INTEGRATION_AUTH_URL=http://127.0.0.1:8001
pytest ../../tests/integration/test_upload_auth.py -m integration -v
```
