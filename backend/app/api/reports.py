"""Routeur du compte rendu final."""

import asyncio
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_analyst
from app.database import get_session
from app.models.analysis import Analysis
from app.models.user import User
from app.services import report_generator

router = APIRouter(prefix="/analyses/{analysis_id}/report", tags=["reports"])

ReportFormat = Literal["json", "csv", "pdf"]


@router.post("")
async def generate_report(
    analysis_id: uuid.UUID,
    format: ReportFormat = "json",
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_analyst),
) -> Response:
    analysis = await session.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Étude introuvable")

    data = await report_generator.build_report_data(session, analysis_id)

    if format == "json":
        from fastapi.responses import JSONResponse

        return JSONResponse(data)

    if format == "csv":
        csv_text = report_generator.to_csv(data["registre_des_risques"])
        return Response(
            content=csv_text,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="registre_{analysis_id}.csv"'},
        )

    # PDF : exécution dans un thread (WeasyPrint est synchrone et coûteux).
    try:
        pdf_bytes = await asyncio.to_thread(report_generator.to_pdf, data)
    except Exception as exc:  # WeasyPrint peut échouer sans librairies système
        raise HTTPException(
            status_code=500,
            detail=f"Génération PDF indisponible sur cette installation : {exc}",
        ) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="compte_rendu_{analysis_id}.pdf"'},
    )
