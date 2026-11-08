def test_index_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "SHORTLINK" in response.text

def test_static_assets_served(client):
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200

def test_static_is_reserved_code():
    from app.services.links import RESERVED_CODES

    assert "static" in RESERVED_CODES