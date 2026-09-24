"""Routeur des études (analyses EBIOS RM)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_analyst
from app.database import get_session
from app.models.analysis import Analysis
from app.models.enums import AnalysisStatus
from app.models.user import User
from app.schemas.analysis import AnalysisCreate, AnalysisRead
from app.services.analysis_service import run_workshop

router = APIRouter(prefix="/analyses", tags=["analyses"])


async def _get_analysis_or_404(session: AsyncSession, analysis_id: uuid.UUID) -> Analysis:
    analysis = await session.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Étude introuvable")
    return analysis


@router.post("", response_model=AnalysisRead, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    payload: AnalysisCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_analyst),
) -> Analysis:
    analysis = Analysis(
        name=payload.name,
        si_description=payload.si_description,
        status=AnalysisStatus.DRAFT,
        created_by=user.id,
    )
    session.add(analysis)
    await session.commit()
    await session.refresh(analysis)
    return analysis


@router.get("", response_model=list[AnalysisRead])
async def list_analyses(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[Analysis]:
    return list(await session.scalars(select(Analysis).order_by(Analysis.created_at.desc())))


@router.get("/{analysis_id}", response_model=AnalysisRead)
async def get_analysis(
    analysis_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Analysis:
    return await _get_analysis_or_404(session, analysis_id)


@router.post("/{analysis_id}/start", response_model=AnalysisRead)
async def start_analysis(
    analysis_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_analyst),
) -> Analysis:
    analysis = await _get_analysis_or_404(session, analysis_id)
    if analysis.current_workshop > 0:
        raise HTTPException(status_code=400, detail="Étude déjà démarrée")
    analysis.status = AnalysisStatus.IN_PROGRESS
    await run_workshop(session, analysis, 1)
    await session.refresh(analysis)
    return analysis


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_analyst),
) -> None:
    analysis = await _get_analysis_or_404(session, analysis_id)
    await session.delete(analysis)
    await session.commit()
