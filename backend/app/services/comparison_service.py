"""Comparaison de deux études (métriques et registres des risques)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis
from app.models.asset import Asset
from app.models.risk import Risk
from app.models.risk_source import RiskSource
from app.models.scenario import Scenario


async def _snapshot(session: AsyncSession, analysis_id: uuid.UUID) -> dict:
    analysis = await session.get(Analysis, analysis_id)
    if analysis is None:
        raise ValueError("Étude introuvable")

    assets = len((await session.scalars(select(Asset).where(Asset.analysis_id == analysis_id))).all())
    sources = len(
        (await session.scalars(select(RiskSource).where(RiskSource.analysis_id == analysis_id))).all()
    )
    strategic = len(
        (
            await session.scalars(
                select(Scenario).where(
                    Scenario.analysis_id == analysis_id, Scenario.kind == "strategique"
                )
            )
        ).all()
    )
    operational = len(
        (
            await session.scalars(
                select(Scenario).where(
                    Scenario.analysis_id == analysis_id, Scenario.kind == "operationnel"
                )
            )
        ).all()
    )
    risks = (await session.scalars(select(Risk).where(Risk.analysis_id == analysis_id))).all()
    niveaux: dict[str, int] = {}
    for r in risks:
        niveau = r.niveau or "non évalué"
        niveaux[niveau] = niveaux.get(niveau, 0) + 1

    return {
        "id": str(analysis.id),
        "nom": analysis.name,
        "statut": analysis.status,
        "atelier_courant": analysis.current_workshop,
        "biens": assets,
        "sources_de_risques": sources,
        "scenarios_strategiques": strategic,
        "scenarios_operationnels": operational,
        "risques": len(risks),
        "par_niveau": niveaux,
    }


def _diff(a: dict, b: dict) -> dict:
    keys = [
        "biens",
        "sources_de_risques",
        "scenarios_strategiques",
        "scenarios_operationnels",
        "risques",
    ]
    evolution = {}
    for key in keys:
        evolution[key] = {
            "a": a.get(key, 0),
            "b": b.get(key, 0),
            "delta": (b.get(key, 0) or 0) - (a.get(key, 0) or 0),
        }
    return evolution


async def compare_analyses(
    session: AsyncSession, analysis_a: uuid.UUID, analysis_b: uuid.UUID
) -> dict:
    """Compare deux études : métriques, répartition par niveau, différences."""
    a = await _snapshot(session, analysis_a)
    b = await _snapshot(session, analysis_b)
    return {
        "etude_a": a,
        "etude_b": b,
        "differences": _diff(a, b),
    }
