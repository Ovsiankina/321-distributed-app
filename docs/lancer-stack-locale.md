# Lancer la stack locale

Démarrage qui sert la SPA sur `http://localhost:5173`. RabbitMQ, Auth, Catalog et Média tournent dans Docker. La Gateway tourne sur l'hôte : son `docker-compose.yml` ne reçoit pas `GATEWAY_JWT_PUBLIC_KEY`, et sans cette clé `GET /api/v2/auth/me` répond 503.

Aucun rebuild n'est nécessaire tant que les Dockerfiles et les `requirements.txt` n'ont pas changé. Les conteneurs déjà construits se relancent avec `docker compose up -d`.

## Ce qui écoute

| Processus | Où | URL |
|-----------|----|-----|
| RabbitMQ | `services/rabbitmq` | `127.0.0.1:5672`, console `127.0.0.1:15672` |
| Auth | `services/auth` | `http://127.0.0.1:8001` |
| Catalog | `services/catalog` | `http://127.0.0.1:8002` |
| Média (upload et stream) | `services/upload` | `http://127.0.0.1:8003` |
| Gateway | `services/gateway`, uvicorn sur l'hôte | `http://127.0.0.1:8000` |
| SPA | `frontend` | `http://localhost:5173` |

La SPA n'appelle que la Gateway, sous `/api/v2`. Vite proxifie `/api` vers le port 8000.

## Une fois, avant le premier lancement

1. Clé Auth et fichier d'environnement, si `services/auth/.env` n'existe pas encore. La génération de la paire Ed25519 est dans [`services/auth/README.md`](../services/auth/README.md). Puis :

   ```bash
   cd services/auth
   cp .env.example .env
   ```

   Renseigner `AUTH_DB_PASSWORD` et coller le PEM privé dans `AUTH_JWT_PRIVATE_KEY`. Le fichier reste hors de git.

2. Environnement Python de la Gateway :

   ```bash
   cd services/gateway
   python3 -m venv .venv
   ./.venv/bin/pip install -r requirements.txt
   ```

3. Dépendances du frontend :

   ```bash
   cd frontend
   npm install
   ```

Le jeu de vidéos `datasets/videos/` n'est pas versionné. Sans ces MP4, le catalogue s'affiche, la lecture échoue.

## Démarrage

Depuis la racine du dépôt. RabbitMQ en premier : il crée le réseau Docker `stream321`, que les trois services suivants rejoignent.

```bash
cd services/rabbitmq && docker compose up -d
cd ../auth && docker compose up -d --build
cd ../catalog && docker compose up -d --build
cd ../upload && docker compose up -d --build
```

`--build` ne sert qu'au premier lancement, ou après un changement d'image. Ensuite, `docker compose up -d` suffit.

Jeu de démo, une fois Catalog et Média démarrés, et seulement si `datasets/videos/` est présent :

```bash
cd services/upload
docker compose cp ../../datasets/videos/. upload:/data/videos/
docker compose exec upload python -m app.announce
```

`announce` publie une miniature par MP4. Le nombre affiché est celui des fichiers publiés.

Gateway, dans le shell qui va lancer uvicorn. La variable ne survit pas à la fermeture de ce shell, et un uvicorn déjà lancé ne la prend pas.

```bash
cd services/auth
export GATEWAY_JWT_PUBLIC_KEY="$(docker compose exec -T auth python -c '
from cryptography.hazmat.primitives.serialization import load_pem_private_key, Encoding, PublicFormat
import os
key = load_pem_private_key(os.environ["AUTH_JWT_PRIVATE_KEY"].encode(), password=None)
print(key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode(), end="")
')"
cd ../gateway
./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Si le port 8000 est déjà pris par un ancien uvicorn, l'arrêter avant (Ctrl+C dans son terminal).

Frontend, autre terminal :

```bash
cd frontend
npm run dev
```

## Vérifier

```bash
curl -s -o /dev/null -w 'health %{http_code}\n' http://127.0.0.1:8000/health
curl -s -o /dev/null -w 'catalog %{http_code}\n' http://127.0.0.1:8000/api/v2/catalog/videos
```

Compte créateur de démo, mot de passe partagé par [`services/auth/fixtures/users.json`](../services/auth/fixtures/users.json) : `micode@stream321.local` / `demo1234`.

Le login doit répondre 200, puis `GET /api/v2/auth/me` aussi. Un 401 sur le login est un mauvais mot de passe. Un 503 sur `/api/v2/auth/me` après un login 200 veut dire que cet uvicorn n'a pas `GATEWAY_JWT_PUBLIC_KEY`.

## Reprendre une session

Les conteneurs Docker restent démarrés après un redémarrage de la Gateway ou du frontend. Ne pas reconstruire les images. Seulement :

1. `docker compose up -d` dans un service qui serait arrêté.
2. Réexporter `GATEWAY_JWT_PUBLIC_KEY` et relancer uvicorn, comme ci-dessus.
3. `npm run dev` dans `frontend`.

## Arrêter

Ctrl+C sur uvicorn et sur Vite. Puis, sans `-v` (les volumes gardent MariaDB et les MP4) :

```bash
cd services/upload && docker compose down
cd ../catalog && docker compose down
cd ../auth && docker compose down
cd ../rabbitmq && docker compose down
```
