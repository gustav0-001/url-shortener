import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_session
from app.config import settings

from app import ratelimit

from app.models import Link


@pytest.fixture(name="session")
def session_fixture():
    """
    Отдельная тестовая база в памяти
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()

@pytest.fixture(name="client")
def client_fixture(session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    client = TestClient(app)
    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.pop(get_session, None)

@pytest.fixture(name="admin_headers")
def admin_headers_fixture(monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "test-admin-token")
    return {"Authorization": "Bearer test-admin-token"}

@pytest.fixture(autouse=True)
def reset_rate_limit():
    ratelimit.reset()
    yield

