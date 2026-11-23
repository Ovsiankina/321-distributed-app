# Migration vers l'architecture cible (`/api/v2`)

> **Statut : guide de migration.** L'architecture cible est décidée (voir
> [`to-be/workspace.dsl`](to-be/workspace.dsl)). Ce document explique comment
> l'atteindre par petites étapes, sans casser l'API actuelle. Il ne remplace pas
> le contrat : les routes v2 doivent être ajoutées à
> [`../api/gateway.openapi.yaml`](../api/gateway.openapi.yaml) et à
> [`../API_GATEWAY.md`](../API_GATEWAY.md) dans la PR qui les implémente.
>
> Base de travail : la branche `dev`. Gateway, Auth et Upload n'existent pas
> encore sur `main`. Le squelette Upload (`services/upload`) devient le
> Service Média de la cible.

## Sommaire

1. [Contexte : ce qui ne va pas aujourd'hui](#1-contexte--ce-qui-ne-va-pas-aujourdhui)
2. [Conformité à la théorie du cours](#2-conformité-à-la-théorie-du-cours)
3. [La cible en une page](#3-la-cible-en-une-page)
4. [Stratégie `/api/v2`](#4-stratégie-apiv2)
5. [Contrat du bus de messages](#5-contrat-du-bus-de-messages)
6. [Changements service par service](#6-changements-service-par-service)
7. [Kubernetes](#7-kubernetes)
8. [Plan de migration](#8-plan-de-migration)
9. [Limites acceptées et hors périmètre](#9-limites-acceptées-et-hors-périmètre)
10. [Décisions de détail à valider](#10-décisions-de-détail-à-valider)

## 1. Contexte : ce qui ne va pas aujourd'hui

L'examen demande une architecture microservices, une API Gateway, et un MOM
(middleware orienté messages) qui fait interagir au moins deux microservices.
L'équipe y ajoute une règle plus stricte que le cours (voir la section 2) : un
microservice n'appelle pas directement un autre microservice. L'état actuel
(`main` + `dev`) ne respecte aucun de ces points.

| Exigence ou principe | Constat dans le code | Où |
|----------------------|----------------------|----|
| API Gateway, point d'entrée unique | La SPA contourne la Gateway : le proxy Vite envoie tout `/api` directement au Catalog (`127.0.0.1:8002`), sur `main` comme sur `dev`. | `frontend/vite.config.ts` |
| API Gateway, point d'entrée unique | Upload n'est pas routé : `/api/upload/*` tombe dans le 404 de la Gateway. | `services/gateway/app/routers/fallback.py` |
| API Gateway, rôle réel | La Gateway est un proxy mince : pas de validation du JWT, pas de versioning, corps entièrement chargés en mémoire, header `Range` perdu (seuls `Authorization` et `Content-Type` sont transmis). | `services/gateway/app/proxy.py` |
| MOM utilisé par au moins deux microservices | Aucun broker, aucun message. Tous les échanges sont des appels HTTP synchrones. | tout le dépôt |
| Aucun appel direct entre microservices | Upload appelle `GET /health` du Catalog avant chaque upload et répond `503 Catalog indisponible` si le Catalog est arrêté. Couplage temporel : une panne du Catalog bloque l'upload. | `services/upload/app/catalog_client.py` |
| Services découvrables et déployables séparément | Un `docker-compose.yml` par service, sans réseau commun. Les services se joignent par des ports publiés sur l'hôte et `host.docker.internal`. | `services/*/docker-compose.yml` |
| Cohérence de la configuration | La Gateway envoie `/api/stream/*` sur le port `8003`, celui d'Upload, qui ne sert aucune route de lecture. Aucun service ne sert les vidéos. | `services/gateway/app/config.py`, `services/upload/docker-compose.yml` |

## 2. Conformité à la théorie du cours

Le projet est évalué selon la théorie du module 321. Le tableau relie chaque
règle du cours à la façon dont la cible la respecte. Les références donnent le
support et la page.

| Règle du cours | Source | Dans la cible |
|----------------|--------|---------------|
| Chaque microservice a sa propre base de données. | 06 - DB dans un système distribué, p.3 | Un seul stockage par service, un seul service par stockage : Auth → Base Auth (MariaDB) ; Catalog → Base Catalog (MariaDB, miniatures comprises) ; Service Média → Stockage vidéo (volume privé) ; Gateway et SPA n'ont aucun stockage. Le bus de messages garde ses queues dans son propre volume, auquel aucun service n'accède. |
| (même règle, correction) | 06 - DB dans un système distribué, p.3 | Une version antérieure de cette cible montait un volume média partagé dans trois services (Upload, Catalog, Streaming) : c'était une violation de la règle. Elle est supprimée ainsi : Upload et Streaming fusionnent en un seul Service Média, seul à écrire et lire les MP4 ; la miniature est produite par Média et voyage dans le message `video.uploaded` ; le Catalog la range dans sa propre base et ne lit plus aucun fichier. |
| Les données peuvent être partagées entre les instances d'un même microservice, et seulement entre elles. | 06 - DB dans un système distribué, p.7 | Le PVC `media-videos` est monté par les deux réplicas du Deployment `media`, et par aucun autre Deployment. C'est le seul partage de données de la cible. |
| Chaque service peut utiliser une base d'une nature différente, adaptée à ses données. | 06 - DB dans un système distribué, p.4 | MariaDB pour les données structurées, recherchées et jointes (vidéos et tags ; comptes et favoris). Volume de fichiers pour les MP4 : gros binaires lus par plages d'octets (`Range`). Les miniatures, petites, tiennent dans une colonne BLOB. |
| Chaque service a sa propre stack technologique, sa propre base de données, sa propre API, son propre versionning, son propre hébergement, sa propre pipeline de déploiement. | 01 - Architecture microservices, p.10 | Stack : un `requirements.txt` et un `Dockerfile` par service (seul Média embarque ffmpeg). Base : voir la première ligne. API : un préfixe par service (`/api/auth`, `/api/catalog`, `/api/upload` et `/api/stream`). Versionning : une version et une image par service. Hébergement : un Deployment et un Service Kubernetes par service. Pipeline : un workflow CI par service (déjà le cas pour Catalog et Auth sur `dev`), un manifeste par service dans `k8s/apps/`. Pas de bibliothèque partagée : chaque service a sa copie de `messaging.py`. |
| Avantages visés : scaling optimisé, moins de couplage, résilience. | 01 - Architecture microservices, p.20 | Chaque Deployment a son nombre de réplicas ; aucun service ne connaît l'adresse d'un autre ; un service arrêté ne bloque pas les autres (voir 5.4). |
| L'API Gateway est un proxy entre le client et les services ; elle peut prendre en charge des tâches communes (vérification des permissions, logging, cache). | 01 - Architecture microservices, p.14 | La Gateway est le seul point d'entrée (l'Ingress n'envoie `/api` qu'à elle). Elle vérifie les permissions (JWT validé, `X-User-Id` injecté, voir 4.4) et ses journaux servent à suivre l'usage de la v1 (voir 4.6). Elle n'agrège pas de réponses (le cours cite aussi ce rôle) : chaque route v2 correspond à un seul service. Pas de cache dans cette cible. |
| Strangler pattern : une façade garde l'ancienne API pendant la migration. | 01 - Architecture microservices, p.24 | La Gateway est la façade : `/api` (v1) reste inchangée pendant que `/api/v2` est ajoutée et que les services migrent un par un derrière elle. La v1 n'est retirée qu'à la fin (voir 4.6). |
| Un MOM fait interagir au moins deux microservices. | 02 - MOM | Média, Catalog et Auth n'échangent que par le Broker RabbitMQ (voir 2.1). |
| Saga : une suite de transactions locales liées par des événements, avec des actions de compensation ; orchestration ou chorégraphie. | 06 - DB dans un système distribué, p.12 à 18 | Le flux d'upload est une saga par chorégraphie (voir 2.2). |

**Appels directs entre services.** Le cours les tolère (01 - Architecture
microservices, p.7 : « Ils peuvent également communiquer entre eux
directement »). L'équipe choisit une règle plus stricte : aucun microservice
n'appelle un autre microservice, tout passe par le MOM, pour supprimer le
couplage temporel que montre aujourd'hui l'appel d'Upload au Catalog.

### 2.1 Le MOM dans le vocabulaire du cours

| Terme du cours (02 - MOM) | Dans la cible |
|---------------------------|---------------|
| Broker | RabbitMQ, conteneur « Bus de messages ». |
| Publisher (producteur) | Le service qui émet : Média (`video.uploaded`), Catalog (`video.published`, `video.removed`, `video.rejected`). |
| Subscriber (consommateur) | Le service qui reçoit : Catalog (`video.uploaded`), Auth (`video.published`, `video.removed`), Média (`video.rejected`). |
| Message | Corps JSON (enveloppe `event_id`, `type`, `occurred_at`, `data`) et en-têtes AMQP (`content_type`, `message_id`, `delivery_mode`). Voir 5.2. |
| Queue (point à point) | Un seul Subscriber reçoit le message. |
| Topic (publication/abonnement) | Chaque Subscriber abonné reçoit sa propre copie. |

| Flux | Publisher → Subscriber | Mode | Pourquoi |
|------|------------------------|------|----------|
| `video.uploaded` | Média → Catalog | Queue (point à point) | Demande de traitement d'une vidéo : un seul service, le Catalog, doit l'enregistrer, une seule fois. |
| `video.published`, `video.removed` | Catalog → Auth | Topic (publication/abonnement) | Annonce d'un fait : Auth s'abonne aujourd'hui ; d'autres Subscribers (Recommendation, Subtitles) pourront s'ajouter sans toucher au Catalog. |
| `video.rejected` | Catalog → Média | Queue (point à point) | Ordre de compensation : seul Média, propriétaire du fichier, peut le supprimer. |

Correspondance avec RabbitMQ : tous les messages passent par un seul exchange
de type `topic`, `stream321.events`, avec une clé de routage égale au `type`.
Chaque service Subscriber déclare **sa propre queue**, liée aux clés qui
l'intéressent. Le mode Topic vient de là : un message dont la clé est liée à
plusieurs queues est copié dans chacune. Le mode point à point vient du fait
qu'une clé n'est liée qu'à une queue, et que les réplicas d'un même service
lisent la même queue : chaque message est livré à une seule instance.

Avantages obtenus (02 - MOM, p.31) :

- **Découplage** : Média ne connaît ni l'adresse ni l'existence du Catalog ;
  le Catalog ne connaît pas Auth. Chacun ne connaît que le Broker et le
  contrat des messages.
- **Asynchronisme** : Média répond `202 Accepted` dès que le message est
  confié au Broker ; le Catalog le traite ensuite.
- **Tolérance aux pannes** : « si le consumer crash, le message est stocké en
  sécurité dans la queue ». Avec le Catalog arrêté, l'upload réussit et la
  vidéo apparaît à son redémarrage, là où Upload répond aujourd'hui
  `503 Catalog indisponible` (voir 5.4).
- **Lissage de la charge** : une rafale d'uploads s'accumule dans
  `catalog.video-uploaded` ; le Catalog la consomme à son rythme
  (`prefetch_count`).

Inconvénients acceptés (02 - MOM, p.32) :

- **Complexification** : un Broker à exploiter, un contrat de messages à
  maintenir, des Subscribers idempotents (voir 5.3).
- **Latence** : une vidéo envoyée n'apparaît au catalogue qu'après le
  traitement du message ; la SPA affiche « vidéo en cours de traitement ».

### 2.2 Le flux d'upload, une saga par chorégraphie

La saga suit le cours (06 - DB dans un système distribué, p.13 à 18) : une
suite de transactions locales, chacune dans la base du service concerné,
reliées par des événements, avec une action de compensation en cas d'échec.

| Étape | Service | Transaction locale | Événement émis |
|-------|---------|--------------------|----------------|
| T1 | Média | écrit `{video_id}.mp4` dans le Stockage vidéo, crée la miniature | `video.uploaded` |
| T2 | Catalog | insère la vidéo, ses tags et sa miniature dans Base Catalog | `video.published` (succès) ou `video.rejected` (échec) |
| T3 | Auth | ajoute la vidéo à `video_refs` dans Base Auth | aucun |
| C1 | Média | compensation de T1 sur `video.rejected` : supprime le fichier | aucun |

T2 échoue de façon définitive si le message est invalide (métadonnées
manquantes, durée nulle, miniature illisible ou trop grosse) : le Catalog
publie `video.rejected` et Média compense. Une erreur transitoire (base
indisponible) n'est pas un échec de la saga : le message est remis en queue et
retraité. T3 ne peut pas échouer fonctionnellement (upsert) : elle est
seulement retentée.

Pourquoi la chorégraphie plutôt que l'orchestration, selon les critères du
cours (06 - DB dans un système distribué, p.16) : la chorégraphie est décrite
comme « piloté par les événements (publication/abonnement) », ce que fournit
déjà le Broker ; elle donne un « couplage minimisé des services » (p.18) ; elle
convient aux « flux de travail simples (3 à 4 étapes) », et ce flux en compte
trois. L'orchestration
demanderait un coordinateur central de plus, qui connaîtrait chaque service.

## 3. La cible en une page

Diagrammes : [`to-be/diagrams/`](to-be/diagrams/) (contexte, conteneurs, flux
asynchrone, déploiement Kubernetes).

| Conteneur | Rôle | Stack | Statut |
|-----------|------|-------|--------|
| Application web | SPA : accueil, recherche, lecteur, connexion, favoris. N'appelle que `/api/v2`. | React, TypeScript, servie par nginx | existe, + Dockerfile nginx |
| API Gateway | Point d'entrée unique. Garde `/api` (v1), ajoute `/api/v2` : valide le JWT, injecte `X-User-Id`, transmet `Range`, diffuse les corps en flux, route l'upload et la lecture vers Média. | Python 3.12, FastAPI, httpx | existe, étendue |
| Service Auth | Comptes, émission du JWT, favoris. Tient une copie locale des vidéos connues, alimentée par les événements. | Python 3.12, FastAPI, SQLAlchemy, PyJWT EdDSA, aio-pika | existe, étendu |
| Base Auth | `users`, `favorites`, `video_refs` | MariaDB 11 | existe, tables ajoutées |
| Service Catalog | Métadonnées, recherche, miniatures (servies depuis sa base). Consomme `video.uploaded`, publie `video.published`, `video.removed` et `video.rejected`. N'accède à aucun fichier vidéo. | Python 3.12, FastAPI, SQLAlchemy, aio-pika | existe, étendu (ffmpeg retiré) |
| Base Catalog | `videos` (miniature en colonne BLOB), `tags` | MariaDB 11 | existe, colonne ajoutée |
| Service Média | Reçoit les uploads, écrit le MP4 dans son volume, crée la miniature (ffmpeg), publie `video.uploaded`, répond `202 Accepted`. Sert `/api/stream/{id}` avec `Range` (206). Consomme `video.rejected` et supprime alors le fichier. | Python 3.12, FastAPI, ffmpeg, aio-pika (port 8003) | squelette Upload (`services/upload`) étendu |
| Stockage vidéo | Fichiers MP4. Privé au Service Média : seuls ses réplicas le montent. | Volume privé (PVC) | remplace le bind mount `datasets/videos` du Catalog |
| Bus de messages | Le MOM : exchange topic `stream321.events`, une queue durable par service Subscriber. | RabbitMQ 3 (AMQP 0-9-1) | nouveau |

**Règle : aucun microservice n'appelle un autre microservice.** Les seuls appels
HTTP partent du navigateur vers la Gateway, puis de la Gateway vers un service.
Entre services, l'information circule uniquement par le bus de messages.
**Chaque stockage a un seul service propriétaire** : aucun volume ni aucune
base n'est monté ou lu par deux services différents.

| Chemin | Nature | Exemples |
|--------|--------|----------|
| Navigateur → Gateway → service | synchrone, HTTP | lister le catalogue, se connecter, lire une vidéo, envoyer un fichier |
| Service → son propre stockage | synchrone, local au service | SQL d'Auth et du Catalog vers leur base, fichiers MP4 de Média dans son volume |
| Service → bus → service | asynchrone, AMQP | Média annonce une vidéo au Catalog, le Catalog annonce une vidéo publiée à Auth ou rejette une vidéo auprès de Média |

Conséquences concrètes :

- Média ne demande plus au Catalog s'il est vivant. Il dépose le fichier et un
  message, puis répond `202`. Le Catalog traitera le message quand il pourra.
- Auth ne demande pas au Catalog si une vidéo existe avant d'ajouter un favori.
  Il consulte sa table `video_refs`, tenue à jour par les événements.
- Le Catalog ne lit aucun fichier : la miniature lui arrive dans le message
  `video.uploaded`, il la range dans sa base et la sert lui-même.
- Média sert la lecture sans demander au Catalog où est le fichier : le nom
  est fixé par convention, `{video_id}.mp4` dans son propre volume.

## 4. Stratégie `/api/v2`

### 4.1 Principe

- Les routes v1 (`/api/*`) restent **inchangées** : mêmes chemins, même
  comportement, mêmes tests. Le code v1 de la Gateway n'est pas modifié.
- Les routes v2 (`/api/v2/*`) sont servies par un nouveau routeur de la Gateway.
- Les services ne connaissent pas la version. La Gateway retire le segment
  `/v2` avant de transmettre : `/api/v2/catalog/videos` arrive au Catalog sous
  la forme `/api/catalog/videos`. Aucun service ne duplique ses routes.
- Tout ce qui change entre v1 et v2 est porté par la Gateway (JWT, en-têtes,
  flux) ou par un service, de façon compatible avec v1.

### 4.2 Routes v2

| Méthode | Route v2 | Service, chemin reçu | JWT vérifié par la Gateway | Changement par rapport à v1 |
|---------|----------|----------------------|----------------------------|-----------------------------|
| POST | `/api/v2/auth/register` | auth, `/api/auth/register` | non | identique |
| POST | `/api/v2/auth/login` | auth, `/api/auth/login` | non | identique |
| GET | `/api/v2/auth/me` | auth, `/api/auth/me` | oui | identique |
| GET | `/api/v2/auth/favorites` | auth, `/api/auth/favorites` | oui | `videos` réduit à `id`, `title`, `channel_id` (voir 6.2) |
| POST, DELETE | `/api/v2/auth/favorites/{video_id}` | auth, `/api/auth/favorites/{video_id}` | oui | Auth valide la vidéo dans `video_refs`, sans appeler le Catalog |
| GET, HEAD | `/api/v2/catalog/*` | catalog, `/api/catalog/*` | non | identique, `thumbnail_url` pointe vers `/api/v2` ; la miniature est servie depuis Base Catalog |
| GET, HEAD | `/api/v2/stream/{video_id}` | média, `/api/stream/{video_id}` | non | `Range` transmis, corps diffusé en flux, 206 |
| POST | `/api/v2/upload/videos` | média, `/api/upload/videos` | oui, compte créateur | nouvelle route, `202 Accepted` (traitement asynchrone) |
| * | autre `/api/v2/*` | aucun | non | `404 Route inconnue` |

Les deux routes de Média arrivent sur le même service (port 8003). C'est déjà
le défaut de `GATEWAY_STREAMING_URL` dans `services/gateway/app/config.py` :
l'ancien conflit de port entre Upload et la lecture disparaît.

`/api/home` (stub) et `/api/subtitles/*` n'ont pas d'équivalent v2 : la SPA
n'utilise pas le premier, le service Subtitles est hors périmètre.

### 4.3 Montage dans la Gateway

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

### 4.4 Authentification à la Gateway

Sur les routes marquées « oui » ci-dessus, une dépendance FastAPI
`require_jwt` :

1. lit `Authorization: Bearer <JWT>`, sinon `401 Authentification requise` ;
2. vérifie la signature avec la **clé publique Ed25519** (algorithme `EdDSA`,
   liste fermée), `iss`, `aud`, `exp`, avec la même tolérance d'horloge que
   Auth (30 s). La logique existe déjà dans `services/upload/app/auth.py` et
   `services/upload/app/config.py` : la reprendre dans
   `services/gateway/app/auth.py` ;
3. construit les en-têtes d'identité à transmettre : `X-User-Id` (claim `sub`)
   et `X-Channel-Id` (claim `channel_id`, s'il existe, voir 6.2).

**Les en-têtes d'identité envoyés par le client ne passent jamais.** La v1 les
ignore déjà car `proxy.py` ne transmet qu'une liste blanche d'en-têtes. La v2
garde ce principe : liste blanche, puis ajout des en-têtes calculés par la
Gateway. Un test vérifie qu'un `X-User-Id: 1` envoyé par le client n'arrive pas
au service.

La Gateway continue de transmettre `Authorization`, ce qui permet aux services
de garder leur vérification v1 pendant la transition.

### 4.5 `Range` et corps en flux

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

### 4.6 Dépréciation de la v1

1. La v2 est livrée à côté de la v1. Rien ne change pour la SPA.
2. La SPA passe son chemin de base de `/api` à `/api/v2` (une constante dans
   `frontend/src/lib/api.ts`).
3. La v1 est marquée dépréciée dans le contrat (OpenAPI `deprecated: true`) et
   la Gateway ajoute un en-tête `Deprecation: true` aux réponses v1.
4. Quand plus aucun client n'appelle la v1 (journaux de la Gateway), les
   routeurs v1 (`routers/auth.py`, `catalog.py`, `streaming.py`, `subtitles.py`,
   `home.py`) sont supprimés. `/api/*` hors `/api/v2` répond alors 404.

## 5. Contrat du bus de messages

Vocabulaire et modes (Queue ou Topic) : voir 2.1.

### 5.1 Topologie RabbitMQ

- Broker : RabbitMQ 3. Exchange `stream321.events`, type `topic`, durable.
- Une queue durable par service Subscriber, liée par clé de routage.
- La clé de routage est égale au champ `type` du message.

| Clé de routage | Publisher | Queue | Subscriber | Mode |
|----------------|-----------|-------|------------|------|
| `video.uploaded` | Média | `catalog.video-uploaded` | Catalog | Queue (point à point) |
| `video.published` | Catalog | `auth.video-events` | Auth | Topic (publication/abonnement) |
| `video.removed` | Catalog | `auth.video-events` | Auth | Topic (publication/abonnement) |
| `video.rejected` | Catalog | `media.video-rejected` | Média | Queue (point à point) |

Un futur Subscriber de `video.published` déclare sa propre queue liée à la même
clé : il reçoit sa copie sans changement du Catalog ni d'Auth.

Chaque service déclare ce qu'il utilise au démarrage (déclarations idempotentes
en AMQP) : le Publisher déclare l'exchange, le Subscriber déclare l'exchange,
sa queue et ses liaisons. L'ordre de démarrage des services n'a donc pas
d'importance.

### 5.2 Enveloppe et contenus

Tous les messages sont en JSON (`content_type: application/json`), avec la même
enveloppe. L'en-tête AMQP `message_id` reprend `event_id`.

```json
{
  "event_id": "5f0c1c8e-3a43-4d1e-9a4b-2a5d0c7e9b11",
  "type": "video.uploaded",
  "occurred_at": "2026-11-23T14:05:12Z",
  "data": {
    "origin": "upload",
    "video_id": "9b2f4c1ad0e84b6f8c3e5a7d1f2b3c4d",
    "channel_id": "UC-demo-channel",
    "title": "Démo du pipeline d'upload",
    "description": "Vidéo envoyée depuis la SPA.",
    "tags": ["demo", "architecture"],
    "duration_seconds": 754,
    "qualities": ["360p", "720p"],
    "thumbnail_jpeg_base64": "/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "uploaded_at": "2026-11-23T14:05:11Z"
  }
}
```

| `type` | Publisher → Subscriber | Champs de `data` |
|--------|------------------------|------------------|
| `video.uploaded` | Média → Catalog | `origin`, `video_id`, `channel_id`, `title`, `description`, `tags`, `duration_seconds`, `qualities`, `thumbnail_jpeg_base64`, `uploaded_at` |
| `video.published` | Catalog → Auth | `video_id`, `channel_id`, `title` |
| `video.removed` | Catalog → Auth | `video_id` |
| `video.rejected` | Catalog → Média | `video_id`, `reason` |

- `event_id` est un UUID v4 généré par le Publisher. `occurred_at` et
  `uploaded_at` sont en ISO 8601, UTC.
- `duration_seconds` est mesuré par Média avec `ffprobe` (entier, au moins 1).
- `qualities` : qualités annoncées par Média pour le fichier, aujourd'hui
  toujours `["360p", "720p"]`, comme le renvoie `qualities_for` pour un fichier
  présent (un seul MP4, voir 9).
- `thumbnail_jpeg_base64` : la miniature, JPEG réduit à 480 px de large et
  encodé en base64, quelques dizaines de ko. La vidéo elle-même ne passe
  jamais par le bus. Le Catalog refuse une miniature de plus de 256 ko une
  fois décodée.
- `origin` : `upload` pour une vidéo envoyée par un créateur ; `dataset` pour
  une vidéo du jeu de démonstration annoncée par Média au chargement initial
  (voir 6.4, étape 7). Avec `dataset`, les champs de métadonnées (`channel_id`,
  `title`, `description`, `tags`) sont absents : le fixture du Catalog en
  reste la source.
- `reason` : `invalid_metadata`, `invalid_duration` ou `invalid_thumbnail`.

### 5.3 Garanties de livraison

- **Durabilité** : exchange et queues durables, messages persistants
  (`delivery_mode=2`). Un redémarrage de RabbitMQ ne perd pas les messages
  déjà acceptés.
- **Confirmation côté Publisher** : publisher confirms activés. Média ne
  répond `202` qu'après la confirmation du Broker.
- **Acquittement manuel** : le Subscriber acquitte (`ack`) seulement après
  avoir validé sa transaction locale et publié les messages qui en découlent.
  S'il plante avant, le message est relivré.
- **Au moins une fois** : une relivraison est donc possible. Chaque
  Subscriber est **idempotent** :
  - Catalog et Auth : table `processed_events (event_id PRIMARY KEY,
    processed_at)` dans leur base, insérée dans la même transaction que
    l'effet ;
  - effets écrits en upsert sur `video_id`, ce qui couvre aussi deux
    messages différents pour la même vidéo ;
  - Média n'a pas de base : son seul effet, supprimer un fichier, est
    idempotent par nature (fichier déjà absent : rien à faire).
- **Message illisible** (JSON invalide, pas de `video_id`) : `reject` sans
  remise en queue, avec un log. **`video.uploaded` lisible mais invalide**
  (origine `upload`) : le Catalog publie `video.rejected` puis acquitte ; c'est
  l'échec de la saga (voir 2.2). **Erreur transitoire** (base indisponible) :
  `nack` avec remise en queue après une courte pause.
- **Débit** : `prefetch_count` faible (1 à 10) pour qu'un Subscriber ne
  monopolise pas les messages.
- **Pas d'ordre global garanti** entre services. Les effets sont écrits pour
  ne pas en dépendre (upsert, suppression idempotente).

### 5.4 Subscriber arrêté : comparaison avec le 503 actuel

| Situation | Aujourd'hui | Cible |
|-----------|-------------|-------|
| Catalog arrêté pendant un upload | Upload répond `503 Catalog indisponible`, le fichier est refusé. | Média écrit le fichier, publie `video.uploaded`, répond `202`. Le message attend dans `catalog.video-uploaded`. Au redémarrage, le Catalog le traite et la vidéo apparaît. |
| Auth arrêté pendant une publication | sans objet | `video.published` attend dans `auth.video-events`. Auth rattrape son retard au redémarrage. |
| Média arrêté pendant un rejet | sans objet | `video.rejected` attend dans `media.video-rejected`. Média supprime le fichier à son redémarrage. |
| Catalog arrêté, ajout d'un favori | sans objet (favoris non implémentés) | Auth répond normalement, avec sa table `video_refs`. |
| Catalog arrêté, lecture d'une vidéo | sans objet (aucun service de lecture) | Média sert le fichier sans consulter le Catalog. |
| Broker arrêté | sans objet | Média ne peut pas publier : il supprime le fichier écrit et répond `503`. Les lectures (catalogue, vidéos, favoris) continuent. |

## 6. Changements service par service

Chaque service garde sa propre copie d'un petit module `messaging.py`
(connexion `aio_pika.connect_robust`, déclaration de la topologie, publication
ou consommation). Pas de bibliothèque partagée entre services : chacun reste
déployable seul.

### 6.1 Gateway (`services/gateway/`)

1. `app/config.py` : ajouter `upload_upstream_base()` (`GATEWAY_UPLOAD_URL`,
   défaut `http://127.0.0.1:8003`), `upload_timeout_seconds()`, et la
   configuration JWT (`GATEWAY_JWT_PUBLIC_KEY`, `GATEWAY_JWT_ISSUER`,
   `GATEWAY_JWT_AUDIENCE`). `GATEWAY_STREAMING_URL` garde son défaut
   (`http://127.0.0.1:8003`) : upload et lecture visent le même Service Média.
   Les deux variables restent séparées, ce qui ne coûte rien et évite de
   toucher au routeur v1 `streaming.py`.
2. `requirements.txt` : ajouter `PyJWT[crypto]` et `cryptography`.
3. `app/auth.py` (nouveau) : dépendance `require_jwt`, voir 4.4.
4. `app/proxy.py` : ajouter `forward_v2` (liste blanche étendue, en-têtes
   d'identité, flux), voir 4.5. Ne pas modifier `forward_request`.
5. `app/routers/v2.py` (nouveau) : routes du tableau 4.2, 404 final.
6. `app/main.py` : `app.include_router(v2.router)` avant `fallback.router` ;
   client httpx partagé dans un `lifespan`.
7. `tests/` : `test_v2_routing.py` (retrait de `/v2`, 404), `test_v2_auth.py`
   (401 sans token, token expiré, `X-User-Id` du client ignoré),
   `test_v2_stream.py` (`Range` transmis, 206 renvoyé). Les tests v1 existants
   ne changent pas.
8. `README.md`, `docker-compose.yml` : nouvelles variables.

### 6.2 Auth (`services/auth/`)

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

### 6.3 Catalog (`services/catalog/`)

Le Catalog perd tout accès aux fichiers : plus de volume, plus de ffmpeg. Sa
seule donnée est Base Catalog, miniatures comprises.

1. **Ne plus effacer les vidéos uploadées.** `app/seed.py`,
   `sync_catalog_db`, supprime au démarrage toute vidéo absente de
   `fixtures/catalog.json`. Une vidéo uploadée disparaîtrait à chaque
   redémarrage. Ajouter une colonne `source` (`fixture` ou `upload`) au modèle
   `Video` (`app/models.py`) et ne supprimer que les lignes `fixture`. Pas
   d'outil de migration dans le projet : recréer la base locale (volume
   Docker) après ce changement ; sur Kubernetes, la base part de zéro.
2. **Miniature en base.** `app/models.py` : remplacer `thumbnail_path` par
   `thumbnail_jpeg`, colonne binaire nullable déclarée
   `LargeBinary().with_variant(mysql.MEDIUMBLOB(), "mysql", "mariadb")`. Un
   `BLOB` MariaDB est limité à 64 ko, `MEDIUMBLOB` laisse de la marge ; la
   variante garde SQLite, utilisé par les tests unitaires
   (`tests/conftest.py`). Même remarque que l'étape 1 sur la recréation de la
   base.
3. **Servir la miniature depuis la base.** `app/routers/catalog.py`, route
   `GET /api/catalog/videos/{video_id}/thumbnail` : remplacer le
   `FileResponse` sur le dossier `thumbs` (`resolve_thumbnail_path`) par
   `Response(content=video.thumbnail_jpeg, media_type="image/jpeg")`.
   `404 Vidéo introuvable` si la vidéo ou sa miniature manque, comme
   aujourd'hui quand le fichier est absent. Le chemin et le contrat ne
   changent pas.
4. **Plus de détection par présence de fichiers.** `app/import_catalog.py` :
   supprimer `qualities_for` et `subtitle_langs_for`, qui testent l'existence
   de fichiers dans `CATALOG_VIDEOS_DIR` et `CATALOG_SUBTITLES_DIR`.
   `CatalogEntry` reçoit deux champs lus dans le fixture, tous deux
   optionnels :
   - `qualities`, par défaut `["360p", "720p"]`, ce que `qualities_for`
     renvoie aujourd'hui pour une vidéo dont le fichier est présent ;
   - `subtitle_langs`, par défaut `[]`.
   `subtitle_formats_for` se calcule à partir de `subtitle_langs` (`["srt"]`
   si la liste n'est pas vide), comme aujourd'hui. `app/seed.py`,
   `_video_fields`, utilise ces champs et n'écrit plus de chemin de miniature ;
   la boucle finale `ensure_thumbnail` disparaît. Pour une vidéo uploadée,
   ces valeurs viennent du message (étape 9).
5. **Retirer le reste de l'accès aux fichiers.** Supprimer `app/media.py` (son
   code ffmpeg part dans Média, voir 6.4) et `tests/test_media.py`.
   `app/config.py` : retirer `CATALOG_VIDEOS_DIR`, `CATALOG_SUBTITLES_DIR`,
   `THUMBS_DIR`, `FFMPEG_TIMEOUT_SECONDS`, puis `CATALOG_DATA_DIR` une fois
   l'étape 6 faite. `Dockerfile` : retirer l'installation de ffmpeg et les
   `ENV` de ces chemins. `docker-compose.yml` : retirer les montages
   `datasets/videos` et `datasets/subtitles` et le volume `catalog-thumbs`.
6. **Verrou de synchronisation.** `catalog_sync_lock` (`app/seed.py`) pose un
   verrou `fcntl` sur un fichier de `CATALOG_DATA_DIR`. Sans volume, chaque
   pod a son propre système de fichiers : le verrou ne sérialise plus les deux
   réplicas. Le remplacer par un verrou dans Base Catalog,
   `SELECT GET_LOCK('catalog_sync', 30)` puis `RELEASE_LOCK` sur la même
   connexion ; sous SQLite (tests), pas de verrou.
7. `app/messaging.py` (nouveau) : publication et consommation, démarrées dans
   le `lifespan` de `app/main.py`, après la synchronisation des fixtures.
8. Au démarrage, après la synchronisation des fixtures : publier
   `video.published` pour chaque vidéo en base et `video.removed` pour chaque
   vidéo supprimée. Cela remplit `video_refs` côté Auth. Avec deux réplicas,
   les doublons sont absorbés par l'upsert d'Auth.
9. Subscriber de `catalog.video-uploaded` (traitement SQL dans
   `asyncio.to_thread`) :
   1. message déjà traité (`processed_events`) : republier `video.published`
      si la vidéo existe, puis ack ;
   2. `origin = dataset` : si une ligne `fixture` existe pour `video_id`,
      n'écrire que `thumbnail_jpeg` (le fixture reste la source des
      métadonnées, de la durée et des qualités) ; sinon, log et ack, sans
      `video.rejected` : ce fichier ne fait partie d'aucune saga d'upload ;
   3. `origin = upload` : valider `title` et `channel_id` non vides, `tags`
      en liste, `duration_seconds >= 1` (exigé par le contrat), miniature
      base64 décodable, commençant par les octets JPEG `FF D8`, 256 ko au
      plus. Si un contrôle échoue : publier `video.rejected` avec le `reason`
      correspondant, insérer `processed_events`, commit, ack ;
   4. sinon, dans une transaction : upsert de `Video` (`source=upload`,
      `featured=False`, `thumbnail_jpeg`, `duration_seconds` et `qualities`
      du message, `subtitle_langs` vide), de ses `Tag` et de
      `processed_events` ;
   5. commit, publication confirmée de `video.published`, puis ack. Une panne
      entre le commit et la publication provoque une relivraison, traitée par
      le cas 1 : l'annonce n'est pas perdue.
10. `thumbnail_url` : `app/serialize.py` écrit en dur
    `/api/catalog/videos/{id}/thumbnail`. La Gateway v2 ajoute
    `X-Forwarded-Prefix: /api/v2` ; le Catalog construit l'URL avec ce
    préfixe, `/api` par défaut. La v1 ne change pas.
11. `app/config.py` : `CATALOG_AMQP_URL`, et un mot de passe de base passé à
    part comme dans Auth (`CATALOG_DB_PASSWORD`) au lieu des identifiants en
    clair de `docker-compose.yml`.
12. `requirements.txt` : `aio-pika`.
13. `tests/` : `conftest.py` ne crée plus les dossiers `videos` et
    `subtitles` ni les variables associées, et la fixture `thumb_jpeg` écrit
    la miniature en base ; adapter `test_thumbnail.py` et `test_db_fields.py`
    (qui vérifie `thumbnail_path`). Nouveaux tests : seed qui garde les lignes
    `upload`, Subscriber idempotent, `video.rejected` sur message invalide,
    miniature `dataset` posée sur une ligne `fixture`, `thumbnail_url` avec et
    sans préfixe.

### 6.4 Service Média (`services/upload/`, squelette Upload étendu)

Le squelette Upload devient le Service Média. Il reçoit les uploads **et** sert
la lecture : le service qui stocke les fichiers vidéo doit être celui qui les
écrit et les lit. Sa seule donnée est le Stockage vidéo (`/data/videos`), qu'il
ne partage qu'avec ses propres réplicas.

- Le dossier garde son nom, `services/upload`, pour limiter le refactor. Le
  renommer en `services/media` est optionnel (voir 10).
- Port `8003` : c'est déjà le défaut de `GATEWAY_STREAMING_URL` dans la
  Gateway. Le conflit de port relevé en section 1 disparaît.

1. Supprimer `app/catalog_client.py` et l'appel `ensure_catalog_ready()` dans
   `app/routers/upload.py`. Supprimer `UPLOAD_CATALOG_URL` et
   `UPLOAD_CATALOG_TIMEOUT_SECONDS` de `app/config.py`, `.env.example`,
   `docker-compose.yml`, et l'appel `config.catalog_timeout_seconds()` de
   `prepare_runtime` (`app/main.py`). Supprimer `tests/test_catalog_ready.py`
   et `tests/test_upload_catalog_gate.py`.
2. Identité : la route d'upload n'est joignable que par `/api/v2/upload`, donc
   après la vérification du JWT par la Gateway. Remplacer
   `require_authenticated_user` (`app/auth.py`) par une dépendance qui lit
   `X-User-Id` (sinon 401) et `X-Channel-Id` (sinon `403`, compte non
   créateur). La clé publique n'est plus nécessaire dans Média :
   `load_jwt_settings` disparaît de `app/config.py` et de `prepare_runtime`.
3. `app/routers/upload.py`, `POST /api/upload/videos` en multipart : champs
   `file`, `title` (obligatoire), `description`, `tags`.
   1. accepter seulement `video/mp4` (`415` sinon) : Média sert des MP4 et
      aucune conversion n'est prévue ; taille maximale configurable ;
   2. générer `video_id` (UUID hexadécimal, 32 caractères) ;
   3. écrire le fichier en flux dans `{video_id}.mp4.part`, puis renommer en
      `{video_id}.mp4` (`os.replace`) : personne ne lit un fichier à moitié
      écrit ;
   4. durée avec `ffprobe` : fichier illisible ou durée inférieure à 1 s,
      supprimer le fichier et répondre `422 Vidéo illisible`. Ce contrôle
      local évite de lancer une saga pour un fichier cassé ;
   5. miniature avec `make_thumbnail` (étape 4), encodée en base64 ;
   6. publier `video.uploaded` (`origin=upload`) avec confirmation du Broker ;
   7. répondre `202` avec `{"video_id": "...", "status": "processing"}`.
   En cas d'échec de publication : supprimer le fichier, répondre
   `503 Service indisponible`. La route devient `async def` pour lire le
   fichier en flux et publier avec aio-pika ; `ffprobe` et `ffmpeg` sont des
   sous-processus bloquants, lancés avec `asyncio.to_thread`.
4. `app/media.py` (nouveau, repris de `services/catalog/app/media.py`) :
   `probe_duration(path)` et `make_thumbnail(path) -> bytes | None`. Même
   commande ffmpeg qu'`ensure_thumbnail` (capture à 30 s, une image, timeout
   `FFMPEG_TIMEOUT_SECONDS`), avec trois changements :
   - sortie en mémoire (`-f image2pipe -c:v mjpeg -`) au lieu d'un fichier
     dans `thumbs/` ;
   - réduction `-vf scale=480:-2` : la commande actuelle garde la résolution
     d'origine, trop lourde pour un message ;
   - repli sur une capture à 1 s pour les vidéos de moins de 30 s.
5. `app/routers/stream.py` (nouveau) : `GET` et `HEAD
   /api/stream/{video_id}?quality=...`, route publique, conforme au contrat v1
   existant :
   - `video_id` contrôlé par une expression régulière
     (`^[A-Za-z0-9_-]{1,64}$`) avant toute construction de chemin ;
   - `quality` hors de `360p`, `720p` : `400 Qualité inconnue (360p ou 720p)`.
     Un seul fichier existe par vidéo : la qualité est validée mais ne change
     pas le fichier servi ;
   - fichier `UPLOAD_DATA_DIR/{video_id}.mp4` absent :
     `404 Vidéo introuvable` ;
   - sans `Range` : `200`, fichier entier ; avec `Range: bytes=a-b` : `206`,
     `Content-Range`, `Accept-Ranges: bytes`. Vérifier si le `FileResponse` de
     la version de Starlette utilisée gère `Range` ; sinon, un générateur qui
     lit la plage par blocs suffit.
   Le routeur v1 de la Gateway (`/api/stream/*`) vise déjà le port 8003 : la
   lecture fonctionne aussi en v1 dès cette étape.
6. `app/messaging.py` (nouveau) : publication avec confirmation, et
   Subscriber de `media.video-rejected`, démarré dans le `lifespan` : contrôle
   de `video_id` par la même expression régulière, suppression de
   `{video_id}.mp4` (et d'un éventuel `.part`), log du `reason`, ack. C'est
   l'action de compensation de la saga (voir 2.2).
7. **Chargement du jeu de démonstration.** `app/announce.py` (nouveau),
   commande ponctuelle `python -m app.announce` : pour chaque
   `{video_id}.mp4` du volume, durée, miniature, puis publication de
   `video.uploaded` avec `origin=dataset` et sans métadonnées. Le Catalog n'en
   retient que la miniature, pour les vidéos de son fixture (voir 6.3,
   étape 9). Relancer la commande est sans risque (upsert). Elle n'est pas
   lancée au démarrage du service : avec deux réplicas, chaque miniature
   serait calculée et publiée deux fois. Copie des fichiers dans le volume :
   voir 7.4.
8. `app/config.py` : `UPLOAD_DATA_DIR` pointe vers le dossier du Stockage
   vidéo (`/data/videos`), `UPLOAD_AMQP_URL`, taille maximale d'upload.
   `/health` répond `{"status": "ok", "service": "media"}`.
9. `Dockerfile` : installer ffmpeg (mêmes lignes que l'actuel `Dockerfile` du
   Catalog), `ENV UPLOAD_DATA_DIR=/data/videos`. `docker-compose.yml` : un
   volume nommé `media-videos` sur `/data/videos` à la place de
   `upload-incoming`.
10. `requirements.txt` : ajouter `aio-pika` ; retirer `PyJWT[crypto]` et
    `cryptography` une fois l'étape 2 faite.
11. `tests/`, `docs/API.md`, `README.md` : nouveau contrat d'upload (202, 403,
    415, 422), lecture (200, 206, 400, 404), Subscriber `video.rejected`
    (fichier supprimé, second message sans effet), commande `announce`.

### 6.5 Application web (`frontend/`)

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

## 7. Kubernetes

### 7.1 Objets

| Objet | Nom | Rôle |
|-------|-----|------|
| Namespace | `stream321` | isole toute l'application |
| Deployment + Service ClusterIP | `spa` (x2), `gateway` (x2), `auth` (x2), `catalog` (x2) | services sans état, sondes sur `/health` ; le Catalog n'a plus aucun volume |
| Deployment + Service ClusterIP | `media` (x2), image construite depuis `services/upload` | Service Média, sondes sur `/health` ; seul à monter le PVC `media-videos` |
| StatefulSet + PVC + Service | `auth-db`, `catalog-db` (MariaDB 11), `rabbitmq` (RabbitMQ 3), x1 chacun | données persistantes, une base par service |
| PersistentVolumeClaim | `media-videos` (ReadWriteMany) | Stockage vidéo, privé au Service Média, partagé entre ses deux réplicas |
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

### 7.2 Arborescence proposée

```text
k8s/
  kustomization.yaml       # kubectl apply -k k8s/
  namespace.yaml
  config/
    configmap.yaml
    secret.example.yaml    # clés sans valeurs ; le vrai Secret n'est pas versionné
  storage/
    media-videos-pvc.yaml  # monté par apps/media.yaml seulement
  data/
    auth-db.yaml           # StatefulSet + Service
    catalog-db.yaml
    rabbitmq.yaml
  apps/
    spa.yaml               # Deployment + Service
    gateway.yaml
    auth.yaml
    catalog.yaml           # aucun volume
    media.yaml             # Deployment media (x2) + PVC media-videos
  ingress.yaml
```

### 7.3 Découverte de services

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
  GATEWAY_UPLOAD_URL: http://media:8003
  GATEWAY_STREAMING_URL: http://media:8003
  AMQP_HOST: rabbitmq
```

Les URLs AMQP contiennent des identifiants : les construire dans le manifeste à
partir du Secret (`env` avec `valueFrom.secretKeyRef`, puis
`value: amqp://$(AMQP_USER):$(AMQP_PASSWORD)@rabbitmq:5672/`).

`host.docker.internal`, `extra_hosts` et les ports publiés disparaissent. Les
fichiers compose restent utilisables pour développer un service seul.

### 7.4 Stockage vidéo du Service Média

Un seul PVC, `media-videos`, monté **uniquement** par le Deployment `media`,
en entier et en lecture-écriture sur `/data/videos`. Aucun autre Deployment ne
le référence. Le Catalog et les autres services n'ont aucun volume de fichiers.

```yaml
# k8s/apps/media.yaml (extrait)
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: media
          ports: [{ containerPort: 8003 }]
          readinessProbe: { httpGet: { path: /health, port: 8003 } }
          livenessProbe: { httpGet: { path: /health, port: 8003 }, failureThreshold: 6 }
          volumeMounts:
            - { name: videos, mountPath: /data/videos }
      volumes:
        - name: videos
          persistentVolumeClaim: { claimName: media-videos }
```

ReadWriteMany parce que les deux réplicas de Média partagent le volume : c'est
le partage autorisé entre instances d'un même microservice (06 - DB dans un
système distribué, p.7). Avec un seul réplica, ReadWriteOnce suffit. Sur un
cluster d'un seul nœud (minikube, kind), un volume `hostPath` convient ; sur
plusieurs nœuds, il faut une StorageClass RWX (NFS, CephFS, Longhorn). Les deux
réplicas n'écrivent jamais le même fichier : chaque upload a un `video_id`
neuf, l'écriture passe par `.part` puis `os.replace`, et la suppression est
idempotente.

Chargement du jeu de démonstration (`datasets/` n'est pas versionné), une
fois, après le déploiement :

```sh
kubectl -n stream321 cp datasets/videos/. <pod media>:/data/videos/
kubectl -n stream321 exec deploy/media -- python -m app.announce
```

La copie passe par un pod de Média lui-même : aucun autre pod ne monte le
volume. `announce` publie un `video.uploaded` (`origin=dataset`) par fichier ;
le Catalog range chaque miniature dans sa base, sans lire de fichier (voir
6.3, étape 9, et 6.4, étape 7). En local, depuis `services/upload/` :
`docker compose cp ../../datasets/videos/. upload:/data/videos/`, puis
`docker compose exec upload python -m app.announce`.

### 7.5 Ingress

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

## 8. Plan de migration

Chaque étape est une PR vers `dev` qui laisse la v1 fonctionnelle. Les étapes
d'un même service peuvent être des commits successifs sur la même branche (voir
[`CONTRIBUTING.md`](../../CONTRIBUTING.md)).

| # | Étape | Terminé quand | Exigence |
|---|-------|---------------|----------|
| 1 | SPA : proxy Vite vers la Gateway (6.5 étape 1) | La SPA fonctionne avec le Catalog seulement joignable par la Gateway ; les requêtes apparaissent dans les journaux de la Gateway. | API Gateway |
| 2 | Gateway : routeur v2 transparent pour auth, catalog, stream, avec retrait de `/v2` et 404 (6.1 étapes 5, 6) | `curl /api/v2/catalog/videos` renvoie la même chose que `/api/catalog/videos` ; tests v1 inchangés et verts. | API Gateway |
| 3 | Auth : claim `channel_id` dans le JWT (6.2 étape 1) | Un login créateur renvoie un token avec `channel_id` ; Upload et Auth acceptent toujours les tokens. | prérequis de 4 et 9 |
| 4 | Gateway : validation du JWT et en-têtes d'identité sur v2 (6.1 étapes 1 à 3) | `GET /api/v2/auth/me` sans token : 401 renvoyé par la Gateway ; un `X-User-Id` envoyé par le client n'atteint pas Auth (test). | API Gateway |
| 5 | Gateway : `forward_v2` (flux, `Range`) et route upload (6.1 étape 4) | Test : `Range` transmis et 206 renvoyé ; un gros fichier traverse la Gateway sans hausse mémoire notable. | API Gateway |
| 6 | Média, lecture : route `/api/stream/{id}` dans `services/upload`, volume `media-videos`, copie du jeu de démonstration (6.4 étapes 5, 8, 9 ; 7.4) | `curl -H 'Range: bytes=0-1023' /api/v2/stream/{id}` renvoie 206 et 1024 octets ; la vidéo se lit et se parcourt dans le lecteur, en v1 comme en v2. Média lit sa propre copie du jeu de démonstration, jamais le montage du Catalog, qui ne change pas. | une base par microservice, aucun appel direct |
| 7 | Broker : RabbitMQ (compose dédié en attendant Kubernetes) et module `messaging.py` | L'interface de gestion RabbitMQ montre `stream321.events` et les queues des services démarrés. | MOM |
| 8 | Catalog : seed corrigé, colonne `thumbnail_jpeg`, publications au démarrage, Subscriber `video.uploaded` avec publication de `video.rejected`, `X-Forwarded-Prefix` (6.3 étapes 1 à 3, 7 à 12). Pendant la transition, la route de miniature sert la colonne si elle est remplie, sinon l'ancien fichier. | Un `video.uploaded` (`origin=upload`, avec miniature) publié à la main depuis l'interface RabbitMQ crée la vidéo, dont la miniature est servie depuis la base ; un message invalide produit un `video.rejected` ; un redémarrage n'efface pas la vidéo ; les miniatures v1 du jeu de démonstration s'affichent toujours. | MOM |
| 9 | Média, upload : identité par en-têtes, écriture, miniature, publication, 202, Subscriber `video.rejected`, commande `announce`, suppression de l'appel au Catalog (6.4 étapes 1 à 4, 6, 7, 10, 11) | Upload via `/api/v2/upload/videos` → 202 ; la vidéo apparaît au catalogue avec sa miniature. Catalog arrêté pendant l'upload : 202 quand même, la vidéo apparaît à son redémarrage. Message rejeté : le fichier est supprimé. `announce` remplit la miniature des dix vidéos du fixture dans Base Catalog. | MOM (Média + Catalog), saga, aucun appel direct |
| 10 | Catalog : retrait de tout accès aux fichiers (6.3 étapes 3 à 6, 13 ; fin du repli de l'étape 8) | Le Catalog démarre sans aucun volume, avec une image sans ffmpeg ; miniatures et qualités inchangées dans `/api/catalog/videos` et `/api/v2/catalog/videos` ; `CATALOG_VIDEOS_DIR` n'apparaît plus dans `services/catalog`. | une base par microservice |
| 11 | Auth : favoris, `video_refs`, Subscriber (6.2 étapes 2 à 8) | Favori sur une vidéo existante : 201 ; inconnue : 404 ; même résultat avec le Catalog arrêté ; une vidéo uploadée devient ajoutable en favori. | MOM (troisième service), aucun appel direct |
| 12 | SPA en v2 : `API_BASE`, favoris, page d'upload, Dockerfile nginx (6.5 étapes 2 à 5) | Plus aucun appel `/api/` hors `/api/v2` dans `frontend/src` ; parcours complet (connexion, lecture, favori, upload) en v2. | API Gateway |
| 13 | Kubernetes : manifestes `k8s/` (section 7) | `kubectl apply -k k8s/` ; tous les pods prêts ; l'application fonctionne par l'Ingress seulement ; supprimer un pod du Catalog ou de Média ne coupe pas le service ; `media-videos` n'est référencé que par `apps/media.yaml`. | déploiement cible, une base par microservice |
| 14 | Dépréciation puis retrait de la v1 (4.6) | Contrat v1 marqué `deprecated`, puis routeurs v1 supprimés de la Gateway ; tests et contrat à jour. | API Gateway |

Récapitulatif des exigences :

| Exigence | Satisfaite par les étapes |
|----------|---------------------------|
| API Gateway, point d'entrée unique | 1, 2, 4, 5, 12, 13 (Ingress `/api` → Gateway seulement) |
| MOM utilisé par au moins deux microservices | 7, 8, 9 (Média et Catalog), 11 (Auth en plus) |
| Aucun appel direct entre microservices | 6, 9, 11 |
| Une base par microservice, aucun stockage partagé entre services | 6, 8, 10, 13 |
| Présentation de la stack et des composants | [`README.md`](README.md) et les deux workspaces C4 |

## 9. Limites acceptées et hors périmètre

La cible n'est volontairement pas parfaite. Ces points sont connus et assumés :

- **Volume RWX entre les réplicas de Média** au lieu d'un stockage objet (S3,
  MinIO). Le partage reste dans un seul microservice (06 - DB dans un système
  distribué, p.7), mais demande une StorageClass RWX sur plusieurs nœuds.
- **Média cumule réception et lecture** : un pic d'uploads (ffmpeg, écriture
  disque) peut ralentir la lecture, et les deux fonctions passent à l'échelle
  ensemble. Les séparer en deux services ferait revenir un stockage partagé.
- **Miniatures dans le corps des messages** : seulement un JPEG réduit
  (quelques dizaines de ko, 256 ko au plus), jamais la vidéo.
- **Limite de tentatives de login en mémoire**, par réplica : avec deux
  réplicas d'Auth, la limite réelle est jusqu'à deux fois plus haute.
- **Bases et Broker en une seule instance** : pas de haute disponibilité des
  données. Un arrêt de RabbitMQ bloque l'upload (pas les lectures).
- **Confiance dans les en-têtes d'identité** : les services croient
  `X-User-Id` parce que seuls les pods du cluster peuvent les joindre
  (Services ClusterIP). Aucune NetworkPolicy n'est prévue.
- **Fichier orphelin après `video.removed`** : seul Auth s'abonne à
  `video.removed`. Le MP4 d'une vidéo retirée du catalogue reste dans le
  Stockage vidéo. Média pourra s'y abonner plus tard, avec sa propre queue,
  sans toucher au Catalog (mode Topic).
- **Pas de conversion vidéo** : un seul fichier MP4 par vidéo ; le paramètre
  `quality` est validé mais ne change rien.
- **Pas d'observabilité** : ni métriques, ni traces, ni journaux centralisés.
- **Hors périmètre** : services Subtitles et Recommendation, HLS, outil de
  migration de schéma (Alembic). Le Catalog ne détecte plus les qualités et
  les langues de sous-titres par la présence de fichiers : elles viennent du
  fixture ou du message `video.uploaded`.

## 10. Décisions de détail à valider

Points que la cible ne fixe pas et que ce guide propose. À confirmer en équipe
avant l'étape concernée :

| Point | Proposition | Étape |
|-------|-------------|-------|
| Source du `channel_id` pour Média | Claim `channel_id` dans le JWT, injecté par la Gateway en `X-Channel-Id` | 3, 4 |
| Nom du dossier du Service Média | Garder `services/upload` ; le renommer en `services/media` est optionnel (chemins de CI, compose, README à suivre) | 6 |
| Variables de la Gateway vers Média | `GATEWAY_UPLOAD_URL` et `GATEWAY_STREAMING_URL` séparées, toutes deux sur `http://media:8003` | 5, 13 |
| Contenu de `GET /api/v2/auth/favorites` | `videos` réduit à `id`, `title`, `channel_id` ; la SPA charge le reste depuis le Catalog | 11, 12 |
| `thumbnail_url` en v2 | En-tête `X-Forwarded-Prefix` posé par la Gateway | 8 |
| Stockage de la miniature | Colonne `thumbnail_jpeg` en `MEDIUMBLOB`, JPEG 480 px de large, 256 ko au plus | 8, 9 |
| Motifs de `video.rejected` | `invalid_metadata`, `invalid_duration`, `invalid_thumbnail` ; une erreur transitoire n'est jamais un rejet | 8, 9 |
| Chargement du jeu de démonstration | Copie dans le volume de Média, puis `python -m app.announce` qui publie `video.uploaded` avec `origin=dataset` ; le Catalog n'en retient que la miniature | 9 |
| Qualités et langues de sous-titres | Champs optionnels `qualities` (défaut `["360p", "720p"]`) et `subtitle_langs` (défaut `[]`) dans le fixture ; pour un upload, `qualities` vient du message | 10 |
| Verrou de synchronisation du Catalog | `GET_LOCK` MariaDB à la place du verrou `fcntl` sur fichier | 10 |
| Formulaire d'upload | multipart `file`, `title`, `description`, `tags` ; MP4 seulement ; réponse `{video_id, status}` | 9 |
| Identifiant d'une vidéo uploadée | UUID hexadécimal généré par Média | 9 |
| Vidéos supprimées du catalogue | `video.removed` émis quand la synchronisation des fixtures retire une vidéo ; Auth supprime aussi les favoris associés | 8, 11 |
| RabbitMQ en local avant Kubernetes | Compose dédié, sur le modèle des autres services | 7 |
