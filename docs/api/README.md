# Contrat API Gateway

Source normative des routes : [`gateway.openapi.yaml`](gateway.openapi.yaml) (OpenAPI 3.0.3).

Périmètre : santé, stub `GET /api/home`, routes Sprint 1 (auth, catalogue, recherche, streaming MP4), et le préfixe proxy `/api/subtitles/*` sans corps métier.

Hors de ce contrat : liste des tags, HLS, fichiers de sous-titres.

## Visualiser

[Swagger Editor](https://editor.swagger.io/) : File, Import file.

## Modifier le contrat

1. Modifier `gateway.openapi.yaml`.
2. Si le routage change (préfixe, code Gateway, format d'erreur), aligner [`../API_GATEWAY.md`](../API_GATEWAY.md) dans la même PR. Ne pas y recopier les schémas.
3. Review de Dmytro obligatoire dès qu'une PR ajoute, modifie ou supprime un endpoint.
4. Ne pas ajouter ici les routes encore hors contrat (tags, HLS, fichiers de sous-titres).
