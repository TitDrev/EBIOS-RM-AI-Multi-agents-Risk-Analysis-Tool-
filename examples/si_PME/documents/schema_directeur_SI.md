# Schéma directeur SI — PME « ACANTHA » (document fictif d'entrée)

> Système d'Information — Architecture globale & applications d'une PME/PMI.
> PME fictive « ACANTHA » — 120 collaborateurs — 2 sites (siège et agence).
> Direction des Systèmes d'Information — version 1.0. Confidentialité : interne.

## 1. Cadrage et objectifs

SI complet pour une PME : noyau **ERP centralisé** (comptabilité, finances, achats, stocks,
ventes) complété par des **applications satellites** spécialisées.

Objectifs :
- centraliser les données à la source et réduire les doubles saisies ;
- automatiser les processus administratifs, logistiques et commerciaux ;
- fiabiliser la clôture mensuelle, le reporting et la conformité réglementaire ;
- sécuriser les accès, les données et la continuité d'activité ;
- passer à l'échelle : 120 à 300 collaborateurs sans refonte.

Chiffres clés : 120 collaborateurs (85 siège A, 35 agence B) ; CA 24 M€ ; 12 000 références ;
1 800 commandes/mois ; systèmes hérités en extinction (comptable local, tableur stocks, GED).

## 2. Architecture d'ensemble

Six couches, de l'utilisateur aux services d'infrastructure, communiquant via des interfaces
contractuelles (API REST, files de messages, EDI). Principe : **l'ERP est le système de
référence** des données maîtres et des transactions ; les satellites y accèdent uniquement via
la **couche d'intégration**, jamais par accès direct aux bases.

## 3. Applications métier

- **Gestion financière & comptable** : ERP Finance (grand livre, trésorerie, immobilisations),
  gestion de trésorerie (SWIFT/EBICS), clôture automatisée.
- **Ventes & relation client** : ERP Ventes/Facturation, CRM (SaaS), portail client B2B.
- **Achats, stocks & logistique** : ERP Achats, WMS (codes-barres), optimisation transport (GPS),
  inventaires.
- **Production & maintenance** : MES (traçabilité des lots), GMAO, Qualité, MRP.
- **RH & paie** : SIRH, paie externalisée (BPO, DSN), portail RH.
- **GED & collaboration** : GED (archivage légal), suite bureautique (messagerie, visio,
  signature électronique).
- **Web, mobile & e-commerce** : site vitrine + e-commerce SaaS, applications mobiles terrain.

## 4. Modèle de données et référentiels

SGBD relationnel central (PostgreSQL ou équivalent). Référentiels uniques partagés : tiers
(clients, fournisseurs, transporteurs), articles, immobilisations et comptes, RH. Intégrité
garantie par le référentiel unique et les interfaces API.

## 5. Informatique décisionnelle

Datamart unique alimenté la nuit (ETL versionné) depuis ERP et CRM ; tableaux de bord par
direction ; reporting réglementaire automatique (TVA, Intrastat, liasses fiscales).

## 6. Intégration et échanges

Plateforme d'intégration (ESB orienté API), files de messages asynchrones, EDI (EDIFACT/XML)
avec grands comptes et fournisseurs, EBICS avec la banque. Journal d'échange consultable,
idempotence des livraisons.

## 7. Infrastructure technique

Hébergement **hybride** : cœur (ERP, données, intégration) dans le datacenter du siège avec
réplication asynchrone vers un **site de secours externe** ; applications SaaS chez leurs
éditeurs. Site B raccordé en WAN (MPLS 100 Mb/s) avec **repli VPN IPSec** sur Internet.
Capacité dimensionnée pour 300 utilisateurs simultanés ; entrepôt extensible.

## 8. Schéma d'infrastructure

Topologie : utilisateurs → réseau LAN/VLAN (+ MPLS vers agence) → pare-feu périmètre
(IDS/IPS + VPN accès distants) → DMZ (portail B2B, API REST) → cœur virtualisé (vSphere/HA) →
SGBD PostgreSQL (répliqué A→B) + SAN 60 To (RAID 6/SSD) + sauvegardes (GFS J+30/M+12/Y+7,
tests trimestriels) → site de secours externe.

## 9. Diagramme des flux

Flux applicatifs convergeant vers l'ERP via la plateforme d'intégration : asynchrones (files)
pour l'événementiel, synchrones (API) pour les référentiels. Connexions : CRM, WMS, MES, GED,
Portail, Banque (EBICS), EDI fournisseurs.

## 10. Sécurité et continuité d'activité

- **Accès** : annuaire central (AD/Azure AD), comptes uniques, SSO (SAML/OIDC), habilitations
  par profil.
- **Authentification forte (MFA)** obligatoire pour : accès admins, accès à distance, portail
  fournisseurs, application bancaire en ligne.
- **Réseau** : pare-feu périmétrique, segmentation, DMZ entre applications exposées et réseau
  interne.
- **Sécurité applicative** : revue de code, tests de pénétration annuels, scans de
  vulnérabilités mensuels, gestion des correctifs.
- **Données** : chiffrement au repos et en transit, anonymisation des environnements de test,
  classification des données.
- **Traçabilité** : journaux d'audit centralisés (SIEM), conservation 12 mois, alertes sur
  comportements anormaux.
- **Conformité** : RGPD (DPO, registre des traitements), archivage légal, DSN.
- **Continuité** : PRA (RPO 1 h, RTO 8 h sur site de secours), PCA (crise, mode dégradé,
  exercices semestriels).

## 11. Gouvernance

Comité SI bimestriel, feuille de route 36 mois (4 vagues : Finance, Ventes/CRM,
Logistique/Production, Décisionnel), méthode agile pour le développement, service desk 1
interne / 2-3 éditeurs, conduite du changement, budget ~4,5 % du CA.

## 12. Plan de déploiement

Total estimé ~1,07 M€ sur 30 mois ; retour attendu sous 4 ans.