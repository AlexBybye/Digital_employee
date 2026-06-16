"""AI service: recall → RRF fusion → cross-encoder rerank, then three-tier routing.

Routing keys off the retriever's ``score``/``score_source``:
  - score_source == "rerank" : calibrated cross-encoder relevance → RERANK_* thresholds
  - score_source == "lexical": BoW cosine fallback when reranker is offline → LEX_* thresholds
RRF is only used to order the recall set, never as a routing confidence.
"""
import re

from database.db import create_ticket, get_faqs
from rag.config import (LEX_DIRECT, LEX_LLM, RERANK_DIRECT, RERANK_LLM)
from rag.reranker import is_ready as reranker_ready
from rag.retriever import retrieve
from services.llm_service import generate_answer

# Phrases that indicate user wants human support — skip RAG, create ticket directly
HUMAN_AGENT_PATTERNS = [
    r"转人工", r"人工客服", r"人工服务", r"找人工",
    r"转接管理员", r"联系管理员", r"找管理员",
    r"人工处理", r"人工帮助", r"人工支持",
    r"我要找人", r"帮我转接",
]


def _is_human_agent_request(question: str) -> bool:
    """Check if the user is explicitly asking for human support."""
    for pattern in HUMAN_AGENT_PATTERNS:
        if re.search(pattern, question):
            return True
    return False


def _thresholds(score_source: str) -> tuple[float, float]:
    """Return (direct, llm) cutoffs matching the score's origin."""
    if score_source == "rerank":
        return RERANK_DIRECT, RERANK_LLM
    return LEX_DIRECT, LEX_LLM


def ask_knowledge_base(question, user="", contact="", category="general", priority="normal",
                       retrieval_query=None):
    """Answer a question, optionally retrieving with a rewritten query.

    ``retrieval_query`` (when given) is used for RETRIEVAL only — e.g. a
    multi-turn follow-up rewritten into a self-contained query. The original
    ``question`` is still what gets stored on any ticket and shown to the user.
    """
    # Direct-to-human: user explicitly asks for human support
    if _is_human_agent_request(question):
        ticket = create_ticket(question, user, contact, category, priority="urgent")
        return {"answer": "已为您转接人工处理，工单已创建，管理员将尽快处理您的问题。",
                "confidence": 1.0, "fallback": True, "ticket_id": ticket["id"], "sources": []}

    sources = retrieve(retrieval_query or question, limit=2)
    if not sources:
        ticket = create_ticket(question, user, contact, category, priority)
        return {"answer": "知识库暂时没有足够信息回答该问题，系统已自动创建工单等待管理员处理。",
                "confidence": 0.0, "fallback": True, "ticket_id": ticket["id"], "sources": []}

    top = sources[0]
    confidence = top["score"]
    direct_cut, llm_cut = _thresholds(top.get("score_source", "lexical"))

    # Direct answer: high relevance
    if confidence >= direct_cut:
        return {"answer": top["answer"], "confidence": confidence,
                "fallback": False, "ticket_id": None, "sources": sources}

    # LLM path: medium relevance — let the model answer with retrieved context
    if confidence >= llm_cut:
        return {"answer": generate_answer(question, sources), "confidence": confidence,
                "fallback": False, "ticket_id": None, "sources": sources}

    # Create ticket: low relevance
    ticket = create_ticket(question, user, contact, category, priority)
    return {"answer": "知识库暂时没有足够信息回答该问题，系统已自动创建工单等待管理员处理。",
            "confidence": confidence, "fallback": True, "ticket_id": ticket["id"], "sources": sources}


def rag_status():
    use_rerank = reranker_ready()
    scorer = "rerank" if use_rerank else "lexical"
    direct_cut, llm_cut = _thresholds(scorer)
    return {"mode": "local-rag",
            "faq_count": len(get_faqs()),
            "confidence_threshold": direct_cut,
            "direct_answer_threshold": llm_cut,
            "llm_provider": "ollama (deepseek-r1:1.5b)",
            "vector_store": "BGE-small-zh recall + BoW recall → RRF fusion"
                            + (" → bge-reranker" if use_rerank else " (reranker offline, lexical routing)"),
            "scorer": scorer}
