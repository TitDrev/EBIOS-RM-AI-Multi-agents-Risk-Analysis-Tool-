# Documentation du projet — index

Analyse de risques **EBIOS RM** pilotée par agents IA (FastAPI + LangGraph + PostgreSQL).

## Par catégorie

| Doc | Contenu | Lien |
|-----|---------|------|
| **1. Démarche & alignement ANSSI** | Méthode EBIOS RM (5 ateliers), échelles G1-G4/V1-V4, référentiels ISO 27005 / 27002 / guides ANSSI, justification du modèle | [01_demarche_ANSSI.md](01_demarche_ANSSI.md) |
| **2. Sécurité applicative** | Mesures par catégorie (auth, contrôle d'accès, données, durcissement, journalisation) **avec preuves** | [02_securite_applicative.md](02_securite_applicative.md) |
| **3. Garde-fous IA** | Risques propres aux LLM (OWASP LLM Top 10) et mesure de parade **avec preuves** | [03_garde_fous_IA.md](03_garde_fous_IA.md) |
| **4. Traçabilité** | Prompts versionnés, tokens, empreinte d'entrée, traces FAILED | [04_tracabilite.md](04_tracabilite.md) |
| **5. Conformité au sujet (E21)** | Matrice : chaque critère / item de la checklist du sujet → statut + preuve | [05_conformite_E21.md](05_conformite_E21.md) |
| **6. Installation & déploiement** | Local, Docker Compose, production | [06_installation_deploiement.md](06_installation_deploiement.md) |
| **Architecture technique** | Vue d'ensemble, modèle de données, API (doc de référence) | [DOCUMENTATION_TECHNIQUE.md](DOCUMENTATION_TECHNIQUE.md) |

## Preuves transversales (à citer en soutenance)

- **Tests** : `pytest` (47 tests) — couvre flux complet, cas A/B/C, injection de prompt, validation croisée, reprise ciblée, WebSocket, comparaison, validation par risque.
- **Audit de sécurité automatisé** : `python backend/scripts/security_audit.py` → OK (clé secrète, secrets commités, contrôle d'accès, docker, garde-fous).
- **Lint / typage** : `ruff check app tests scripts` · `mypy app scripts` — 0 erreur.