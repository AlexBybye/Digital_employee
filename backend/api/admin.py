"""Admin API for tickets and knowledge-base maintenance."""

from fastapi import APIRouter, Depends, HTTPException, Response

from auth import get_current_user, require_role
from database.db import add_faq, delete_faq, get_faqs, list_tickets, update_faq
from models.schemas import FaqCreate, FaqResponse, FaqUpdate, TicketResolve, TicketResponse
from services.ticket_service import resolve_ticket


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tickets", response_model=list[TicketResponse])
def admin_tickets(status: str | None = None, keyword: str | None = None,
                  _user: dict = Depends(get_current_user)) -> list[dict]:
    """Return tickets for admin review with optional filters."""
    return list_tickets(status=status, keyword=keyword)


@router.patch("/tickets/{ticket_id}/resolve", response_model=TicketResponse)
def admin_resolve(ticket_id: int, payload: TicketResolve,
                  _user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Resolve a ticket and optionally teach the FAQ knowledge base."""
    ticket = resolve_ticket(
        ticket_id,
        payload.resolution_note,
        payload.resolver,
        payload.add_to_kb,
        payload.kb_answer,
        payload.callback_status,
        payload.callback_note,
    )
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    return ticket


@router.get("/faqs", response_model=list[FaqResponse])
def faqs(_user: dict = Depends(get_current_user)) -> list[dict]:
    """List FAQ knowledge-base items."""
    return get_faqs()


@router.post("/faqs", response_model=FaqResponse, status_code=201)
def create_faq(payload: FaqCreate,
               _user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Create a FAQ knowledge-base item."""
    return add_faq(payload.question, payload.answer, payload.tags)


@router.patch("/faqs/{faq_id}", response_model=FaqResponse)
def edit_faq(faq_id: int, payload: FaqUpdate,
             _user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Update a FAQ knowledge-base item."""
    faq = update_faq(faq_id, payload.model_dump(exclude_unset=True))
    if faq is None:
        raise HTTPException(status_code=404, detail="faq not found")
    return faq


@router.delete("/faqs/{faq_id}", status_code=204)
def remove_faq(faq_id: int,
               _user: dict = Depends(require_role("admin", "operator"))) -> Response:
    """Delete a FAQ knowledge-base item."""
    if not delete_faq(faq_id):
        raise HTTPException(status_code=404, detail="faq not found")
    return Response(status_code=204)
