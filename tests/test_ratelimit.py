from app.config import settings

URL = {"original_url": "https://example.com/"}


def test_create_link_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(settings, "create_rate_limit", 2)

    assert client.post("/links", json=URL).status_code == 201
    assert client.post("/links", json=URL).status_code == 201

    response = client.post("/links", json=URL)

    assert response.status_code == 429
    assert "retry-after" in response.headers


def test_rate_limit_is_per_client(client, monkeypatch):
    monkeypatch.setattr(settings, "create_rate_limit", 1)
    first_ip = {"True-Client-IP": "1.1.1.1"}
    second_ip = {"True-Client-IP": "2.2.2.2"}

    assert client.post("/links", json=URL, headers=first_ip).status_code == 201
    assert client.post("/links", json=URL, headers=second_ip).status_code == 201
    assert client.post("/links", json=URL, headers=first_ip).status_code == 429


def test_redirect_is_not_rate_limited(client, monkeypatch):
    monkeypatch.setattr(settings, "create_rate_limit", 1)
    short_code = client.post("/links", json=URL).json()["short_code"]

    for _ in range(3):
        response = client.get(f"/{short_code}", follow_redirects=False)
        assert response.status_code == 302