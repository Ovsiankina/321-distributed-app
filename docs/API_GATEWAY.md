# API Gateway

> **Status: partial (E0-05, E1-05).** Les sections remplies ci-dessous sont stables.
> Tout ce qui reste en _TODO_ n'est pas défini.
>
> **Do not implement a TODO section. IT WILL BREAK.** Wait until that section
> is finalized and marked stable.
>
> Once a section is stable, every API MUST strictly comply with it and with
> [`api/gateway.openapi.yaml`](api/gateway.openapi.yaml). Schemas and examples
> live in the OpenAPI file. If the two diverge, the YAML wins and this file is
> updated in the same PR (see [`CONTRIBUTING.md`](../CONTRIBUTING.md)).

## Conventions

- Préfixe public : `/api`. Exception : `GET /health`.
- Erreur produite par la Gateway : `Content-Type: application/json`, corps `{ "detail": "<message>" }`.
- Les headers `Authorization` et `Content-Type` sont forwardés tels quels vers le microservice.
- `Authorization: Bearer <JWT>` est requis sur `GET /api/auth/me` et sur `GET|POST|DELETE /api/auth/favorites/*`. Il est émis par `POST /api/auth/register` et `POST /api/auth/login`. Catalogue, recherche et streaming n'exigent pas de JWT.
- Le client n'appelle aucun microservice directement.

_TODO: Base URL (le port d'écoute est fixé par E0-04), versioning._

## Endpoints

Méthode, chemin et codes seulement. Les schémas et les exemples sont dans le fichier OpenAPI, pas recopiés ici.

| Méthode | Chemin | Comportement | Codes |
|---------|--------|--------------|-------|
| GET | `/health` | Réponse Gateway | 200 |
| GET | `/api/home` | Réponse Gateway, stub (`sections` vide) | 200, 502 |
| POST | `/api/auth/register` | Crée un compte, retourne un JWT | 201, 400, 409, 502 |
| POST | `/api/auth/login` | Retourne un JWT | 200, 401, 502 |
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

_TODO: For each remaining endpoint define: method, path, request schema, response schema, status codes, and examples (catalogue tags, HLS, fichiers de sous-titres)._

## Errors

| Code | `detail` | Cas |
|------|----------|-----|
| 400 | `Email invalide` | Corps d'inscription invalide |
| 400 | `Qualité inconnue (480p ou 720p)` | Query `quality` du streaming |
| 401 | `Authentification requise` | JWT absent ou invalide sur `/me` et les favoris |
| 401 | `Identifiants incorrects` | Login |
| 404 | `Route inconnue` | Préfixe non géré par la Gateway |
| 404 | `Vidéo introuvable` | Vidéo, vignette ou fichier MP4 inconnu |
| 409 | `Cet email est déjà utilisé` | Inscription |
| 502 | `Service indisponible` | Microservice injoignable |

Le streaming répond aussi `206` quand la requête porte un header `Range`. Ce n'est pas une erreur.

## Testing

_TODO: Describe the conformance tests every API implementation must pass._
