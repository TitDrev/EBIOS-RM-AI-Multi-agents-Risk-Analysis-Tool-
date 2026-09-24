"""Routeur de comparaison d'études."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, user_can_access
from app.database import get_session
from app.models.analysis import Analysis
from app.models.user import User
from app.services.comparison_service import compare_analyses

router = APIRouter(prefix="/analyses/compare", tags=["analyses"])


class CompareRequest(BaseModel):
    etude_a: uuid.UUID
    etude_b: uuid.UUID


@router.post("")
async def compare(
    payload: CompareRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    analyses = list(
        await session.scalars(
            select(Analysis).where(Analysis.id.in_([payload.etude_a, payload.etude_b]))
        )
    )
    if len(analyses) != 2:
        raise HTTPException(status_code=404, detail="Une ou plusieurs études introuvables")
    if not all(user_can_access(user, a.created_by) for a in analyses):
        raise HTTPException(status_code=403, detail="Accès non autorisé à l'une des études")
    try:
        return await compare_analyses(session, payload.etude_a, payload.etude_b)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
