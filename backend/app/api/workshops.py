"""Routeur des ateliers et de la validation humaine."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_analyst
from app.database import get_session
from app.models.analysis import Analysis
from app.models.user import User
from app.models.workshop import Workshop
from app.schemas.workshop import WorkshopRead, WorkshopValidate
from app.services.analysis_service import validate_workshop

router = APIRouter(prefix="/analyses/{analysis_id}/workshops", tags=["workshops"])


async def _get_analysis(session: AsyncSession, analysis_id: uuid.UUID) -> Analysis:
    analysis = await session.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Étude introuvable")
    return analysis


@router.get("", response_model=list[WorkshopRead])
async def list_workshops(
    analysis_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[Workshop]:
    await _get_analysis(session, analysis_id)
    return list(
        await session.scalars(
            select(Workshop)
            .where(Workshop.analysis_id == analysis_id)
            .order_by(Workshop.numero)
        )
    )


@router.get("/{numero}", response_model=WorkshopRead)
async def get_workshop(
    analysis_id: uuid.UUID,
    numero: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Workshop:
    await _get_analysis(session, analysis_id)
    workshop = await session.scalar(
        select(Workshop).where(
            Workshop.analysis_id == analysis_id, Workshop.numero == numero
        )
    )
    if workshop is None:
        raise HTTPException(status_code=404, detail="Atelier introuvable")
    return workshop


@router.post("/{numero}/validate", response_model=WorkshopRead)
async def validate(
    analysis_id: uuid.UUID,
    numero: int,
    payload: WorkshopValidate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_analyst),
) -> Workshop:
    analysis = await _get_analysis(session, analysis_id)
    workshop = await validate_workshop(session, analysis, numero, user.username)

    if workshop is None:
        raise HTTPException(
            status_code=409,
            detail="Cet atelier n'est pas en attente de validation ou n'existe pas",
        )
    return workshop
