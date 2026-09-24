# 6. Installation & déploiement

## Prérequis

- Python 3.11+, PostgreSQL (17/18) avec l'extension `vector`, Node 20 (frontend).
- Clé d'API Opencode Go (ou `LLM_PROVIDER=mock` pour tourner sans appel réseau).

## Environnement local (backend)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Base de données : créer `risk_agents` et activer l'extension
createuser -s admin && createdb -O admin risk_agents
psql -d risk_agents -c "CREATE EXTENSION IF NOT EXISTS vector;"

cp .env.example .env     # renseigner LLM_ENDPOINT_URL / LLM_API_KEY / LLM_MODEL
alembic upgrade head      # appliquer les migrations

uvicorn app.main:app --reload   # API sur :8000, docs OpenAPI sur /docs
```

Un **smoke-test** LLM : `python scripts/smoke_llm.py` (vérifie l'endpoint Opencode Go).

## Docker Compose (développement)

```bash
cp backend/.env.example .env   # à la racine, utilisé pour LLM/SECRET_KEY
docker compose up --build
# backend : http://localhost:8000  · frontend : http://localhost:3000
```

Le démarrage du backend exécute `alembic upgrade head` avant de lancer `uvicorn`.
`DEBUG=true` par défaut en dev ; définir `SECRET_KEY` et `DEBUG=false` pour la production.

## Production

Copier `backend/.env.production.example` vers `.env` puis **forger chaque secret** :

```env
DEBUG=false
SECRET_KEY=<clé forte aléatoire>        # sinon refus au démarrage
DATABASE_URL=postgresql+asyncpg://...:5432/risk_agents
LLM_API_KEY=<clé Opencode Go>
CORS_ORIGINS=https://<domaine.frontend>
```

Recommandations :
- backend derrière un reverse proxy TLS (Nginx, fourni pour le front),
- plusieurs workers `uvicorn` pour l'API,
- SSH/TLS sur la base PostgreSQL,
- rotation des clés, sauvegardes de la base.

## Matrice de déploiement

| Composant | Dev (Docker Compose) | Prod (recommandé) |
|-----------|----------------------|-------------------|
| PostgreSQL + pgvector | service `postgres` | hébergé managé ou VM dédiée (TLS) |
| Redis | service `redis` | managé ou dédié |
| API FastAPI | service `backend` (1 worker) | multi-workers uvicorn + reverse proxy |
| Worker Celery | service `worker` (prêt) | SSH/TLS + redémarrage auto |
| Frontend | service `frontend` (Nginx) | statique servi par CDN/Nginx, HTTPS |