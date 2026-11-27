# Frontend 321-distributed-app

Interface React 19 + TypeScript, construite avec Vite. Toutes les routes appelées
suivent le contrat de la Gateway ([`docs/api/gateway.openapi.yaml`](../docs/api/gateway.openapi.yaml)).

## Lancer en local

```sh
npm install
npm run dev
```

Le serveur de dev Vite redirige `/api` vers la Gateway sur `http://127.0.0.1:8000`.
Le client n'appelle que `/api/v2`.

## Scripts

| Commande        | Rôle                                   |
| --------------- | -------------------------------------- |
| `npm run dev`   | serveur de développement               |
| `npm test`      | tests unitaires (vitest) de `src/lib/` |
| `npm run lint`  | analyse oxlint                         |
| `npm run build` | vérification TypeScript + build        |

## Structure

- `src/components/` : composants réutilisables, chacun avec son CSS.
- `src/pages/` : une page par route.
- `src/auth/` : contexte de session (JWT stocké dans `localStorage`).
- `src/lib/` : logique pure et client de l'API, testée avec vitest.
