"""Ticket workflow service with self-learning FAQ updates."""

from database.db import add_faq, get_ticket, update_ticket


def resolve_ticket(
    ticket_id: int,
    resolution_note: str = "",
    resolver: str = "",
    add_to_kb: bool = False,
    kb_answer: str = "",
    callback_status: str = "contacted",
    callback_note: str = "已回访并告知处理结果",
) -> dict | None:
    """Resolve a ticket and optionally add the answer to data/faq.json."""
    ticket = get_ticket(ticket_id)
    if ticket is None:
        return None

    resolved = update_ticket(
        ticket_id,
        {
            "status": "resolved",
            "answer": resolution_note,
            "resolver": resolver,
            "callback_status": callback_status,
            "callback_note": callback_note,
        },
    )

    # Save to FAQ only when add_to_kb is True and kb_answer is not empty
    if add_to_kb and kb_answer.strip():
        add_faq(ticket["question"], kb_answer, ["自学习", "工单沉淀", ticket["category"]])

    return resolved
