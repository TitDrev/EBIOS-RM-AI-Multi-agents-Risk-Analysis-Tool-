"""Routeur des études (analyses EBIOS RM)."""

import io
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_owned_analysis, require_analyst
from app.database import get_session
from app.models.analysis import Analysis
from app.models.enums import AnalysisStatus, UserRole
from app.models.knowledge import KnowledgeDocument
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


def _extract_file_text(filename: str, raw: bytes) -> str | None:
    """Extrait le texte d'un fichier PDF, Markdown, texte ou JSON."""
    lower = filename.lower()
    try:
        if lower.endswith(".pdf"):
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(raw))
            return "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()
        if lower.endswith((".md", ".txt", ".json")):
            return raw.decode("utf-8", errors="ignore").strip()
    except Exception:
        return None
    return None


async def _ingest_document(session: AsyncSession, filename: str, content: str) -> None:
    """Ajoute le document à la base de connaissances (RAG) s'il n'existe pas déjà."""
    title = Path(filename).stem
    existing = await session.scalar(
        select(KnowledgeDocument).where(KnowledgeDocument.title == title)
    )
    if existing is None and content:
        session.add(
            KnowledgeDocument(title=title, source="user-document", content=content)
        )
        await session.commit()


@router.post("/upload", response_model=AnalysisRead, status_code=status.HTTP_201_CREATED)
async def upload_analysis(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_analyst),
    name: str | None = Form(default=None),
    files: list[UploadFile] = File(...),
) -> Analysis:
    """Crée une étude à partir d'un ou plusieurs documents (PDF / Markdown / JSON)."""
    if not files:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni")

    si_description: dict = {}
    documents: list[dict] = []

    for upload in files:
        filename = upload.filename or "document"
        raw = await upload.read()
        text = _extract_file_text(filename, raw)
        if text is None:
            raise HTTPException(
                status_code=400,
                detail=f"Format non pris en charge : {filename} (PDF, MD, TXT, JSON acceptés).",
            )

        if filename.lower().endswith(".json"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail=f"JSON invalide : {filename}") from None
            if isinstance(parsed, dict):
                base = parsed.get("si_description")
                si_description.update(base if isinstance(base, dict) else parsed)

        documents.append({"titre": filename, "contenu": text})
        await _ingest_document(session, filename, text)

    si_description.setdefault("nom", name or documents[0]["titre"])
    si_description["documents"] = documents

    analysis = Analysis(
        name=si_description["nom"],
        si_description=si_description,
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
