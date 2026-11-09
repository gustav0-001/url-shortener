import logging

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import links as link_service

URL = {"original_url": "https://example.com/"}


def test_link_creation_is_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger="app"):
        response = client.post("/links", json=URL)

    assert f"code={response.json()['short_code']}" in caplog.text


def test_rate_limit_hit_is_logged(client, monkeypatch, caplog):
    monkeypatch.setattr(settings, "create_rate_limit", 1)
    client.post("/links", json=URL)

    with caplog.at_level(logging.WARNING, logger="app"):
        client.post("/links", json=URL)

    assert "rate limit exceeded" in caplog.text


def test_unhandled_error_returns_json_500(client, monkeypatch, caplog):
    '''
    Создает отдельный TestClient с raise_server_exceptions=False
    '''
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(link_service, "create_link", boom)
    safe_client = TestClient(app, raise_server_exceptions=False)

    response = safe_client.post("/links", json=URL)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert "boom" in caplog.text