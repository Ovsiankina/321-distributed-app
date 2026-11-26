# Architecture C4 de Stream321

Ce dossier décrit l'architecture de Stream321 avec le [modèle C4](https://c4model.com),
en deux états : l'existant et la cible. Les modèles sont écrits dans le DSL de
c4rizer (proche de Structurizr) ; les diagrammes en sont générés.

## Les deux workspaces

| Workspace | Contenu |
|-----------|---------|
| [`as-is/workspace.dsl`](as-is/workspace.dsl) | État actuel, relevé dans le code. Base : `main` (SPA, Catalog, sa base, fichiers média). Les conteneurs qui n'existent que sur `dev` (Gateway, Auth et sa base, Upload) portent le tag `DevSeulement`, ce qui donne une vue avec `dev` et une vue limitée à `main`. Les écarts aux principes (SPA qui contourne la Gateway, Upload qui appelle le Catalog) sont marqués. |
| [`to-be/workspace.dsl`](to-be/workspace.dsl) | Architecture cible décidée : Gateway en point d'entrée unique avec `/api/v2`, bus de messages RabbitMQ, Service Média (le squelette Upload étendu : réception et lecture des vidéos), un stockage par microservice et aucun stockage partagé entre services, déploiement Kubernetes. Les nouveaux conteneurs et les flux asynchrones sont distingués par des tags. |

La référence contraignante est [`../ARCHITECTURE.md`](../ARCHITECTURE.md) : elle
fixe les règles et résume la cible. Les workspaces en sont la vue en diagrammes.

Le passage de l'un à l'autre est décrit dans [`MIGRATION_V2.md`](MIGRATION_V2.md),
qui relie aussi la cible à la théorie du cours (section 2).

## Niveaux C4 couverts

| Niveau | Couvert | Vues |
|--------|---------|------|
| C1, contexte système | oui | `asis-c1`, `tobe-c1` |
| C2, conteneurs | oui | `asis-c2-dev`, `asis-c2-main`, `tobe-c2`, `tobe-c2-mom` (flux asynchrone seul) |
| Déploiement (diagramme complémentaire) | cible seulement | `tobe-k8s` : cluster Kubernetes, namespace `stream321`, PVC `media-videos` monté par le seul Deployment `media` |
| C3, composants | non, par choix | |
| C4, code | non, par choix | |

Les niveaux C3 et C4 ne sont pas produits : les services sont petits, et leur
structure interne se lit directement dans le code. Kubernetes n'est pas un
conteneur C4 : il n'apparaît que dans la vue de déploiement, sous forme de
nœuds. L'existant n'a pas de vue de déploiement : un fichier compose par
service, décrit dans la description du workspace.

## Fichiers

```text
docs/architecture/
  README.md            # ce fichier
  MIGRATION_V2.md      # guide de migration vers la cible
  as-is/
    workspace.dsl
    diagrams/          # SVG générés, un par vue
  to-be/
    workspace.dsl
    diagrams/          # SVG générés, un par vue
```

Les SVG sont générés : ne pas les modifier à la main. Modifier le
`workspace.dsl`, puis régénérer.

## Valider et générer les diagrammes

c4rizer se construit depuis son dépôt, branche `dev` (Rust requis) :

```sh
cargo build --release -p c4rizer-cli
# binaire : target/release/c4rizer, à placer dans le PATH
```

Depuis la racine de ce dépôt :

```sh
c4rizer validate docs/architecture/to-be/workspace.dsl
c4rizer lint docs/architecture/to-be/workspace.dsl
c4rizer render docs/architecture/to-be/workspace.dsl -o docs/architecture/to-be/diagrams
```

Même chose pour `as-is/`.

| Commande | Résultat attendu |
|----------|------------------|
| `c4rizer validate FICHIER` | code 0, aucune sortie |
| `c4rizer lint FICHIER` | code 0 ; 1 si des règles du lint échouent ; 2 si le fichier ne se lit pas |
| `c4rizer render FICHIER -o DOSSIER` | un `DOSSIER/<clé de vue>.svg` par vue |

Une modification d'un `workspace.dsl` n'est terminée que si `validate` et
`lint` passent et si les SVG régénérés sont committés avec elle. `c4rizer help`
liste les autres options.
