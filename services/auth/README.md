# Microservice Auth

Inscription, connexion et vérification des JWT pour Stream321 (E1-03). Les routes publiques suivent le contrat gateway (`/api/auth/*`). Conception : [`docs/AUTH_SERVICE.md`](../../docs/AUTH_SERVICE.md).

Les comptes sont persistés dans **MariaDB 11** (conteneur `auth-db`). Les mots de passe sont hachés en Argon2id. Les JWT sont signés en EdDSA (Ed25519) et valables 1 heure.

Pas encore implémentés : les favoris (`/api/auth/favorites*`), prévus dans une story séparée. Ces routes répondent `404 Route inconnue` en attendant.

## Routes

| Méthode | Chemin | Codes |
|---------|--------|-------|
| POST | `/api/auth/register` | 201, 400, 409 |
| POST | `/api/auth/login` | 200, 400, 401, 429 |
| GET | `/api/auth/me` | 200, 401 |
| GET | `/health` | 200, 503 si MariaDB est injoignable |

Schémas et messages d'erreur : [`docs/api/gateway.openapi.yaml`](../../docs/api/gateway.openapi.yaml) et [`docs/API_GATEWAY.md`](../../docs/API_GATEWAY.md).

## Comptes créateurs

Au démarrage, le service crée les comptes de [`fixtures/users.json`](fixtures/users.json) : 8 créateurs, un par chaîne. Le fichier est dérivé de `poc-gateway/content/youtube/users.json` et ne garde que les champs lus par Auth.

| Champ | Rôle |
|-------|------|
| `default_password` | Mot de passe commun, haché en `password_hash`, avec un sel différent par compte |
| `users[].email` | Login unique |
| `users[].channel_id` | Clé d'appartenance, égale à `videos.channel_id` du service Catalog |

- Un compte absent est créé. Un compte existant garde son mot de passe et reprend le `channel_id` du fichier.
- Le fichier fait foi pour ses chaînes : une chaîne tenue par un autre compte (créateur renommé, chaînes échangées) lui est retirée.
- Deux écritures d'un même email ne font qu'un compte. Un email avec deux chaînes, ou une chaîne pour deux emails, arrête le démarrage avec un message qui les nomme.
- Aucun compte n'est supprimé, y compris ceux créés par l'inscription.
- Les adresses sont en `@stream321.local`, un domaine réservé que l'inscription refuse : personne ne peut s'inscrire avec l'adresse d'un créateur.
- `UCENv8pH4LkzvuSV_qHIcslg` (C'est pas sorcier) n'a encore aucune vidéo dans le catalogue seedé.

Ces comptes partagent un mot de passe publié dans le dépôt : ils servent à la démo, pas à la production.

## Clé de signature

Le service refuse de démarrer sans clé privée Ed25519. Générer une paire, hors de git :

```bash
cd services/auth
mkdir -p secrets
openssl genpkey -algorithm ed25519 -out secrets/auth-private.pem
openssl pkey -in secrets/auth-private.pem -pubout -out secrets/auth-public.pem
```

`secrets/`, `*.pem` et `.env` sont ignorés par git. La clé publique sert aux services qui vérifient les JWT (Upload). La clé privée ne quitte pas Auth.

## Docker (auth + MariaDB)

```bash
cd services/auth
cp .env.example .env   # puis y coller le contenu de secrets/auth-private.pem
docker compose up --build
```

API sur le port **8001**. Si `.env` est incomplet, `docker compose` s'arrête et nomme la variable manquante.

## Développement local

```bash
cd services/auth
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # requirements.txt + outils de test
export AUTH_DATABASE_URL=sqlite:///./auth-dev.db   # ou l'URL d'un MariaDB joignable
export AUTH_JWT_PRIVATE_KEY="$(cat secrets/auth-private.pem)"
uvicorn app.main:app --reload --port 8001
```

SQLite suffit pour essayer le service. Le déploiement reste MariaDB.

Tests (SQLite temporaire et clé générée à la volée) :

```bash
pytest
```

Comme pour Catalog, les réponses sont validées contre le contrat gateway, avec le module partagé [`tests/contract/gateway_openapi.py`](../../tests/contract/gateway_openapi.py) (à la racine du dépôt, dans le `pythonpath` de `pytest.ini`).

## Vérification rapide

```bash
curl -s http://127.0.0.1:8001/health
curl -s -X POST http://127.0.0.1:8001/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "micode@stream321.local", "password": "demo1234"}'
```

## Variables d'environnement

| Variable | Défaut | Rôle |
|----------|--------|------|
| `AUTH_DATABASE_URL` | **obligatoire** | URL SQLAlchemy de la base |
| `AUTH_DB_PASSWORD` | aucun | Mot de passe de la base, ajouté à l'URL sans la relire : tous les caractères sont permis |
| `AUTH_JWT_PRIVATE_KEY` | **obligatoire** | Clé privée Ed25519, contenu PEM complet |
| `AUTH_JWT_ISSUER` | `stream321-auth` | Claim `iss`, à configurer à l'identique dans les services qui vérifient |
| `AUTH_JWT_AUDIENCE` | `stream321-api` | Claim `aud`, idem |
| `AUTH_TOKEN_TTL_HOURS` | `1` | Durée de vie du token, en heures entières |
| `AUTH_FIXTURES_DIR` | `fixtures/` | Dossier de `users.json` |

Une variable obligatoire absente ou illisible arrête le service au démarrage, avant qu'il écoute. Une variable facultative vide prend sa valeur par défaut.

## Vérifier un token dans un autre service

```python
claims = jwt.decode(
    token,
    public_key_pem,
    algorithms=["EdDSA"],
    issuer="stream321-auth",
    audience="stream321-api",
    leeway=30,
    options={"require": ["exp", "iat", "sub", "iss", "aud"]},
)
user_id = int(claims["sub"])
```

Il faut `PyJWT[crypto]` : EdDSA passe par `cryptography`. Sans `issuer` ni `audience`, PyJWT refuse le token, qui porte un claim `aud`.

## Limites

- Le compteur de tentatives de login vit en mémoire : il repart de zéro au redémarrage et suppose une seule instance (un seul worker uvicorn, comme dans le Dockerfile).
- Changer de clé invalide les tokens en cours : les utilisateurs se reconnectent.
