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
    assert scenario["gravite"] == "g3"
    # Vraisemblance estimée à l'atelier 3 (affinée à l'atelier 4) + niveau calculé
    assert scenario["vraisemblance"] == "v2"
    assert scenario["niveau"] == "eleve"
    assert output["parties_prenantes"][0]["name"] == "Hébergeur"
