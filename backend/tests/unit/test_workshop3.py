"""Tests de l'Atelier 3 (Scénarios stratégiques)."""

from app.agents.state import AnalysisState
from app.agents.workshop3_strategic import run_workshop_3


async def test_workshop_3_computes_risk_level(mock_llm):
    state: AnalysisState = {
        "analysis_id": "test",
        "si_description": {"nom": "Boutique"},
        "workshop_outputs": {
            1: {
                "evenements_redoutes": [
                    {"label": "Fuite de données clients", "gravite": "eleve"}
                ]
            },
            2: {
                "sources_risques": [
                    {"type": "attaquant_externe", "name": "Pirate"}
                ]
            },
        },
    }
    output = await run_workshop_3(state)

    scenario = output["scenarios_strategiques"][0]
    assert scenario["identifiant"] == "S-01"
    # gravite=eleve, vraisemblance=moyenne → niveau "eleve"
    assert scenario["niveau"] == "eleve"
