"""Génération du compte rendu final (JSON / CSV / PDF)."""

import csv
import io
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis
from app.models.asset import Asset
from app.models.feared_event import FearedEvent
from app.models.risk import Risk
from app.models.risk_source import RiskSource
from app.models.scenario import Scenario
from app.models.workshop import Workshop


async def build_report_data(session: AsyncSession, analysis_id: uuid.UUID) -> dict:
    """Assemble toutes les données de l'étude pour le compte rendu."""
    analysis = await session.get(Analysis, analysis_id)
    if analysis is None:
        raise ValueError("Étude introuvable")

    workshops = list(
        await session.scalars(
            select(Workshop).where(Workshop.analysis_id == analysis_id).order_by(Workshop.numero)
        )
    )
    assets = list(await session.scalars(select(Asset).where(Asset.analysis_id == analysis_id)))
    feared_events = list(
        await session.scalars(select(FearedEvent).where(FearedEvent.analysis_id == analysis_id))
    )
    risk_sources = list(
        await session.scalars(select(RiskSource).where(RiskSource.analysis_id == analysis_id))
    )
    scenarios = list(
        await session.scalars(
            select(Scenario).where(Scenario.analysis_id == analysis_id).order_by(Scenario.identifiant)
        )
    )
    risks = list(await session.scalars(select(Risk).where(Risk.analysis_id == analysis_id)))

    return {
        "analyse": {
            "id": str(analysis.id),
            "nom": analysis.name,
            "statut": analysis.status,
            "atelier_courant": analysis.current_workshop,
            "description_si": analysis.si_description,
            "cree_le": analysis.created_at.isoformat() if analysis.created_at else None,
        },
        "ateliers": [
            {"numero": w.numero, "statut": w.status, "valide_par": w.validated_by, "sortie": w.output}
            for w in workshops
        ],
        "biens": [
            {
                "name": a.name,
                "kind": a.kind,
                "description": a.description,
                "supports": a.supports,
            }
            for a in assets
        ],
        "evenements_redoutes": [
            {"label": e.label, "besoin": e.besoin, "gravite": e.gravite} for e in feared_events
        ],
        "sources_de_risques": [
            {
                "type": s.type,
                "name": s.name,
                "capacite": s.capacite,
                "biens_vises": s.biens_vises,
                "pertinence": s.pertinence,
            }
            for s in risk_sources
        ],
        "scenarios": [
            {
                "kind": s.kind,
                "identifiant": s.identifiant,
                "niveau": s.niveau,
                "description": s.description,
                "detail": s.detail,
            }
            for s in scenarios
        ],
        "registre_des_risques": [
            {
                "identifiant": r.identifiant,
                "niveau": r.niveau,
                "traitement": r.traitement,
                "mesures": r.mesures,
                "risque_residuel": r.risque_residuel,
                "sources": r.sources,
                "justification": r.justification,
                "valide_par": r.valide_par,
            }
            for r in risks
        ],
    }


def to_json(data: dict) -> str:
    import json

    return json.dumps(data, ensure_ascii=False, indent=2)


def to_csv(risks: list[dict]) -> str:
    """Exporte le registre des risques en CSV."""
    output = io.StringIO()
    fieldnames = [
        "identifiant",
        "niveau",
        "traitement",
        "risque_residuel",
        "mesures",
        "sources",
        "justification",
        "valide_par",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in risks:
        row = {
            "identifiant": r.get("identifiant"),
            "niveau": r.get("niveau"),
            "traitement": r.get("traitement"),
            "risque_residuel": r.get("risque_residuel"),
            "mesures": "; ".join(r.get("mesures", [])),
            "sources": "; ".join(r.get("sources", [])),
            "justification": r.get("justification"),
            "valide_par": r.get("valide_par"),
        }
        writer.writerow(row)
    return output.getvalue()


_PDF_TEMPLATE = """\
<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><style>
body {{ font-family: sans-serif; margin: 2cm; color: #1f2937; }}
h1 {{ color: #111827; }} h2 {{ color: #374151; font-size: 1.1em; }}
table {{ width: 100%; border-collapse: collapse; margin: 1em 0; }}
th, td {{ border: 1px solid #d1d5db; padding: 6px 8px; font-size: 0.85em; text-align: left; }}
th {{ background: #f3f4f6; }}
</style></head>
<body>
<h1>Compte rendu — Analyse de risques EBIOS RM</h1>
<p><strong>{nom}</strong> · statut : {statut}</p>
<h2>Registre des risques</h2>
<table>
<tr><th>ID</th><th>Niveau</th><th>Traitement</th><th>Risque résiduel</th><th>Mesures</th></tr>
{rows}
</table>
</body></html>
"""


def to_pdf(data: dict) -> bytes:
    """Génère un PDF via WeasyPrint (mode dégradé si la bibliothèque échoue)."""
    rows = []
    for r in data.get("registre_des_risques", []):
        mesures = "<br>".join(r.get("mesures", [])) or "—"
        rows.append(
            "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>".format(
                r.get("identifiant", ""),
                r.get("niveau", ""),
                r.get("traitement", ""),
                r.get("risque_residuel", ""),
                mesures,
            )
        )
    html = _PDF_TEMPLATE.format(
        nom=data.get("analyse", {}).get("nom", ""),
        statut=data.get("analyse", {}).get("statut", ""),
        rows="\n".join(rows),
    )
    from weasyprint import HTML

    return HTML(string=html).write_pdf()
