import secrets
import string

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import Link

RESERVED_CODES = {"health", "links", "docs", "redoc"}
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


def create_link(session: Session, original_url: str) -> Link:
    """
    Создание ссылки с проверкой повторной генерации short_code
    """
    for _ in range(MAX_ATTEMPTS):
        link = Link(
            short_code=generate_short_code(),
            original_url=original_url,
        )
        session.add(link)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            continue

        session.refresh(link)
        return link

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