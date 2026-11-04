# Changelog

## [Unreleased]

### Fixed

- Le handler d'upload est synchrone, pour que l'appel HTTP vers le catalog ne bloque pas la boucle d'événements.
- Un `/health` catalog qui n'est pas un objet JSON répond 503 (`Catalog indisponible`).
- `UPLOAD_CATALOG_TIMEOUT_SECONDS` illisible ou non positif empêche le démarrage, au lieu d'un 500 au moment de l'upload.
- Les tests du garde catalog patchent `ensure_catalog_ready` tel qu'il est appelé par la route.
