# EBIOS RM — Analyse de risques par agents IA

Application web multi-agents pour l'analyse de risques des systèmes d'information selon la méthode **EBIOS Risk Manager** (ANSSI). L'utilisateur décrit un système d'information, et un pipeline d'agents IA déroule les **5 ateliers EBIOS RM** avec **validation humaine entre chaque atelier**, jusqu'au **compte rendu** final.

> Projet pédagogique (M2 Cybersécurité) — « Des agents IA pour analyser les risques ».
> L'IA assiste l'analyste : l'humain reste responsable de la décision finale.

---

## Fonctionnalités

- **5 ateliers EBIOS RM automatisés** :
  1. Cadrage et socle de sécurité (biens essentiels/supports, besoins DICP, événements redoutés, socle avec écarts relevés)
  2. Sources de risques (menaces intentionnelles, couples source de risque / objectif visé SR/OV)
  3. Scénarios stratégiques (parties prenantes critiques + scénarios **cotés en gravité G1→G4**)
  4. Scénarios opérationnels (chemins d'attaque, MITRE ATT&CK, **vraisemblance V1→V4 évaluée ici**)
  5. Traitement du risque (stratégies réduire/transférer/éviter/accepter, mesures, risque résiduel → **registre des risques**)
- **Échelles EBIOS RM** : gravité **G1→G4**, vraisemblance **V1→V4**, matrice 4×4 → niveau faible/moyen/élevé/critique calculé de façon **déterministe dans le code**
- **Validation humaine entre chaque atelier** : valider, **corriger** (reprise ciblée avec corrections) ou **relancer** un atelier
- **Suivi temps réel** via WebSocket (`/ws/analyses/{id}`) : événements atelier lancé / validé / étude terminée
- **Comparaison d'études** (`/api/analyses/compare`) : métriques et registres entre deux analyses
- **Compte rendu final** : registre des risques argumenté + plan de traitement (JSON/CSV/PDF)
- **Multi-agents** : un agent par atelier, orchestrés par LangGraph, consignes versionnées (v1.1)
- **RAG** : base de connaissances (EBIOS RM, ISO 27005, ISO 27002, ANSSI)
- **Garde-fous IA** :
  - **Validation croisée entre ateliers** (références fantômes rejetées/alignées, techniques ATT&CK hors catalogue filtrées)
  - Champ `sources` obligatoire sur les scénarios et les risques
  - Protection contre l'injection de prompt (données délimitées `[DONNÉES]…[/DONNÉES]` + détection de motifs + consigne de sécurité)
  - Outils en lecture seule, rôles et accès par propriétaire, `SECRET_KEY` refusée au démarrage si faible hors DEBUG

---

## Documentation (par catégorie)

| Catégorie | Doc |
|-----------|-----|
| Index + preuves | [`docs/README.md`](docs/README.md) |
| Démarche & alignement ANSSI (EBIOS RM, échelles, ISO) | [`docs/01_demarche_ANSSI.md`](docs/01_demarche_ANSSI.md) |
| Sécurité applicative (mesures + preuves) | [`docs/02_securite_applicative.md`](docs/02_securite_applicative.md) |
| Garde-fous IA (OWASP LLM Top 10 + preuves) | [`docs/03_garde_fous_IA.md`](docs/03_garde_fous_IA.md) |
| Traçabilité | [`docs/04_tracabilite.md`](docs/04_tracabilite.md) |
| Conformité au sujet E21 (matrice critères → preuves) | [`docs/05_conformite_E21.md`](docs/05_conformite_E21.md) |
| Installation & déploiement | [`docs/06_installation_deploiement.md`](docs/06_installation_deploiement.md) |
| Architecture technique (référence) | [`docs/DOCUMENTATION_TECHNIQUE.md`](docs/DOCUMENTATION_TECHNIQUE.md) |

**Audit de sécurité automatisé** : `python backend/scripts/security_audit.py` → retourne OK
(clé secrète, secrets commités, contrôle d'accès, docker, garde-fous).

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

## Installation & configuration

### Prérequis

| Outil | Version | Remarque |
|-------|---------|----------|
| Python | ≥ 3.11 | venv recommandée |
| PostgreSQL | 16 / 17 / 18 | avec l'extension **`vector`** (pgvector) |
| Node.js | ≥ 18 | avec `npm` (frontend uniquement) |
| Clé LLM | — | Opencode Go *(ou mode `mock` pour tester sans clé)* |

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

> Après activation, tu peux utiliser `python …` ou directement `.venv/bin/python …`.

### 2. Base de données

Créer la base puis activer l'extension :

```bash
createdb risk_agents
psql -d risk_agents -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Appliquer les migrations (schéma complet du projet) :

```bash
alembic upgrade head
```

### 3. Configuration (`backend/.env`)

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | URL de connexion PostgreSQL (pilote `asyncpg`) |
| `SECRET_KEY` | Clé de signature JWT (forte ; le démarrage est refusé si faible hors `DEBUG`) |
| `DEBUG` | `true` en dev, `false` en production |
| `LLM_PROVIDER` | `opencode_go` (LLM réel) ou `mock` (réponses déterministes, hors ligne) |
| `LLM_ENDPOINT_URL` | Endpoint Opencode Go (compatible OpenAI) |
| `LLM_API_KEY` | Clé d'API Opencode Go |
| `LLM_MODEL` | Modèle utilisé (ex. `deepseek-v4-pro`) |
| `CORS_ORIGINS` | Origines autorisées du frontend (séparées par des virgules) |

Exemple avec le LLM réel :

```
LLM_PROVIDER=opencode_go
LLM_ENDPOINT_URL=https://opencode.ai/inference/openai/v1/chat/completions
LLM_API_KEY=…                     # ta clé Opencode Go
LLM_MODEL=deepseek-v4-pro
```

> **Pas encore de clé ?** Mets `LLM_PROVIDER=mock` : l'analyse se déroule avec des sorties
> déterministes, idéal pour découvrir l'outil. Pour vérifier l'endpoint LLM :
> `python scripts/smoke_llm.py`.

### 4. Lancer le backend

```bash
uvicorn app.main:app --reload
# API      : http://localhost:8000
# OpenAPI  : http://localhost:8000/docs
```

### 5. Lancer le frontend (facultatif, recommandé)

```bash
cd frontend
npm install
npm run dev
# application : http://localhost:3000
```

### Alternative : Docker Compose (tout d'un coup)

```bash
cp backend/.env.example .env
docker compose up --build
# backend : http://localhost:8000  ·  frontend : http://localhost:3000
```

---

## Utilisation

### A. Version web (recommandée)

1. **Créer un compte** — `http://localhost:3000` → « Se connecter » → « Créer un compte »
   (choisir le rôle **Analyste** pour créer / valider / corriger).
2. **Créer une étude** (2 façons) :
   - **Importer un document** : un ou plusieurs fichiers **PDF / Markdown / JSON** suffisent —
     le texte est lu et devient l'entrée de l'analyse (et rejoint la base de connaissances).
   - **Saisie manuelle** : nom, écosystème, flux de données, contexte métier.
   *(Exemples prêts à importer : `examples/si_boutique/`, `examples/si_PME/`.)*
3. **Démarrer** — dans l'étude : « Démarrer l'analyse ». La **barre des 5 ateliers** suit
   l'avancée (couleur par statut, **progression en temps réel** pendant la génération).
4. **Valider** — chaque atelier affiche sa sortie (tableaux et badges colorés) ; clique
   « Valider cet atelier » pour enchaîner. *(Corriger / relancer : voir API ou CLI `--pas-a-pas`.)*
5. **Compte rendu** — étude terminée → boutons **JSON / CSV / PDF / Excel**. L'export **Excel**
   contient : entrées & contexte, un onglet par atelier, plan de traitement, et une synthèse
   finale (matrices des risques d'origine et résiduels).
6. **Comparer** — menu « Comparer » pour comparer deux études (métriques et écarts).

### B. Ligne de commande (CLI)

Une commande lance l'analyse complète à partir d'un dossier de livrables d'un SI :

```bash
cd backend
.venv/bin/python scripts/demo.py --si ../examples/si_boutique          # mode auto
.venv/bin/python scripts/demo.py --si ../examples/si_PME --pas-a-pas    # validation/corrections interactives
```

Dossier SI attendu :

```
ma-etude/
├── description.json      # si_description : nom, ecosysteme, flux, contexte_metier, contraintes
└── documents/            # (optionnel) fichiers .md/.txt intégrés à la base de connaissances
```

Sorties dans `ma-etude/rapport/` : `compte_rendu.json`, `registre.csv`. Avec une clé LLM
l'analyse est **réelle** ; en `LLM_PROVIDER=mock`, une analyse de démonstration plausible est
produite hors ligne.

### C. API secondairement

Toutes les actions web sont disponibles en REST (voir le tableau ci-dessous) et la reprise
ciblée (`/correct`, `/retry`) se pilote via l'API.


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
| POST | `/api/analyses/upload` | **Créer une étude depuis un fichier** (PDF / Markdown / JSON) |
| POST | `/api/analyses/{id}/start` | Lancer le pipeline des 5 ateliers |
| GET | `/api/analyses/{id}/workshops` | Statut des ateliers |
| POST | `/api/analyses/{id}/workshops/{n}/validate` | **Validation humaine** d'un atelier |
| POST | `/api/analyses/{id}/workshops/{n}/correct` | **Corriger** un atelier (reprise ciblée) |
| POST | `/api/analyses/{id}/workshops/{n}/retry` | **Relancer** un atelier |
| GET | `/api/analyses/{id}/assets` | Biens essentiels / supports |
| GET | `/api/analyses/{id}/risk-sources` | Sources de risques |
| GET | `/api/analyses/{id}/scenarios` | Scénarios stratégiques & opérationnels |
| GET | `/api/analyses/{id}/risks` | Registre des risques |
| POST | `/api/analyses/{id}/report?format=json\|csv\|pdf\|xlsx` | Compte rendu (JSON/CSV/PDF/**Excel**) |
| GET | `/ws/analyses/{id}` | WebSocket de suivi temps réel (token en query) |
| POST | `/api/analyses/compare` | Comparer deux études |

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

## Outils IA utilisés (dossier)

Transparence exigée par le cadre du projet (item 7 de la liste de contrôle) :

- **Moteur d'analyse des agents** : `deepseek-v4-pro` fourni par la plateforme **Opencode Go**,
  accédé via un endpoint compatible OpenAI. Choix justifié : bon compromis qualité/coût sur des
  tâches structurées (génération JSON, raisonnement sur des grilles), modèle remplaçable derrière
  la couche `LLMProvider`.
- **Assistance au développement** : le code a été rédigé avec l'aide d'un assistant de code IA
  (opencode), à partir du cahier des charges et du modèle de sprint fournis dans le dépôt.
- **Bibliothèques** : FastAPI, LangGraph, SQLAlchemy, Pydantic, pgvector, WeasyPrint (PDF).

> Note honnête sur le périmètre EBIOS RM : l'outil simplifie volontairement la méthode
> (échelles G1-G4/V1-V4, socle synthétisé). Les livrables « humains » du projet — dossier écrit,
> analyse manuelle de référence (pour comparer les agents), description des cas A/B/C et noms des
> membres de l'équipe — restent à produire par le groupe.

---

## Roadmap / statut des sprints

- [x] Sprint 1 — Fondations (backend, BDD, auth, LLMProvider, Docker, CI)
- [x] Sprint 2 — Orchestrateur LangGraph + Atelier 1 (cadrage) + API + validation
- [x] Sprint 3 — Ateliers 2 & 3 (sources de risques, scénarios stratégiques) + RAG
- [x] Sprint 4 — Atelier 4 (scénarios opérationnels, MITRE ATT&CK) + outils
- [x] Sprint 5 — Atelier 5 (traitement du risque) + registre + compte rendu (JSON/CSV/PDF)
- [x] Sprint 6 — WebSocket de suivi en temps réel + comparaison d'études
- [x] Sprint 7 — Cas de référence A/B/C, audit de sécurité, documentation technique et déploiement

> **Livrables humains restants** (à produire par le groupe) : dossier écrit, analyse manuelle de
> référence, identités des membres. Voir `docs/DOCUMENTATION_TECHNIQUE.md`.
> Les reprises ciblées (corriger/relancer un atelier) sont d'ores et déjà disponibles via
> `/workshops/{n}/correct` et `/workshops/{n}/retry`.

---

## Tests

```bash
cd backend
pytest                      # unitaire + intégration (49 tests)
ruff check app tests        # lint
mypy app                    # typage
```
> Les tests utilisent un LLM mock (aucun appel réseau) et une base `risk_agents_test` (PostgreSQL + pgvector). Ils couvrent aussi l'injection de prompt et la validation croisée entre ateliers.