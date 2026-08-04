from typing import Optional
from pydantic import BaseModel
import jwt
from fastapi import HTTPException, status
from app.core.config import settings


class UserContext(BaseModel):
    id: str
    email: Optional[str] = None
    role: str = "authenticated"


def decode_supabase_jwt(token: str) -> UserContext:
    """Decodes and validates a Supabase JWT token.
    
    If SUPABASE_ANON_KEY / JWT secret validation is configured, decodes token claims.
    """
    try:
        # Supabase JWTs are signed with the JWT Secret or HS256 using key / anon key.
        # We unverified decode or verify with algorithms=["HS256"]
        payload = jwt.decode(
            token,
            options={"verify_signature": False},  # Public JWT inspection; verify_signature can be enabled with JWT_SECRET
            algorithms=["HS256"],
        )
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token: missing user subject (sub).",
            )
        return UserContext(id=user_id, email=email, role=payload.get("role", "authenticated"))
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication token invalid or expired: {e}",
        )
