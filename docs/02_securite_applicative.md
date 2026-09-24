# 2. Sécurité applicative — mesures par catégorie (avec preuves)

Chaque mesure est accompagnée de sa **preuve** (fichier de code et/ou test).

## 2.1 Authentification & gestion des sessions

| Mesure | Implémentation | Preuve |
|--------|----------------|--------|
| Hash des mots de passe | bcrypt (jamais en clair) | `backend/app/core/security.py` (`hash_password`) |
| Jetons | JWT HS256, expiration 8 h | `security.py` (`create_access_token`), `config.py` (`ACCESS_TOKEN_EXPIRE_MINUTES`) |
| Connexion | `/api/auth/login` et `/api/auth/login/json` | `backend/app/api/auth.py` |
| Désinscription / rotation | session côté client (token) | `frontend/src/lib/api.ts` |

## 2.2 Contrôle d'accès (RBAC + horizontal + par objet)

| Mesure | Implémentation | Preuve |
|--------|----------------|--------|
| Rôles admin / analyst / viewer | dépendance `require_role` | `backend/app/core/deps.py` |
| Lecture limitée à ses études (hors admin) | `list_analyses` filtre par `created_by` | `backend/app/api/analyses.py` |
| Accès par **propriétaire ou admin** sur toutes les ressources | dépendance `get_owned_analysis` utilisée dans analyses, workshops, resources, reports, comparison | `deps.py` + `app/api/*.py` ; vérifié par `scripts/security_audit.py` |
| Pas d'auto-inscription en admin | `register` force `role != ADMIN` | `app/api/auth.py` |
| WebSocket authentifié + contrôlé | JWT en query + `user_can_access` | `app/api/ws.py` |

## 2.3 Protection des données & secrets

| Mesure | Implémentation | Preuve |
|--------|----------------|--------|
| Secrets hors git | `.env` ignoré (`.gitignore`) | `.gitignore` ; `scripts/security_audit.py` (aucun `oc_sk_`/`ghp_`) |
| Aucun secret réel dans le dépôt | scan automatisé | `backend/scripts/security_audit.py` → **OK** |
| Clé au démarrage | refus de démarrer si `SECRET_KEY` faible et `DEBUG=false` | `backend/app/config.py` (`_check_secret_key`) ; `.env.production.example` |
| CORS restreint | liste explicite `CORS_ORIGINS` | `backend/app/main.py` |

## 2.4 Durcissement applicatif

| Mesure | Implémentation | Preuve |
|--------|----------------|--------|
| Validation stricte des entrées | schémas Pydantic par atelier (`schemas/workshop.py`) | `backend/app/schemas/*.py` |
| Rôles effectifs sur écritures | `require_analyst` sur créer/démarrer/valider/corriger/relancer | `app/api/analyses.py`, `app/api/workshops.py`, `app/api/resources.py` |
| Pas d'exécution sur les systèmes réels | les agents ne font que des appels LLM + calculs (aucune action) | architecture (doc technique) |

## 2.5 Journalisation & audit

| Mesure | Implémentation | Preuve |
|--------|----------------|--------|
| Trace d'exécution de chaque atelier | table `agent_runs` (agent, prompt versionné, tokens, durée, hash, statut) | `backend/app/models/agent_run.py`, `app/services/analysis_service.py` |
| Validation humaine horodatée | `validated_by` / `validated_at` (ateliers ET risques) | `app/api/workshops.py`, `app/api/resources.py` (`validate_risk`) |
| Échec tracé | trace `FAILED` + statut étude `failed` en cas d'erreur | `app/services/analysis_service.py` |

## 2.6 Exécution / files d'attente

- Le pipeline est **pas à pas et persistant** (chaque atelier est une ligne `workshops`) : une
  interruption laisse l'étude reprise au bon endroit (pas de tout-perdre).
- Workers Celery disponibles (`app/tasks/celery_app.py`) ; exécution actuellement synchrone
  (documenté).

> **Vérification automatisée** : `python backend/scripts/security_audit.py` (contrôle clé,
> secrets, garde-fous, docker, contrôle d'accès) → **OK**.