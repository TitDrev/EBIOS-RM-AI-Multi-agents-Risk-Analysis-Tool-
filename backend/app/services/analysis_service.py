"""Orchestration des ateliers : exécution pas à pas + validation humaine."""

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import WORKSHOP_FUNCTIONS
from app.agents.prompts import WORKSHOP_PROMPTS
from app.agents.state import AnalysisState
from app.models.agent_run import AgentRun
from app.models.analysis import Analysis
from app.models.asset import Asset
from app.models.enums import AgentRunStatus, AnalysisStatus, AssetKind, ScenarioKind, WorkshopStatus
from app.models.feared_event import FearedEvent
from app.models.risk_source import RiskSource
from app.models.scenario import Scenario
from app.models.workshop import Workshop
from app.services.rag_service import build_context, seed_knowledge

AGENT_BY_WORKSHOP = {
    1: "workshop1_framing",
    2: "workshop2_risk_sources",
    3: "workshop3_strategic",
    4: "workshop4_operational",
    5: "workshop5_treatment",
}

KNOWLEDGE_QUERIES = {
    2: "typologie et caractérisation des sources de risques EBIOS RM",
    3: "scénarios stratégiques gravité vraisemblance appréciation du risque EBIOS RM",
    4: "scénarios opérationnels chemin d'attaque techniques MITRE ATT&CK",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _load_outputs(session: AsyncSession, analysis_id: uuid.UUID) -> dict[int, dict]:
    rows = await session.scalars(
        select(Workshop).where(Workshop.analysis_id == analysis_id).order_by(Workshop.numero)
    )
    return {w.numero: w.output for w in rows}


async def run_workshop(session: AsyncSession, analysis: Analysis, numero: int) -> Workshop:
    """Exécute l'atelier `numero` et persiste sa sortie (status awaiting_validation)."""
    start = time.monotonic()
    knowledge_context = ""
    if numero >= 2:
        await seed_knowledge(session)
        query = KNOWLEDGE_QUERIES.get(numero)
        if query:
            knowledge_context = await build_context(session, query)

    state: AnalysisState = {
        "analysis_id": str(analysis.id),
        "si_description": analysis.si_description,
        "workshop_outputs": await _load_outputs(session, analysis.id),
        "knowledge_context": knowledge_context,
    }

    output = await WORKSHOP_FUNCTIONS[numero](state)

    workshop = Workshop(
        analysis_id=analysis.id,
        numero=numero,
        status=WorkshopStatus.AWAITING_VALIDATION,
        output=output,
    )
    session.add(workshop)
    await session.flush()

    duration_ms = int((time.monotonic() - start) * 1000)
    agent_name = AGENT_BY_WORKSHOP[numero]
    session.add(
        AgentRun(
            analysis_id=analysis.id,
            agent=agent_name,
            workshop=numero,
            prompt_version=WORKSHOP_PROMPTS[agent_name]["version"],
            input_snapshot=None,
            output=output,
            duration_ms=duration_ms,
            status=AgentRunStatus.SUCCESS,
        )
    )

    if numero == 1:
        await _persist_cadrage(session, analysis.id, output)
    elif numero == 2:
        await _persist_risk_sources(session, analysis.id, output)
    elif numero == 3:
        await _persist_scenarios(session, analysis.id, output)
    elif numero == 4:
        await _persist_operational_scenarios(session, analysis.id, output)

    analysis.current_workshop = numero
    analysis.status = AnalysisStatus.AWAITING_VALIDATION
    await session.commit()
    await session.refresh(workshop)
    return workshop


async def _persist_cadrage(session: AsyncSession, analysis_id: uuid.UUID, output: dict) -> None:
    """Matérialise les biens et événements redoutés issus de l'Atelier 1."""
    essentiel_ids: dict[str, uuid.UUID] = {}
    for bien in output.get("biens_essentiels", []):
        asset = Asset(
            analysis_id=analysis_id,
            name=bien["name"],
            kind=AssetKind.BIEN_ESSENTIEL,
            description=bien.get("description", ""),
        )
        session.add(asset)
        await session.flush()
        essentiel_ids[bien["name"]] = asset.id

    for bien in output.get("biens_supports", []):
        session.add(
            Asset(
                analysis_id=analysis_id,
                name=bien["name"],
                kind=AssetKind.BIEN_SUPPORT,
                description=bien.get("description", ""),
                supports=bien.get("supports", ""),
            )
        )

    for ev in output.get("evenements_redoutes", []):
        session.add(
            FearedEvent(
                analysis_id=analysis_id,
                label=ev["label"],
                bien_essentiel_id=essentiel_ids.get(ev.get("bien_essentiel")),
                besoin=ev.get("besoin"),
                gravite=ev.get("gravite"),
            )
        )


async def _persist_risk_sources(session: AsyncSession, analysis_id: uuid.UUID, output: dict) -> None:
    """Matérialise les sources de risques issues de l'Atelier 2."""
    for source in output.get("sources_risques", []):
        session.add(
            RiskSource(
                analysis_id=analysis_id,
                type=source.get("type"),
                name=source.get("name"),
                objectif=source.get("objectif"),
                motivation=source.get("motivation"),
                capacite=source.get("capacite"),
                biens_vises=source.get("biens_vises", []),
                pertinence=source.get("pertinence"),
                description=source.get("description"),
            )
        )


async def _persist_scenarios(session: AsyncSession, analysis_id: uuid.UUID, output: dict) -> None:
    """Matérialise les scénarios stratégiques issus de l'Atelier 3."""
    for scenario in output.get("scenarios_strategiques", []):
        source = scenario.get("source_risque", "")
        evenement = scenario.get("evenement_redoute", "")
        session.add(
            Scenario(
                analysis_id=analysis_id,
                kind=ScenarioKind.STRATEGIQUE,
                identifiant=scenario.get("identifiant"),
                gravite=scenario.get("gravite"),
                vraisemblance=scenario.get("vraisemblance"),
                niveau=scenario.get("niveau"),
                description=f"{source} provoque « {evenement} »",
                detail=scenario,
            )
        )


async def _persist_operational_scenarios(
    session: AsyncSession, analysis_id: uuid.UUID, output: dict
) -> None:
    """Matérialise les scénarios opérationnels issus de l'Atelier 4 (liés au stratégique)."""
    rows = await session.scalars(
        select(Scenario).where(
            Scenario.analysis_id == analysis_id, Scenario.kind == ScenarioKind.STRATEGIQUE
        )
    )
    strategic_ids = {s.identifiant: s.id for s in rows if s.identifiant}

    for scenario in output.get("scenarios_operationnels", []):
        ref = scenario.get("scenario_strategique", "")
        steps = scenario.get("chemin_attaque", [])
        session.add(
            Scenario(
                analysis_id=analysis_id,
                kind=ScenarioKind.OPERATIONNEL,
                identifiant=scenario.get("identifiant"),
                parent_id=strategic_ids.get(ref),
                gravite=scenario.get("gravite"),
                vraisemblance=scenario.get("vraisemblance"),
                niveau=scenario.get("niveau"),
                description=" → ".join(steps) if steps else ref,
                detail=scenario,
            )
        )


async def validate_workshop(
    session: AsyncSession, analysis: Analysis, numero: int, user: str
) -> Workshop | None:
    """Valide l'atelier `numero`, puis enchaîne sur l'atelier suivant (s'il existe).

    Retourne l'atelier suivant nouvellement produit, ou l'atelier validé si `numero`
    est le dernier (5).
    """
    workshop = await session.scalar(
        select(Workshop).where(
            Workshop.analysis_id == analysis.id, Workshop.numero == numero
        )
    )
    if workshop is None or workshop.status != WorkshopStatus.AWAITING_VALIDATION:
        return None

    workshop.status = WorkshopStatus.VALIDATED
    workshop.validated_by = user
    workshop.validated_at = _now()
    await session.commit()
    await session.refresh(workshop)

    if numero >= 5:
        analysis.status = AnalysisStatus.COMPLETED
        await session.commit()
        return workshop

    return await run_workshop(session, analysis, numero + 1)
