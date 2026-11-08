from app.config import settings


def test_list_links_requires_token(client):
    assert client.get("/links").status_code == 401


def test_delete_requires_token(client):
    created = client.post("/links", json={"original_url": "https://example.com/"})
    short_code = created.json()["short_code"]

    assert client.delete(f"/links/{short_code}").status_code == 401
    assert client.get(f"/links/{short_code}").status_code == 200


def test_wrong_token_rejected(client, admin_headers):
    response = client.get("/links", headers={"Authorization": "Bearer wrong"})

    assert response.status_code == 401


def test_admin_disabled_when_token_not_set(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "")

    response = client.get("/links", headers={"Authorization": "Bearer anything"})

    assert response.status_code == 401