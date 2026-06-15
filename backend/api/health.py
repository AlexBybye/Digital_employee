"""Health-check API."""

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """Return service health."""
    return {"status": "ok", "service": "Ops Digital Employee"}

