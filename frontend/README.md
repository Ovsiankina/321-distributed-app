# Frontend Stream321

Interface React 19 + TypeScript, construite avec Vite. Toutes les routes appelées
suivent le contrat de la Gateway ([`docs/api/gateway.openapi.yaml`](../docs/api/gateway.openapi.yaml)).

## Lancer en local

```sh
npm install
npm run dev
```

Tant que la Gateway (E0-04) n'existe pas, le serveur de dev Vite redirige `/api`
vers le service catalogue sur `http://127.0.0.1:8002` (voir `vite.config.ts`).
Les routes `/api/auth/*` et `/api/stream/*` répondent donc 404 : la connexion,
les favoris et la lecture vidéo ne fonctionnent qu'avec la Gateway.

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
