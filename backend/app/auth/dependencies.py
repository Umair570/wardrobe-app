from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.security import UserContext, decode_supabase_jwt


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> UserContext:
    """Extracts and verifies Supabase JWT token from the Authorization header.
    
    Format: Authorization: Bearer <token>
    If no authorization header is provided during development, falls back to a default user context.
    """
    if not authorization:
        # Development fallback when frontend is running without auth header yet
        return UserContext(id="default_user", email="default@example.com", role="anonymous")

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'.",
        )

    token = authorization.split(" ", 1)[1].strip()
    return decode_supabase_jwt(token)
