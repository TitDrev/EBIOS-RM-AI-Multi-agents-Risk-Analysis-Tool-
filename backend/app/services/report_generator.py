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


# --------------------------------------------------------------------------
# Export Excel (un onglet par atelier + synthèse + plan de traitement)
# --------------------------------------------------------------------------

_LEVEL_FILL = {
    "faible": "C6EFCE",     # vert clair
    "moyen": "FFF2CC",      # jaune clair
    "eleve": "FCE4D6",      # orange clair
    "critique": "FFC7CE",   # rouge clair
}
_HEADER_FILL = "DDEBF7"
_TRAITEMENT = {
    "reduire": "2E75B6", "transferer": "7030A0", "eviter": "808080", "accepter": "BF9000",
}


def to_excel(data: dict) -> bytes:
    """Génère un classeur Excel : synthèse (matrices origine/résiduel) + plan de traitement + 1 onglet/atelier."""

    def fill(cell, value: str | None, fills: dict) -> None:
        if value in fills:
            cell.fill = PatternFill("solid", fgColor=fills[value])

    def level_fill(cell, value: str | None) -> None:
        fill(cell, value, _LEVEL_FILL)

    def cell_val(value: object) -> str:
        if isinstance(value, list):
            return "; ".join(str(v) for v in value)
        return "" if value is None else str(value)

    def section(ws, text: str) -> None:
        ws.append([text])
        for cell in ws[ws.max_row]:
            cell.font = Font(bold=True, size=12)
            cell.fill = PatternFill("solid", fgColor=_HEADER_FILL)

    def kpi(ws, label: str, value: object) -> None:
        ws.append([label, value])

    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()

    # --- Synthèse ---
    ws = wb.active
    ws.title = "Synthèse"
    ws.append(["Compte rendu EBIOS RM — Synthèse"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([])
    a = data.get("analyse", {})
    kpi(ws, "Étude", a.get("nom", ""))
    kpi(ws, "Statut", a.get("statut", ""))
    kpi(ws, "Atelier courant", a.get("atelier_courant", ""))
    ws.append([])

    section(ws, "Métriques")
    kpi(ws, "Biens", len(data.get("biens", [])))
    kpi(ws, "Événements redoutés", len(data.get("evenements_redoutes", [])))
    kpi(ws, "Sources de risques", len(data.get("sources_de_risques", [])))
    kpi(ws, "Scénarios stratégiques", len([s for s in data.get("scenarios", []) if s.get("kind") == "strategique"]))
    kpi(ws, "Scénarios opérationnels", len([s for s in data.get("scenarios", []) if s.get("kind") == "operationnel"]))
    kpi(ws, "Risques", len(data.get("registre_des_risques", [])))

    # Matrice d'origine (comptage gravité × vraisemblance des risques)
    risks = data.get("registre_des_risques", [])
    counts = {f"g{i}": {f"v{j}": 0 for j in range(1, 5)} for i in range(1, 5)}
    for r in risks:
        g = r.get("gravite") or "g1"
        v = r.get("vraisemblance") or "v1"
        counts.setdefault(g, {})
        counts[g][v] = counts[g].get(v, 0) + 1
    ws.append([])
    section(ws, "Matrice des risques d'origine (gravité × vraisemblance)")
    ws.append(["", "V1", "V2", "V3", "V4"])
    for col in ws[ws.max_row]:
        col.font = Font(bold=True)
    for g in ("g1", "g2", "g3", "g4"):
        row = [g.upper()] + [counts[g][f"v{i}"] for i in range(1, 5)]
        ws.append(row)
    ws.append([])

    # Synthèse des niveaux : origine vs résiduel
    section(ws, "Comparaison origine ↔ résiduel (par niveau de risque)")
    ws.append(["Niveau", "Risques d'origine", "Risques résiduels"])
    for col in ws[ws.max_row]:
        col.font = Font(bold=True)
    levels = ["faible", "moyen", "eleve", "critique"]
    orig = {lv: 0 for lv in levels}
    resid = {lv: 0 for lv in levels}
    for r in risks:
        orig[r.get("niveau", "eleve")] = orig.get(r.get("niveau", "eleve"), 0) + 1
        resid[r.get("risque_residuel", "eleve")] = resid.get(r.get("risque_residuel", "eleve"), 0) + 1
    for lv in levels:
        rw = [lv, orig[lv], resid[lv]]
        ws.append(rw)
        for cell in ws[ws.max_row][:1]:
            level_fill(cell, lv)
    ws.append([])

    # Liste des risques retenus
    section(ws, "Risques retenus")
    ws.append(["ID", "Événement redouté", "Niveau", "Traitement", "Résiduel"])
    for col in ws[ws.max_row]:
        col.font = Font(bold=True)
    for r in risks:
        rw = [r.get("identifiant"), cell_val(r.get("justification") or r.get("sources", "")),
              r.get("niveau"), r.get("traitement"), r.get("risque_residuel")]
        ws.append(rw)
        level_fill(ws.cell(row=ws.max_row, column=3), r.get("niveau"))
        level_fill(ws.cell(row=ws.max_row, column=5), r.get("risque_residuel"))
    ws.append([])
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 60

    # --- Plan de traitement ---
    ws2 = wb.create_sheet("Plan de traitement")
    header2 = ["ID", "Bien", "Événement redouté", "Source", "Gravité", "Vraisemblance", "Niveau",
               "Traitement", "Mesures", "Résiduel", "Justification"]
    ws2.append(header2)
    for col in ws2[1]:
        col.font = Font(bold=True, color="FFFFFF")
        col.fill = PatternFill("solid", fgColor="4472C4")
    for r in risks:
        ws2.append([
            r.get("identifiant"), "", cell_val(r.get("justification")), "",
            r.get("gravite"), r.get("vraisemblance"), r.get("niveau"),
            r.get("traitement"), "; ".join(r.get("mesures", [])), r.get("risque_residuel"),
            cell_val(r.get("sources", "")),
        ])
        last = ws2.max_row
        level_fill(ws2.cell(row=last, column=7), r.get("niveau"))
        level_fill(ws2.cell(row=last, column=10), r.get("risque_residuel"))
        fill(ws2.cell(row=last, column=8), r.get("traitement"), _TRAITEMENT)
    widths = [10, 22, 34, 16, 10, 14, 10, 12, 60, 12, 40]
    for i, w in enumerate(widths, start=1):
        ws2.column_dimensions[chr(64 + i)].width = w
    ws2.freeze_panes = "A2"

    # --- Un onglet par atelier ---
    for atelier in data.get("ateliers", []):
        numero = atelier.get("numero", "?")
        ws_n = wb.create_sheet(f"Atelier {numero}")
        ws_n.append([f"Atelier {numero} — {atelier.get('statut', '')}"])
        ws_n["A1"].font = Font(bold=True, size=13)
        ws_n.append([])

        def dump(d: dict, indent: str = "") -> None:
            for k, v in d.items():
                if k.startswith("_") or k == "documents":
                    continue
                if isinstance(v, dict):
                    ws_n.append([f"{indent}{k} :"])
                    dump(v, indent + "  ")
                elif isinstance(v, list):
                    ws_n.append([f"{indent}{k} :"])
                    for item in v:
                        if isinstance(item, dict):
                            dump(item, indent + "  ")
                        else:
                            ws_n.append([f"{indent}  - {item}"])
                else:
                    ws_n.append([f"{indent}{k} : {v}"])

        dump(atelier.get("sortie", {}))
        ws_n.column_dimensions["A"].width = 100

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
