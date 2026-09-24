"""Catalogue MITRE ATT&CK (sous-ensemble) et recherche de techniques.

Sous-ensemble curaté des techniques les plus courantes pour les systèmes
d'information web et d'entreprise. Sert d'outil de référence pour l'Atelier 4
(chemins d'attaque), afin que l'agent cite de vrais identifiants ATT&CK.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AttackTechnique:
    id: str
    name: str
    tactic: str


TECHNIQUES: list[AttackTechnique] = [
    # Initial Access
    AttackTechnique("T1190", "Exploit Public-Facing Application", "initial-access"),
    AttackTechnique("T1566", "Phishing", "initial-access"),
    AttackTechnique("T1078", "Valid Accounts", "initial-access"),
    AttackTechnique("T1133", "External Remote Services", "initial-access"),
    AttackTechnique("T1195", "Supply Chain Compromise", "initial-access"),
    # Execution
    AttackTechnique("T1059", "Command and Scripting Interpreter", "execution"),
    AttackTechnique("T1203", "Exploitation for Client Execution", "execution"),
    # Persistence
    AttackTechnique("T1505", "Server Software Component", "persistence"),
    AttackTechnique("T1136", "Create Account", "persistence"),
    # Privilege Escalation
    AttackTechnique("T1068", "Exploitation for Privilege Escalation", "privilege-escalation"),
    # Defense Evasion
    AttackTechnique("T1070", "Indicator Removal", "defense-evasion"),
    # Credential Access
    AttackTechnique("T1110", "Brute Force", "credential-access"),
    AttackTechnique("T1555", "Credentials from Password Stores", "credential-access"),
    AttackTechnique("T1552", "Unsecured Credentials", "credential-access"),
    AttackTechnique("T1567", "Exfiltration Over Web Service", "exfiltration"),
    # Discovery
    AttackTechnique("T1046", "Network Service Discovery", "discovery"),
    AttackTechnique("T1087", "Account Discovery", "discovery"),
    # Lateral Movement
    AttackTechnique("T1021", "Remote Services", "lateral-movement"),
    AttackTechnique("T1550", "Use Alternate Authentication Material", "lateral-movement"),
    # Collection
    AttackTechnique("T1119", "Automated Collection", "collection"),
    # Exfiltration
    AttackTechnique("T1041", "Exfiltration Over C2 Channel", "exfiltration"),
    AttackTechnique("T1048", "Exfiltration Over Alternative Protocol", "exfiltration"),
    # Impact
    AttackTechnique("T1486", "Data Encrypted for Impact", "impact"),
    AttackTechnique("T1499", "Endpoint Denial of Service", "impact"),
    AttackTechnique("T1490", "Inhibit System Recovery", "impact"),
    AttackTechnique("T1485", "Data Destruction", "impact"),
    AttackTechnique("T1531", "Account Access Removal", "impact"),
    AttackTechnique("T1491", "Defacement", "impact"),
]


def search_attack_techniques(query: str = "", tactic: str = "", limit: int = 30) -> list[dict]:
    """Recherche des techniques ATT&CK par mot-clé ou tactique."""
    q = query.lower()
    t = tactic.lower()
    results = []
    for tech in TECHNIQUES:
        if t and t not in tech.tactic:
            continue
        if q and q not in tech.id.lower() and q not in tech.name.lower() and q not in tech.tactic:
            continue
        results.append({"id": tech.id, "name": tech.name, "tactic": tech.tactic})
    return results[:limit]


def all_techniques() -> list[dict]:
    """Retourne l'ensemble du catalogue (pour l'injecter dans un prompt)."""
    return [{"id": t.id, "name": t.name, "tactic": t.tactic} for t in TECHNIQUES]
