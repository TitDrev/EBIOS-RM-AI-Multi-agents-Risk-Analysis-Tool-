"""Tests de la base de connaissances (RAG)."""

from app.services.rag_service import build_context, search, seed_knowledge


async def test_seed_and_search(test_session_factory):
    async with test_session_factory() as session:
        await seed_knowledge(session)

        docs = await search(session, "sources de risques EBIOS RM")
        assert docs
        assert any("sources de risques" in d["title"].lower() for d in docs)

        docs2 = await search(session, "scénarios stratégiques gravité vraisemblance")
        assert any("scénarios stratégiques" in d["title"].lower() for d in docs2)


async def test_seed_is_idempotent(test_session_factory):
    async with test_session_factory() as session:
        await seed_knowledge(session)
        await seed_knowledge(session)
        ctx = await build_context(session, "mesures de sécurité ISO 27002")
        assert "27002" in ctx
