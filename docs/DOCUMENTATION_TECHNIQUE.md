# Documentation technique

Analyse de risques EBIOS RM par agents IA — application web multi-agents.

---

## 1. Vue d'ensemble

L'application prend en entrée la **description d'un système d'information** (écosystème, flux, contexte métier). Un pipeline de **5 agents** (un par atelier EBIOS RM) produit un **registre des risques argumenté** et un **compte rendu**, avec :
- une **validation humaine entre chaque atelier** ;
- des **garde-fous anti-hallucination** (sources, validation croisée) ;
- une **traçabilité** complète (prompt versionné, tokens, empreinte d'entrée).

### Flux

```
Analyste → Décrit le SI (API) → start
   └─ Atelier 1 (cadrage) → [validation] → Atelier 2 (sources de risques)
      → [validation] → Atelier 3 (scénarios stratégiques)
      → [validation] → Atelier 4 (scénarios opérationnels)
      → [validation] → Atelier 5 (traitement) → [validation]
      → Compte rendu (JSON / CSV / PDF)
```

Chaque validation enchaîne automatiquement sur l'atelier suivant ; `/correct` et `/retry` permettent une **reprise ciblée**.

---

## 2. Architecture & stack

| Couche | Choix |
|--------|-------|
| API | **FastAPI** (asynchrone, OpenAPI auto) |
| Orchestration | **LangGraph** (graphe des 5 ateliers) piloté par le service d'orchestration (pas-à-pas, persisté) |
| LLM | `LLMProvider` (Opencode Go → `deepseek-v4-pro`, ou `mock` pour les tests) |
| BDD | **PostgreSQL 16 + pgvector** (embeddings réservés pour le RAG) |
| Queue | Celery + Redis (workers prévus, exécution actuellement synchrone) |
| Frontend | React 18 + TypeScript + Tailwind + Zustand |
| Déploiement | Docker Compose (dev) · Nginx (front) · GitHub Actions (CI) |

```
frontend (React)  →  FastAPI  →  service d'orchestration  →  agents (LangGraph)
                                     │  PostgreSQL (persistance)
                                     │  LLM Provider (Opencode Go)
                                     ▼
                               WebSocket /ws/analyses/{id}
```

---

## 3. Démarche EBIOS RM par atelier

Échelles : **gravité G1→G4**, **vraisemblance V1→V4**, niveau de risque calculé de façon
**déterministe** par la matrice 4×4 (`app/tools/risk_math.py`).

| Atelier | Produit | Méthodologie |
|---------|---------|--------------|
| 1 · Cadrage & socle | biens essentiels/supports, besoins DICP, événements redoutés, socle (avec écarts) | périmètre, échelles |
| 2 · Sources de risques | menaces **intentionnelles** (couples SR/objectif visé) | motivation, ressources, activité ; sinistres → socle |
| 3 · Scénarios stratégiques | **parties prenantes** critiques + scénarios **cotés en gravité seule** | gravité G1-G4 |
| 4 · Scénarios opérationnels | chemins d'attaque + MITRE ATT&CK, **vraisemblance V1-V4 évaluée ici** | affinage gravité |
| 5 · Traitement | stratégie (réduire/transférer/éviter/accepter), mesures, **risque résiduel**, plan | ISO 27002, ANSSI |

### Garde-fous anti-hallucination
- **Champ `sources`** obligatoire sur scénarios et risques ;
- **Validation croisée** (`app/agents/cross_validation.py`) : les références doivent exister aux
  ateliers précédents (biens, sources, événements, scénarios) ; les techniques ATT&CK sont
  **filtrées sur le catalogue** ; les anomalies sont tracées dans `_validation` ;
- **Injection de prompt** (`app/core/prompt_guard.py`) : les données sont délimitées
  `[DONNÉES]…[/DONNÉES]`, une détection de motifs signale les entrées suspectes, et les consignes
  système précisent que les données sont non exécutables ;
- **Reprise sur sortie invalide** : `run_json_workshop` renvoie l'erreur de validation au modèle
  (jusqu'à 3 tentatives) ;
- **Homoglyphes** : normalisés uniquement sur les **clés** du JSON (valeurs préservées).

---

## 4. Modèle de données (PostgreSQL)

| Table | Rôle |
|-------|------|
| `analyses` | une étude (description du SI, statut, atelier courant, propriétaire) |
| `assets` | biens essentiels / supports |
| `feared_events` | événements redoutés (besoin DICP, gravité) |
| `risk_sources` | sources de risques (SR/OV, activité, capacité) |
| `scenarios` | scénarios **stratégiques** (gravité) et **opérationnels** (gravité+vraisemblance, chemin, techniques) |
| `risks` | registre des risques (traitement, mesures, risque résiduel, sources) |
| `workshops` | état de chaque atelier (sortie JSON, statut, corrections, validateur) |
| `agent_runs` | trace d'exécution (prompt versionné, tokens, durée, hash d'entrée, statut) |
| `knowledge_documents` | base RAG |
| `users` | utilisateurs (rôles admin / analyst / viewer) |

Les colonnes d'échelle (`gravite`, `vraisemblance`) stockent `g1`…`g4` / `v1`…`v4` (chaînes).

---

## 5. Sécurité

- **Mots de passe** : bcrypt ; **tokens** : JWT (HS256), expiration 8 h.
- **Contrôle d'accès horizontal** : chaque route vérifie que l'utilisateur est **propriétaire de
  l'étude ou admin** (`get_owned_analysis`) — listes filtrées pour les non-admin.
- **Rôles** : `admin` (tout), `analyst` (crée/valide/corrige), `viewer` (lecture de ses études) ;
  l'auto-inscription ne permet **pas** de devenir admin.
- **Clé secrète** : le démarrage est **refusé** si `SECRET_KEY` est faible hors `DEBUG=true`.
- **Secrets** : `.env` ignoré de git ; aucun secret suivi (vérifié par l'audit).

---

## 6. API

Principaux endpoints (préfixe `/api`) :

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/auth/register` · `/auth/login` | inscription · connexion (JWT) |
| POST | `/analyses` | créer une étude |
| POST | `/analyses/{id}/start` | lancer le pipeline |
| GET | `/analyses/{id}/workshops` | statut des ateliers |
| POST | `/analyses/{id}/workshops/{n}/validate` | valider la sortie d'un atelier (enchaîne) |
| POST | `/analyses/{id}/workshops/{n}/correct` | corriger (reprise ciblée) |
| POST | `/analyses/{id}/workshops/{n}/retry` | relancer |
| GET | `/analyses/{id}/risks` | registre des risques |
| POST | `/analyses/{id}/report?format=json\|csv\|pdf` | compte rendu |
| POST | `/analyses/compare` | comparer deux études |
| GET (WS) | `/ws/analyses/{id}?token=…` | suivi temps réel |

---

## 7. Installation & déploiement

### Environnement local
Prérequis : Python 3.11+, PostgreSQL (17/18) avec extension `vector`, Node 20.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# base : créer 'risk_agents' et activer l'extension vector
alembic upgrade head
cp .env.example .env   # renseigner LLM_ENDPOINT_URL / LLM_API_KEY / LLM_MODEL
uvicorn app.main:app --reload
```

### Docker Compose (dev)
```bash
cp backend/.env.example .env
docker compose up --build
# backend http://localhost:8000 (/docs) · frontend http://localhost:3000
```

### Production (`backend/.env.production.example`)
Définir et **forger** : `DEBUG=false`, `SECRET_KEY` forte, `DATABASE_URL`,
`LLM_API_KEY`. Le backend refuse de démarrer si la clé est faible. Le frontend est servi par
Nginx (multi-stage Dockerfile), le backend par de multiples workers `uvicorn` derrière un reverse
proxy, et `alembic upgrade head` est exécuté au démarrage.

---

## 8. Tests & audit

```bash
cd backend
pytest            # 44 tests : unitaire + intégration + cas A/B/C
ruff check app tests
mypy app
python scripts/security_audit.py   # audit de sécurité automatisé
```

Les tests utilisent un **LLM mock** déterministe (aucun appel réseau) et une base
`risk_agents_test`. Ils couvrent : le flux complet, la validation croisée (anti-hallucination),
l'injection de prompt, la reprise ciblée (`/correct`), le WebSocket et la comparaison.

---

## 9. Outils IA utilisés & limites

- **Moteur des agents** : `deepseek-v4-pro` (Opencode Go), remplaçable via `LLMProvider`.
- **Assistance au code** : assistant IA (opencode) à partir du cahier des charges et du modèle de
  sprint du dépôt.

Simplifications assumées : échelles G1-G4/V1-V4, socle synthétisé, exécution synchrone des
ateliers (Celery disponible mais non câblé). Doctrine : **écriture du dossier, analyse manuelle
de référence, description détaillée des cas A/B/C et identités de l'équipe** restent à produire
par le groupe (livrables humains du projet).