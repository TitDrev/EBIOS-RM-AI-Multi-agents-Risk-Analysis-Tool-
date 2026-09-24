"""Routeur des ressources EBIOS RM (lecture seule)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_session
from app.models.analysis import Analysis
from app.models.asset import Asset
from app.models.feared_event import FearedEvent
from app.models.risk_source import RiskSource
from app.models.scenario import Scenario
from app.models.user import User
from app.schemas.resources import AssetRead, FearedEventRead, RiskSourceRead, ScenarioRead

router = APIRouter(prefix="/analyses/{analysis_id}", tags=["resources"])


async def _ensure_exists(session: AsyncSession, analysis_id: uuid.UUID) -> None:
    analysis = await session.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Étude introuvable")


@router.get("/assets", response_model=list[AssetRead])
async def list_assets(
    analysis_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[Asset]:
    await _ensure_exists(session, analysis_id)
    return list(
        await session.scalars(
            select(Asset).where(Asset.analysis_id == analysis_id).order_by(Asset.created_at)
        )
    )


@router.get("/feared-events", response_model=list[FearedEventRead])
async def list_feared_events(
    analysis_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[FearedEvent]:
    await _ensure_exists(session, analysis_id)
    return list(
        await session.scalars(
            select(FearedEvent).where(FearedEvent.analysis_id == analysis_id)
        )
    )


@router.get("/risk-sources", response_model=list[RiskSourceRead])
async def list_risk_sources(
    analysis_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[RiskSource]:
    await _ensure_exists(session, analysis_id)
    return list(
        await session.scalars(
            select(RiskSource).where(RiskSource.analysis_id == analysis_id)
        )
    )


@router.get("/scenarios", response_model=list[ScenarioRead])
async def list_scenarios(
    analysis_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[Scenario]:
    await _ensure_exists(session, analysis_id)
    return list(
        await session.scalars(
            select(Scenario).where(Scenario.analysis_id == analysis_id).order_by(Scenario.identifiant)
        )
    )
