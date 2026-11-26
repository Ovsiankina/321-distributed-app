# RabbitMQ

Bus de messages local, en attendant les manifestes Kubernetes. Chaque service déclare l'exchange `stream321.events` et ses files au démarrage, si son URL AMQP est définie.

```bash
docker compose up -d
```

| Port | Usage |
|------|--------|
| 127.0.0.1:5672 | AMQP |
| 127.0.0.1:15672 | Console. Utilisateur `stream`, mot de passe `stream` |

URL depuis l'hôte : `amqp://stream:stream@127.0.0.1:5672/`.

Depuis un autre compose : `amqp://stream:stream@host.docker.internal:5672/`.

| Service | Variable |
|---------|----------|
| Auth | `AUTH_AMQP_URL` |
| Catalog | `CATALOG_AMQP_URL` |
| Média | `UPLOAD_AMQP_URL` |

La console montre l'exchange et les files des services qui tournent avec leur variable.
