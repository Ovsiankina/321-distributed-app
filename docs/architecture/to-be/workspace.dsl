// Stream321 - architecture CIBLE (to-be), modèle C4 au format c4rizer.
//
// Légende des tags :
//   Nouveau  : conteneur qui n'existe pas encore dans le code (Bus de messages) ;
//              bordure orange épaisse, pour voir l'écart avec l'as-is.
//   Async    : relation asynchrone via le bus (AMQP) ; trait pointillé orange.
//   Broker   : le MOM (RabbitMQ), forme Pipe (file de messages).
//   Database : base de données, forme Cylinder. Storage : stockage de fichiers, forme Folder.
//   WebApp   : application exécutée dans le navigateur, forme WebBrowser.
//   Gateway  : la passerelle API, forme Hexagon.
//   Evenements : conteneurs reliés au bus ; la vue filtrée tobe-c2-mom garde
//              ces conteneurs et les relations Async (flux MOM seul).
// Aucune relation ne va d'un microservice à un autre : les services ne parlent
// qu'à la passerelle (qui les appelle), à leur propre stockage et au bus.
// Chaque stockage a un seul service propriétaire (une base par microservice) :
// Base Auth -> Auth, Base Catalog -> Catalog, Stockage vidéo -> Média.
// Mise en ligne = SAGA par chorégraphie : Média publie video.uploaded, Catalog
// publie video.published (ou video.rejected, et Média supprime le fichier).
//
// Vérifier et générer les diagrammes (depuis la racine du dépôt) :
//   c4rizer validate docs/architecture/to-be/workspace.dsl
//   c4rizer lint docs/architecture/to-be/workspace.dsl
//   c4rizer render docs/architecture/to-be/workspace.dsl -o docs/architecture/to-be/diagrams

workspace "Stream321 - architecture cible" "Cible : microservices derrière une passerelle /api/v2, un stockage privé par service, échanges asynchrones par RabbitMQ, déploiement Kubernetes." {

    model {
        visitor = person "Visiteur" "Personne anonyme : parcourt, recherche et regarde des vidéos sans compte."
        member = person "Utilisateur inscrit" "Se connecte et gère ses vidéos favorites."
        creator = person "Créateur" "Compte lié à une chaîne (channel_id) ; téléverse des vidéos."

        stream321 = softwareSystem "Stream321" "Plateforme de streaming vidéo : catalogue, lecture, favoris et mise en ligne de vidéos." {
            spa = container "Application web" "SPA : accueil, recherche, lecteur, connexion, favoris, upload. N'appelle que /api/v2." "React, TypeScript, servie par nginx" "WebApp"
            gateway = container "API Gateway" "Point d'entrée unique : garde /api (v1), route /api/v2 vers Auth, Catalog et Média (JWT validé, Range relayé)." "Python 3.12, FastAPI, httpx" "Gateway"
            auth = container "Service Auth" "Comptes, émission des JWT (Ed25519), favoris ; garde une copie locale des vidéos connues." "Python 3.12, FastAPI, SQLAlchemy, PyJWT EdDSA, aio-pika" "Service,Evenements"
            authDb = container "Base Auth" "Tables users, favorites et video_refs (copie alimentée par les événements)." "MariaDB 11" "Database"
            catalog = container "Service Catalog" "Métadonnées, recherche et miniatures (stockées en base) ; valide les vidéos annoncées par le bus." "Python 3.12, FastAPI, SQLAlchemy, aio-pika" "Service,Evenements"
            catalogDb = container "Base Catalog" "Tables videos (dont miniatures) et tags." "MariaDB 11" "Database"
            media = container "Service Média" "Reçoit les vidéos (202), crée la miniature, publie video.uploaded ; sert les MP4 par plages (206)." "Python 3.12, FastAPI, ffmpeg, aio-pika" "Service,Evenements"
            broker = container "Bus de messages" "MOM : exchange topic stream321.events, une file durable par service consommateur." "RabbitMQ 3 (AMQP 0-9-1)" "Broker,Nouveau,Evenements"
            videoStore = container "Stockage vidéo" "Fichiers MP4, privés au Service Média (partagés seulement entre ses réplicas)." "Volume privé (PVC)" "Storage"
        }

        // Personnes -> SPA
        visitor -> spa "Parcourt, recherche et regarde des vidéos" "HTTPS"
        member -> spa "Se connecte et gère ses favoris" "HTTPS"
        creator -> spa "Téléverse des vidéos" "HTTPS"

        // SPA -> passerelle (seul point d'entrée)
        spa -> gateway "Appelle l'API /api/v2" "JSON/HTTPS"

        // Passerelle -> services (requêtes synchrones)
        gateway -> auth "Route /api/v2/auth (comptes, favoris)" "JSON/HTTP"
        gateway -> catalog "Route /api/v2/catalog (lecture publique)" "JSON/HTTP"
        gateway -> media "Route /api/v2/upload/videos (JWT requis) et /api/v2/stream/{id} (Range relayé)" "HTTP (multipart, Range 206)"

        // Services -> leur propre stockage (un seul service propriétaire par stockage)
        auth -> authDb "Lit et écrit comptes, favoris et video_refs" "SQL (PyMySQL)"
        catalog -> catalogDb "Lit et écrit vidéos, miniatures et tags" "SQL (PyMySQL)"
        media -> videoStore "Écrit et lit les MP4" "Système de fichiers"

        // Services -> bus de messages (asynchrone, publication/abonnement)
        media -> broker "Publie video.uploaded ; consomme video.rejected" "AMQP" "Async"
        catalog -> broker "Consomme video.uploaded ; publie video.published, video.removed et video.rejected" "AMQP" "Async"
        auth -> broker "Consomme video.published et video.removed" "AMQP" "Async"

        prod = deploymentEnvironment "Production" {
            cluster = deploymentNode "Cluster Kubernetes" "Cluster de production. Tous les Services Kubernetes sont de type ClusterIP." "Kubernetes" {
                ns = deploymentNode "stream321" "Namespace de l'application. Chaque Deployment et StatefulSet est exposé par un Service ClusterIP." "Namespace" {
                    config = infrastructureNode "ConfigMap stream321-config" "URL des services par le DNS du cluster (ex. http://catalog:8002), exchange stream321.events." "ConfigMap"
                    secret = infrastructureNode "Secret stream321-secrets" "Clés JWT Ed25519, identifiants des bases MariaDB et de RabbitMQ." "Secret"
                    ingress = infrastructureNode "Ingress" "Seule entrée depuis l'extérieur : / vers la SPA, /api vers la passerelle." "NGINX Ingress Controller"
                    spaDep = deploymentNode "spa" "Pods sans état, sondes readiness et liveness sur /health." "Deployment" {
                        instances 2
                        spaPod = containerInstance spa
                    }
                    gatewayDep = deploymentNode "gateway" "Pods sans état, sondes readiness et liveness sur /health." "Deployment" {
                        instances 2
                        gatewayPod = containerInstance gateway
                    }
                    authDep = deploymentNode "auth" "Pods sans état, sondes readiness et liveness sur /health." "Deployment" {
                        instances 2
                        authPod = containerInstance auth
                    }
                    catalogDep = deploymentNode "catalog" "Pods sans état, sondes readiness et liveness sur /health." "Deployment" {
                        instances 2
                        catalogPod = containerInstance catalog
                    }
                    mediaDep = deploymentNode "media" "Deux réplicas qui partagent le PVC media-videos, sondes readiness et liveness sur /health." "Deployment" {
                        instances 2
                        streamingPod = containerInstance media
                    }
                    authDbSts = deploymentNode "auth-db" "StatefulSet avec son PersistentVolumeClaim." "StatefulSet + PVC" {
                        instances 1
                        authDbPod = containerInstance authDb
                    }
                    catalogDbSts = deploymentNode "catalog-db" "StatefulSet avec son PersistentVolumeClaim." "StatefulSet + PVC" {
                        instances 1
                        catalogDbPod = containerInstance catalogDb
                    }
                    rabbitSts = deploymentNode "rabbitmq" "StatefulSet avec son PersistentVolumeClaim." "StatefulSet + PVC" {
                        instances 1
                        brokerPod = containerInstance broker
                    }
                    mediaPvc = deploymentNode "media-videos" "Volume privé du Service Média, monté uniquement par le Deployment media." "PVC ReadWriteMany" {
                        mediaVol = containerInstance videoStore
                    }
                }
            }
            ingress -> spaPod "Route / vers la SPA" "HTTP"
            ingress -> gatewayPod "Route /api vers la passerelle" "HTTP"
        }
    }

    views {
        systemContext stream321 "tobe-c1" "Contexte système de Stream321 (cible)" {
            title "Stream321 - contexte système (cible)"
            subtitle "Les trois profils d'utilisateurs et la plateforme ; aucun système externe."
            include *
            technology off
        }

        container stream321 "tobe-c2" "Conteneurs de Stream321 (cible)" {
            title "Stream321 - conteneurs (cible)"
            subtitle "Passerelle /api/v2 unique, aucun appel direct entre services, événements via RabbitMQ (pointillés)."
            include *
            maxCrossings 0
            at visitor 740 170
            at member 1100 170
            at creator 1460 170
            at spa 1100 480
            at gateway 1100 800
            at authDb 120 1160
            at auth 560 1160
            at catalog 920 1160
            at media 1280 1160
            at catalogDb 740 1480
            at videoStore 1280 1480
            at broker 920 1800
            size gateway 280 160
            size broker 1680 140
        }

        filtered "tobe-c2" include "Evenements,Async" "tobe-c2-mom" "Stream321 - flux d'événements par le bus de messages (cible)"

        deployment stream321 "Production" "tobe-k8s" "Déploiement Kubernetes de Stream321 (cible)" {
            title "Stream321 - déploiement Kubernetes (Production)"
            subtitle "Namespace stream321 : Deployments sans état (sondes /health), StatefulSets avec PVC, Services ClusterIP ; l'Ingress est la seule entrée."
            include *
            maxCrossings 0
            labelWidth 20
            at config 100 1920
            at secret 90 2120
            at ingress 1510 1970
            at spaPod 790 1960
            at gatewayPod 1260 1630
            at authDbPod 370 950
            at authPod 550 1250
            at catalogPod 1140 1260
            at streamingPod 1670 1250
            at catalogDbPod 960 960
            at mediaVol 1670 890
            at brokerPod 1370 610
            size gatewayPod 1560 160
            size brokerPod 1720 140
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
            element "Gateway" {
                shape Hexagon
                background #3949ab
            }
            element "Database" {
                shape Cylinder
                background #00796b
            }
            element "Storage" {
                shape Folder
                background #00796b
            }
            element "Broker" {
                shape Pipe
                background #6a1b9a
            }
            element "Nouveau" {
                stroke #ff6d00
                strokeWidth 5
            }
            element "Infrastructure Node" {
                background #e8f0e0
                color #1b1b1b
            }
            relationship "Relationship" {
                routing Orthogonal
            }
            relationship "Async" {
                style dashed
                color #e65100
                thickness 2
            }
        }
    }
}
