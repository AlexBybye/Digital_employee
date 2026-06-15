"""Unified AI chat service.

Delegates to ``ai_service.ask_knowledge_base()`` which handles
BGE vector + BoW scoring, three-tier routing, and ticket creation.
"""

import logging

from services.ai_service import ask_knowledge_base

logger = logging.getLogger(__name__)


def chat(message: str, user: str = "anonymous") -> dict:
    """Unified chat entry point. Delegates to the knowledge-base service.

    The service automatically:
    - Returns a direct FAQ answer when confident (score >= 0.55)
    - Generates an LLM answer with context (score 0.40-0.55)
    - Creates a ticket when confidence is low (score < 0.40)
    """
    result = ask_knowledge_base(message, user=user)

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
