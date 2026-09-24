"""Démo en ligne de commande : analyse de risques EBIOS RM d'un SI.

Usage :
    cd backend
    # Mode automatique (recommandé) :
    .venv/bin/python scripts/demo.py --si ../examples/si_boutique
    # Mode pas-à-pas (validation / correction humaines interactives) :
    .venv/bin/python scripts/demo.py --si ../examples/si_boutique --pas-a-pas

Contenu du dossier SI (livrables entrants) :
    description.json      ->  si_description (nom, ecosysteme, flux, contexte_metier, contraintes)
    documents/            ->  (optionnel) fichiers .md/.txt intégrés à la base de connaissances (RAG)

Sorties :
    <dossier_si>/rapport/  ->  compte_rendu.json, registre.csv
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.database import async_session_factory  # noqa: E402
from app.models.analysis import Analysis  # noqa: E402
from app.models.enums import AnalysisStatus  # noqa: E402
from app.models.knowledge import KnowledgeDocument  # noqa: E402
from app.models.risk import Risk  # noqa: E402
from app.models.workshop import Workshop  # noqa: E402
from app.services.analysis_service import (  # noqa: E402
    correct_workshop,
    retry_workshop,
    run_workshop,
    validate_workshop,
)
from app.services.rag_service import seed_knowledge  # noqa: E402

# --------------------------------------------------------------------------
# Affichage
# --------------------------------------------------------------------------

def _print_summary(numero: int, output: dict) -> None:
    print(f"  → sortie Atelier {numero} :")
    if numero == 1:
        biens = output.get("biens_essentiels", [])
        events = output.get("evenements_redoutes", [])
        mesures = output.get("socle_securite", [])
        print(f"    biens essentiels : {[b['name'] for b in biens]}")
        print(f"    événements redoutés : {len(events)} · mesures du socle : {len(mesures)}")
    elif numero == 2:
        for s in output.get("sources_risques", []):
            print(f"    - {s.get('type'):20s} · {s.get('name')} · cap={s.get('capacite')} · {s.get('pertinence')}")
    elif numero == 3:
        print(f"    parties prenantes : {len(output.get('parties_prenantes', []))}")
        for s in output.get("scenarios_strategiques", []):
            print(f"    - {s.get('identifiant')} · {s.get('evenement_redoute')} · G={s.get('gravite')}")
    elif numero == 4:
        for s in output.get("scenarios_operationnels", [])[:5]:
            print(f"    - {s.get('identifiant')} · {s.get('scenario_strategique')} · "
                  f"G={s.get('gravite')} V={s.get('vraisemblance')} N={s.get('niveau')} "
                  f"· techniques={s.get('techniques_attaque')}")
    elif numero == 5:
        risques = output.get("risques", [])
        repartition: dict[str, int] = {}
        for r in risques:
            repartition[r.get("niveau", "?")] = repartition.get(r.get("niveau", "?"), 0) + 1
        print(f"    risques : {len(risques)} · répartition : {repartition}")
        for r in risques[:3]:
            print(f"    - {r.get('identifiant')} · {r.get('traitement')} · résiduel={r.get('risque_residuel')}")


# --------------------------------------------------------------------------
# Logique
# --------------------------------------------------------------------------

async def _ingest_user_docs(session, si_folder: Path) -> int:
    docs_dir = si_folder / "documents"
    added = 0
    if docs_dir.is_dir():
        for f in sorted(docs_dir.rglob("*")):
            if f.suffix.lower() in (".md", ".txt"):
                title = f.stem
                exists = await session.scalar(
                    select(KnowledgeDocument).where(KnowledgeDocument.title == title)
                )
                if exists:
                    continue
                session.add(
                    KnowledgeDocument(title=title, source="user-document",
                                      content=f.read_text(errors="ignore"))
                )
                added += 1
    if added:
        await session.commit()
    return added


async def _write_report(session, analysis_id, out_dir: Path) -> None:
    from app.services.report_generator import build_report_data, to_csv, to_json

    data = await build_report_data(session, analysis_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "compte_rendu.json").write_text(to_json(data), encoding="utf-8")
    (out_dir / "registre.csv").write_text(to_csv(data["registre_des_risques"]), encoding="utf-8")
    print(f"\nCompte rendu écrit dans : {out_dir}")


async def _ask(numero: int) -> str:
    return input(f"[Atelier {numero}] Entrée=valider · 'c <texte>'=corriger · 'r'=relancer : ").strip()


async def main(args: argparse.Namespace) -> int:
    si_folder = Path(args.si).resolve()
    desc_file = si_folder / "description.json"
    if not desc_file.is_file():
        print(f"ERREUR : {desc_file} absent. Le dossier SI doit contenir description.json.")
        return 2

    si_description = json.loads(desc_file.read_text(encoding="utf-8"))
    name = si_description.get("nom") or si_folder.name
    print(f"\nÉtude : {name}\nCas fourni par : {si_folder}")

    async with async_session_factory() as session:
        await seed_knowledge(session)
        added = await _ingest_user_docs(session, si_folder)
        print(f"Base de connaissances prête ({added} document(s) utilisateur intégré(s)).")

        analysis = Analysis(name=name, si_description=si_description, status=AnalysisStatus.IN_PROGRESS)
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)

        print("\n▶ Lancement du pipeline EBIOS RM (5 ateliers)…\n")
        workshop: Workshop | None = await run_workshop(session, analysis, 1)

        for numero in range(1, 6):
            assert workshop is not None
            print(f"\n═══ Atelier {numero} ═══")
            _print_summary(numero, workshop.output)

            if not args.pas_a_pas:
                # Mode auto : validation puis enchaînement (validate_workshop renvoie l'atelier suivant).
                workshop = await validate_workshop(session, analysis, numero, "demo")
                continue

            # Mode interactif : validation / correction / relance
            action = await _ask(numero)
            while action:
                if action.lower().startswith("c"):
                    correction = action[1:].strip() or "Revoir la sortie de l'atelier"
                    workshop = await correct_workshop(session, analysis, numero, [correction], "demo")
                    print("  (relance avec corrections)")
                    _print_summary(numero, workshop.output)
                elif action.lower() == "r":
                    workshop = await retry_workshop(session, analysis, numero, "demo")
                    print("  (relance)")
                    _print_summary(numero, workshop.output)
                elif action.lower() == "q":
                    print("Démo interrompue.")
                    return 1
                else:
                    print("  Commande inconnue.")
                action = await _ask(numero)

            workshop = await validate_workshop(session, analysis, numero, "demo")

        # Synthèse du registre
        risks = (await session.scalars(select(Risk).where(Risk.analysis_id == analysis.id))).all()
        print("\n═══ REGISTRE DES RISQUES (synthèse) ═══")
        print(f"  {len(risks)} risque(s) au total · étude : {analysis.status}")
        print("  validez manuellement chaque risque via POST /risks/{id}/validate (UI : boutons).")

        await _write_report(session, analysis.id, si_folder / "rapport")
        print("\nTerminé. L'analyse peut aussi être consultée via l'API/UI (id :", analysis.id, ")")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse de risques EBIOS RM (démo CLI)")
    parser.add_argument("--si", required=True, help="Dossier contenant description.json (+ documents/ optionnel)")
    parser.add_argument("--pas-a-pas", action="store_true", help="Mode interactif (validation/corrections humaines)")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args)))
