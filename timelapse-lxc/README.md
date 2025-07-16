# Timelapse LXC - Dahua IP Camera

Ce projet est une application Flask permettant de gérer un timelapse automatique à partir d’une caméra IP Dahua.  
L’application offre une interface web avec gestion des utilisateurs et rôles (user, plus, admin), et permet de démarrer/arrêter la capture d’images à intervalle régulier.

## Fonctionnalités

- Captures d’images entre 6h et 20h, une image par heure.
- Exécution d’une commande PTZ avant chaque capture (avec délai de 10 secondes).
- Interface web sécurisée avec 3 niveaux d’utilisateurs :
  - **user** : consultation uniquement.
  - **plus** : consultation + démarrer/arrêter le timelapse.
  - **admin** : accès complet, gestion utilisateurs (ajout/suppression).
- Gestion simple des utilisateurs en mémoire (à adapter en base de données si besoin).
- Stockage des images dans `~/Bureau/timelapse-chantier-MAS`.

## Installation

1. Cloner le dépôt ou décompresser l’archive.
2. Installer les dépendances Python :
   ```bash
   pip install -r requirements.txt
