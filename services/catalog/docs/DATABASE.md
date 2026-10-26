# Base de données Catalog

## Moteur et déploiement

- **Production / Docker** : **MariaDB 11** dans le conteneur `catalog-db` ([`docker-compose.yml`](../docker-compose.yml)), volume `catalog-mariadb-data`.
- **Connexion** : `CATALOG_DATABASE_URL` (ex. `mariadb+pymysql://catalog:catalog@catalog-db:3306/catalog`).
- **Fichiers hors SGBD** : vignettes JPEG sur le volume `{CATALOG_DATA_DIR}` (voir section Vignettes).

Le microservice possède sa propre base (bloc « DB vidéo / catalogue » du schéma d'architecture), distincte des services login, favoris ou streaming.

Les tests pytest utilisent un SQLite temporaire via `CATALOG_DATABASE_URL` pour aller vite ; ce n'est pas le modèle de déploiement.

## Schéma

```mermaid
erDiagram
  videos ||--o{ tags : has
  videos {
    varchar id PK
    varchar channel_id
    varchar title
    text description
    varchar thumbnail_path
    int duration_seconds
    bool featured
    text qualities
    text subtitle_langs
    text stream_modes
    text subtitle_formats
  }
  tags {
    int id PK
    varchar tag
    varchar video_id FK
  }
```

### Table `videos`

| Colonne | Type MariaDB | Notes |
|---------|----------------|-------|
| `id` | `VARCHAR(64)` PK | Identifiant vidéo (`catalog.json` → `id`) |
| `channel_id` | `VARCHAR(64)` | Identifiant stable du créateur / chaîne (voir Créateur) |
| `title` | `VARCHAR(512)` | |
| `description` | `TEXT` | |
| `thumbnail_path` | `VARCHAR(512)` | Chemin relatif sous `CATALOG_DATA_DIR` (voir Vignettes) |
| `duration_seconds` | `INT` | Dérivé de `duration_string` |
| `featured` | `BOOLEAN` | `fixtures/featured.json`, pas le JSON YouTube |
| `qualities` | `TEXT` | JSON array, ex. `["360p","720p"]` |
| `subtitle_langs` | `TEXT` | JSON array, scan filesystem au seed |
| `stream_modes` | `TEXT` | JSON array, ex. `["mp4"]` |
| `subtitle_formats` | `TEXT` | JSON array, ex. `["srt"]` |

Index : `channel_id` (filtres / agrégations par créateur plus tard).

### Table `tags`

| Colonne | Type | Notes |
|---------|------|-------|
| `id` | `INT` PK AUTO_INCREMENT | |
| `tag` | `VARCHAR(128)` | Index pour la recherche |
| `video_id` | `VARCHAR(64)` FK | `ON DELETE CASCADE` |
| | | UNIQUE (`tag`, `video_id`) |

**Hors MVP** : pas de table `video_chapters` (`chapter_count` / `chapters` du JSON) tant qu'il n'y a pas de story navigation par chapitres.

## Créateur (`channel_id` vs `uploader_id`)

Dans `catalog.json`, YouTube expose à la fois :

| Champ JSON | Exemple | Usage catalog |
|------------|---------|----------------|
| **`channel_id`** | `UCENv8pH4LkzvuSV_qHIcslg` | **Stocké en base** : clé stable pour regrouper les vidéos d'un même créateur. |
| `uploader_id` | `@Cestpassorcierofficiel` | Handle affichable, peut changer : **non importé** au MVP (affichage / service créateur ultérieur). |

Colonne retenue : **`videos.channel_id`**, remplie au seed depuis `catalog.json`.

## Vignettes

Une vignette par vidéo au MVP.

| Couche | Emplacement |
|--------|-------------|
| **Fichier** | `{CATALOG_DATA_DIR}/thumbs/{video_id}.jpg` |
| **Base** | `videos.thumbnail_path` = chemin **relatif** à `CATALOG_DATA_DIR`, ex. `thumbs/{video_id}.jpg` |
| **API publique** | `thumbnail_url` = `/api/catalog/videos/{id}/thumbnail` (contrat gateway ; pas le chemin disque) |

Génération : au seed, si `{CATALOG_VIDEOS_DIR}/{video_id}.mp4` existe et que le JPEG est absent, `ffmpeg` extrait une image vers le chemin ci-dessus. L'endpoint thumbnail lit le fichier via `thumbnail_path` (ou la convention `thumbs/{id}.jpg`).

Pas de BLOB en MariaDB pour les images.

## Mapping `catalog.json` → DB

| Champ source | Destination |
|--------------|-------------|
| `id` | `videos.id` |
| `channel_id` | `videos.channel_id` |
| `title` | `videos.title` |
| `description` | `videos.description` |
| `tags` + `categories` | lignes `tags` (dédupliquées) |
| `duration_string` | `videos.duration_seconds` |
| (convention) | `videos.thumbnail_path` = `thumbs/{id}.jpg` |

Champs **non** importés au MVP : `channel`, `uploader_id`, `channel_follower_count`, dates, compteurs, `language`, `chapters`, `chapter_count`, `webpage_url`.

## Politique de seed

Au démarrage (`lifespan` FastAPI) :

1. `CREATE TABLE` si besoin (`Base.metadata.create_all`).
2. Lecture `catalog.json` et `featured.json`.
3. Upsert des vidéos (dont `channel_id`, `thumbnail_path`), remplacement complet des tags.
4. Suppression des vidéos absentes du JSON.
5. Génération optionnelle des JPEG via `ffmpeg`.

Re-lancer le service resynchronise la DB avec les fixtures.

Évolution possible : migrations versionnées (Alembic) au lieu de `create_all` seul.
