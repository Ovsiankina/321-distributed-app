# Questions ouvertes (service Upload)

Décisions non tranchées. Ne pas implémenter sans accord équipe / spec gateway stable.

## Catalog indisponible pendant un upload

**Contexte actuel :** après authentification JWT, le service appelle `GET {UPLOAD_CATALOG_URL}/health`. Si le catalog ne répond pas **200** avec `{"status":"ok","service":"catalog"}`, l’upload est refusé avec **503** `Catalog indisponible` (aucun fichier conservé pour traitement ultérieur).

**Question à trancher :**

> Si le service catalog n’est pas disponible, doit-on accepter quand même l’upload dans un **stockage temporaire** local (volume dédié, file d’attente, etc.), puis **déverser** vers le catalog (métadonnées + fichiers) dès que le catalog revient en ligne ?

### Pistes à évaluer

| Option | Idée | Points d’attention |
|--------|------|-------------------|
| **A. Refus immédiat (actuel)** | 503, le client réessaie | Simple, pas de données orphelines ; mauvaise UX si catalog court |
| **B. Buffer temporaire** | Persister MP4 + job « pending catalog » ; worker ou retry HTTP vers catalog au retour | Cohérence (id vidéo, doublons), taille disque, secret partagé, qui possède la vérité métier |
| **C. Hybride** | Buffer seulement si catalog répond mais refuse l’écriture (futur API interne) vs indisponibilité totale | Deux chemins d’erreur à documenter |

### Critères de décision suggérés

- Alignement avec le schéma d’architecture (Upload appelle le MS « query / catalog » après conversion).
- Comportement gateway attendu une fois la route upload stable dans `docs/API_GATEWAY.md`.
- Tests d’intégration et reprise après panne (catalog redémarré, upload toujours up).

**Statut :** ouvert. Dernière mise à jour : squelette upload + garde `/health` catalog.
