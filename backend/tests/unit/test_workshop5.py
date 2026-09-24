"""Tests de l'Atelier 5 (Traitement du risque)."""

from app.agents.state import AnalysisState
from app.agents.workshop5_treatment import run_workshop_5


async def test_workshop_5_produces_risk_register(mock_llm):
    state: AnalysisState = {
        "analysis_id": "test",
        "si_description": {"nom": "Boutique"},
        "workshop_outputs": {
            1: {
                "biens_essentiels": [{"name": "Données clients", "description": ""}],
                "socle_securite": [],
            },
            4: {
                "scenarios_operationnels": [
                    {"identifiant": "O-01", "scenario_strategique": "S-01"}
                ]
            },
        },
    }
    output = await run_workshop_5(state)

    risque = output["risques"][0]
    assert risque["identifiant"] == "R-01"
    assert risque["traitement"] == "reduire"
    assert "MFA" in risque["mesures"]
    assert risque["risque_residuel"] == "faible"
    assert output["plan_traitement"]
