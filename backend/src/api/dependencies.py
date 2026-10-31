import secrets
from fastapi import Header, HTTPException, status
from core.config import settings


async def verify_admin_token(authorization: str = Header(None)) -> bool:
    if not settings.auth_enabled:
        return True

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header."
        )

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must follow 'Bearer <token>' format."
        )

    token = parts[1]
    expected = settings.knowledge_admin_secret.get_secret_value()

    if not secrets.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin credentials for knowledge refresh."
        )

    return True

