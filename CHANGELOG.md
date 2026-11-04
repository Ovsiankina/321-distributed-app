# Changelog

## [Unreleased]

### Fixed

- Le catalog borne `ffmpeg` à 30 s lors de la génération des vignettes, pour qu'un MP4 bloquant ne fige plus le démarrage.
- `GET /health` interroge MariaDB et répond 503 quand la base est injoignable.
- Le pool SQLAlchemy MariaDB utilise `pool_pre_ping` pour écarter les connexions coupées après un redémarrage de `catalog-db`.
- Le CORS du catalog n'envoie plus `Access-Control-Allow-Credentials` avec une origine `*`.
- Le démarrage resynchronise le catalogue sous un verrou fichier. L'entrée `seed_if_empty`, qui synchronisait toujours malgré son nom, est retirée.
