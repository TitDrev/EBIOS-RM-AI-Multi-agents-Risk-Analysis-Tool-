# Note d'architecture — boutique en ligne

La boutique s'appuie sur un site marchand (SPA) servi par un front Nginx, une API applicative
et une base PostgreSQL. Le paiement est externalisé vers un prestataire de paiement (PSP) via
redirection serveur-à-serveur (jetons de paiement, aucun numéro de carte stocké localement).

Points notables :
- authentification des clients par identifiant/mot de passe + session ;
- back-office d'administration accessible aux employés (compte dédié) ;
- hébergement cloud mutualisé (garanties contractuelles, pas d'isolation dédiée) ;
- sauvegardes quotidiennes de la base chez l'hébergeur ;
- accès à l'administration sans double facteur aujourd'hui ;
- correctifs appliqués manuellement et irrégulièrement sur les composants du site.