"""Ticket API for escalation and status updates."""

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user, require_role
from database.db import create_ticket, get_ticket, list_tickets, update_ticket
from models.schemas import TicketCreate, TicketResponse, TicketUpdate


router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=201)
def create(payload: TicketCreate) -> dict:
    """Create a support ticket manually."""
    return create_ticket(
        payload.question,
        payload.user,
        payload.contact,
        payload.category,
        payload.priority,
    )


@router.get("", response_model=list[TicketResponse])
def list_all(status: str | None = None, keyword: str | None = None,
             user: str | None = None,
             _user: dict = Depends(get_current_user)) -> list[dict]:
    """List tickets, optionally filtered by status, keyword, and user."""
    return list_tickets(status=status, keyword=keyword, user=user)


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_one(ticket_id: int, _user: dict = Depends(get_current_user)) -> dict:
    """Get one ticket."""
    ticket = get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update(ticket_id: int, payload: TicketUpdate,
           _user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Update ticket status, answer, or resolver."""
    ticket = update_ticket(ticket_id, payload.model_dump(exclude_unset=True))
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    return ticket
