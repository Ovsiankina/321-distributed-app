# API Gateway

> **Status: partial (E0-05).** Les sections remplies ci-dessous sont stables.
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
- Le client n'appelle aucun microservice directement.

_TODO: Base URL (le port d'écoute est fixé par E0-04), versioning, schéma d'authentification au-delà du simple forward du header._

## Endpoints

Stable pour E0-05. Méthode, chemin et codes Gateway seulement. Les schémas de requête et de réponse sont dans le fichier OpenAPI, pas recopiés ici.

| Méthode | Chemin | Comportement | Codes Gateway |
|---------|--------|--------------|---------------|
| GET | `/health` | Réponse Gateway | 200 |
| GET | `/api/home` | Réponse Gateway, stub (`sections` vide tant que le catalogue n'est pas contracté) | 200, 502 |
| * | `/api/auth/*` | Proxy vers Auth | 404, 502 |
| * | `/api/catalog/*` | Proxy vers Catalog | 404, 502 |
| * | `/api/stream/*` | Proxy vers Streaming | 404, 502 |
| * | `/api/subtitles/*` | Proxy vers Subtitles | 404, 502 |

Hors de ces préfixes : 404.

_TODO: For each business endpoint define: method, path, request schema, response schema, status codes, and examples (E1-05)._

## Errors

Stable pour les erreurs produites par la Gateway :

| Code | `detail` | Cas |
|------|----------|-----|
| 404 | `Route inconnue` | Préfixe non géré par la Gateway |
| 502 | `Service indisponible` | Microservice injoignable |

Une 404 produite par le microservice est transmise telle quelle. Elle n'utilise pas forcément ce schéma.

_TODO: Define upstream error codes (400, 401, 409, ...) and when they apply._

## Testing

_TODO: Describe the conformance tests every API implementation must pass._
