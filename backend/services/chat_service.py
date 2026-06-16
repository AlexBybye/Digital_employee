"""Unified AI chat service.

Delegates to ``ai_service.ask_knowledge_base()`` which handles
BGE vector + BoW scoring, three-tier routing, and ticket creation.
For multi-turn conversations it first rewrites the latest message into a
self-contained retrieval query using the conversation history.
"""

import logging

from rag.query_rewrite import rewrite_query
from services.ai_service import ask_knowledge_base

logger = logging.getLogger(__name__)


def chat(message: str, user: str = "anonymous", history: list[dict] | None = None) -> dict:
    """Unified chat entry point. Delegates to the knowledge-base service.

    ``history`` is the prior conversation turns ([{role, text}, ...]). When
    present, the latest ``message`` is rewritten into a self-contained query
    (LLM if Ollama is up, else rule-based) so follow-ups with pronouns/ellipsis
    retrieve correctly. The original message is still shown and stored.
    """
    retrieval_query = None
    if history:
        rewritten = rewrite_query(history, message)
        if rewritten and rewritten != message:
            retrieval_query = rewritten
            logger.info("multi-turn rewrite: %r -> %r", message, rewritten)

    result = ask_knowledge_base(message, user=user, retrieval_query=retrieval_query)

    if result.get("fallback"):
        return {
            "intent": "unknown",
            "type": "ticket",
            "content": f"知识库暂时没有足够信息回答该问题，已自动创建工单 #{result['ticket_id']}，等待管理员处理。",
            "ticket_id": result["ticket_id"],
            "confidence": result["confidence"],
        }

    return {
        "intent": "knowledge",
        "type": "answer",
        "content": result["answer"],
        "confidence": result["confidence"],
        "sources": result["sources"],
    }
