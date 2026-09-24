"""Validation croisée entre ateliers : garde-fou contre l'hallucination.

Chaque atelier est vérifié vis-à-vis des sorties des ateliers précédents afin de
rejeter les références fantômes (biens, sources, événements, scénarios, techniques
ATT&CK). Les références invalides sont soit alignées sur l'existant (correspondance
floue) soit retirées, et les corrections sont tracées dans `_validation`.
"""

import unicodedata
from collections.abc import Mapping
from typing import Any

from app.tools.attack_techniques import TECHNIQUES


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return value.strip().lower()


def best_match(value: str, candidates: list[str]) -> str | None:
    """Retourne le meilleur candidat pour `value` (exact puis flou), sinon None."""
    target = _norm(value)
    if not target:
        return None
    for c in candidates:
        if _norm(c) == target and c:
            return c
    for c in candidates:
        nc = _norm(c)
        if nc and min(len(nc), len(target)) >= 3 and (nc in target or target in nc):
            return c
    return None


def sanitize_workshop_2(output: dict[str, Any], state: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Atelier 2 : les biens visés doivent exister à l'Atelier 1."""
    cadrage = state.get("workshop_outputs", {}).get(1, {})
    biens = [b.get("name", "") for b in cadrage.get("biens_essentiels", [])]
    issues: list[str] = []
    for src in output.get("sources_risques", []):
        cleaned: list[str] = []
        for b in src.get("biens_vises", []):
            match = best_match(b, biens)
            if match is None:
                issues.append(
                    f"Source « {src.get('name', '?')} » cible un bien non inventorié « {b} » (retiré)."
                )
                continue
            if match != b:
                issues.append(f"Bien « {b} » aligné sur « {match} ».")
            if match not in cleaned:
                cleaned.append(match)
        src["biens_vises"] = cleaned
    return output, issues


def sanitize_workshop_3(output: dict[str, Any], state: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Atelier 3 : sources et événements référencés doivent exister (Ateliers 2 et 1)."""
    cadrage = state.get("workshop_outputs", {}).get(1, {})
    sources_2 = state.get("workshop_outputs", {}).get(2, {})
    events = cadrage.get("evenements_redoutes", [])
    event_labels = [e.get("label", "") for e in events]
    event_bien = {_norm(e.get("label", "")): e.get("bien_essentiel", "") for e in events}
    source_names = [
        s.get("name") or s.get("type", "")
        for s in sources_2.get("sources_risques", [])
    ]
    biens = [b.get("name", "") for b in cadrage.get("biens_essentiels", [])]
    issues: list[str] = []
    kept: list[dict] = []
    for sc in output.get("scenarios_strategiques", []):
        event = best_match(sc.get("evenement_redoute", ""), event_labels)
        source = best_match(sc.get("source_risque", ""), source_names)
        if event is None:
            issues.append(
                f"Scénario {sc.get('identifiant')} référence un événement redouté inexistant (retiré)."
            )
            continue
        if source is None:
            issues.append(
                f"Scénario {sc.get('identifiant')} référence une source de risques inexistante (retiré)."
            )
            continue
        sc["evenement_redoute"] = event
        sc["source_risque"] = source
        if not sc.get("bien_essentiel") or best_match(sc["bien_essentiel"], biens) is None:
            fallback = event_bien.get(_norm(event), sc.get("bien_essentiel", ""))
            sc["bien_essentiel"] = fallback
            if fallback:
                issues.append(
                    f"Scénario {sc.get('identifiant')} : bien essentiel fixé à « {fallback} »."
                )
        kept.append(sc)
    output["scenarios_strategiques"] = kept
    return output, issues


def sanitize_workshop_4(output: dict[str, Any], state: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Atelier 4 : techniques ATT&CK dans le catalogue + référence à un S-XX existant."""
    allowed = {t.id.upper() for t in TECHNIQUES}
    strategiques = state.get("workshop_outputs", {}).get(3, {})
    s_ids = [s.get("identifiant", "") for s in strategiques.get("scenarios_strategiques", [])]
    issues: list[str] = []
    for op in output.get("scenarios_operationnels", []):
        techs: list[str] = []
        for t in op.get("techniques_attaque", []):
            t2 = str(t).strip().upper()
            if t2 in allowed:
                if t2 not in techs:
                    techs.append(t2)
            else:
                issues.append(
                    f"Scénario {op.get('identifiant')} : technique ATT&CK inconnue « {t} » (retirée)."
                )
        op["techniques_attaque"] = techs
        ref = best_match(op.get("scenario_strategique", ""), s_ids)
        if ref is None:
            issues.append(
                f"Scénario {op.get('identifiant')} référence un scénario stratégique inexistant."
            )
        else:
            op["scenario_strategique"] = ref
    return output, issues


def sanitize_workshop_5(output: dict[str, Any], state: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Atelier 5 : chaque risque référence un scénario opérationnel existant."""
    operationnels = state.get("workshop_outputs", {}).get(4, {})
    o_ids = [s.get("identifiant", "") for s in operationnels.get("scenarios_operationnels", [])]
    issues: list[str] = []
    for r in output.get("risques", []):
        ref = best_match(r.get("scenario_operationnel", ""), o_ids)
        if ref is None:
            issues.append(
                f"Risque {r.get('identifiant')} référence un scénario opérationnel inexistant."
            )
        else:
            r["scenario_operationnel"] = ref
    return output, issues


def attach_validation(cleaned: dict[str, Any], issues: list[str]) -> dict[str, Any]:
    """Ajoute les corrections croisées dans la sortie (transparence pour l'analyste)."""
    if issues:
        cleaned["_validation"] = {"issues": issues}
    return cleaned
