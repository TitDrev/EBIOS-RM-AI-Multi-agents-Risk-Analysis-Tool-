"""Atelier 5 · Traitement du risque (agent)."""

from app.agents.base import run_json_workshop
from app.agents.prompts import WORKSHOP5_SYSTEM, build_workshop5_prompt
from app.agents.state import AnalysisState
from app.schemas.workshop import TraitementOutput
from app.tools.risk_math import compute_risk_level


async def run_workshop_5(state: AnalysisState) -> dict:
    """Exécute l'Atelier 5 et construit le registre des risques + plan de traitement."""
    user_prompt = build_workshop5_prompt(state)
    output = await run_json_workshop(WORKSHOP5_SYSTEM, user_prompt, TraitementOutput)

    risques = []
    for risque in output.risques:
        data = risque.model_dump(mode="json")
        # Le niveau est recalculé de façon déterministe (gravité × vraisemblance).
        data["niveau"] = compute_risk_level(risque.vraisemblance, risque.gravite).value
        risques.append(data)

    return {"risques": risques, "plan_traitement": output.plan_traitement}
