"""Routeur des ressources EBIOS RM (lecture, accès propriétaire/admin)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_owned_analysis, require_analyst
from app.database import get_session
from app.models.analysis import Analysis
from app.models.asset import Asset
from app.models.feared_event import FearedEvent
from app.models.risk import Risk
from app.models.risk_source import RiskSource
from app.models.scenario import Scenario
from app.models.user import User
from app.schemas.resources import AssetRead, FearedEventRead, RiskRead, RiskSourceRead, ScenarioRead

router = APIRouter(prefix="/analyses/{analysis_id}", tags=["resources"])


@router.get("/assets", response_model=list[AssetRead])
async def list_assets(
    session: AsyncSession = Depends(get_session),
    analysis: Analysis = Depends(get_owned_analysis),
) -> list[Asset]:
    return list(
        await session.scalars(
            select(Asset).where(Asset.analysis_id == analysis.id).order_by(Asset.created_at)
        )
    )


@router.get("/feared-events", response_model=list[FearedEventRead])
async def list_feared_events(
    session: AsyncSession = Depends(get_session),
    analysis: Analysis = Depends(get_owned_analysis),
) -> list[FearedEvent]:
    return list(
        await session.scalars(
            select(FearedEvent).where(FearedEvent.analysis_id == analysis.id)
        )
    )


@router.get("/risk-sources", response_model=list[RiskSourceRead])
async def list_risk_sources(
    session: AsyncSession = Depends(get_session),
    analysis: Analysis = Depends(get_owned_analysis),
) -> list[RiskSource]:
    return list(
        await session.scalars(
            select(RiskSource).where(RiskSource.analysis_id == analysis.id)
        )
    )


@router.get("/scenarios", response_model=list[ScenarioRead])
async def list_scenarios(
    session: AsyncSession = Depends(get_session),
    analysis: Analysis = Depends(get_owned_analysis),
) -> list[Scenario]:
    return list(
        await session.scalars(
            select(Scenario).where(Scenario.analysis_id == analysis.id).order_by(Scenario.identifiant)
        )
    )


@router.get("/risks", response_model=list[RiskRead])
async def list_risks(
    session: AsyncSession = Depends(get_session),
    analysis: Analysis = Depends(get_owned_analysis),
) -> list[Risk]:
    return list(
        await session.scalars(
            select(Risk).where(Risk.analysis_id == analysis.id).order_by(Risk.identifiant)
        )
    )


@router.post("/risks/{risk_id}/validate", response_model=RiskRead)
async def validate_risk(
    risk_id: str,
    session: AsyncSession = Depends(get_session),
    analysis: Analysis = Depends(get_owned_analysis),
    user: User = Depends(require_analyst),
) -> Risk:
    """Validation humaine d'UN risque précis (critère E21 n°3)."""
    risk = await session.get(Risk, risk_id)
    if risk is None or risk.analysis_id != analysis.id:
        raise HTTPException(status_code=404, detail="Risque introuvable")
    risk.valide_par = user.username
    risk.validated_at = datetime.now(timezone.utc).isoformat()
    await session.commit()
    await session.refresh(risk)
    return risk
