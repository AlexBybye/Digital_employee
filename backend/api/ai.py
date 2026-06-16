"""AI question-answering API backed by local RAG retrieval."""

from typing import Optional

from fastapi import APIRouter, Depends, Request

from auth import get_current_user, require_role
from models.schemas import AskRequest, AskResponse, ChatRequest, ChatResponse, RagStatusResponse, RpaCommandRequest, RpaCommandResponse
from services.ai_service import ask_knowledge_base, rag_status
from services.ai_rpa_service import execute_rpa
from services.chat_service import chat


router = APIRouter(prefix="/ai", tags=["ai"])


def _get_optional_user(request: Request) -> Optional[dict]:
    """Try to get the current user from token, return None if not authenticated."""
    try:
        return get_current_user(request)
    except Exception:
        return None


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> dict:
    """Answer a question or create a ticket when confidence is low."""
    return ask_knowledge_base(
        payload.question,
        payload.user,
        payload.contact,
        payload.category,
        payload.priority,
    )


@router.get("/status", response_model=RagStatusResponse)
def status() -> dict:
    """Return the current local RAG and LLM integration mode."""
    return rag_status()


@router.post("/rpa", response_model=RpaCommandResponse)
def ai_rpa(payload: RpaCommandRequest,
           _user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Execute an RPA operation via natural-language command (AI-driven)."""
    return execute_rpa(payload.command)


@router.post("/chat", response_model=ChatResponse)
def ai_chat(payload: ChatRequest, user: Optional[dict] = Depends(_get_optional_user)) -> dict:
    """Unified AI chat — uses logged-in identity if available, otherwise anonymous."""
    username = user["username"] if user else "anonymous"
    history = [{"role": t.role, "text": t.text} for t in payload.history]
    return chat(payload.message, username, history=history)
