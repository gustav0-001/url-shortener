import logging
import secrets
import string
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import Link, get_current_time

logger = logging.getLogger(__name__)

RESERVED_CODES = {"health", "links", "docs", "redoc", "static"}
MAX_ATTEMPTS = 10


class ShortCodeGenerationError(Exception):
    """Не удалось подобрать уникальный short_code за MAX_ATTEMPTS попыток"""


def generate_short_code() -> str:
    """
    Генерация короткого кода для сокращенной ссылки, латинские буквы обоих регистров и цифры
    :return: строка
    """
    alphabet = string.ascii_letters + string.digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        if code.lower() not in RESERVED_CODES:
            return code


def create_link(
    session: Session, original_url: str, expires_at: datetime | None = None
) -> Link:
    """
    Создание ссылки с проверкой повторной генерации short_code
    """
    for _ in range(MAX_ATTEMPTS):
        link = Link(
            short_code=generate_short_code(),
            original_url=original_url,
            expires_at=expires_at,
        )
        session.add(link)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning("Short code collision, retrying")
            continue

        session.refresh(link)
        logger.info("Link created code=%s", link.short_code)
        return link

    logger.error("Could not generate a unique short code in %s attempts", MAX_ATTEMPTS)
    raise ShortCodeGenerationError


def get_link_by_code(session: Session, short_code: str) -> Link | None:
    """
    Поиск ссылки в БД по short_code
    """
    statement = select(Link).where(Link.short_code == short_code)
    return session.exec(statement).first()


def increment_clicks(session: Session, link_id: int) -> None:
    """
    Атомарное увеличение счетчика кликов
    """
    session.execute(
        update(Link).where(Link.id == link_id).values(clicks=Link.clicks + 1)
    )
    session.commit()


def is_expired(link: Link) -> bool:
    """
    Истёк ли срок жизни ссылки (ссылка без срока не истекает)
    """
    if link.expires_at is None:
        return False
    expires_at = link.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= get_current_time()