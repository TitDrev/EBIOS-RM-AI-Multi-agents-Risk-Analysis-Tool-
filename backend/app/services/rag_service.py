"""Base de connaissances (RAG) : ingestion et recherche par mots-clés.

En l'absence d'endpoint d'embeddings côté Opencode Go, la recherche repose sur
une similarité lexicale (recouvrement de tokens). La colonne `embedding`
(pgvector) est prête pour brancher ultérieurement un modèle d'embedding.
"""

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeDocument

SEED_DOCUMENTS: list[dict] = [
    {
        "title": "EBIOS RM — Typologie des sources de risques",
        "source": "anssi-ebios-rm",
        "content": (
            "EBIOS Risk Manager classe les sources de risques en plusieurs familles : "
            "les attaquants (externes ou internes, malveillants), les personnes internes "
            "négligentes ou maladroites, et les sinistres (naturels : incendie, inondation ; "
            "ou d'origine accidentelle : panne, erreur). Chaque source est caractérisée par "
            "son objectif, sa motivation, son niveau de capacité et les biens qu'elle vise."
        ),
    },
    {
        "title": "EBIOS RM — Scénarios stratégiques et appréciation du risque",
        "source": "anssi-ebios-rm",
        "content": (
            "Un scénario stratégique croise une source de risques avec un événement redouté. "
            "Il est évalué selon deux axes : la gravité (importance de l'impact) et la "
            "vraisemblance (possibilité de réalisation). La matrice gravité × vraisemblance "
            "donne un niveau de risque : faible, moyen, élevé ou critique."
        ),
    },
    {
        "title": "ISO/IEC 27005 — Appréciation du risque",
        "source": "iso-27005",
        "content": (
            "La norme ISO/IEC 27005 décrit la démarche d'appréciation du risque : identification "
            "des actifs et des menaces, évaluation des conséquences et de la vraisemblance, puis "
            "détermination du niveau de risque pour prioriser le traitement."
        ),
    },
    {
        "title": "ISO/IEC 27002 — Exemples de mesures de sécurité",
        "source": "iso-27002",
        "content": (
            "ISO/IEC 27002 fournit des mesures types : contrôle d'accès, authentification "
            "multifacteur, chiffrement, sauvegardes, segmentation réseau, journalisation, "
            "gestion des correctifs et sensibilisation du personnel."
        ),
    },
    {
        "title": "ANSSI — Hygiène informatique",
        "source": "anssi-guide",
        "content": (
            "Les mesures d'hygiène informatique de l'ANSSI recommandent notamment : des mots de "
            "passe robustes, l'authentification multifacteur, la mise à jour régulière des "
            "logiciels, des sauvegardes hors ligne, et la séparation des usages personnels et "
            "professionnels."
        ),
    },
]

_QUERY_RE = re.compile(r"[a-zà-ÿ0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_QUERY_RE.findall(text.lower()))


def _score(query_tokens: set[str], doc_tokens: set[str]) -> float:
    if not query_tokens:
        return 0.0
    return len(query_tokens & doc_tokens) / len(query_tokens)


async def seed_knowledge(session: AsyncSession) -> None:
    """Insère les documents de référence s'ils sont absents (idempotent)."""
    count = await session.scalar(select(KnowledgeDocument.id).limit(1))
    if count is not None:
        return
    for doc in SEED_DOCUMENTS:
        session.add(
            KnowledgeDocument(
                title=doc["title"],
                source=doc["source"],
                content=doc["content"],
            )
        )
    await session.commit()


async def search(session: AsyncSession, query: str, top_k: int = 3) -> list[dict]:
    """Recherche lexicale des documents les plus proches de la requête."""
    rows = await session.scalars(select(KnowledgeDocument))
    docs = [
        {"title": d.title, "source": d.source, "content": d.content}
        for d in rows
    ]
    query_tokens = _tokens(query)
    scored = [
        (d, _score(query_tokens, _tokens(d["content"])))
        for d in docs
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    return [d for d, s in scored if s > 0][:top_k]


async def build_context(session: AsyncSession, query: str, top_k: int = 3) -> str:
    """Construit un bloc de texte de référence à injecter dans un prompt."""
    docs = await search(session, query, top_k)
    if not docs:
        return ""
    return "\n\n".join(
        f"[{d['source']}] {d['title']}\n{d['content']}" for d in docs
    )
