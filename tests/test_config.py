from app.config import Settings


def test_database_url_scheme_is_normalized():
    expected = "postgresql+psycopg://user:pass@host/db"

    assert Settings(database_url="postgres://user:pass@host/db").database_url == expected
    assert Settings(database_url="postgresql://user:pass@host/db").database_url == expected
    assert Settings(database_url=expected).database_url == expected


def test_sqlite_url_is_unchanged():
    url = "sqlite:///links.db"

    assert Settings(database_url=url).database_url == url