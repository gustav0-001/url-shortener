from datetime import timedelta
from sqlmodel import select

from app.models import Link, get_current_time


URL = {"original_url": "https://example.com/"}

def test_link_without_expiry_has_null_expires_at(client):
    response = client.post("/links", json=URL)

    assert response.json()["expires_at"] is None


def test_create_link_with_expiry(client):
    response = client.post("/links", json={**URL, "expires_in_days": 7})

    assert response.status_code == 201
    assert response.json()["expires_at"] is not None


def test_expires_in_days_is_validated(client):
    for value in (0, -1, 366):
        response = client.post("/links", json={**URL, "expires_in_days": value})
        assert response.status_code == 422


def test_link_with_future_expiry_redirects(client):
    short_code = client.post("/links", json={**URL, "expires_in_days": 7}).json()["short_code"]

    response = client.get(f"/{short_code}", follow_redirects=False)

    assert response.status_code == 302


def test_expired_link_returns_410_and_is_not_counted(client, session):
    short_code = client.post("/links", json={**URL, "expires_in_days": 1}).json()["short_code"]
    link = session.exec(select(Link).where(Link.short_code == short_code)).one()
    link.expires_at = get_current_time() - timedelta(days=1)
    session.add(link)
    session.commit()

    response = client.get(f"/{short_code}", follow_redirects=False)

    assert response.status_code == 410
    assert response.json() == {"detail": "Link expired"}
    assert client.get(f"/links/{short_code}").json()["clicks"] == 0