# API Gateway

> **Statut : partiel (E0-05).** Les sections remplies ci-dessous sont stables.
> Tout ce qui reste en _TODO_ n'est pas défini.
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
- Le client n'appelle aucun microservice directement.

_TODO : URL de base (le port d'écoute est fixé par E0-04), versioning, schéma d'authentification au-delà du simple forward du header._

## Points d'entrée

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

_TODO : pour chaque endpoint métier, définir la méthode, le chemin, le schéma de requête, le schéma de réponse, les codes et des exemples (E1-05)._

## Erreurs

Stable pour les erreurs produites par la Gateway :

| Code | `detail` | Cas |
|------|----------|-----|
| 404 | `Route inconnue` | Préfixe non géré par la Gateway |
| 502 | `Service indisponible` | Microservice injoignable |

Une 404 produite par le microservice est transmise telle quelle. Elle n'utilise pas forcément ce schéma.

_TODO : définir les codes d'erreur amont (400, 401, 409, ...) et quand ils s'appliquent._

## Tests

_TODO : décrire les tests de conformité que toute implémentation doit passer._
