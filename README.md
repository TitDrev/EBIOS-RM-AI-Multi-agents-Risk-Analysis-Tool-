# EBIOS RM — Analyse de risques par agents IA

Application web multi-agents pour l'analyse de risques des systèmes d'information selon la méthode **EBIOS Risk Manager** (ANSSI). L'utilisateur décrit un système d'information, et un pipeline d'agents IA déroule les **5 ateliers EBIOS RM** avec **validation humaine entre chaque atelier**, jusqu'au **compte rendu** final.

> Projet pédagogique (M2 Cybersécurité) — « Des agents IA pour analyser les risques ».
> L'IA assiste l'analyste : l'humain reste responsable de la décision finale.

---

## Fonctionnalités

- **5 ateliers EBIOS RM automatisés** :
  1. Cadrage et socle de sécurité (biens essentiels/supports, besoins DICP, événements redoutés, socle)
  2. Sources de risques (attaquants, internes, sinistres)
  3. Scénarios stratégiques (gravité × vraisemblance)
  4. Scénarios opérationnels (chemins d'attaque, MITRE ATT&CK)
  5. Traitement du risque (stratégies, mesures, risque résiduel → registre)
- **Validation humaine entre chaque atelier** (pipeline pas à pas, reprise ciblée)
- **Compte rendu final** : registre des risques argumenté + plan de traitement (JSON/CSV/PDF)
- **Multi-agents** : un agent par atelier, orchestrés par LangGraph, consignes versionnées
- **RAG** : base de connaissances (EBIOS RM, ISO 27005, ISO 27002, ANSSI)
- **Garde-fous IA** : sources obligatoires par risque, outils en lecture seule, filtrage des injections de prompt

---

## Architecture

```
Client Web (React + Tailwind)
        │
        ▼
FastAPI (API REST + WebSocket)
        │
        ▼
LangGraph (orchestrateur)
   ├─ Atelier 1 → [validation → Atelier 2 → [validation]
   ├─ → Atelier 3 → [validation] → Atelier 4 → [validation]
   └─ → Atelier 5 → [validation] → Compte rendu
        │
        ▼
PostgreSQL + pgvector        LLM (Opencode Go → deepseek-v4-pro)
```

### Stack

| Couche | Choix |
|--------|-------|
| Backend | Python 3.11+, FastAPI, LangGraph, SQLAlchemy 2.0 (async) |
| Base de données | PostgreSQL 16 + pgvector |
| Files d'attente | Celery + Redis |
| LLM | Couche d'abstraction `LLMProvider` (Opencode Go, mock pour tests) |
| Frontend | React 18 + TypeScript + Tailwind + Zustand |
| Conteneurisation | Docker Compose |
| CI | GitHub Actions (ruff, mypy, pytest) |

---

## Démarrage rapide

### Avec Docker Compose

```bash
cp backend/.env.example .env        # puis renseigner les variables LLM
docker compose up --build
# backend : http://localhost:8000 (docs : /docs)
# frontend : http://localhost:3000
```

### En développement (sans Docker)

Prérequis : PostgreSQL (17/18) avec extension `vector`, Redis (optionnel), Python 3.11+.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# créer la base et appliquer les migrations
createdb risk_agents   # (ou équivalent)
alembic upgrade head

# configuration LLM (Opencode Go)
cp .env.example .env
# renseigner LLM_ENDPOINT_URL, LLM_API_KEY, LLM_MODEL

uvicorn app.main:app --reload
```

Config du LLM (`.env`) :

```
LLM_PROVIDER=opencode_go
LLM_ENDPOINT_URL=https://opencode.ai/inference/openai/v1/chat/completions
LLM_API_KEY=...
LLM_MODEL=deepseek-v4-pro
```

> Le mode `LLM_PROVIDER=mock` permet de tourner sans appel réseau (réponses déterministes pour les tests).

---

## Structure du dépôt

```
backend/
├── app/
│   ├── agents/          # Orchestrateur LangGraph + ateliers + prompts
│   ├── api/             # Routeurs FastAPI (auth, analyses, workshops, ressources)
│   ├── core/            # Sécurité (JWT, rôles)
│   ├── llm/             # Abstraction LLMProvider (Opencode Go, mock)
│   ├── models/          # Modèles SQLAlchemy (EBIOS RM)
│   ├── schemas/         # Schémas Pydantic (contrats JSON des ateliers)
│   ├── services/        # Orchestration, RAG, compte rendu
│   ├── tools/           # risk_math, MITRE ATT&CK, CVE/NVD
│   └── tasks/           # Celery
├── alembic/             # Migrations
└── tests/               # Unitaires + intégration
frontend/                # React + Tailwind
docker-compose.yml
Cahier-des-charges-v2.md
sprint.md
```

---

## API principales

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/auth/register` | Inscription |
| POST | `/api/auth/login` | Connexion (JWT) |
| POST | `/api/analyses` | Créer une étude (description du SI) |
| POST | `/api/analyses/{id}/start` | Lancer le pipeline des 5 ateliers |
| GET | `/api/analyses/{id}/workshops` | Statut des ateliers |
| POST | `/api/analyses/{id}/workshops/{n}/validate` | **Validation humaine** d'un atelier |
| GET | `/api/analyses/{id}/assets` | Biens essentiels / supports |
| GET | `/api/analyses/{id}/risk-sources` | Sources de risques |
| GET | `/api/analyses/{id}/scenarios` | Scénarios stratégiques & opérationnels |
| GET | `/api/analyses/{id}/risks` | Registre des risques |
| POST | `/api/analyses/{id}/report?format=json\|csv\|pdf` | Compte rendu final |

---

## Sécurité et limites de l'IA

Risques propres aux LLM traités (référence : OWASP Top 10 for LLM Applications) :

| Risque | Mesure |
|--------|--------|
| Hallucination | Champ `sources` obligatoire, RAG sur documents officiels, validation humaine |
| Injection de prompt | Séparation consignes/données, filtrage des entrées |
| Fuite de données | Cas d'étude 100 % fictifs |
| Excès d'autonomie | Outils en lecture seule, aucun accès à un SI réel |
| Empoisonnement | Base de connaissances sourcée et contrôlée |
| Dépendance fournisseur | Couche `LLMProvider` remplaçable |

**Seules des descriptions de systèmes fictifs doivent être analysées** (projet pédagogique).

---

## Roadmap / statut des sprints

- [x] Sprint 1 — Fondations (backend, BDD, auth, LLMProvider, Docker, CI)
- [x] Sprint 2 — Orchestrateur LangGraph + Atelier 1 (cadrage) + API + validation
- [x] Sprint 3 — Ateliers 2 & 3 (sources de risques, scénarios stratégiques) + RAG
- [x] Sprint 4 — Atelier 4 (scénarios opérationnels, MITRE ATT&CK) + outils
- [x] Sprint 5 — Atelier 5 (traitement du risque) + registre + compte rendu (JSON/CSV/PDF)
- [ ] Sprint 6 — WebSocket de suivi en temps réel + reprises ciblées complètes
- [ ] Sprint 7 — Tests complets, cas de référence, documentation, audit, déploiement

---

## Tests

```bash
cd backend
pytest                      # unitaire + intégration
ruff check app tests        # lint
mypy app                    # typage
```

> Les tests utilisent un LLM mock (aucun appel réseau) et une base `risk_agents_test` (PostgreSQL + pgvector).