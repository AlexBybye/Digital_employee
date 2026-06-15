"""RPA simulation API for common ops tasks."""

from fastapi import APIRouter, Depends

from auth import get_current_user, require_role
from database.db import get_rpa_jobs
from models.schemas import CreateAccountRequest, FreezeAccountRequest, ResetPasswordRequest, RpaJobResponse, RpaJobHistoryItem
from services.rpa_service import create_account_job, freeze_account_job, reset_password_job, unfreeze_account_job


router = APIRouter(tags=["rpa"])


@router.post("/reset-password", response_model=RpaJobResponse)
def reset_password(payload: ResetPasswordRequest,
                   _user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Simulate password reset automation."""
    return reset_password_job(payload.username, payload.new_password, payload.requested_by)


@router.post("/create-account", response_model=RpaJobResponse)
def create_account(payload: CreateAccountRequest,
                   _user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Simulate account creation automation."""
    return create_account_job(
        payload.username,
        payload.password,
        payload.role,
        payload.requested_by,
        payload.full_name,
        payload.department,
        payload.phone,
        payload.email,
    )


@router.post("/freeze-account", response_model=RpaJobResponse)
def freeze_account(payload: FreezeAccountRequest,
                   _user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Simulate account freeze and cleanup automation."""
    return freeze_account_job(payload.username, payload.requested_by, payload.reason)


@router.post("/unfreeze-account", response_model=RpaJobResponse)
def unfreeze_account(payload: FreezeAccountRequest,
                     _user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Simulate account unfreeze automation."""
    return unfreeze_account_job(payload.username, payload.requested_by, payload.reason)


@router.get("/rpa-jobs", response_model=list[RpaJobHistoryItem])
def rpa_job_history(_user: dict = Depends(get_current_user)) -> list[dict]:
    """Return the most recent RPA job records."""
    return get_rpa_jobs()
