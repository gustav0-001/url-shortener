from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlmodel import Session, col, select

from app.database import get_session
from app.models import Link
from app.schemas import LinkCreate, LinkResponse
from app.services import links as link_service

from app.security import require_admin
from app.ratelimit import rate_limit_create


router = APIRouter(
    tags=["Links"],
)


def get_link_or_404(session: Session, short_code: str) -> Link:
    link = link_service.get_link_by_code(session, short_code)
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


@router.post("/links", response_model=LinkResponse, status_code=201, dependencies=[Depends(rate_limit_create)])
def create_link(payload: LinkCreate, session: Session = Depends(get_session)):
    """
    Создание ссылки с проверкой повторной генерации short_code
    """
    try:
        return link_service.create_link(session, str(payload.original_url))
    except link_service.ShortCodeGenerationError:
        raise HTTPException(
            status_code=503,
            detail="Could not generate a unique short code. Try again",
        )


@router.get("/links", response_model=list[LinkResponse], dependencies=[Depends(require_admin)])
def get_links(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """
    Получение добавленных ссылок: сначала новые, с пагинацией
    """
    statement = (
        select(Link)
        .order_by(col(Link.id).desc())
        .offset(offset)
        .limit(limit)
    )
    return session.exec(statement).all()


@router.get("/{short_code}")
def redirect_link(short_code: str, session: Session = Depends(get_session)):
    link = get_link_or_404(session, short_code)

    target_url = link.original_url
    link_service.increment_clicks(session, link.id)

    return RedirectResponse(target_url)


@router.get("/links/{short_code}", response_model=LinkResponse)
def get_link(short_code: str, session: Session = Depends(get_session)):
    """
    Проверить клики
    """
    return get_link_or_404(session, short_code)


@router.delete("/links/{short_code}", status_code=204, dependencies=[Depends(require_admin)])
def delete_link(short_code: str, session: Session = Depends(get_session)):
    """
    Удалить ссылку (запись из БД) по short_code
    """
    link = get_link_or_404(session, short_code)
    session.delete(link)
    session.commit()
