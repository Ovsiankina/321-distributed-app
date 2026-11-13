# Changelog

## [Unreleased]

### Added

- Microservice Auth (Python 3.12, port 8001) : `POST /api/auth/register`, `POST /api/auth/login` et `GET /api/auth/me` (E1-03). JWT signés en EdDSA et valables 1 h, mots de passe hachés en Argon2id, base MariaDB `auth-db`, 8 comptes créateurs seedés avec leur `channel_id`.
- Contrat Gateway 0.3.0 : `POST /api/auth/login` répond aussi 400 (corps invalide) et 429 (10 échecs en 60 s pour un même email, header `Retry-After`). Les exemples de `expires_in_hours` passent à 1.

### Fixed

- Le catalog borne `ffmpeg` à 30 s lors de la génération des vignettes, pour qu'un MP4 bloquant ne fige plus le démarrage.
- `GET /health` interroge MariaDB et répond 503 quand la base est injoignable.
- Le pool SQLAlchemy MariaDB utilise `pool_pre_ping` pour écarter les connexions coupées après un redémarrage de `catalog-db`.
- Le CORS du catalog n'envoie plus `Access-Control-Allow-Credentials` avec une origine `*`.
- Le démarrage resynchronise le catalogue sous un verrou fichier. L'entrée `seed_if_empty`, qui synchronisait toujours malgré son nom, est retirée.
