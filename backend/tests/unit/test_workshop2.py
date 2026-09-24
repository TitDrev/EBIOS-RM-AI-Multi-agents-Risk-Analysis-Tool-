"""Tests de l'Atelier 2 (Sources de risques)."""

from app.agents.state import AnalysisState
from app.agents.workshop2_risk_sources import run_workshop_2


async def test_workshop_2_produces_sources(mock_llm):
    state: AnalysisState = {
        "analysis_id": "test",
        "si_description": {"nom": "Boutique"},
        "workshop_outputs": {
            1: {"biens_essentiels": [{"name": "Données clients", "description": ""}]}
        },
    }
    output = await run_workshop_2(state)

    assert output["sources_risques"][0]["type"] == "attaquant_externe"
    assert output["sources_risques"][0]["pertinence"] == "retenue"
