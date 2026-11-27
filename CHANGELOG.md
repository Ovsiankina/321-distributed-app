# Changelog

## [Unreleased]

### Added

- Gateway `/api/v2` : le préfixe `/v2` est retiré avant le proxy. Upload et lecture visent le même service (port 8003). Le JWT est vérifié sur la Gateway pour `me`, les favoris et l'upload ; l'identité part en `X-User-Id` / `X-Channel-Id`. Les réponses `/api/*` (v1) portent `Deprecation: true`.
- Service média (`services/upload`) : `POST /api/upload/videos` répond 202 après publication `video.uploaded` ; `GET /api/stream/{id}` sert le MP4 avec `Range`. Plus d'appel HTTP vers le catalog (R2).
- Catalog : traitement de `video.uploaded` (publication ou `video.rejected`), miniature JPEG en base, `thumbnail_url` selon `X-Forwarded-Prefix`.
- Auth : favoris et copie `video_refs` alimentée par `video.published` / `video.removed`. Le JWT d'un créateur porte `channel_id`.
- SPA : appels sous `/api/v2`, proxy Vite vers la Gateway (port 8000).
- RabbitMQ local : `services/rabbitmq` (AMQP 5672 et console 15672 sur localhost, utilisateur `stream`). Auth, Catalog et Média déclarent l'exchange `stream321.events` quand leur `*_AMQP_URL` est défini.
- Catalog : une vidéo `source=upload` survit au redémarrage. Après la synchro, le catalog publie `video.published` pour chaque vidéo restante et `video.removed` pour chaque fixture retirée. Le mot de passe MariaDB passe par `CATALOG_DB_PASSWORD`.
- Média : au démarrage, consommation de `video.rejected` (suppression du MP4). `python -m app.announce` publie les miniatures du jeu de démonstration (`origin=dataset`).
- Catalog : plus d'accès aux fichiers vidéo ni à ffmpeg. Les qualités et les langues de sous-titres viennent du fixture. La miniature est servie depuis `thumbnail_jpeg`. Le verrou de synchro est `GET_LOCK` MariaDB.

- Microservice Auth (Python 3.12, port 8001) : `POST /api/auth/register`, `POST /api/auth/login` et `GET /api/auth/me` (E1-03). JWT signés en EdDSA et valables 1 h, mots de passe hachés en Argon2id, base MariaDB `auth-db`, 8 comptes créateurs seedés avec leur `channel_id`.
- Contrat Gateway 0.3.0 : `POST /api/auth/login` répond aussi 400 (corps invalide) et 429 (10 échecs en 60 s pour un même email, header `Retry-After`). Les exemples de `expires_in_hours` passent à 1.
- Microservice Gateway (Python 3.12) : port **8000** (E0-04), `GET /health`, stub `GET /api/home`, proxy `/api/subtitles/*` avec 502 si service cible injoignable (E0-05). Routes `/api/*` non couvertes : 404 `Route inconnue`.
- Gateway : proxy transparent `GET /api/catalog/*` vers le microservice catalog (E1-05), 502 si catalog injoignable.
- Gateway : proxy transparent `* /api/auth/*` et `GET /api/stream/*` vers auth (8001) et streaming (8003), 502 si service injoignable (E1-05).

### Fixed

- Auth, Catalog et Média rejoignent RabbitMQ par le réseau Docker `stream321` (`amqp://rabbitmq:5672`). Le port publié seulement sur `127.0.0.1` était injoignable depuis les conteneurs, et l'upload finissait en 502.
- Le verrou `catalog_sync` MariaDB est pris sur une connexion dédiée. `Session.commit()` ne la rend plus au pool avant `RELEASE_LOCK`, ce qui bloquait le test d'intégration suivant.
- Le catalog borne `ffmpeg` à 30 s lors de la génération des vignettes, pour qu'un MP4 bloquant ne fige plus le démarrage.
- `GET /health` interroge MariaDB et répond 503 quand la base est injoignable.
- Le pool SQLAlchemy MariaDB utilise `pool_pre_ping` pour écarter les connexions coupées après un redémarrage de `catalog-db`.
- Le CORS du catalog n'envoie plus `Access-Control-Allow-Credentials` avec une origine `*`.
- Le démarrage resynchronise le catalogue sous un verrou fichier. L'entrée `seed_if_empty`, qui synchronisait toujours malgré son nom, est retirée.
- Le handler d'upload est synchrone, pour que l'appel HTTP vers le catalog ne bloque pas la boucle d'événements.
- Un `/health` catalog qui n'est pas un objet JSON répond 503 (`Catalog indisponible`).
- `UPLOAD_CATALOG_TIMEOUT_SECONDS` illisible ou non positif empêche le démarrage, au lieu d'un 500 au moment de l'upload.
- Les tests du garde catalog patchent `ensure_catalog_ready` tel qu'il est appelé par la route.
- Upload vérifie les JWT auth en EdDSA (`UPLOAD_JWT_PUBLIC_KEY`, `iss`, `aud`) au lieu d'un secret HS256 partagé.