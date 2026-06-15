"""Simple token-based auth for demo purposes.

Stores login tokens in-memory and provides a FastAPI dependency
that verifies the Authorization header and returns the current user.
"""

from fastapi import Depends, HTTPException, Request

# In-memory token store: {token: user_dict}
_token_store: dict[str, dict] = {}


def store_token(token: str, user: dict) -> None:
    """Remember a login token for subsequent requests."""
    _token_store[token] = user


def remove_token(token: str) -> None:
    """Invalidate a token (logout)."""
    _token_store.pop(token, None)


def get_current_user(request: Request) -> dict:
    """FastAPI dependency: extract and verify Bearer token, return user dict."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供有效的认证令牌")
    token = auth[7:]
    user = _token_store.get(token)
    if user is None:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    return user


def require_role(*roles: str):
    """Return a dependency that requires one of the given roles."""

    def check(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return user

    return check
