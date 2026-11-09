import secrets
import logging

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings


logger = logging.getLogger(__name__)

bearer = HTTPBearer(auto_error=False)


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> None:
    """
    Пропускает только запросы с верным токеном администратора.
    Если ADMIN_TOKEN не задан, закрыто для всех
    """
    token = settings.admin_token
    if (
        not token
        or credentials is None
        or not secrets.compare_digest(
            credentials.credentials.encode(), token.encode()
        )
    ):
        logger.warning("admin authentication failed")
        raise HTTPException(
            status_code=401,
            detail="Admin token required",
            headers={"WWW-Authenticate": "Bearer"},
        )