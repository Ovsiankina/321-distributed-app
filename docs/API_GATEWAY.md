# API Gateway

> **Statut : partiel (E0-05, E1-05, E0-09, v2).** Les sections remplies ci-dessous sont stables.
> Tout ce qui reste en _TODO_ n'est pas défini.
>
> **Deux versions.** La v1 (`/api/*`) est le contrat en service ; elle ne change
> plus. La v2 (`/api/v2/*`) est le contrat cible, décrit en
> [Version 2](#version-2-apiv2) : il est stable, mais pas encore servi par la
> Gateway. Tout nouveau développement vise la v2.
>
> **Ne pas implémenter une section en _TODO_. Ça cassera.** Attendre qu'elle
> soit finalisée et marquée stable.
>
> Dès qu'une section est stable, toute API doit s'y conformer, ainsi qu'à
> [`api/gateway.openapi.yaml`](api/gateway.openapi.yaml). Les schémas et les
> exemples vivent dans le fichier OpenAPI. En cas d'écart, le YAML fait foi
> et ce fichier est mis à jour dans la même PR
> (voir [`CONTRIBUTING.md`](../CONTRIBUTING.md)).

## Conventions

- Préfixe public : `/api`. Exception : `GET /health`.
- Erreur produite par la Gateway : `Content-Type: application/json`, corps `{ "detail": "<message>" }`.
- Les headers `Authorization` et `Content-Type` sont forwardés tels quels vers le microservice.
- `Authorization: Bearer <JWT>` est requis sur `GET /api/auth/me` et sur `GET|POST|DELETE /api/auth/favorites/*`. Il est émis par `POST /api/auth/register` et `POST /api/auth/login`. Catalogue, recherche et streaming n'exigent pas de JWT.
- Le client n'appelle aucun microservice directement.

**Port d'écoute (E0-04) :** `8000` en local et en Docker (`GATEWAY_PORT`). Origine client : `http://127.0.0.1:8000/`. Implémentation : `services/gateway/`.

### Versions

- La version est dans le chemin : `/api/...` est la v1, `/api/v2/...` est la v2. `GET /health` n'est pas versionné.
- La v1 est figée : ni ajout, ni modification, ni suppression de route, jusqu'à son retrait. Toute évolution va en v2.
- Les microservices ne connaissent pas la version. La Gateway retire le segment `/v2` avant de transmettre : `/api/v2/catalog/videos` arrive au Catalog sous la forme `/api/catalog/videos`. Un microservice ne déclare jamais de route `/api/v2/...`.
- Une modification incompatible de la v2, une fois servie, demandera une `/api/v3`.

## Points d'entrée

Méthode, chemin et codes seulement. Les schémas et les exemples sont dans le fichier OpenAPI, pas recopiés ici.

| Méthode | Chemin | Comportement | Codes |
|---------|--------|--------------|-------|
| GET | `/health` | Réponse Gateway | 200 |
| GET | `/api/home` | Réponse Gateway, stub (`sections` vide) | 200, 502 |
| POST | `/api/auth/register` | Crée un compte, retourne un JWT | 201, 400, 409, 502 |
| POST | `/api/auth/login` | Retourne un JWT | 200, 400, 401, 429, 502 |
| GET | `/api/auth/me` | Profil, JWT requis | 200, 401, 502 |
| GET | `/api/auth/favorites` | Liste des favoris, JWT requis | 200, 401, 502 |
| POST | `/api/auth/favorites/{video_id}` | Ajoute un favori, JWT requis | 201, 401, 404, 502 |
| DELETE | `/api/auth/favorites/{video_id}` | Retire un favori, JWT requis | 204, 401, 502 |
| GET | `/api/catalog/videos` | Liste du catalogue | 200, 502 |
| GET | `/api/catalog/featured` | Vidéos mises en avant | 200, 502 |
| GET | `/api/catalog/search` | Recherche, query `q` | 200, 502 |
| GET | `/api/catalog/videos/{video_id}` | Détail d'une vidéo | 200, 404, 502 |
| GET | `/api/catalog/videos/{video_id}/thumbnail` | Vignette JPEG | 200, 404, 502 |
| GET | `/api/stream/{video_id}` | MP4 progressif, query `quality`, header `Range` pour le 206 | 200, 206, 400, 404, 502 |
| * | `/api/subtitles/*` | Proxy, corps non contracté | 404, 502 |

Hors de ces chemins : 404.

_TODO : pour chaque endpoint restant, définir la méthode, le chemin, le schéma de requête, le schéma de réponse, les codes et des exemples (tags du catalogue, HLS, fichiers de sous-titres)._

## Version 2 (`/api/v2`)

La v2 est l'API de l'architecture cible ([`ARCHITECTURE.md`](ARCHITECTURE.md)). Les conventions de la v1 s'appliquent, sauf mention contraire ci-dessous.

**État : contrat stable, pas encore servi.** Chaque route s'implémente à l'étape indiquée du [plan de migration](architecture/MIGRATION_V2.md#8-plan-de-migration), pas avant et pas dans un autre ordre. Les deux routes marquées « à confirmer » ne s'implémentent qu'après validation en équipe de leur corps.

### Ce qui change par rapport à la v1

- **La Gateway vérifie le JWT.** Sur les routes « JWT requis », elle contrôle `Authorization: Bearer <JWT>` (signature Ed25519, algorithme `EdDSA` seulement, `iss`, `aud`, `exp`, tolérance d'horloge de 30 s). JWT absent ou invalide : la Gateway répond `401 Authentification requise` sans appeler le microservice.
- **En-têtes d'identité.** Après vérification, la Gateway transmet au microservice `X-User-Id` (claim `sub`) et, si le claim existe, `X-Channel-Id` (claim `channel_id`). Un `X-User-Id` ou un `X-Channel-Id` envoyé par le client est toujours retiré. `Authorization` reste transmis.
- **En-têtes transmis au microservice** (liste fermée) : `Authorization`, `Content-Type`, `Content-Length`, `Range`, `If-Range`, les deux en-têtes d'identité, et `X-Forwarded-Prefix: /api/v2`.
- **Corps en flux.** La Gateway ne charge en mémoire ni le corps de la requête, ni celui de la réponse. `Range`, `Content-Range`, `Accept-Ranges`, `Content-Length` et le code `206` passent tels quels.
- **Chemins des réponses.** `thumbnail_url` commence par `/api/v2`.
- **Envoi asynchrone.** `POST /api/v2/upload/videos` répond `202` : la vidéo est acceptée, elle apparaît au catalogue plus tard. Il n'existe pas de route d'état ; le client consulte le catalogue.

### Points d'entrée v2

| Méthode | Chemin | Service, chemin reçu | JWT requis | Codes | Étape |
|---------|--------|----------------------|------------|-------|-------|
| POST | `/api/v2/auth/register` | Auth, `/api/auth/register` | non | 201, 400, 409, 502 | 2 |
| POST | `/api/v2/auth/login` | Auth, `/api/auth/login` | non | 200, 400, 401, 429, 502 | 2 |
| GET | `/api/v2/auth/me` | Auth, `/api/auth/me` | oui | 200, 401, 502 | 2, 4 |
| GET | `/api/v2/auth/favorites` | Auth, `/api/auth/favorites` | oui | 200, 401, 502 | 11, à confirmer |
| POST | `/api/v2/auth/favorites/{video_id}` | Auth, `/api/auth/favorites/{video_id}` | oui | 201, 401, 404, 502 | 11 |
| DELETE | `/api/v2/auth/favorites/{video_id}` | Auth, `/api/auth/favorites/{video_id}` | oui | 204, 401, 502 | 11 |
| GET | `/api/v2/catalog/videos` | Catalog, `/api/catalog/videos` | non | 200, 502 | 2 |
| GET | `/api/v2/catalog/featured` | Catalog, `/api/catalog/featured` | non | 200, 502 | 2 |
| GET | `/api/v2/catalog/search` | Catalog, `/api/catalog/search` | non | 200, 502 | 2 |
| GET | `/api/v2/catalog/videos/{video_id}` | Catalog, `/api/catalog/videos/{video_id}` | non | 200, 404, 502 | 2 |
| GET | `/api/v2/catalog/videos/{video_id}/thumbnail` | Catalog, `/api/catalog/videos/{video_id}/thumbnail` | non | 200, 404, 502 | 2 |
| GET, HEAD | `/api/v2/stream/{video_id}` | Média, `/api/stream/{video_id}` | non | 200, 206, 400, 404, 502 | 5, 6 |
| POST | `/api/v2/upload/videos` | Média, `/api/upload/videos` | oui, compte créateur | 202, 401, 403, 413, 415, 422, 502, 503 | 5, 9, à confirmer |

Hors de ces chemins, sous `/api/v2` : `404 Route inconnue`. `/api/home` et `/api/subtitles/*` n'ont pas d'équivalent v2.

Différences de corps avec la v1 (schémas dans le fichier OpenAPI) :

| Route | Différence |
|-------|------------|
| `GET /api/v2/auth/favorites` | `videos` ne contient que `id`, `title`, `channel_id`. Le client charge le reste depuis le catalogue. **À confirmer.** |
| `POST /api/v2/auth/favorites/{video_id}` | Même corps. Auth valide la vidéo dans sa propre table, sans appeler le Catalog. |
| `GET /api/v2/catalog/*` | Même corps. `thumbnail_url` commence par `/api/v2`. |
| `POST /api/v2/upload/videos` | Nouvelle route. Requête `multipart/form-data` : `file` (MP4), `title`, `description`, `tags`. Réponse `{ "video_id": "...", "status": "processing" }`. **À confirmer.** |

### Fin de la v1

1. La v2 est servie à côté de la v1.
2. La SPA passe de `/api` à `/api/v2`.
3. La v1 est marquée `deprecated: true` dans le fichier OpenAPI, et la Gateway ajoute `Deprecation: true` à ses réponses v1.
4. Quand plus aucun client ne l'appelle, les routes v1 sont retirées : `/api/*` hors `/api/v2` répond `404`.

## Erreurs

| Code | `detail` | Cas |
|------|----------|-----|
| 400 | `Email invalide` | Champ `email` invalide ou absent (inscription, login) |
| 400 | `Mot de passe invalide` | Champ `password` invalide ou absent (inscription, login) |
| 400 | `Requête invalide` | JSON illisible ou champ inconnu (inscription, login) |
| 400 | `Qualité inconnue (360p ou 720p)` | Query `quality` du streaming |
| 401 | `Authentification requise` | JWT absent ou invalide sur `/me` et les favoris |
| 401 | `Identifiants incorrects` | Login |
| 404 | `Route inconnue` | Préfixe non géré par la Gateway |
| 404 | `Vidéo introuvable` | Vidéo, vignette ou fichier MP4 inconnu |
| 409 | `Cet email est déjà utilisé` | Inscription |
| 429 | `Trop de tentatives, réessayez plus tard` | Login : 10 échecs en 60 s pour un même email, header `Retry-After` |
| 502 | `Service indisponible` | Microservice injoignable |

Erreurs propres à la v2 :

| Code | `detail` | Cas |
|------|----------|-----|
| 401 | `Authentification requise` | JWT absent ou invalide sur une route « JWT requis ». Répondu par la Gateway. |
| 403 | `Compte créateur requis` | Envoi avec un JWT sans `channel_id` |
| 413 | `Fichier trop volumineux` | Envoi au-delà de la taille maximale |
| 415 | `Format non pris en charge (MP4 seulement)` | Envoi d'un fichier qui n'est pas `video/mp4` |
| 422 | `Vidéo illisible` | Envoi d'un fichier illisible ou de moins d'une seconde |
| 503 | `Service indisponible` | Envoi alors que le bus de messages est injoignable : rien n'est gardé, le client peut réessayer |

Le streaming répond aussi `206` quand la requête porte un header `Range`. Ce n'est pas une erreur.

## Tests

_TODO : décrire les tests de conformité que toute implémentation doit passer._

Tests attendus pour la v2, à livrer avec la route (`services/gateway/tests/`) :

- la route v2 renvoie la même réponse que la route v1 équivalente, et le microservice reçoit le chemin sans `/v2` ;
- une route « JWT requis » sans JWT, ou avec un JWT expiré, répond `401` sans appel au microservice ;
- un `X-User-Id` envoyé par le client n'atteint pas le microservice ;
- `Range` est transmis et le `206` revient avec `Content-Range` ;
- un chemin inconnu sous `/api/v2` répond `404 Route inconnue` ;
- les tests v1 passent sans modification.
