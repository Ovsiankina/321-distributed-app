# Tests d'intégration (monorepo)

Tests **entre composants** ou avec **MariaDB réelle**, distincts des tests unitaires dans chaque `services/*/tests/`.

## Périmètre actuel

| Fichier | Couplage | Statut |
|---------|----------|--------|
| `test_catalog_mariadb.py` | Catalog ↔ MariaDB | Exécutable (Docker) |
| `test_auth_catalog.py` | Auth (JWT) ↔ catalog (favoris / `video_id`) | Actif si `INTEGRATION_AUTH_URL` est défini |
| `test_upload_auth.py` | Upload ↔ Auth | Actif si `INTEGRATION_UPLOAD_URL` est défini (API upload pas encore dans l'OpenAPI gateway) |

Le contrat gateway précise que **catalog et recherche sont publics** (pas de JWT). Le lien Auth ↔ catalog passe surtout par les **favoris** (`POST /api/auth/favorites/{video_id}` → 404 si la vidéo n'est pas au catalog).

## Prérequis

- Docker (pour MariaDB)
- Python 3.12

## Catalog + MariaDB

```bash
cd services/catalog
docker compose -f docker-compose.yml -f docker-compose.integration.yml -p catalog-int up -d catalog-db
```

```bash
cd /chemin/vers/321-distributed-app
python3 -m venv tests/integration/.venv
source tests/integration/.venv/bin/activate
pip install -r tests/integration/requirements.txt
pip install -r services/catalog/requirements.txt
pytest tests/integration/test_catalog_mariadb.py -m integration -v
```

Arrêt :

```bash
cd services/catalog
docker compose -f docker-compose.yml -f docker-compose.integration.yml -p catalog-int down -v
```

## Auth ↔ catalog (quand le service auth existe)

Démarrer catalog (port 8002) et auth, puis :

```bash
export INTEGRATION_CATALOG_URL=http://127.0.0.1:8002
export INTEGRATION_AUTH_URL=http://127.0.0.1:8001   # exemple
pytest tests/integration/test_auth_catalog.py -m integration -v
```

## Upload ↔ Auth (quand upload est spécifié et implémenté)

```bash
export INTEGRATION_AUTH_URL=http://127.0.0.1:8001
export INTEGRATION_UPLOAD_URL=http://127.0.0.1:8003
pytest tests/integration/test_upload_auth.py -m integration -v
```
