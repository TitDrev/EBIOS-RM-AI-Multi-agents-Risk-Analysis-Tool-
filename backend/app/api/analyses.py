"""Routeur des études (analyses EBIOS RM)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_owned_analysis, require_analyst
from app.database import get_session
from app.models.analysis import Analysis
from app.models.enums import AnalysisStatus, UserRole
from app.models.user import User
from app.schemas.analysis import AnalysisCreate, AnalysisRead
from app.services.analysis_service import run_workshop

router = APIRouter(prefix="/analyses", tags=["analyses"])


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
    query = select(Analysis)
    if user.role != UserRole.ADMIN:
        query = query.where(Analysis.created_by == user.id)
    return list(await session.scalars(query.order_by(Analysis.created_at.desc())))


@router.get("/{analysis_id}", response_model=AnalysisRead)
async def get_analysis(
    analysis: Analysis = Depends(get_owned_analysis),
    user: User = Depends(get_current_user),
) -> Analysis:
    return analysis


@router.post("/{analysis_id}/start", response_model=AnalysisRead)
async def start_analysis(
    analysis: Analysis = Depends(get_owned_analysis),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_analyst),
) -> Analysis:
    if analysis.current_workshop > 0:
        raise HTTPException(status_code=400, detail="Étude déjà démarrée")
    analysis.status = AnalysisStatus.IN_PROGRESS
    await run_workshop(session, analysis, 1)
    await session.refresh(analysis)
    return analysis


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis: Analysis = Depends(get_owned_analysis),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_analyst),
) -> None:
    await session.delete(analysis)
    await session.commit()
