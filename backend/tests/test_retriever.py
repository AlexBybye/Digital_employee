"""Tests for the RAG retrieval pipeline and three-tier routing.

These run WITHOUT the heavy ML models loaded. The vector channel and the
cross-encoder both degrade gracefully when their models are absent, so on a
bare CI box the pipeline falls back to BoW-recall + RRF scoring — which is
exactly the fallback path we want to keep verified.

Run from the backend/ directory:  python -m pytest tests/ -v
"""
import sys
from pathlib import Path

import pytest

# Make `import rag...`, `import database...` resolve like the app does.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from rag import retriever  # noqa: E402
from rag import reranker as reranker_mod  # noqa: E402
from services import ai_service  # noqa: E402
from database.db import init_database, seed_database, get_faqs  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    """Create SQLite tables + seed data so ticket-creation paths work in tests.

    Also initialize the vector store when the embedding model is present, so the
    reranker tests exercise the real vector-recall path. Both are best-effort:
    if the models aren't installed the pipeline degrades and those tests skip.
    """
    init_database()
    seed_database()
    try:
        from rag.chroma_store import init_vector_store
        init_vector_store(get_faqs())
    except Exception:
        pass  # no embedding model -> lexical fallback, degraded tests still run


def test_tokens_chinese_bigrams():
    """Chinese text expands into unigrams + bigrams; stop words dropped."""
    toks = retriever.tokens("账号冻结")
    assert "账" in toks and "号" in toks
    assert "账号" in toks and "号冻" in toks  # bigrams
    assert "the" not in retriever.tokens("the account")  # English stop word


def test_clean_query_strips_noise():
    assert retriever.clean_query("请问账号冻结怎么办") == "账号冻结"
    # "我想知道" is a noise phrase and gets removed wherever it appears.
    assert "我想知道" not in retriever.clean_query("你好，我想知道VPN无法登录")
    # Trailing politeness "你好…" is stripped only at end of string.
    assert retriever.clean_query("VPN无法登录你好") == "VPN无法登录"


def test_rrf_fuse_rewards_agreement():
    """A doc ranked #1 in both channels beats one ranked #1 in only one."""
    fused = retriever._rrf_fuse(["a", "b"], ["a", "c"])
    assert fused["a"] > fused["b"]
    assert fused["a"] > fused["c"]


def test_cosine_similarity_bounds():
    a = retriever.vectorize("账号冻结怎么处理")
    assert retriever.cosine_similarity(a, a) == pytest.approx(1.0, abs=1e-6)
    assert retriever.cosine_similarity(a, retriever.vectorize("")) == 0.0


def test_retrieve_returns_scored_sources():
    """A clear FAQ hit returns results carrying a score + score_source."""
    results = retriever.retrieve("账号冻结怎么处理", limit=3)
    assert results, "expected at least one candidate for an in-KB question"
    top = results[0]
    assert "score" in top and "score_source" in top
    assert top["score_source"] in ("rerank", "lexical")
    # The frozen-account FAQ (id 1) should win on a near-verbatim query.
    assert top["question"].startswith("账号冻结")


def test_routing_buckets_are_ordered():
    """Direct cutoff must sit above the LLM cutoff for whichever scorer is active."""
    for source in ("rerank", "lexical"):
        direct, llm = ai_service._thresholds(source)
        assert direct > llm > 0


def test_off_topic_query_creates_ticket():
    """An off-topic query has near-zero lexical overlap -> must become a ticket."""
    res = ai_service.ask_knowledge_base("帮我推荐一家附近的火锅店", user="tester")
    assert res["fallback"] is True
    assert res["ticket_id"] is not None


def test_near_verbatim_query_answers_directly():
    """A near-verbatim in-KB question should be answered directly (no ticket)."""
    res = ai_service.ask_knowledge_base("账号冻结怎么处理", user="tester")
    assert res["fallback"] is False
    assert res["ticket_id"] is None


def test_human_handoff_creates_ticket():
    res = ai_service.ask_knowledge_base("我要转人工", user="tester")
    assert res["fallback"] is True
    assert res["ticket_id"] is not None


# --- Non-degraded path: only runs when the cross-encoder model is available ---

_RERANKER = reranker_mod.is_ready()


@pytest.mark.skipif(not _RERANKER, reason="bge-reranker model not available")
def test_rerank_semantic_match_beats_lexical():
    """With the reranker, a paraphrase routes to the semantically correct FAQ.

    'How do I open an account for a new colleague' must hit the *create-account*
    FAQ (#3), not the lexically-similar *freeze-account* FAQ (#1) that the
    keyword-only fallback mis-picks.
    """
    results = retriever.retrieve("怎么给新同事开账号", limit=1)
    assert results and results[0]["score_source"] == "rerank"
    assert "创建" in results[0]["question"] or results[0]["id"] == 3


@pytest.mark.skipif(not _RERANKER, reason="bge-reranker model not available")
def test_rerank_off_topic_creates_ticket():
    """Off-topic queries sit at the reranker's neutral ~0.5 band -> ticket, not LLM."""
    res = ai_service.ask_knowledge_base("今天星期几", user="tester")
    assert res["fallback"] is True
    assert res["ticket_id"] is not None

