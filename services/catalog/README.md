# Microservice Catalog

Métadonnées vidéos, recherche et vignettes pour Stream321. Les routes publiques suivent le contrat gateway (`/api/catalog/*`).

Le catalogue est persisté dans **MariaDB 11** (conteneur `catalog-db`). Les vignettes JPEG restent sur disque (`{CATALOG_DATA_DIR}/thumbs/`).

## Prérequis

- Python 3.12
- MariaDB 11 (local ou via Docker)
- `ffmpeg` (génération des vignettes si des MP4 sont montés)

## Développement local

Démarrer MariaDB :

```bash
cd services/catalog
docker compose up -d catalog-db
```

Puis l'API :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export CATALOG_DATA_DIR=/tmp/catalog-data
export CATALOG_VIDEOS_DIR=../../datasets/videos
export CATALOG_SUBTITLES_DIR=../../datasets/subtitles
export CATALOG_DATABASE_URL=mariadb+pymysql://catalog:catalog@localhost:3306/catalog
uvicorn app.main:app --reload --port 8002
```

Tests (SQLite temporaire **uniquement** dans pytest) :

```bash
pytest
```

Les réponses JSON des routes catalog sont validées contre le contrat gateway (`docs/api/gateway.openapi.yaml`) via `jsonschema` et `prance` (voir `tests/gateway_openapi.py`).

### Fixtures de test et recherche `internet`

Deux jeux de données coexistent :

| Jeu | Chemin | Fixture pytest | Usage |
|-----|--------|----------------|--------|
| Mini | `tests/fixtures/` | `client` | Comportement ciblé (peu de vidéos, titres/tags simples) |
| Complet | `fixtures/` (10 vidéos seed) | `full_client` | Volume réel du catalogue + schéma OpenAPI |

**Recherche `internet`**

- **Mini-fixture** : `tests/test_search.py` utilise `q=Internet` et vérifie le match sur le **titre** (`test-video-one`, « Internet et réseaux »). Le même enregistrement a le tag `internet`, mais ce cas n’est pas couvert par un test dédié sur le tag en minuscules.
- **Fixture complet** : `tests/test_gateway_openapi.py` (`test_full_catalog_search_internet_matches_gateway_schema`) appelle `q=internet`, valide le schéma gateway et exige la présence de `UXielWVovBo`. Le match vient d’une occurrence dans la **description** (« Liens Internet »), pas d’un tag `internet` dans `fixtures/catalog.json` (aucun tag de ce nom dans le catalogue seedé).
- **Manuel** (section [Vérification rapide](#vérification-rapide)) : même requête `curl` que le test complet ; à revérifier si `fixtures/catalog.json` change (ID ou texte matché).

Le fixture `fixtures/catalog.json` contient **10** vidéos. `Hq1fGXpI2_I` et `AiytemqB_F0` sont exclues (réservées au service Upload, assets sous `datasets/toUpload/`).

## Docker (catalog + MariaDB)

Depuis `services/catalog` (monter `datasets/` à la racine du dépôt si présent) :

```bash
docker compose up --build
```

API sur le port **8002**.

## Vérification rapide

Une fois l'API démarrée (local ou `docker compose up`) :

```bash
curl -s http://127.0.0.1:8002/health
curl -s http://127.0.0.1:8002/api/catalog/videos | jq .total          # → 10
curl -s "http://127.0.0.1:8002/api/catalog/search?q=internet" | jq '.items[].id'
```

La recherche `internet` doit renvoyer au moins `UXielWVovBo` (match dans la description ; voir [Fixtures de test et recherche `internet`](#fixtures-de-test-et-recherche-internet)).

## Variables d'environnement

| Variable | Défaut | Rôle |
|----------|--------|------|
| `CATALOG_DATABASE_URL` | `mariadb+pymysql://catalog:catalog@localhost:3306/catalog` | Métadonnées catalogue (MariaDB) |
| `CATALOG_DATA_DIR` | `/data/catalog` | Volume `thumbs/` (fichiers) |
| `CATALOG_FIXTURES_DIR` | `fixtures/` (dans l'image) | `catalog.json`, `featured.json` |
| `CATALOG_VIDEOS_DIR` | `/data/videos` | `{video_id}.mp4` pour qualités et vignettes |
| `CATALOG_SUBTITLES_DIR` | `/data/subtitles` | `{lang}/{video_id}_{lang}.srt` |

## Documentation

- [docs/API.md](docs/API.md)
- [docs/DATABASE.md](docs/DATABASE.md)
- Contrat gateway : [`../../docs/api/gateway.openapi.yaml`](../../docs/api/gateway.openapi.yaml)
