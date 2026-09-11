# Description du projet

En date du 28/08/2026, Rédigé par Mostoslavski David, DEVA 4A, Pour le module 321.

## Description générale de l’application

Une plateforme de streaming pour vidéo moyen à long format (20 min et 45 min).

## En pratique

Un petit serveur avec moins de 10 vidéos de moyen-long format avec une vraie
implémentation d’un service de streaming miniature.

## Fonctionnalités

• Un système de login
• Un système de recherche par mots clés uniquement
• Une home/landing page avec simples recommandations
• Une implémentation de streaming simulée
• Gestion de la qualité de streaming.
• Sous-titres autogénérés avec light PML (pre-trained machine learning)
  ou pré-écrits au format *.srt
• Visionnage sans compte
• Favoris

### landing page

- Vignettes style youtube
- barre de recherche (stub)
- Bouton "upload" (stub)
- bouton "account"
- filtre par tag (recherche de video)

### 

## Description de l’attribution des rôles

Les rôles sont attribués selon les préférences de chacun, et les besoins
du groupe.

## En classe DEVA 4A

• Adrien Wavelet
• Timothee Delacrétaz
• Dmytro Beznoskovych
• David Mostoslavski

## Les rôles

• Adrien : Dev (Front), Scrum master
• Timothee : Dev, Responsable de la capture video des daily scrums
• Dmytro : Dev, Responsable de la DX et du design de l’API
• David : Product Owner, Dev Back, Planification architecturale

# Description de la méthodologie de travail

Light Scrum, un scrum un peu allégé.

### Warning acceptance

Warnings OK.

A discuter selon le warning.

### Documentation de l'API

- Exhaustive
- Pas nécessairement détaillée pour tous les services

### Definition de "tâche terminée"

- les critères d'acceptation de la story sont satisfaits et vérifiés manuellement par l'auteur.
- une PR a été ouverte, relue et approuvée par une personne autre que l'auteur, puis mergée par le vérificateur.
- la CI passe au vert: build, tests unitaires, linter sans warning
- la documentation d'API est à jour si un endpoint a été ajouté, modifié ou supprimé (responsabilité de l'auteur, contrôle par Dmytro en review) ;
- aucune régression fonctionnelle constatée sur les fonctionnalités déjà livrées ;
- la carte est déplacée en Done par l'auteur, et la branche supprimée.

### Definition des priorités

TODO

### Gestion des Pull-Requests

- Main branch sur github (protected).
- Une Dev branch
- Utilisation des conventional commits et branches
- PR obligatoire vers main ; push direct interdit sur main.
- Une seule lecture/validation par PR suffit
- L'auteur de la PR ne peut pas merge ses modifications lui-même

### CI/CD

#### Définition du GitHub Actions

- Unit tests

### Qui gère les backlog, et comment

David, le PO.

GitHub Kanban

### Testing

Déterminer si utile pour ce projet

#### Code coverage ?

Le code coverage n'est pas strictement enforcé.

#### Integration testing ?

## Liste des outils de collaboration

- MS Teams (communication et daily scrum)
- Repo GitHub maintenu par David
- Trello OU GitHub kanban (à confirmer avec Adrien)
- OBS pour capturer les daily scrums
