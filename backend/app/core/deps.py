
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import get_db

# Use HTTPBearer for clean Authorization: Bearer <token> parsing
http_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency enforcing that the request carries a valid, non-expired Bearer access token."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedError("Missing authentication token in Authorization header")

    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise UnauthorizedError("Invalid token subject")

    user = await db.get(User, user_id)
    if not user:
        raise UnauthorizedError("User associated with token no longer exists")

    if not user.is_active:
        raise UnauthorizedError("User account is inactive")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def require_role(required_role: str):
    """Dependency factory checking that the authenticated user possesses the required role."""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role and current_user.role != "admin":
            raise ForbiddenError(f"Operation requires '{required_role}' privileges")
        return current_user

    return role_checker
