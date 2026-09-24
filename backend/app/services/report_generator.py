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


def to_excel(data: dict) -> bytes:
    """Génère un classeur Excel : entrées & contexte, 1 onglet/atelier en tableaux,
    plan de traitement, puis synthèse finale (matrices origine/résiduel)."""

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    _HEADER = "4472C4"
    _SECTION = "DDEBF7"
    _GRAVITY = {"g1": "C6EFCE", "g2": "D9EAD3", "g3": "FFE699", "g4": "FFC7CE"}
    _LIKELIHOOD = {"v1": "F2F2F2", "v2": "DDEBF7", "v3": "BDD7EE", "v4": "9DC3E6"}
    _PERTINENCE = {"retenue": "C6EFCE", "a_suivre": "FFF2CC", "ecartee": "D9D9D9"}

    def cell_val(v):
        if v is None:
            return ""
        return "; ".join(str(x) for x in v) if isinstance(v, list) else str(v)

    def section(ws, text):
        ws.append([text])
        for c in ws[ws.max_row]:
            c.font = Font(bold=True, size=12, color="1F3864")
            c.fill = PatternFill("solid", fgColor=_SECTION)

    def table(ws, headers, rows, colored=None):
        ws.append(headers)
        for c in ws[ws.max_row]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor=_HEADER)
        for r in rows:
            ws.append([cell_val(v) for v in r])
        for col_index, fillmap in (colored or {}).items():
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=col_index, max_col=col_index):
                cell = row[0]
                if cell.value in fillmap:
                    cell.fill = PatternFill("solid", fgColor=fillmap[cell.value])

    def finish(ws, overrides=None):
        """Bordures visibles, texte centré verticalement (enveloppé), largeurs et
        hauteurs de lignes adaptées au contenu."""
        import math as _math

        overrides = overrides or {}
        thin = Side(style="thin", color="9CA3AF")

        # Largeurs : sur mesure par colonne, plafonnées, en tenant compte des surcharges.
        widths: dict[str, int] = {}
        for col in range(1, ws.max_column + 1):
            letter = get_column_letter(col)
            if letter in overrides:
                widths[letter] = int(overrides[letter])
                continue
            lens = [
                len(str(c.value))
                for row in ws.iter_rows(min_col=col, max_col=col)
                for c in row
                if c.value is not None and not isinstance(c.value, (int, float))
            ]
            num = max(lens) if lens else 0
            widths[letter] = max(10, min(num + 2, 55))
        for letter, w in widths.items():
            ws.column_dimensions[letter].width = w

        # Hauteurs de lignes estimées (texte enroulé) + bordures + alignement.
        for r in range(1, ws.max_row + 1):
            row_has_value = any(
                ws.cell(row=r, column=col).value is not None
                for col in range(1, ws.max_column + 1)
            )
            if not row_has_value:
                continue
            max_lines = 1
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=r, column=col)
                letter = get_column_letter(col)
                cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
                if cell.value is not None:
                    cell.alignment = Alignment(
                        vertical="center",
                        horizontal="center" if r == 1 else "left",
                        wrap_text=True,
                    )
                    if isinstance(cell.value, str) and cell.value:
                        wcol = max(2, widths.get(letter, 12) - 3)
                        lines = _math.ceil(len(cell.value) / wcol)
                        max_lines = max(max_lines, lines)
            ws.row_dimensions[r].height = max(18, max_lines * 14 + 6)

    wb = Workbook()
    a = data.get("analyse", {})

    # ---- 1) Entrées & contexte ----
    ws_in = wb.active
    ws_in.title = "Entrées & contexte"
    section(ws_in, "Données d'entrée du SI")
    table(ws_in, ["Champ", "Contenu"], [])
    desc = a.get("description_si") or {}
    for key, label in [("nom", "Nom"), ("ecosysteme", "Écosystème"), ("flux", "Flux de données"),
                       ("contexte_metier", "Contexte métier"), ("contraintes", "Contraintes")]:
        ws_in.append([label, cell_val(desc.get(key, ""))])
    docs = desc.get("documents") or []
    if docs:
        ws_in.append([])
        section(ws_in, "Documents fournis (intégrés à la base de connaissances)")
        table(ws_in, ["Titre", "Extrait (200 caractères)"],
              [[d.get("titre", ""), cell_val(d.get("contenu"))[:200]] for d in docs])
    finish(ws_in, overrides={"A": 24, "B": 90})

    # ---- 2) Un onglet par atelier (tableaux propres) ----
    def atelier_sheets():
        for atelier in data.get("ateliers", []):
            numero = atelier.get("numero")
            sortie = atelier.get("sortie", {}) or {}
            ws = wb.create_sheet(f"Atelier {numero}")
            if numero == 1:
                section(ws, "Périmètre")
                ws.append(["Périmètre", cell_val(sortie.get("perimetre"))])
                ws.append([])
                section(ws, "Biens essentiels")
                table(ws, ["Nom", "Description"],
                      [[b.get("name"), b.get("description")] for b in sortie.get("biens_essentiels", [])])
                ws.append([])
                section(ws, "Biens supports")
                table(ws, ["Nom", "Description", "Supporte"],
                      [[b.get("name"), b.get("description"), b.get("supports")] for b in sortie.get("biens_supports", [])])
                ws.append([])
                section(ws, "Événements redoutés")
                table(ws, ["Bien essentiel", "Besoin", "Description", "Gravité"],
                      [[e.get("bien_essentiel"), e.get("besoin"), e.get("label"), e.get("gravite")]
                       for e in sortie.get("evenements_redoutes", [])],
                      colored={4: _GRAVITY})
                ws.append([])
                section(ws, "Socle de sécurité")
                table(ws, ["Mesure", "Référentiel", "Écart"],
                      [[m.get("mesure"), m.get("referentiel"), m.get("ecart")]
                       for m in sortie.get("socle_securite", [])])
            elif numero == 2:
                section(ws, "Sources de risques (couples SR/objectif visé)")
                table(ws, ["Type", "Nom", "Objectif (OV)", "Motivation", "Activité", "Capacité", "Biens visés", "Pertinence"],
                      [[s.get("type"), s.get("name"), s.get("objectif"), s.get("motivation"),
                        s.get("activite"), s.get("capacite"), cell_val(s.get("biens_vises")), s.get("pertinence")]
                       for s in sortie.get("sources_risques", [])],
                      colored={6: _GRAVITY, 8: _PERTINENCE})
            elif numero == 3:
                pp = sortie.get("parties_prenantes", [])
                if pp:
                    section(ws, "Parties prenantes critiques")
                    table(ws, ["Nom", "Rôle", "Motif de criticité"],
                          [[p.get("name"), p.get("role"), p.get("motif_criticite")] for p in pp])
                    ws.append([])
                section(ws, "Scénarios stratégiques")
                table(ws, ["ID", "Source", "Événement redouté", "Bien", "Gravité", "Vraisemblance", "Niveau", "Sources"],
                      [[s.get("identifiant"), s.get("source_risque"), s.get("evenement_redoute"),
                        s.get("bien_essentiel"), s.get("gravite"), s.get("vraisemblance"),
                        s.get("niveau"), cell_val(s.get("sources"))]
                       for s in sortie.get("scenarios_strategiques", [])],
                      colored={5: _GRAVITY, 6: _LIKELIHOOD, 7: _LEVEL_FILL})
            elif numero == 4:
                section(ws, "Scénarios opérationnels")
                table(ws, ["ID", "Stratégique", "Source", "Événement", "Gravité", "Vraisemblance",
                           "Niveau", "Techniques", "Chemin d'attaque"],
                      [[s.get("identifiant"), s.get("scenario_strategique"), s.get("source_risque"),
                        s.get("evenement_redoute"), s.get("gravite"), s.get("vraisemblance"),
                        s.get("niveau"), cell_val(s.get("techniques_attaque")),
                        " -> ".join(s.get("chemin_attaque", []))]
                       for s in sortie.get("scenarios_operationnels", [])],
                      colored={5: _GRAVITY, 6: _LIKELIHOOD, 7: _LEVEL_FILL})
            elif numero == 5:
                section(ws, "Plan de traitement")
                ws.append(["Synthèse", cell_val(sortie.get("plan_traitement"))])
                ws.append([])
                section(ws, "Registre des risques")
                table(ws, ["ID", "Opérationnel", "Bien", "Événement", "Gravité", "Vraisemblance",
                           "Niveau", "Traitement", "Mesures", "Résiduel", "Sources"],
                      [[r.get("identifiant"), r.get("scenario_operationnel"), r.get("bien_essentiel"),
                        r.get("evenement_redoute"), r.get("gravite"), r.get("vraisemblance"),
                        r.get("niveau"), r.get("traitement"), cell_val(r.get("mesures")),
                        r.get("risque_residuel"), cell_val(r.get("sources"))]
                       for r in sortie.get("risques", [])],
                      colored={5: _GRAVITY, 6: _LIKELIHOOD, 7: _LEVEL_FILL, 10: _LEVEL_FILL})
            finish(ws)

    atelier_sheets()

    # ---- 3) Plan de traitement ----
    ws2 = wb.create_sheet("Plan de traitement")
    risks = data.get("registre_des_risques", [])
    table(ws2, ["ID", "Bien", "Événement redouté", "Source", "Gravité", "Vraisemblance", "Niveau",
                "Traitement", "Mesures", "Résiduel", "Justification"],
          [[r.get("identifiant"), "", cell_val(r.get("justification")), "", r.get("gravite"),
            r.get("vraisemblance"), r.get("niveau"), r.get("traitement"),
            "; ".join(r.get("mesures", [])), r.get("risque_residuel"), cell_val(r.get("sources"))]
           for r in risks],
          colored={5: _GRAVITY, 6: _LIKELIHOOD, 7: _LEVEL_FILL, 10: _LEVEL_FILL})
    finish(ws2, overrides={
        "A": 10, "B": 24, "C": 40, "D": 16, "E": 10, "F": 14,
        "G": 10, "H": 14, "I": 70, "J": 12, "K": 44,
    })
    ws2.freeze_panes = "A2"

    # ---- 4) Synthèse (en dernier) ----
    ws = wb.create_sheet("Synthèse")
    ws.append(["Compte rendu EBIOS RM — Synthèse"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([])
    for label, value in [("Étude", a.get("nom")), ("Statut", a.get("statut")), ("Atelier courant", a.get("atelier_courant"))]:
        ws.append([label, value])
    ws.append([])

    section(ws, "Métriques")
    ws.append(["Biens", len(data.get("biens", []))])
    ws.append(["Événements redoutés", len(data.get("evenements_redoutes", []))])
    ws.append(["Sources de risques", len(data.get("sources_de_risques", []))])
    ws.append(["Scénarios stratégiques", len([s for s in data.get("scenarios", []) if s.get("kind") == "strategique"])])
    ws.append(["Scénarios opérationnels", len([s for s in data.get("scenarios", []) if s.get("kind") == "operationnel"])])
    ws.append(["Risques", len(risks)])
    ws.append([])

    section(ws, "Matrice des risques d'origine (gravité x vraisemblance)")
    counts = {g: {f"v{j}": 0 for j in range(1, 5)} for g in ("g1", "g2", "g3", "g4")}
    for r in risks:
        g = r.get("gravite") or "g1"
        v = r.get("vraisemblance") or "v1"
        counts.setdefault(g, {})
        counts[g][v] = counts[g].get(v, 0) + 1
    table(ws, ["", "V1", "V2", "V3", "V4"], [[g.upper()] + [counts[g][f"v{i}"] for i in range(1, 5)] for g in ("g1", "g2", "g3", "g4")])
    ws.append([])

    section(ws, "Comparaison origine <- résiduel (par niveau)")
    levels = ["faible", "moyen", "eleve", "critique"]
    orig = {lv: 0 for lv in levels}
    resid = {lv: 0 for lv in levels}
    for r in risks:
        orig[r.get("niveau", "eleve")] = orig.get(r.get("niveau", "eleve"), 0) + 1
        resid[r.get("risque_residuel", "eleve")] = resid.get(r.get("risque_residuel", "eleve"), 0) + 1
    table(ws, ["Niveau", "Risques d'origine", "Risques résiduels"], [[lv, orig[lv], resid[lv]] for lv in levels],
          colored={1: _LEVEL_FILL})
    ws.append([])

    section(ws, "Risques retenus")
    table(ws, ["ID", "Événement redouté", "Niveau", "Traitement", "Résiduel"],
          [[r.get("identifiant"), cell_val(r.get("justification") or r.get("sources", "")),
            r.get("niveau"), r.get("traitement"), r.get("risque_residuel")] for r in risks],
          colored={3: _LEVEL_FILL, 5: _LEVEL_FILL})
    finish(ws, overrides={"A": 22, "B": 90})

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
