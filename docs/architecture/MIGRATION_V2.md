# Migration vers l'architecture cible (`/api/v2`)

> **Statut : guide de migration.** L'architecture cible est décidée (voir
> [`to-be/workspace.dsl`](to-be/workspace.dsl)). Ce document explique comment
> l'atteindre par petites étapes, sans casser l'API actuelle. Il ne remplace pas
> le contrat : les routes v2 doivent être ajoutées à
> [`../api/gateway.openapi.yaml`](../api/gateway.openapi.yaml) et à
> [`../API_GATEWAY.md`](../API_GATEWAY.md) dans la PR qui les implémente.
>
> Base de travail : la branche `dev`. Gateway, Auth et Upload n'existent pas
> encore sur `main`.

## Sommaire

1. [Contexte : ce qui ne va pas aujourd'hui](#1-contexte--ce-qui-ne-va-pas-aujourdhui)
2. [La cible en une page](#2-la-cible-en-une-page)
3. [Stratégie `/api/v2`](#3-stratégie-apiv2)
4. [Contrat du bus de messages](#4-contrat-du-bus-de-messages)
5. [Changements service par service](#5-changements-service-par-service)
6. [Kubernetes](#6-kubernetes)
7. [Plan de migration](#7-plan-de-migration)
8. [Limites acceptées et hors périmètre](#8-limites-acceptées-et-hors-périmètre)
9. [Décisions de détail à valider](#9-décisions-de-détail-à-valider)

## 1. Contexte : ce qui ne va pas aujourd'hui

L'examen demande une architecture microservices, une API Gateway, et un MOM
(middleware orienté messages) qui fait interagir au moins deux microservices.
Un principe découle des deux premiers points : un microservice n'appelle pas
directement un autre microservice. L'état actuel (`main` + `dev`) ne respecte
aucun de ces points.

| Exigence ou principe | Constat dans le code | Où |
|----------------------|----------------------|----|
| API Gateway, point d'entrée unique | La SPA contourne la Gateway : le proxy Vite envoie tout `/api` directement au Catalog (`127.0.0.1:8002`), sur `main` comme sur `dev`. | `frontend/vite.config.ts` |
| API Gateway, point d'entrée unique | Upload n'est pas routé : `/api/upload/*` tombe dans le 404 de la Gateway. | `services/gateway/app/routers/fallback.py` |
| API Gateway, rôle réel | La Gateway est un proxy mince : pas de validation du JWT, pas de versioning, corps entièrement chargés en mémoire, header `Range` perdu (seuls `Authorization` et `Content-Type` sont transmis). | `services/gateway/app/proxy.py` |
| MOM utilisé par au moins deux microservices | Aucun broker, aucun message. Tous les échanges sont des appels HTTP synchrones. | tout le dépôt |
| Aucun appel direct entre microservices | Upload appelle `GET /health` du Catalog avant chaque upload et répond `503 Catalog indisponible` si le Catalog est arrêté. Couplage temporel : une panne du Catalog bloque l'upload. | `services/upload/app/catalog_client.py` |
| Services découvrables et déployables séparément | Un `docker-compose.yml` par service, sans réseau commun. Les services se joignent par des ports publiés sur l'hôte et `host.docker.internal`. | `services/*/docker-compose.yml` |
| Cohérence de la configuration | La Gateway attend le streaming sur le port `8003`, déjà pris par Upload. Le service Streaming n'existe pas. | `services/gateway/app/config.py`, `services/upload/docker-compose.yml` |

## 2. La cible en une page

Diagrammes : [`to-be/diagrams/`](to-be/diagrams/) (contexte, conteneurs, flux
asynchrone, déploiement Kubernetes).

| Conteneur | Rôle | Stack | Statut |
|-----------|------|-------|--------|
| Application web | SPA : accueil, recherche, lecteur, connexion, favoris. N'appelle que `/api/v2`. | React, TypeScript, servie par nginx | existe, + Dockerfile nginx |
| API Gateway | Point d'entrée unique. Garde `/api` (v1), ajoute `/api/v2` : valide le JWT, injecte `X-User-Id`, transmet `Range`, diffuse les corps en flux, route upload et streaming. | Python 3.12, FastAPI, httpx | existe, étendue |
| Service Auth | Comptes, émission du JWT, favoris. Tient une copie locale des vidéos connues, alimentée par les événements. | Python 3.12, FastAPI, SQLAlchemy, PyJWT EdDSA, aio-pika | existe, étendu |
| Base Auth | `users`, `favorites`, `video_refs` | MariaDB 11 | existe, tables ajoutées |
| Service Catalog | Métadonnées, recherche, vignettes. Consomme `video.uploaded`, publie `video.published` et `video.removed`. | Python 3.12, FastAPI, SQLAlchemy, ffmpeg, aio-pika | existe, étendu |
| Base Catalog | `videos`, `tags` | MariaDB 11 | existe |
| Service Upload | Reçoit le fichier, l'écrit dans le stockage média, publie `video.uploaded`, répond `202 Accepted`. | Python 3.12, FastAPI, aio-pika | squelette à terminer |
| Service Streaming | Sert le MP4 avec `Range` (206) depuis le stockage média. Trouve le fichier par convention `{video_id}.mp4`. | Python 3.12, FastAPI | nouveau |
| Bus de messages | Le MOM : exchange topic `stream321.events`, une queue durable par service consommateur. | RabbitMQ 3 (AMQP 0-9-1) | nouveau |
| Stockage média | Fichiers vidéo et vignettes. Un seul écrivain pour les vidéos : Upload. | Volume partagé (PVC ReadWriteMany) | remplace le bind mount |

**Règle : aucun microservice n'appelle un autre microservice.** Les seuls appels
HTTP partent du navigateur vers la Gateway, puis de la Gateway vers un service.
Entre services, l'information circule par le bus de messages ou par le stockage
média partagé.

| Chemin | Nature | Exemples |
|--------|--------|----------|
| Navigateur → Gateway → service | synchrone, HTTP | lister le catalogue, se connecter, lire une vidéo, envoyer un fichier |
| Service → base ou stockage | synchrone, local au service | SQL vers sa propre base, lecture ou écriture de fichiers |
| Service → bus → service | asynchrone, AMQP | Upload annonce une vidéo au Catalog, le Catalog annonce une vidéo publiée à Auth |

Conséquences concrètes :

- Upload ne demande plus au Catalog s'il est vivant. Il dépose le fichier et un
  message, puis répond `202`. Le Catalog traitera le message quand il pourra.
- Auth ne demande pas au Catalog si une vidéo existe avant d'ajouter un favori.
  Il consulte sa table `video_refs`, tenue à jour par les événements.
- Streaming ne demande pas au Catalog où est le fichier. Le nom est fixé par
  convention : `{video_id}.mp4`.

## 3. Stratégie `/api/v2`

### 3.1 Principe

- Les routes v1 (`/api/*`) restent **inchangées** : mêmes chemins, même
  comportement, mêmes tests. Le code v1 de la Gateway n'est pas modifié.
- Les routes v2 (`/api/v2/*`) sont servies par un nouveau routeur de la Gateway.
- Les services ne connaissent pas la version. La Gateway retire le segment
  `/v2` avant de transmettre : `/api/v2/catalog/videos` arrive au Catalog sous
  la forme `/api/catalog/videos`. Aucun service ne duplique ses routes.
- Tout ce qui change entre v1 et v2 est porté par la Gateway (JWT, en-têtes,
  flux) ou par un service, de façon compatible avec v1.

### 3.2 Routes v2

| Méthode | Route v2 | Service, chemin reçu | JWT vérifié par la Gateway | Changement par rapport à v1 |
|---------|----------|----------------------|----------------------------|-----------------------------|
| POST | `/api/v2/auth/register` | auth, `/api/auth/register` | non | identique |
| POST | `/api/v2/auth/login` | auth, `/api/auth/login` | non | identique |
| GET | `/api/v2/auth/me` | auth, `/api/auth/me` | oui | identique |
| GET | `/api/v2/auth/favorites` | auth, `/api/auth/favorites` | oui | `videos` réduit à `id`, `title`, `channel_id` (voir 5.2) |
| POST, DELETE | `/api/v2/auth/favorites/{video_id}` | auth, `/api/auth/favorites/{video_id}` | oui | Auth valide la vidéo dans `video_refs`, sans appeler le Catalog |
| GET, HEAD | `/api/v2/catalog/*` | catalog, `/api/catalog/*` | non | identique, `thumbnail_url` pointe vers `/api/v2` |
| GET, HEAD | `/api/v2/stream/{video_id}` | streaming, `/api/stream/{video_id}` | non | `Range` transmis, corps diffusé en flux, 206 |
| POST | `/api/v2/upload/videos` | upload, `/api/upload/videos` | oui, compte créateur | nouvelle route, `202 Accepted` (traitement asynchrone) |
| * | autre `/api/v2/*` | aucun | non | `404 Route inconnue` |

`/api/home` (stub) et `/api/subtitles/*` n'ont pas d'équivalent v2 : la SPA
n'utilise pas le premier, le service Subtitles est hors périmètre.

### 3.3 Montage dans la Gateway

Nouveau fichier `services/gateway/app/routers/v2.py`, préfixe `/api/v2`. Le
retrait de `/v2` ne demande rien de spécial : `forward_request` construit déjà
l'URL amont avec `path_prefix` + `path_suffix`, il suffit de passer le préfixe
v1 du service.

```python
# services/gateway/app/routers/v2.py (esquisse)
router = APIRouter(prefix="/api/v2", tags=["v2"])

@router.api_route("/catalog/{path:path}", methods=["GET", "HEAD", "OPTIONS"])
async def catalog_v2(path: str, request: Request):
    return await forward_v2(
        request,
        upstream_base=config.catalog_upstream_base(),
        path_prefix="/api/catalog/",   # /v2 retiré ici
        path_suffix=path,
        timeout_seconds=config.catalog_timeout_seconds(),
    )
```

Ordre d'inclusion dans `services/gateway/app/main.py` : le routeur v2 doit être
inclus **avant** `fallback.router`, sinon `/api/{path:path}` capture
`/api/v2/...` et répond 404. Le routeur v2 se termine par son propre
`/{path:path}` qui répond `404 Route inconnue`.

### 3.4 Authentification à la Gateway

Sur les routes marquées « oui » ci-dessus, une dépendance FastAPI
`require_jwt` :

1. lit `Authorization: Bearer <JWT>`, sinon `401 Authentification requise` ;
2. vérifie la signature avec la **clé publique Ed25519** (algorithme `EdDSA`,
   liste fermée), `iss`, `aud`, `exp`, avec la même tolérance d'horloge que
   Auth (30 s). La logique existe déjà dans `services/upload/app/auth.py` et
   `services/upload/app/config.py` : la reprendre dans
   `services/gateway/app/auth.py` ;
3. construit les en-têtes d'identité à transmettre : `X-User-Id` (claim `sub`)
   et `X-Channel-Id` (claim `channel_id`, s'il existe, voir 5.2).

**Les en-têtes d'identité envoyés par le client ne passent jamais.** La v1 les
ignore déjà car `proxy.py` ne transmet qu'une liste blanche d'en-têtes. La v2
garde ce principe : liste blanche, puis ajout des en-têtes calculés par la
Gateway. Un test vérifie qu'un `X-User-Id: 1` envoyé par le client n'arrive pas
au service.

La Gateway continue de transmettre `Authorization`, ce qui permet aux services
de garder leur vérification v1 pendant la transition.

### 3.5 `Range` et corps en flux

`proxy.py` charge aujourd'hui toute la requête (`await request.body()`) et
toute la réponse (`upstream_response.content`) en mémoire. Pour une vidéo de
plusieurs centaines de Mo, c'est inutilisable. La v2 utilise une variante
`forward_v2` (la fonction v1 reste telle quelle) :

- en-têtes transmis : `authorization`, `content-type`, `content-length`,
  `range`, `if-range`, plus les en-têtes d'identité ;
- requête : le corps est passé en flux (`content=request.stream()`), pour
  l'upload multipart ;
- réponse : `client.send(..., stream=True)` puis `StreamingResponse` sur
  `aiter_raw()`, avec fermeture de la réponse amont en tâche de fond ;
- les en-têtes `Content-Range`, `Accept-Ranges`, `Content-Length` et le code
  `206` du service sont renvoyés tels quels ;
- un `httpx.AsyncClient` partagé, créé dans le `lifespan` de l'application,
  plutôt qu'un client par requête ;
- un timeout dédié à l'upload (`GATEWAY_UPLOAD_TIMEOUT_SECONDS`), plus long que
  les autres.

### 3.6 Dépréciation de la v1

1. La v2 est livrée à côté de la v1. Rien ne change pour la SPA.
2. La SPA passe son chemin de base de `/api` à `/api/v2` (une constante dans
   `frontend/src/lib/api.ts`).
3. La v1 est marquée dépréciée dans le contrat (OpenAPI `deprecated: true`) et
   la Gateway ajoute un en-tête `Deprecation: true` aux réponses v1.
4. Quand plus aucun client n'appelle la v1 (journaux de la Gateway), les
   routeurs v1 (`routers/auth.py`, `catalog.py`, `streaming.py`, `subtitles.py`,
   `home.py`) sont supprimés. `/api/*` hors `/api/v2` répond alors 404.

## 4. Contrat du bus de messages

### 4.1 Topologie RabbitMQ

- Exchange `stream321.events`, type `topic`, durable.
- Une queue durable par service consommateur, liée par clé de routage.
- La clé de routage est égale au champ `type` de l'événement.

| Clé de routage | Producteur | Queue | Consommateur |
|----------------|------------|-------|--------------|
| `video.uploaded` | Upload | `catalog.video-uploaded` | Catalog |
| `video.published` | Catalog | `auth.video-events` | Auth |
| `video.removed` | Catalog | `auth.video-events` | Auth |

Chaque service déclare ce qu'il utilise au démarrage (déclarations idempotentes
en AMQP) : le producteur déclare l'exchange, le consommateur déclare l'exchange,
sa queue et ses liaisons. L'ordre de démarrage des services n'a donc pas
d'importance.

### 4.2 Enveloppe et contenus

Tous les messages sont en JSON (`content_type: application/json`), avec la même
enveloppe :

```json
{
  "event_id": "5f0c1c8e-3a43-4d1e-9a4b-2a5d0c7e9b11",
  "type": "video.uploaded",
  "occurred_at": "2026-11-23T14:05:12Z",
  "data": {
    "video_id": "9b2f4c1ad0e84b6f8c3e5a7d1f2b3c4d",
    "channel_id": "UC-demo-channel",
    "title": "Démo du pipeline d'upload",
    "description": "Vidéo envoyée depuis la SPA.",
    "tags": ["demo", "architecture"],
    "file_name": "9b2f4c1ad0e84b6f8c3e5a7d1f2b3c4d.mp4",
    "uploaded_at": "2026-11-23T14:05:11Z"
  }
}
```

| `type` | Producteur → consommateur | Champs de `data` |
|--------|---------------------------|------------------|
| `video.uploaded` | Upload → Catalog | `video_id`, `channel_id`, `title`, `description`, `tags`, `file_name`, `uploaded_at` |
| `video.published` | Catalog → Auth | `video_id`, `channel_id`, `title` |
| `video.removed` | Catalog → Auth | `video_id` |

`event_id` est un UUID v4 généré par le producteur. `occurred_at` et
`uploaded_at` sont en ISO 8601, UTC. `file_name` est relatif au dossier des
vidéos du stockage média.

### 4.3 Garanties de livraison

- **Durabilité** : exchange et queues durables, messages persistants
  (`delivery_mode=2`). Un redémarrage de RabbitMQ ne perd pas les messages
  déjà acceptés.
- **Confirmation côté producteur** : publisher confirms activés. Upload ne
  répond `202` qu'après la confirmation du broker.
- **Acquittement manuel** : le consommateur acquitte (`ack`) seulement après
  avoir validé sa transaction en base. S'il plante avant, le message est
  relivré.
- **Au moins une fois** : une relivraison est donc possible. Chaque
  consommateur est **idempotent** :
  - table `processed_events (event_id PRIMARY KEY, processed_at)` dans sa base,
    insérée dans la même transaction que l'effet ;
  - effets écrits en upsert sur `video_id`, ce qui couvre aussi deux
    événements différents pour la même vidéo.
- **Message invalide** (JSON illisible, champ manquant) : `reject` sans remise
  en queue, avec un log. **Erreur transitoire** (base indisponible) : `nack`
  avec remise en queue après une courte pause.
- **Débit** : `prefetch_count` faible (1 à 10) pour qu'un consommateur ne
  monopolise pas les messages.
- **Pas d'ordre global garanti** entre services. Les effets sont écrits pour
  ne pas en dépendre (upsert, suppression idempotente).

### 4.4 Consommateur arrêté : comparaison avec le 503 actuel

| Situation | Aujourd'hui | Cible |
|-----------|-------------|-------|
| Catalog arrêté pendant un upload | Upload répond `503 Catalog indisponible`, le fichier est refusé. | Upload écrit le fichier, publie `video.uploaded`, répond `202`. Le message attend dans `catalog.video-uploaded`. Au redémarrage, le Catalog le traite et la vidéo apparaît. |
| Auth arrêté pendant une publication | sans objet | `video.published` attend dans `auth.video-events`. Auth rattrape son retard au redémarrage. |
| Catalog arrêté, ajout d'un favori | sans objet (favoris non implémentés) | Auth répond normalement, avec sa table `video_refs`. |
| Broker arrêté | sans objet | Upload ne peut pas publier : il supprime le fichier écrit et répond `503`. Les lectures (catalogue, streaming, favoris) continuent. |

## 5. Changements service par service

Chaque service garde sa propre copie d'un petit module `messaging.py`
(connexion `aio_pika.connect_robust`, déclaration de la topologie, publication
ou consommation). Pas de bibliothèque partagée entre services : chacun reste
déployable seul.

### 5.1 Gateway (`services/gateway/`)

1. `app/config.py` : ajouter `upload_upstream_base()` (`GATEWAY_UPLOAD_URL`),
   `upload_timeout_seconds()`, et la configuration JWT
   (`GATEWAY_JWT_PUBLIC_KEY`, `GATEWAY_JWT_ISSUER`, `GATEWAY_JWT_AUDIENCE`).
   Passer le défaut de `GATEWAY_STREAMING_URL` sur le port du nouveau service
   Streaming (`8005`, voir 5.5) pour supprimer le conflit avec Upload.
2. `requirements.txt` : ajouter `PyJWT[crypto]` et `cryptography`.
3. `app/auth.py` (nouveau) : dépendance `require_jwt`, voir 3.4.
4. `app/proxy.py` : ajouter `forward_v2` (liste blanche étendue, en-têtes
   d'identité, flux), voir 3.5. Ne pas modifier `forward_request`.
5. `app/routers/v2.py` (nouveau) : routes du tableau 3.2, 404 final.
6. `app/main.py` : `app.include_router(v2.router)` avant `fallback.router` ;
   client httpx partagé dans un `lifespan`.
7. `tests/` : `test_v2_routing.py` (retrait de `/v2`, 404), `test_v2_auth.py`
   (401 sans token, token expiré, `X-User-Id` du client ignoré),
   `test_v2_stream.py` (`Range` transmis, 206 renvoyé). Les tests v1 existants
   ne changent pas.
8. `README.md`, `docker-compose.yml` : nouvelles variables.

### 5.2 Auth (`services/auth/`)

Sur `dev`, Auth ne sert que `register`, `login`, `me`. Les favoris sont dans le
contrat et dans la SPA, mais pas encore dans Auth.

1. `app/tokens.py` : `issue_token` ajoute le claim `channel_id` quand le compte
   en a un (`users.channel_id`). `app/routers/auth.py` : `login` lit aussi
   `User.channel_id`. Un claim en plus ne gêne aucun vérificateur existant.
2. `app/models.py` : ajouter
   - `Favorite` : `user_id` (clé étrangère `users.id`), `video_id`,
     `created_at`, unicité `(user_id, video_id)` ;
   - `VideoRef` : `video_id` (clé primaire), `channel_id`, `title`,
     `updated_at` ;
   - `ProcessedEvent` : `event_id` (clé primaire), `processed_at`.
   `init_db()` utilise `create_all`, qui crée les tables manquantes.
3. Identité de l'appelant : une dépendance qui prend `X-User-Id` s'il est
   présent (requête v2, déjà vérifiée par la Gateway), sinon le Bearer comme
   aujourd'hui (`current_user`, requête v1).
4. `app/routers/favorites.py` (nouveau), préfixe `/api/auth/favorites` :
   - `GET` : `video_ids` et `videos` construits depuis `favorites` joint à
     `video_refs` (`id`, `title`, `channel_id`) ;
   - `POST /{video_id}` : `404 Vidéo introuvable` si absent de `video_refs`,
     sinon `201` (aussi si déjà présent) ;
   - `DELETE /{video_id}` : `204`, même si absent.
   Ces routes répondent aussi en v1 via le proxy `/api/auth/*` existant.
5. `app/messaging.py` (nouveau) : consommateur de `auth.video-events`, démarré
   dans le `lifespan` de `app/main.py`.
   - `video.published` : upsert de `video_refs` ;
   - `video.removed` : suppression de la ligne `video_refs` et des favoris
     associés.
   SQLAlchemy est synchrone : exécuter le traitement avec
   `asyncio.to_thread`.
6. `app/config.py` : `AUTH_AMQP_URL` (identifiants via le Secret).
7. `requirements.txt` : `aio-pika`.
8. `tests/` : favoris (201, 404, 204, idempotence), consommateur (même
   `event_id` reçu deux fois, une seule ligne).

### 5.3 Catalog (`services/catalog/`)

1. **Ne plus effacer les vidéos uploadées.** `app/seed.py`,
   `sync_catalog_db`, supprime au démarrage toute vidéo absente de
   `fixtures/catalog.json`. Une vidéo uploadée disparaîtrait à chaque
   redémarrage. Ajouter une colonne `source` (`fixture` ou `upload`) au modèle
   `Video` (`app/models.py`) et ne supprimer que les lignes `fixture`. Pas
   d'outil de migration dans le projet : recréer la base locale (volume
   Docker) après ce changement ; sur Kubernetes, la base part de zéro.
2. `app/messaging.py` (nouveau) : publication et consommation, démarrées dans
   le `lifespan` de `app/main.py`.
3. Au démarrage, après la synchronisation des fixtures : publier
   `video.published` pour chaque vidéo en base et `video.removed` pour chaque
   vidéo supprimée. Cela remplit `video_refs` côté Auth. Avec deux réplicas,
   les doublons sont absorbés par l'upsert d'Auth.
4. Consommateur de `catalog.video-uploaded` :
   1. vérifier que `videos/{video_id}.mp4` existe dans le stockage média
      (sinon `nack` avec remise en queue) ;
   2. durée avec `ffprobe` (fourni avec ffmpeg dans l'image) : le contrat exige
      `duration_seconds >= 1` ;
   3. upsert de `Video` (`source=upload`, `featured=False`, champs dérivés
      comme dans `_video_fields`) et de ses `Tag` ;
   4. vignette avec `ensure_thumbnail` (`app/media.py`). Elle capture l'image à
      30 s : prévoir un repli pour les vidéos plus courtes ;
   5. commit, ack, puis publication de `video.published`. Si l'événement était
      déjà traité, republier quand même `video.published` : une panne entre le
      commit et la publication ne perd ainsi pas l'annonce.
5. `thumbnail_url` : `app/serialize.py` écrit en dur
   `/api/catalog/videos/{id}/thumbnail`. La Gateway v2 ajoute
   `X-Forwarded-Prefix: /api/v2` ; le Catalog construit l'URL avec ce préfixe,
   `/api` par défaut. La v1 ne change pas.
6. `app/config.py` : `CATALOG_AMQP_URL`, et un mot de passe de base passé à
   part comme dans Auth (`CATALOG_DB_PASSWORD`) au lieu des identifiants en
   clair de `docker-compose.yml`.
7. `requirements.txt` : `aio-pika`.
8. `tests/` : seed qui garde les lignes `upload`, consommateur idempotent,
   `thumbnail_url` avec et sans préfixe.

### 5.4 Upload (`services/upload/`)

1. Supprimer `app/catalog_client.py` et l'appel `ensure_catalog_ready()` dans
   `app/routers/upload.py`. Supprimer `UPLOAD_CATALOG_URL` et
   `UPLOAD_CATALOG_TIMEOUT_SECONDS` de `app/config.py`, `.env.example`,
   `docker-compose.yml`. Supprimer `tests/test_catalog_ready.py` et
   `tests/test_upload_catalog_gate.py`.
2. Identité : Upload n'est joignable que par `/api/v2/upload`, donc après la
   vérification du JWT par la Gateway. Remplacer `require_authenticated_user`
   (`app/auth.py`) par une dépendance qui lit `X-User-Id` (sinon 401) et
   `X-Channel-Id` (sinon `403`, compte non créateur). La clé publique n'est
   plus nécessaire dans Upload.
3. `app/routers/upload.py`, `POST /api/upload/videos` en multipart : champs
   `file`, `title` (obligatoire), `description`, `tags`.
   1. accepter seulement `video/mp4` (`415` sinon) : Streaming sert des MP4
      et aucune conversion n'est prévue ; taille maximale configurable ;
   2. générer `video_id` (UUID hexadécimal, 32 caractères) ;
   3. écrire le fichier en flux dans `videos/{video_id}.mp4.part`, puis
      renommer en `{video_id}.mp4` (`os.replace`) : personne ne lit un fichier
      à moitié écrit ;
   4. publier `video.uploaded` avec confirmation du broker ;
   5. répondre `202` avec `{"video_id": "...", "status": "processing"}`.
   En cas d'échec de publication : supprimer le fichier, répondre
   `503 Service indisponible`.
   La route devient `async def` pour lire le fichier en flux et publier avec
   aio-pika.
4. `app/config.py` : `UPLOAD_DATA_DIR` pointe vers le dossier des vidéos du
   stockage média (`/data/videos`), `UPLOAD_AMQP_URL`.
5. `requirements.txt` : ajouter `aio-pika` ; retirer `PyJWT[crypto]` une fois
   l'étape 2 faite.
6. `tests/`, `docs/API.md`, `README.md` : nouveau contrat (202, 403, 415).

### 5.5 Streaming (`services/streaming/`, nouveau)

Même structure que les autres services : `app/main.py`, `app/config.py`,
`app/routers/stream.py`, `Dockerfile`, `requirements.txt`, `pytest.ini`,
`tests/`, `README.md`, `docker-compose.yml`.

1. Port `8005` (`8003` est pris par Upload, `8004` est réservé à Subtitles).
2. `GET` et `HEAD /api/stream/{video_id}?quality=...`, conforme au contrat v1
   existant :
   - `video_id` contrôlé par une expression régulière
     (`^[A-Za-z0-9_-]{1,64}$`) avant toute construction de chemin ;
   - `quality` hors de `360p`, `720p` : `400 Qualité inconnue (360p ou 720p)`.
     Un seul fichier existe par vidéo : la qualité est validée mais ne change
     pas le fichier servi ;
   - fichier `STREAMING_VIDEOS_DIR/{video_id}.mp4` absent :
     `404 Vidéo introuvable` ;
   - sans `Range` : `200`, fichier entier ; avec `Range: bytes=a-b` : `206`,
     `Content-Range`, `Accept-Ranges: bytes`. Vérifier si le `FileResponse` de
     la version de Starlette utilisée gère `Range` ; sinon, un générateur qui
     lit la plage par blocs suffit.
3. `GET /health` : `{"status": "ok", "service": "streaming"}`.
4. Aucun appel au Catalog, aucune base, aucun broker.

### 5.6 Application web (`frontend/`)

1. `vite.config.ts` : le proxy `/api` pointe vers la Gateway
   (`http://127.0.0.1:8000`) au lieu du Catalog. Cette étape seule supprime le
   contournement de la Gateway, v1 comprise.
2. `src/lib/api.ts` : une constante `API_BASE = '/api/v2'` utilisée par toutes
   les routes et par `streamUrl`. Adapter `src/lib/api.test.ts`.
3. `src/pages/FavoritesPage.tsx` : la réponse v2 ne contient plus les fiches
   complètes. Charger les détails depuis `/api/v2/catalog/videos/{id}` (ou
   filtrer `/api/v2/catalog/videos`). La SPA compose les données : c'est le
   client, pas un microservice.
4. Page d'upload (créateurs) : formulaire multipart vers
   `/api/v2/upload/videos`, message « vidéo en cours de traitement » sur `202`.
5. `Dockerfile` (nouveau) : build multi-étapes (Node pour `npm run build`, puis
   `nginx` qui sert `dist/`) et `nginx.conf` avec repli
   `try_files $uri /index.html` pour les routes de la SPA. nginx ne fait pas
   proxy de `/api` : l'Ingress s'en charge.

## 6. Kubernetes

### 6.1 Objets

| Objet | Nom | Rôle |
|-------|-----|------|
| Namespace | `stream321` | isole toute l'application |
| Deployment + Service ClusterIP | `spa` (x2), `gateway` (x2), `auth` (x2), `catalog` (x2), `upload` (x1), `streaming` (x2) | services sans état, sondes sur `/health` |
| StatefulSet + PVC + Service | `auth-db`, `catalog-db` (MariaDB 11), `rabbitmq` (RabbitMQ 3), x1 chacun | données persistantes |
| PersistentVolumeClaim | `media` (ReadWriteMany) | stockage média partagé |
| Ingress (NGINX Ingress Controller) | `stream321` | seule entrée externe : `/` vers `spa`, `/api` vers `gateway` |
| ConfigMap | `stream321-config` | URLs des services par DNS du cluster, noms de queues, chemins |
| Secret | `stream321-secrets` | clé privée JWT (Auth), clé publique JWT (Gateway), mots de passe des bases et du broker |

Sondes :

- `readinessProbe` `httpGet /health` sur chaque Deployment : un pod n'entre
  dans le Service que s'il est prêt.
- `livenessProbe` `httpGet /health` avec un `failureThreshold` large : le
  `/health` d'Auth et du Catalog répond `503` quand la base est indisponible,
  et redémarrer le pod n'y changerait rien.
- MariaDB : `healthcheck.sh --connect --innodb_initialized` (comme dans les
  fichiers compose actuels). RabbitMQ : `rabbitmq-diagnostics -q ping`.

### 6.2 Arborescence proposée

```text
k8s/
  kustomization.yaml       # kubectl apply -k k8s/
  namespace.yaml
  config/
    configmap.yaml
    secret.example.yaml    # clés sans valeurs ; le vrai Secret n'est pas versionné
  storage/
    media-pvc.yaml
  data/
    auth-db.yaml           # StatefulSet + Service
    catalog-db.yaml
    rabbitmq.yaml
  apps/
    spa.yaml               # Deployment + Service
    gateway.yaml
    auth.yaml
    catalog.yaml
    upload.yaml
    streaming.yaml
  ingress.yaml
  tools/
    media-loader.yaml      # pod temporaire pour copier datasets/ dans le PVC
```

### 6.3 Découverte de services

Aujourd'hui, la Gateway joint le Catalog par `http://host.docker.internal:8002`
parce que chaque service tourne dans son propre compose. Dans le cluster,
chaque Service ClusterIP a un nom DNS stable : `catalog` dans le namespace
(`catalog.stream321.svc.cluster.local` en entier). Kubernetes répartit les
requêtes entre les pods prêts. Les URLs passent par la ConfigMap, sans
changement de code : les services lisent déjà leurs URLs dans l'environnement.

```yaml
# k8s/config/configmap.yaml (extrait)
data:
  GATEWAY_AUTH_URL: http://auth:8001
  GATEWAY_CATALOG_URL: http://catalog:8002
  GATEWAY_UPLOAD_URL: http://upload:8003
  GATEWAY_STREAMING_URL: http://streaming:8005
  AMQP_HOST: rabbitmq
```

Les URLs AMQP contiennent des identifiants : les construire dans le manifeste à
partir du Secret (`env` avec `valueFrom.secretKeyRef`, puis
`value: amqp://$(AMQP_USER):$(AMQP_PASSWORD)@rabbitmq:5672/`).

`host.docker.internal`, `extra_hosts` et les ports publiés disparaissent. Les
fichiers compose restent utilisables pour développer un service seul.

### 6.4 Stockage média

Un seul PVC `media`, monté par sous-dossier (`subPath`) avec les droits
minimaux. Les chemins dans les conteneurs restent ceux d'aujourd'hui, donc pas
de changement de configuration pour le Catalog.

| Service | `subPath` → point de montage | Accès |
|---------|------------------------------|-------|
| Upload | `videos` → `/data/videos` | lecture-écriture |
| Catalog | `videos` → `/data/videos`, `subtitles` → `/data/subtitles` | lecture seule |
| Catalog | `catalog` → `/data/catalog` (vignettes) | lecture-écriture |
| Streaming | `videos` → `/data/videos` | lecture seule |

```yaml
# k8s/apps/streaming.yaml (extrait)
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: streaming
          ports: [{ containerPort: 8005 }]
          readinessProbe: { httpGet: { path: /health, port: 8005 } }
          livenessProbe: { httpGet: { path: /health, port: 8005 }, failureThreshold: 6 }
          volumeMounts:
            - { name: media, mountPath: /data/videos, subPath: videos, readOnly: true }
      volumes:
        - name: media
          persistentVolumeClaim: { claimName: media }
```

Le dossier `datasets/` n'est pas versionné : le copier une fois dans le PVC
avec `kubectl cp` vers le pod `tools/media-loader.yaml`, qui monte `media` et
attend.

ReadWriteMany : sur un cluster d'un seul nœud (minikube, kind), un volume
`hostPath` convient. Sur plusieurs nœuds, il faut une StorageClass RWX (NFS,
CephFS, Longhorn). Avec deux réplicas du Catalog sur un volume partagé,
vérifier que le verrou `fcntl` de `catalog_sync_lock` (`app/seed.py`)
fonctionne sur le stockage choisi.

### 6.5 Ingress

```yaml
# k8s/ingress.yaml (extrait)
metadata:
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "2g"         # uploads
    nginx.ingress.kubernetes.io/proxy-request-buffering: "off"
    nginx.ingress.kubernetes.io/proxy-buffering: "off"        # streaming
spec:
  ingressClassName: nginx
  rules:
    - http:
        paths:
          - { path: /api, pathType: Prefix, backend: { service: { name: gateway, port: { number: 8000 } } } }
          - { path: /,    pathType: Prefix, backend: { service: { name: spa, port: { number: 80 } } } }
```

Seul l'Ingress est joignable de l'extérieur. Aucun Service n'est de type
`NodePort` ou `LoadBalancer`.

## 7. Plan de migration

Chaque étape est une PR vers `dev` qui laisse la v1 fonctionnelle. Les étapes
d'un même service peuvent être des commits successifs sur la même branche (voir
[`CONTRIBUTING.md`](../../CONTRIBUTING.md)).

| # | Étape | Terminé quand | Exigence |
|---|-------|---------------|----------|
| 1 | SPA : proxy Vite vers la Gateway (5.6 étape 1) | La SPA fonctionne avec le Catalog seulement joignable par la Gateway ; les requêtes apparaissent dans les journaux de la Gateway. | API Gateway |
| 2 | Gateway : routeur v2 transparent pour auth, catalog, stream, avec retrait de `/v2` et 404 (5.1 étapes 5, 6) | `curl /api/v2/catalog/videos` renvoie la même chose que `/api/catalog/videos` ; tests v1 inchangés et verts. | API Gateway |
| 3 | Auth : claim `channel_id` dans le JWT (5.2 étape 1) | Un login créateur renvoie un token avec `channel_id` ; Upload et Auth acceptent toujours les tokens. | prérequis de 4 et 9 |
| 4 | Gateway : validation du JWT et en-têtes d'identité sur v2 (5.1 étapes 1 à 3) | `GET /api/v2/auth/me` sans token : 401 renvoyé par la Gateway ; un `X-User-Id` envoyé par le client n'atteint pas Auth (test). | API Gateway |
| 5 | Gateway : `forward_v2` (flux, `Range`) et route upload (5.1 étape 4) | Test : `Range` transmis et 206 renvoyé ; un gros fichier traverse la Gateway sans hausse mémoire notable. | API Gateway |
| 6 | Service Streaming (5.5) | `curl -H 'Range: bytes=0-1023' /api/v2/stream/{id}` renvoie 206 et 1024 octets ; la vidéo se lit et se parcourt dans le lecteur. | aucun appel direct |
| 7 | Broker : RabbitMQ (compose dédié en attendant Kubernetes) et module `messaging.py` | L'interface de gestion RabbitMQ montre `stream321.events` et les deux queues après démarrage du Catalog et d'Auth. | MOM |
| 8 | Catalog : seed corrigé, publications au démarrage, consommateur `video.uploaded`, `X-Forwarded-Prefix` (5.3) | Un `video.uploaded` publié à la main depuis l'interface RabbitMQ crée la vidéo dans `/api/v2/catalog/videos` ; un redémarrage ne l'efface pas. | MOM |
| 9 | Upload : identité par en-têtes, écriture dans le stockage, publication, 202, suppression de l'appel au Catalog (5.4) | Upload via `/api/v2/upload/videos` → 202 ; la vidéo apparaît au catalogue. Catalog arrêté pendant l'upload : 202 quand même, la vidéo apparaît à son redémarrage. | MOM (Upload + Catalog), aucun appel direct |
| 10 | Auth : favoris, `video_refs`, consommateur (5.2 étapes 2 à 8) | Favori sur une vidéo existante : 201 ; inconnue : 404 ; même résultat avec le Catalog arrêté ; une vidéo uploadée devient ajoutable en favori. | MOM (troisième service), aucun appel direct |
| 11 | SPA en v2 : `API_BASE`, favoris, page d'upload, Dockerfile nginx (5.6 étapes 2 à 5) | Plus aucun appel `/api/` hors `/api/v2` dans `frontend/src` ; parcours complet (connexion, lecture, favori, upload) en v2. | API Gateway |
| 12 | Kubernetes : manifestes `k8s/` (section 6) | `kubectl apply -k k8s/` ; tous les pods prêts ; l'application fonctionne par l'Ingress seulement ; supprimer un pod du Catalog ne coupe pas le service. | déploiement cible |
| 13 | Dépréciation puis retrait de la v1 (3.6) | Contrat v1 marqué `deprecated`, puis routeurs v1 supprimés de la Gateway ; tests et contrat à jour. | API Gateway |

Récapitulatif des exigences :

| Exigence | Satisfaite par les étapes |
|----------|---------------------------|
| API Gateway, point d'entrée unique | 1, 2, 4, 5, 11, 12 (Ingress `/api` → Gateway seulement) |
| MOM utilisé par au moins deux microservices | 7, 8, 9 (Upload et Catalog), 10 (Auth en plus) |
| Aucun appel direct entre microservices | 6, 9, 10 |
| Présentation de la stack et des composants | [`README.md`](README.md) et les deux workspaces C4 |

## 8. Limites acceptées et hors périmètre

La cible n'est volontairement pas parfaite. Ces points sont connus et assumés :

- **Volume partagé RWX** au lieu d'un stockage objet (S3, MinIO). Plus simple,
  mais lié à une StorageClass RWX et partagé par trois services.
- **Limite de tentatives de login en mémoire**, par réplica : avec deux
  réplicas d'Auth, la limite réelle est jusqu'à deux fois plus haute.
- **Bases et broker en une seule instance** : pas de haute disponibilité des
  données. Un arrêt de RabbitMQ bloque l'upload (pas les lectures).
- **Confiance dans les en-têtes d'identité** : les services croient
  `X-User-Id` parce que seuls les pods du cluster peuvent les joindre
  (Services ClusterIP). Aucune NetworkPolicy n'est prévue.
- **Pas de conversion vidéo** : un seul fichier MP4 par vidéo ; le paramètre
  `quality` est validé mais ne change rien.
- **Pas d'observabilité** : ni métriques, ni traces, ni journaux centralisés.
- **Hors périmètre** : services Subtitles et Recommendation, HLS, outil de
  migration de schéma (Alembic).

## 9. Décisions de détail à valider

Points que la cible ne fixe pas et que ce guide propose. À confirmer en équipe
avant l'étape concernée :

| Point | Proposition | Étape |
|-------|-------------|-------|
| Source du `channel_id` pour Upload | Claim `channel_id` dans le JWT, injecté par la Gateway en `X-Channel-Id` | 3, 4 |
| Port du service Streaming | `8005` | 6 |
| Contenu de `GET /api/v2/auth/favorites` | `videos` réduit à `id`, `title`, `channel_id` ; la SPA charge le reste depuis le Catalog | 10, 11 |
| `thumbnail_url` en v2 | En-tête `X-Forwarded-Prefix` posé par la Gateway | 8 |
| Formulaire d'upload | multipart `file`, `title`, `description`, `tags` ; MP4 seulement ; réponse `{video_id, status}` | 9 |
| Identifiant d'une vidéo uploadée | UUID hexadécimal généré par Upload | 9 |
| Vidéos supprimées du catalogue | `video.removed` émis quand la synchronisation des fixtures retire une vidéo ; Auth supprime aussi les favoris associés | 8, 10 |
| RabbitMQ en local avant Kubernetes | Compose dédié, sur le modèle des autres services | 7 |
