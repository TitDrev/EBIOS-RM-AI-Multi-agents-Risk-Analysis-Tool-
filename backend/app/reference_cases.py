"""Cas d'étude de référence (A/B/C) utilisés pour les tests et la démonstration.

Chaque cas est une description de système d'information fictive servant d'entrée
au pipeline d'agents (les 5 ateliers EBIOS RM).
"""

REFERENCE_CASES: dict[str, dict] = {
    "boutique_en_ligne": {
        "label": "A · Boutique en ligne",
        "si_description": {
            "nom": "Boutique en ligne d'une PME",
            "ecosysteme": (
                "Site marchand public (catalogue + commande), plateforme de paiement externe "
                "(PSP) en redirection, back-office administratif, base de données clients et "
                "commandes, hébergement cloud mutualisé."
            ),
            "flux": (
                "Le client navigue et passe commande ; le paiement est délégué au PSP via "
                "redirection ; les commandes et données clients sont stockées en base ; le "
                "back-office accède aux données par l'application d'administration."
            ),
            "contexte_metier": (
                "PME e-commerce (vêtements), volume saisonnier, conformité RGPD sur les "
                "données clients, dépendance à la disponibilité du site pendant les campagnes."
            ),
            "contraintes": "RGPD, PSD2 pour le paiement, exigences de l'hébergeur.",
        },
    },
    "teleconsultation_medicale": {
        "label": "B · Téléconsultation médicale",
        "si_description": {
            "nom": "Plateforme de téléconsultation médicale",
            "ecosysteme": (
                "Application web/mobile de rendez-vous et de visioconférence, fournisseur de "
                "visio tiers (WebRTC), base de données de santé (dossiers patients), service "
                "d'identité/authentification, hébergement cloud."
            ),
            "flux": (
                "Le patient prend rendez-vous ; la visio se déroule via le fournisseur tiers ; "
                "les données de santé (comptes-rendus, ordonnances) sont stockées et échangées "
                "avec les praticiens."
            ),
            "contexte_metier": (
                "Données de santé hautement sensibles (RGPD et données de santé), obligation de "
                "confidentialité médicale, disponibilité en heures ouvrables, flux vidéo en "
                "temps réel."
            ),
            "contraintes": (
                "RGPD données de santé, réglementation de la télémédecine, traçabilité des accès."
            ),
        },
    },
    "reseau_pme": {
        "label": "C · Réseau d'une PME",
        "si_description": {
            "nom": "Réseau informatique d'une PME",
            "ecosysteme": (
                "Postes de travail PC (Windows), messagerie (Exchange), serveur de fichiers "
                "(SMB), réseau Wi-Fi salariés/invités, connexion internet (box), accès VPN pour "
                "les salariés nomades, NAS de sauvegarde."
            ),
            "flux": (
                "Les salariés accèdent à la messagerie et aux fichiers partagés ; les nomades se "
                "connectent via VPN ; les postes rejoignent le domaine ; accès internet via la box."
            ),
            "contexte_metier": (
                "PME de 30 salariés, bureautique et fichiers partagés, télétravail régulier, "
                "équipe SI réduite, dépendance à la continuité de service."
            ),
            "contraintes": "Sauvegardes, RGPD (données RH), budget limité.",
        },
    },
}
