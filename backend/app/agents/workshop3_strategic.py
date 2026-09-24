"""Atelier 3 · Scénarios stratégiques (agent)."""

from app.agents.base import run_json_workshop
from app.agents.prompts import WORKSHOP3_SYSTEM, build_workshop3_prompt
from app.agents.state import AnalysisState
from app.schemas.workshop import ScenariosStrategiquesOutput
from app.tools.risk_math import compute_risk_level


async def run_workshop_3(state: AnalysisState) -> dict:
    """Exécute l'Atelier 3 et calcule le niveau de risque (matrice gravité × vraisemblance)."""
    user_prompt = build_workshop3_prompt(state)
    output = await run_json_workshop(WORKSHOP3_SYSTEM, user_prompt, ScenariosStrategiquesOutput)

    scenarios = []
    for scenario in output.scenarios_strategiques:
        niveau = compute_risk_level(scenario.vraisemblance, scenario.gravite)
        data = scenario.model_dump(mode="json")
        data["niveau"] = niveau.value
        scenarios.append(data)

    return {"scenarios_strategiques": scenarios}
