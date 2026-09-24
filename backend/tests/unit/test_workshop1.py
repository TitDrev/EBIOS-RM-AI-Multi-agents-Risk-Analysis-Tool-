"""Tests de l'Atelier 1 (Cadrage & socle)."""

from app.agents.state import AnalysisState
from app.agents.workshop1_framing import run_workshop_1


async def test_workshop_1_produces_valid_cadrage(mock_llm):
    state: AnalysisState = {
        "analysis_id": "test",
        "si_description": {
            "nom": "Boutique en ligne",
            "ecosysteme": "Serveur web + base clients",
            "contexte_metier": "PME e-commerce",
        },
    }
    output = await run_workshop_1(state)

    assert "perimetre" in output
    assert output["biens_essentiels"][0]["name"] == "Données clients"
    assert output["evenements_redoutes"][0]["besoin"] == "confidentialite"
    assert output["socle_securite"][0]["mesure"] == "Pare-feu"
