"""Protection contre l'injection de prompt via les données utilisateur.

Détection de motifs d'injection classiques dans les entrées utilisateur. La
défense principale reste structurelle : les données sont délimitées par des
balises dans le prompt, et la consigne « système » précise que tout contenu
entre ces balises est une donnée non exécutable.
"""

import re

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ignore_instructions", re.compile(r"ignore\s+(les\s+)?(instructions|consignes|regles|rules|previous)", re.I)),
    ("ignore_system", re.compile(r"ignore\s+(the\s+|toutes\s+|)?(system|consigne\s+systeme)\s*prompt", re.I)),
    ("nouvelle_consigne", re.compile(r"(nouvelle|nouveau|new)\s+(consigne|instruction|regle|rule|role)", re.I)),
    ("tu_es_maintenant", re.compile(r"tu\s+es\s*maintenant|you\s+are\s+now", re.I)),
    ("reveal_prompt", re.compile(r"revele|révèle|reveal\s.*(prompt|consigne)|affiche\s+ton\s+prompt", re.I)),
    ("bypass_regles", re.compile(r"(sans\s+suivre|outrepasser|bypass|ignore\s+the\s+rules)", re.I)),
    ("delimiteur_trompeur", re.compile(r"\[DONNÉES\]|\[SYSTEM\]|</system>|<\|endoftext\|>", re.I)),
]


def detect_injection(text: str) -> list[str]:
    """Retourne la liste des motifs d'injection détectés dans `text` (vide si aucun)."""
    found: list[str] = []
    for name, pattern in _PATTERNS:
        if pattern.search(text):
            found.append(name)
    return found


def has_injection(text: str) -> bool:
    """Vrai si au moins un motif d'injection est détecté."""
    return bool(detect_injection(text))
