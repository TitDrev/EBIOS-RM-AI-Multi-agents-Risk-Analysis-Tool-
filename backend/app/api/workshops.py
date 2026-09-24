"""Routeur des ateliers et de la validation humaine (valider / corriger / relancer)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_owned_analysis, require_analyst
from app.database import get_session
from app.models.analysis import Analysis
from app.models.user import User
from app.models.workshop import Workshop
from app.schemas.workshop import WorkshopRead, WorkshopValidate
from app.services.analysis_service import correct_workshop, retry_workshop, validate_workshop

router = APIRouter(prefix="/analyses/{analysis_id}/workshops", tags=["workshops"])


@router.get("", response_model=list[WorkshopRead])
async def list_workshops(
    session: AsyncSession = Depends(get_session),
    analysis: Analysis = Depends(get_owned_analysis),
    user: User = Depends(require_analyst),
) -> list[Workshop]:
    return list(
        await session.scalars(
            select(Workshop).where(Workshop.analysis_id == analysis.id).order_by(Workshop.numero)
        )
    )


@router.get("/{numero}", response_model=WorkshopRead)
async def get_workshop(
    numero: int,
    session: AsyncSession = Depends(get_session),
    analysis: Analysis = Depends(get_owned_analysis),
    user: User = Depends(require_analyst),
) -> Workshop:
    workshop = await session.scalar(
        select(Workshop).where(Workshop.analysis_id == analysis.id, Workshop.numero == numero)
    )
    if workshop is None:
        raise HTTPException(status_code=404, detail="Atelier introuvable")
    return workshop


@router.post("/{numero}/validate", response_model=WorkshopRead)
async def validate(
    numero: int,
    payload: WorkshopValidate,
    session: AsyncSession = Depends(get_session),
    analysis: Analysis = Depends(get_owned_analysis),
    user: User = Depends(require_analyst),
) -> Workshop:
    workshop = await validate_workshop(session, analysis, numero, user.username)
    if workshop is None:
        raise HTTPException(
            status_code=409,
            detail="Cet atelier n'est pas en attente de validation ou n'existe pas",
        )
    return workshop


@router.post("/{numero}/correct", response_model=WorkshopRead)
async def correct(
    numero: int,
    payload: WorkshopValidate,
    session: AsyncSession = Depends(get_session),
    analysis: Analysis = Depends(get_owned_analysis),
    user: User = Depends(require_analyst),
) -> Workshop:
    try:
        return await correct_workshop(session, analysis, numero, payload.corrections, user.username)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{numero}/retry", response_model=WorkshopRead)
async def retry(
    numero: int,
    session: AsyncSession = Depends(get_session),
    analysis: Analysis = Depends(get_owned_analysis),
    user: User = Depends(require_analyst),
) -> Workshop:
    try:
        return await retry_workshop(session, analysis, numero, user.username)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
