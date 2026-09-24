"""Fournisseur de test : réponses structurées et plausibles par atelier (aucun appel réseau).

Permet de dérouler une analyse EBIOS RM complète et réaliste sans clé LLM
(utile pour la démonstration hors ligne et pour les tests).
"""

import json

from app.llm.base import LLMProvider, LLMResponse, LLMTool

_CADRAGE = {
    "perimetre": "Système de démonstration (périmètre défini par le fournisseur mock).",
    "biens_essentiels": [
        {"name": "Processus de vente en ligne", "description": "Chaîne de commande et paiement"},
        {"name": "Données clients (RGPD)", "description": "Données personnelles et commandes"},
    ],
    "biens_supports": [
        {"name": "Serveur web public", "description": "Frontal du site", "supports": "Processus de vente en ligne"},
        {"name": "Base de données", "description": "Stockage des données", "supports": "Données clients (RGPD)"},
    ],
    "evenements_redoutes": [
        {"bien_essentiel": "Processus de vente en ligne", "besoin": "disponibilite",
         "label": "Indisponibilité du site", "gravite": "g4"},
        {"bien_essentiel": "Données clients (RGPD)", "besoin": "confidentialite",
         "label": "Fuite de données clients", "gravite": "g4"},
    ],
    "socle_securite": [
        {"mesure": "Pare-feu", "referentiel": "ISO 27002", "ecart": None},
        {"mesure": "MFA administration", "referentiel": "ANSSI", "ecart": "non déployé"},
    ],
    "echelles": {"gravite": ["g1", "g2", "g3", "g4"], "vraisemblance": ["v1", "v2", "v3", "v4"]},
}

_SOURCES = {
    "sources_risques": [
        {"type": "attaquant_externe", "name": "Cybercriminel", "objectif": "Vol de données et extorsion",
         "motivation": "financière", "activite": "Exploitation de failles web",
         "capacite": "g3", "biens_vises": ["Données clients (RGPD)"], "pertinence": "retenue",
         "description": "Pirate ciblant le site marchand."},
        {"type": "interne_malveillant", "name": "Employé mécontent", "objectif": "Sabotage ou vol de données",
         "motivation": "vengeance", "activite": "Abus de privilèges",
         "capacite": "g2", "biens_vises": ["Données clients (RGPD)"], "pertinence": "a_suivre",
         "description": "Accès légitime détourné."},
    ]
}

_STRATEGIC = {
    "parties_prenantes": [
        {"name": "Hébergeur cloud", "role": "Prestataire", "motif_criticite": "dépendance technique"},
        {"name": "PSP (paiement)", "role": "Tiers", "motif_criticite": "disponibilité paiement"},
    ],
    "scenarios_strategiques": [
        {"identifiant": "S-01", "source_risque": "Cybercriminel",
         "evenement_redoute": "Fuite de données clients", "bien_essentiel": "Données clients (RGPD)",
         "gravite": "g4", "sources": ["EBIOS RM"]},
        {"identifiant": "S-02", "source_risque": "Cybercriminel",
         "evenement_redoute": "Indisponibilité du site", "bien_essentiel": "Processus de vente en ligne",
         "gravite": "g4", "sources": ["EBIOS RM"]},
    ],
}

_OPERATIONAL = {
    "scenarios_operationnels": [
        {"identifiant": "O-01", "scenario_strategique": "S-01", "source_risque": "Cybercriminel",
         "evenement_redoute": "Fuite de données clients",
         "chemin_attaque": ["Exploiter une faille du site", "Élever les privilèges", "Exfiltrer la base"],
         "biens_supports_impliques": ["Serveur web public", "Base de données"],
         "techniques_attaque": ["T1190", "T1068", "T1048"],
         "gravite": "g4", "vraisemblance": "v3", "sources": ["MITRE ATT&CK"]},
        {"identifiant": "O-02", "scenario_strategique": "S-02", "source_risque": "Cybercriminel",
         "evenement_redoute": "Indisponibilité du site",
         "chemin_attaque": ["DDoS sur le front", "Saturation de l'API", "Coupure de service"],
         "biens_supports_impliques": ["Serveur web public"],
         "techniques_attaque": ["T1499"],
         "gravite": "g4", "vraisemblance": "v4", "sources": ["MITRE ATT&CK"]},
    ],
}

_TRAITEMENT = {
    "risques": [
        {"identifiant": "R-01", "scenario_operationnel": "O-01", "scenario_strategique": "S-01",
         "bien_essentiel": "Données clients (RGPD)", "evenement_redoute": "Fuite de données clients",
         "source_risque": "Cybercriminel", "gravite": "g4", "vraisemblance": "v3",
         "niveau": "critique", "traitement": "reduire",
         "mesures": ["Déployer un WAF", "MFA back-office", "Chiffrement en base"],
         "risque_residuel": "moyen", "justification": "Mesures ISO 27002 / ANSSI",
         "sources": ["ISO 27002", "ANSSI"]},
        {"identifiant": "R-02", "scenario_operationnel": "O-02", "scenario_strategique": "S-02",
         "bien_essentiel": "Processus de vente en ligne", "evenement_redoute": "Indisponibilité du site",
         "source_risque": "Cybercriminel", "gravite": "g4", "vraisemblance": "v4",
         "niveau": "critique", "traitement": "reduire",
         "mesures": ["Protection anti-DDoS", "Plan de continuité"],
         "risque_residuel": "eleve", "justification": "ISO 27002",
         "sources": ["ISO 27002"]},
    ],
    "plan_traitement": "Prioriser la protection des données clients (R-01) puis la disponibilité (R-02).",
}


def _select(system_prompt: str) -> dict:
    if "ATELIER 2" in system_prompt:
        return _SOURCES
    if "ATELIER 3" in system_prompt:
        return _STRATEGIC
    if "ATELIER 4" in system_prompt:
        return _OPERATIONAL
    if "ATELIER 5" in system_prompt:
        return _TRAITEMENT
    return _CADRAGE


class MockLLMProvider(LLMProvider):
    """Réponses déterministes, plausibles par atelier (aucun appel réseau)."""

    name = "mock"

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[LLMTool] | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        content = json.dumps(_select(system_prompt), ensure_ascii=False)
        return LLMResponse(content=content, tokens_in=10, tokens_out=10)
