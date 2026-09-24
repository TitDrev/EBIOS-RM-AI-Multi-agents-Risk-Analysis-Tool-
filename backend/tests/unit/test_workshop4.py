"""Tests de l'Atelier 4 (Scénarios opérationnels)."""

from app.agents.state import AnalysisState
from app.agents.workshop4_operational import run_workshop_4


async def test_workshop_4_produces_operational_scenarios(mock_llm):
    state: AnalysisState = {
        "analysis_id": "test",
        "si_description": {"nom": "Boutique"},
        "workshop_outputs": {
            1: {"biens_supports": [{"name": "Serveur web", "description": ""}]},
            3: {
                "scenarios_strategiques": [
                    {"identifiant": "S-01", "source_risque": "Pirate",
                     "evenement_redoute": "Fuite de données clients"}
                ]
            },
        },
    }
    output = await run_workshop_4(state)

    scenario = output["scenarios_operationnels"][0]
    assert scenario["identifiant"] == "O-01"
    assert scenario["scenario_strategique"] == "S-01"
    assert "T1190" in scenario["techniques_attaque"]
    # gravite=eleve, vraisemblance=moyen → niveau "eleve"
    assert scenario["niveau"] == "eleve"
