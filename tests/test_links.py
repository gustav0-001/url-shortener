from app.config import settings

def test_create_link(client):
    response = client.post(
        "/links",
        json={"original_url": "https://example.com/"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["original_url"] == "https://example.com/"
    assert len(data["short_code"]) == 6
    assert data["clicks"] == 0

def test_get_nonexistent_link(client):
    response = client.get("/links/absent")

    assert response.status_code == 404

    assert response.json() == {"detail": "Link not found"}

def test_get_link(client):
    create_response = client.post("/links", json={"original_url": "https://example.com/"})
    created_link = create_response.json()

    short_code = created_link["short_code"]
    response = client.get(f"/links/{short_code}")

    assert response.status_code == 200

    data = response.json()

    assert data["short_code"] == short_code
    assert data["original_url"] == "https://example.com/"
    assert data["clicks"] == 0

def test_redirect(client):
    create_response = client.post("/links", json={"original_url": "https://example.com/"})
    created_link = create_response.json()
    short_code = created_link["short_code"]

    response = client.get(f"/{short_code}", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"

def test_clicks_increment(client):
    create_response = client.post("/links", json={"original_url": "https://example.com/"})
    created_link = create_response.json()
    short_code = created_link["short_code"]

    stats_before = client.get(f"/links/{short_code}").json()
    assert stats_before["clicks"] == 0

    client.get(f"/{short_code}", follow_redirects=False)

    stats_after = client.get(f"/links/{short_code}").json()
    assert stats_after["clicks"] == 1

def test_create_link_invalid_url(client):
    response = client.post("/links", json={"original_url": "not-a-url"})

    assert response.status_code == 422

def test_create_duplicate_link(client):
    first_response = client.post("/links", json={"original_url": "https://example.com/"})
    first_link = first_response.json()
    second_response = client.post("/links", json={"original_url": "https://example.com/"})
    second_link = second_response.json()

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_link["short_code"] != second_link["short_code"]

def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_different_links(client):
    first = client.post("/links", json={"original_url": "https://example.com/"})
    second = client.post("/links", json={"original_url": "https://example.org/"})

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["short_code"] != second.json()["short_code"]

def test_short_code_collision_is_retried(client, monkeypatch):
    codes = iter(["aaaaaa", "aaaaaa", "bbbbbb"])
    monkeypatch.setattr("app.services.links.generate_short_code", lambda: next(codes))

    first = client.post("/links", json={"original_url": "https://example.com/"})
    second = client.post("/links", json={"original_url": "https://example.org/"})

    assert first.json()["short_code"] == "aaaaaa"
    assert second.status_code == 201
    assert second.json()["short_code"] == "bbbbbb"


def test_create_link_returns_503_after_too_many_collisions(client, monkeypatch):
    monkeypatch.setattr("app.services.links.generate_short_code", lambda: "aaaaaa")

    first = client.post("/links", json={"original_url": "https://example.com/"})
    second = client.post("/links", json={"original_url": "https://example.org/"})

    assert first.status_code == 201
    assert second.status_code == 503

def test_redirect_nonexistent_link(client):
    response = client.get("/absent", follow_redirects=False)

    assert response.status_code == 404
    assert response.json() == {"detail": "Link not found"}


def test_delete_link(client, admin_headers):
    created = client.post("/links", json={"original_url": "https://example.com/"})
    short_code = created.json()["short_code"]

    response = client.delete(f"/links/{short_code}", headers=admin_headers)
    assert response.status_code == 204

    assert client.get(f"/links/{short_code}").status_code == 404


def test_delete_nonexistent_link(client, admin_headers):
    response = client.delete("/links/absent", headers=admin_headers)

    assert response.status_code == 404


def test_get_links(client, admin_headers):
    client.post("/links", json={"original_url": "https://example.com/"})
    client.post("/links", json={"original_url": "https://example.org/"})

    response = client.get("/links", headers=admin_headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_generate_short_code_skips_reserved(monkeypatch):
    from app.services import links

    monkeypatch.setattr(links, "RESERVED_CODES", {"aaaaaa"})
    chars = iter("aaaaaa" + "bbbbbb")
    monkeypatch.setattr(links.secrets, "choice", lambda alphabet: next(chars))

    assert links.generate_short_code() == "bbbbbb"
{"original_url": "https://example.com/"}

def test_create_link_returns_short_url(client, monkeypatch):
    monkeypatch.setattr(settings, "base_url", "https://sho.rt/")

    response = client.post("/links", json={"original_url": "https://example.com/"})
    data = response.json()

    assert data["short_url"] == f"https://sho.rt/{data['short_code']}"
    assert isinstance(data["id"], int)
    assert "created_at" in data

def test_get_links_pagination(client, admin_headers):
    for i in range(3):
        client.post("/links", json={"original_url": f"https://example.com/{i}"})

    first_page = client.get("/links", params={"limit": 2}, headers=admin_headers)
    second_page = client.get("/links", params={"limit": 2, "offset": 2}, headers=admin_headers)

    assert len(first_page.json()) == 2
    assert len(second_page.json()) == 1


def test_get_links_newest_first(client, admin_headers):
    client.post("/links", json={"original_url": "https://example.com/old"})
    client.post("/links", json={"original_url": "https://example.com/new"})

    links = client.get("/links", headers=admin_headers).json()

    assert links[0]["original_url"] == "https://example.com/new"


def test_get_links_invalid_pagination(client, admin_headers):
    assert client.get("/links", params={"limit": 0}, headers=admin_headers).status_code == 422
    assert client.get("/links", params={"limit": 1000}, headers=admin_headers).status_code == 422
    assert client.get("/links", params={"offset": -1}, headers=admin_headers).status_code == 422

def test_create_link_too_long_url(client):
    long_url = "https://example.com/" + "a" * 3000

    response = client.post("/links", json={"original_url": long_url})

    assert response.status_code == 422

def test_create_link_to_own_domain_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "base_url", "https://sho.rt")

    response = client.post("/links", json={"original_url": "https://sho.rt/abc123"})

    assert response.status_code == 422