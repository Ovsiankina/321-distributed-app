# Contrat API Gateway

Source normative des routes : [`gateway.openapi.yaml`](gateway.openapi.yaml) (OpenAPI 3.0.3).

Périmètre de ce fichier : santé, stub `GET /api/home`, préfixes proxy. Les routes métier du sprint 1 ne s'ajoutent pas ici tant que l'issue E1-05 n'est pas ouverte en implémentation.

## Visualiser

[Swagger Editor](https://editor.swagger.io/) : File, Import file.

## Modifier le contrat

1. Modifier `gateway.openapi.yaml`.
2. Si le routage change (préfixe, code Gateway, format d'erreur), aligner [`../API_GATEWAY.md`](../API_GATEWAY.md) dans la même PR. Ne pas y recopier les schémas.
3. Review de Dmytro obligatoire dès qu'une PR ajoute, modifie ou supprime un endpoint.
4. Ne pas documenter ici le corps des réponses des microservices.
