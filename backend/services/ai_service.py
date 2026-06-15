"""AI service: weighted avg (0.7vec+0.3bow) with three-tier routing."""
import re
from database.db import create_ticket, get_faqs
from rag.retriever import retrieve
from services.llm_service import generate_answer

DIRECT_ANSWER = 0.55   # >= 0.55 -> direct FAQ answer (no LLM needed)
LLM_LOWER = 0.40       # 0.40-0.55 -> LLM with top-K context (if bow >= BOW_GATE)
BOW_GATE = 0.10        # Even if combined score >= 0.40, if bow < 0.10
                       # there's no keyword overlap -> create ticket

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


def ask_knowledge_base(question, user="", contact="", category="general", priority="normal"):
    # Direct-to-human: user explicitly asks for human support
    if _is_human_agent_request(question):
        ticket = create_ticket(question, user, contact, category, priority="urgent")
        return {"answer": "已为您转接人工处理，工单已创建，管理员将尽快处理您的问题。",
                "confidence": 1.0, "fallback": True, "ticket_id": ticket["id"], "sources": []}

    sources = retrieve(question, limit=2)
    if not sources:
        ticket = create_ticket(question, user, contact, category, priority)
        return {"answer": "知识库暂时没有足够信息回答该问题，系统已自动创建工单等待管理员处理。",
                "confidence": 0.0, "fallback": True, "ticket_id": ticket["id"], "sources": []}

    confidence = sources[0]["score"]
    bow = sources[0].get("bow_score", 0.0)

    # Direct answer: high combined score
    if confidence >= DIRECT_ANSWER:
        return {"answer": sources[0]["answer"], "confidence": confidence,
                "fallback": False, "ticket_id": None, "sources": sources}

    # LLM path: medium confidence with keyword overlap
    if confidence >= LLM_LOWER and bow >= BOW_GATE:
        return {"answer": generate_answer(question, sources), "confidence": confidence,
                "fallback": False, "ticket_id": None, "sources": sources}

    # Create ticket: low confidence OR no keyword overlap but LLM range
    ticket = create_ticket(question, user, contact, category, priority)
    return {"answer": "知识库暂时没有足够信息回答该问题，系统已自动创建工单等待管理员处理。",
            "confidence": confidence, "fallback": True, "ticket_id": ticket["id"], "sources": sources}


def rag_status():
    return {"mode": "local-rag", "faq_count": len(get_faqs()),
            "confidence_threshold": DIRECT_ANSWER,
            "direct_answer_threshold": LLM_LOWER,
            "llm_provider": "ollama (deepseek-r1:1.5b)",
            "vector_store": "BGE-small-zh + BoW weighted (0.7v+0.3b)"}
