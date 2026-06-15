"""User management API for ops accounts."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Response

from auth import get_current_user, require_role, store_token
from database.db import (
    authenticate_user,
    create_user,
    delete_user,
    freeze_user,
    get_user,
    list_users,
    update_user,
)
from models.schemas import LoginRequest, LoginResponse, UserCreate, UserResponse, UserStatusUpdate, UserUpdate


router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=201)
def create(payload: UserCreate, user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Create an ops account. viewer cannot create."""
    try:
        return create_user(
            payload.username,
            payload.password,
            payload.role,
            payload.full_name,
            payload.department,
            payload.phone,
            payload.email,
            payload.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[UserResponse])
def list_all(
    keyword: str | None = None,
    role: str | None = None,
    status: str | None = None,
    _user: dict = Depends(get_current_user),
) -> list[dict]:
    """List ops accounts — all authenticated users can list."""
    return list_users(keyword=keyword, role=role, status=status)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> dict:
    """Demo login endpoint for course-design authentication flow."""
    user = authenticate_user(payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid username/password or frozen account")
    token = secrets.token_urlsafe(24)
    store_token(token, user)
    return {"token": token, "user": user}


@router.get("/{user_id}", response_model=UserResponse)
def get_one(user_id: int, _user: dict = Depends(get_current_user)) -> dict:
    """Get one ops account."""
    user = get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user


def _check_target_role(user_id: int, current_user: dict) -> None:
    """Operator cannot modify admin accounts."""
    target = get_user(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="user not found")
    current_role = current_user.get("role", "")
    target_role = target.get("role", "")
    if current_role == "operator" and target_role == "admin":
        raise HTTPException(status_code=403, detail="operator 无权操作 admin 账号")


@router.put("/{user_id}", response_model=UserResponse)
def update(user_id: int, payload: UserUpdate, user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Update an ops account."""
    _check_target_role(user_id, user)
    try:
        result = update_user(user_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="user not found")
    return result


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_status(user_id: int, payload: UserStatusUpdate, user: dict = Depends(require_role("admin", "operator"))) -> dict:
    """Freeze or reactivate an ops account."""
    _check_target_role(user_id, user)
    result = freeze_user(user_id, payload.status)
    if result is None:
        raise HTTPException(status_code=404, detail="user not found")
    return result


@router.delete("/{user_id}", status_code=204)
def delete(user_id: int, user: dict = Depends(require_role("admin", "operator"))) -> Response:
    """Delete an ops account."""
    _check_target_role(user_id, user)
    if not delete_user(user_id):
        raise HTTPException(status_code=404, detail="user not found")
    return Response(status_code=204)
