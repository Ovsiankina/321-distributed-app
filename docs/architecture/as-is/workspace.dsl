// Stream321 - architecture ACTUELLE (as-is), modèle C4 au format c4rizer.
//
// Périmètre : la branche `main`. Gateway, Auth et Upload n'existent que sur
// `origin/dev` (fusionnés là-bas, pas encore sur main) : ils sont modélisés
// ici avec le tag DevSeulement pour montrer l'état complet du code.
//
// Légende (tags) :
//   DevSeulement  élément ou relation présent seulement sur la branche dev :
//                 bordure ou trait en pointillés, couleur plus claire.
//   Violation     relation qui enfreint un principe d'architecture distribuée
//                 (contournement de la passerelle, appel direct entre
//                 microservices) : trait rouge épais.
//   NonCable      relation documentée (docs/API_GATEWAY.md) mais pas
//                 branchée dans le code : trait gris en pointillés fins.
//   WebApp        application web (forme navigateur).
//   Database      base de données (cylindre) ; Fichiers : stockage fichiers.
//
// Vues :
//   asis-c1       contexte système (personnes + Stream321), main et dev.
//   asis-c2-main  conteneurs présents sur main uniquement. Vue conteneur
//                 explicite (exclude) plutôt que vue `filtered` : une vue
//                 filtrée n'accepte pas de `subtitle` et hérite de celui de la
//                 vue de base, qui décrit la branche dev.
//   asis-c2-dev   conteneurs de main + dev, avec les violations.
//
// Détails non dessinés : la passerelle (dev) ne valide pas le JWT, n'a pas de
// versions, met les corps en mémoire et perd l'en-tête Range ; elle route
// /api/stream (:8003) et /api/subtitles (:8004) vers des services qui
// n'existent pas, et /api/upload tombe dans son 404.
//
// Valider et dessiner (depuis la racine du dépôt) :
//   c4rizer validate docs/architecture/as-is/workspace.dsl
//   c4rizer lint docs/architecture/as-is/workspace.dsl
//   c4rizer render docs/architecture/as-is/workspace.dsl -o docs/architecture/as-is/diagrams

workspace "Stream321 (as-is)" "Architecture actuelle de Stream321. Déploiement : un fichier docker-compose par service, sans réseau partagé ; les services sont publiés sur des ports de l'hôte et se joignent via host.docker.internal. Ni broker, ni Kubernetes." {

    model {
        // Personnes : des rôles, jamais des individus.
        visitor = person "Visiteur" "Anonyme : parcourt, recherche et regarde des vidéos sans compte."
        member = person "Utilisateur inscrit" "Se connecte et gère ses favoris (écrans présents ; Auth seulement sur dev)."
        creator = person "Créateur" "Compte lié à une chaîne (channel_id), pour envoyer des vidéos (branche dev, pas encore sur main)." "DevSeulement"

        stream321 = softwareSystem "Stream321" "Plateforme de streaming vidéo." {
            // Présents sur main.
            spa = container "Application web" "SPA : accueil, recherche, lecteur, connexion, favoris. Appelle /api en relatif, JWT en localStorage." "React, TypeScript, Vite (serveur de dev)" "WebApp"
            catalog = container "Service Catalog" "Métadonnées des vidéos, recherche, mises en avant et miniatures." "Python 3.12, FastAPI, SQLAlchemy, ffmpeg (port 8002)"
            catalogDb = container "Base Catalog" "Tables videos et tags." "MariaDB 11" "Database"
            mediaFiles = container "Fichiers média" "Vidéos sources (lecture seule) et miniatures générées." "Système de fichiers (bind mount datasets/videos, volume catalog-thumbs)" "Fichiers"

            // Présents seulement sur origin/dev.
            gateway = container "API Gateway" "Proxy inverse mince, sans JWT ; route vers Streaming et Subtitles, absents (branche dev, pas encore sur main)." "Python 3.12, FastAPI, httpx (port 8000)" "DevSeulement" {
                tags "stream321.gateway"
            }
            auth = container "Service Auth" "Inscription, connexion, /me, émet les JWT Ed25519 (branche dev, pas encore sur main)." "Python 3.12, FastAPI, SQLAlchemy, Argon2id, PyJWT EdDSA (port 8001)" "DevSeulement"
            authDb = container "Base Auth" "Table users (branche dev, pas encore sur main)." "MariaDB 11" "Database,DevSeulement"
            upload = container "Service Upload" "Squelette : valide le JWT, répond toujours 501, hors passerelle (branche dev, pas encore sur main)." "Python 3.12, FastAPI, httpx, PyJWT (port 8003)" "DevSeulement"
        }

        // Personnes -> SPA (dans le navigateur).
        visitor -> spa "Parcourt, recherche et regarde des vidéos" "HTTPS (navigateur)"
        member -> spa "Se connecte et gère ses favoris" "HTTPS (navigateur)"
        creator -> spa "Se connecte avec son compte de chaîne (branche dev, pas encore sur main)" "HTTPS (navigateur)" "DevSeulement"

        // SPA -> services. Sur main ET sur dev, le proxy Vite envoie tout /api
        // directement à Catalog (127.0.0.1:8002) : la passerelle est contournée.
        spa -> catalog "Appelle tout /api via le proxy Vite, sans passer par la passerelle" "JSON/HTTP" "Violation"
        spa -> gateway "Devrait appeler /api (contrat documenté, non branché) (branche dev, pas encore sur main)" "JSON/HTTP" "DevSeulement,NonCable"

        // Passerelle -> services (branche dev).
        gateway -> auth "Relaie /api/auth (branche dev, pas encore sur main)" "JSON/HTTP" "DevSeulement"
        gateway -> catalog "Relaie /api/catalog (branche dev, pas encore sur main)" "JSON/HTTP" "DevSeulement"

        // Upload -> Catalog : appel synchrone direct entre microservices,
        // 503 si Catalog est arrêté.
        upload -> catalog "Vérifie GET /health avant d'accepter un envoi, appel direct (branche dev, pas encore sur main)" "JSON/HTTP" "DevSeulement,Violation"

        // Données.
        catalog -> catalogDb "Lit et écrit les vidéos et les tags" "SQL (PyMySQL)"
        catalog -> mediaFiles "Lit les vidéos, écrit les miniatures" "Système de fichiers"
        auth -> authDb "Lit et écrit les comptes (branche dev, pas encore sur main)" "SQL (PyMySQL)" "DevSeulement"
    }

    views {
        systemContext stream321 "asis-c1" "Contexte de Stream321, état actuel" {
            title "Stream321 - contexte système (as-is)"
            subtitle "Branches main et dev. En pointillés : seulement sur dev (le Créateur n'a aucune fonction sur main)."
            include *
            technology off
            maxCrossings 0
            at visitor 200 170
            at member 600 170
            at creator 1000 170
            at stream321 600 470
            size stream321 280 160
        }

        container stream321 "asis-c2-main" "Conteneurs de Stream321 sur la branche main" {
            title "Stream321 - conteneurs, branche main (as-is)"
            subtitle "Seulement ce qui est sur main. Rouge : violation (la SPA joint Catalog sans passerelle)."
            include *
            exclude creator gateway auth authDb upload
            maxCrossings 0
            at visitor 400 170
            at member 800 170
            at spa 600 450
            at catalog 600 750
            at catalogDb 400 1050
            at mediaFiles 800 1050
        }

        container stream321 "asis-c2-dev" "Conteneurs de Stream321 sur main et dev" {
            title "Stream321 - conteneurs, branches main + dev (as-is)"
            subtitle "Tout le code existant. Pointillés : seulement sur dev. Rouge : violation. Gris pointillé : documenté, non branché."
            include *
            maxCrossings 0
            at visitor -30 240
            at member 370 240
            at creator 770 240
            at spa 370 520
            at gateway -20 830
            at catalog 770 830
            at upload 1270 830
            at auth -30 1130
            at authDb -30 1410
            at catalogDb 570 1130
            at mediaFiles 970 1130
            paperSize A6_Portrait
        }

        styles {
            element "Person" {
                shape Person
                background #0b3c6f
                color #ffffff
            }
            element "Software System" {
                background #1565c0
                color #ffffff
            }
            element "Container" {
                background #1e88e5
                color #ffffff
            }
            element "WebApp" {
                shape WebBrowser
            }
            element "Database" {
                shape Cylinder
                background #00796b
                color #ffffff
            }
            element "Fichiers" {
                shape Folder
                background #00796b
                color #ffffff
            }
            element "DevSeulement" {
                border dashed
                background #dce8f5
                color #1a1a1a
            }
            relationship "Relationship" {
                routing Orthogonal
            }
            relationship "DevSeulement" {
                style dashed
                color #7a8fa6
            }
            relationship "NonCable" {
                style dotted
                color #9e9e9e
            }
            relationship "Violation" {
                color #c62828
                thickness 3
            }
            element "stream321.gateway" {
                background #bc84bf
            }
        }
    }
}
