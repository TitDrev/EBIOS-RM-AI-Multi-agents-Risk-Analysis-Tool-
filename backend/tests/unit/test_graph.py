"""Tests du squelette LangGraph (déroulé des 5 ateliers)."""

from app.agents.graph import pipeline
from app.agents.state import AnalysisState


async def test_pipeline_runs_all_5_workshops(mock_llm):
    state: AnalysisState = {
        "analysis_id": "test",
        "si_description": {"nom": "Système de test"},
        "workshop_outputs": {},
        "current_workshop": 0,
    }
    result = await pipeline.ainvoke(state)

    assert set(result["workshop_outputs"].keys()) == {1, 2, 3, 4, 5}
    assert result["current_workshop"] == 5
    # Les 5 ateliers sont maintenant réels.
    assert "biens_essentiels" in result["workshop_outputs"][1]
    assert "sources_risques" in result["workshop_outputs"][2]
    assert "scenarios_strategiques" in result["workshop_outputs"][3]
    assert "scenarios_operationnels" in result["workshop_outputs"][4]
    assert "risques" in result["workshop_outputs"][5]
