"""Tests de la validation croisée entre ateliers (anti-hallucination)."""

from app.agents.cross_validation import (
    sanitize_workshop_2,
    sanitize_workshop_3,
    sanitize_workshop_4,
    sanitize_workshop_5,
)


def test_workshop_2_filters_unknown_assets():
    state = {
        "workshop_outputs": {
            1: {"biens_essentiels": [{"name": "Données clients", "description": ""}]}
        }
    }
    output = {"sources_risques": [{"name": "Pirate", "biens_vises": ["Fantôme", "Données clients"]}]}
    cleaned, issues = sanitize_workshop_2(output, state)
    assert cleaned["sources_risques"][0]["biens_vises"] == ["Données clients"]
    assert issues


def test_workshop_3_drops_fantome_references():
    state = {
        "workshop_outputs": {
            1: {
                "evenements_redoutes": [
                    {"label": "Fuite de données clients", "bien_essentiel": "Données clients"}
                ],
                "biens_essentiels": [{"name": "Données clients", "description": ""}],
            },
            2: {"sources_risques": [{"name": "Pirate", "type": "attaquant_externe"}]},
        }
    }
    output = {
        "scenarios_strategiques": [
            {"identifiant": "S-01", "source_risque": "Fantôme",
             "evenement_redoute": "Fuite de données clients", "bien_essentiel": "Données clients",
             "gravite": "g3"},
            {"identifiant": "S-02", "source_risque": "Pirate",
             "evenement_redoute": "Événement inexistant", "bien_essentiel": "Données clients",
             "gravite": "g3"},
        ]
    }
    cleaned, issues = sanitize_workshop_3(output, state)
    assert cleaned["scenarios_strategiques"] == []
    assert len(issues) == 2


def test_workshop_4_filters_unknown_attack_techniques():
    state = {
        "workshop_outputs": {
            3: {"scenarios_strategiques": [{"identifiant": "S-01", "gravite": "g3"}]}
        }
    }
    output = {
        "scenarios_operationnels": [
            {"identifiant": "O-01", "scenario_strategique": "S-01",
             "chemin_attaque": ["Étape 1"], "techniques_attaque": ["T1190", "T9999", "n'importe quoi"],
             "gravite": "g3", "vraisemblance": "v2"},
        ]
    }
    cleaned, issues = sanitize_workshop_4(output, state)
    assert cleaned["scenarios_operationnels"][0]["techniques_attaque"] == ["T1190"]
    assert issues


def test_workshop_5_reports_missing_operational_ref():
    state = {
        "workshop_outputs": {
            4: {"scenarios_operationnels": [{"identifiant": "O-01"}]}
        }
    }
    output = {"risques": [{"identifiant": "R-01", "scenario_operationnel": "O-99"}]}
    cleaned, issues = sanitize_workshop_5(output, state)
    assert cleaned["risques"][0]["scenario_operationnel"] == "O-99"  # conservé mais signalé
    assert issues
