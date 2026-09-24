"""Point d'entrée FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyses import router as analyses_router
from app.api.auth import router as auth_router
from app.api.comparison import router as comparison_router
from app.api.reports import router as reports_router
from app.api.resources import router as resources_router
from app.api.workshops import router as workshops_router
from app.api.ws import router as ws_router
from app.config import settings

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(analyses_router, prefix="/api")
app.include_router(comparison_router, prefix="/api")
app.include_router(workshops_router, prefix="/api")
app.include_router(resources_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(ws_router)


@app.get("/", tags=["health"])
async def root() -> dict:
    return {"app": settings.APP_NAME, "status": "ok"}


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "healthy", "llm_provider": settings.LLM_PROVIDER, "model": settings.LLM_MODEL}
