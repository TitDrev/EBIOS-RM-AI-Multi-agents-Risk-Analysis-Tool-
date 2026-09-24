"""Audit de sécurité automatisé (Sprint 7).

Vérifie la configuration et le code pour des failles courantes :
clé secrète, secrets commités, accès non protégés, docker-compose,
présence des garde-fous (injection, cross-validation), etc.

Usage :
    .venv/bin/python scripts/security_audit.py
Sortie : rapport + code de sortie 0 (OK) ou 1 (problèmes).
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"

sys.path.insert(0, str(BACKEND))

WEAK_KEYS = {"change-me", "change-me-en-production", "dev-secret-key-not-for-production", ""}
SECRET_PATTERNS = [
    re.compile(r"oc_sk_[A-Za-z0-9]{10,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-(ant|proj)-[A-Za-z0-9_-]{10,}"),
]
IGNORED_DIRS = {".venv", "node_modules", ".git", "__pycache__"}


def _tracked_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout
        return [f for f in out.decode("utf-8", "ignore").split("\0") if f]
    except Exception:
        tracked = []
        for folder in ("backend", "frontend", ".github"):
            for path in (ROOT / folder).rglob("*"):
                if path.is_file() and not any(part in IGNORED_DIRS for part in path.parts):
                    tracked.append(str(path.relative_to(ROOT)))
        return tracked


def check_secret_key(fail: list[str], pass_: list[str]) -> None:
    try:
        from app.config import Settings

        cfg = Settings()
    except Exception as exc:
        fail.append(f"Impossible de charger la configuration : {exc}")
        return
    if not cfg.DEBUG and cfg.SECRET_KEY in WEAK_KEYS:
        fail.append("SECRET_KEY faible alors que DEBUG=false (démarrage refusé).")
    elif cfg.SECRET_KEY in WEAK_KEYS:
        pass_.append("SECRET_KEY faible mais DEBUG=true (mode dev accepté).")
    else:
        pass_.append("SECRET_KEY définie et robuste.")


def check_tracked_secrets(fail: list[str], pass_: list[str]) -> None:
    hits: list[str] = []
    for path in _tracked_files():
        if path.endswith(".env") or "/.venv/" in path:
            continue
        try:
            full = ROOT / path
            content = full.read_text(errors="ignore")
        except Exception:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                hits.append(f"{path} contient un secret plausible ({pattern.pattern[:12]}…).")
                break
    if hits:
        fail.extend(hits[:10])
    else:
        pass_.append("Aucun secret suivi (oc_sk_ / ghp_ / sk-ant-…).")


def check_gardes_fous(fail: list[str], pass_: list[str]) -> None:
    required = [
        BACKEND / "app/agents/cross_validation.py",
        BACKEND / "app/core/prompt_guard.py",
        BACKEND / "tests/unit/test_injection.py",
        BACKEND / "tests/unit/test_cross_validation.py",
        BACKEND / "app/api/ws.py",
    ]
    missing = [str(p.relative_to(BACKEND)) for p in required if not p.exists()]
    if missing:
        fail.append(f"Garde-fous manquants : {missing}")
    else:
        pass_.append("Garde-fous présents : validation croisée, anti-injection, WebSocket + tests.")


def check_docker(fail: list[str], pass_: list[str]) -> None:
    compose = (ROOT / "docker-compose.yml").read_text()
    if "https://opencode.ai/inference/openai/v1/chat/completions" not in compose:
        fail.append("docker-compose.yml : endpoint LLM non configuré.")
    else:
        pass_.append("docker-compose.yml : services et endpoint LLM cohérents.")


def check_auth_endpoints(fail: list[str], pass_: list[str]) -> None:
    routers = {
        "analyses.py": "get_owned_analysis",
        "workshops.py": "get_owned_analysis",
        "resources.py": "get_owned_analysis",
        "reports.py": "get_owned_analysis",
    }
    missing = [name for name, token in routers.items()
               if token not in (BACKEND / f"app/api/{name}").read_text()]
    if missing:
        fail.append(f"Contrôle d'accès par propriétaire absent dans : {missing}")
    else:
        pass_.append("Contrôle d'accès par propriétaire/admin sur analyses, ateliers, ressources, rapports.")


def main() -> int:
    fail: list[str] = []
    ok: list[str] = []
    check_secret_key(fail, ok)
    check_tracked_secrets(fail, ok)
    check_gardes_fous(fail, ok)
    check_docker(fail, ok)
    check_auth_endpoints(fail, ok)

    print("=== AUDIT DE SÉCURITÉ — EBIOS-RM-AI ===\n")
    for item in ok:
        print(f"  [OK]   {item}")
    if fail:
        print("\nPROBLÈMES :")
        for item in fail:
            print(f"  [!!]  {item}")
        print("\nRésultat : ÉCHEC")
        return 1
    print("\nRésultat : OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
