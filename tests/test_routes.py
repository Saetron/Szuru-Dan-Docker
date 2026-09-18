import base64
import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from services.auth import extract_auth_from_request


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_proxy_path_traversal_blocked(client):
    response = client.get("/data/../../etc/passwd")
    assert response.status_code in (403, 404)


@patch("routes.posts.requests.get")
def test_counts_posts(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 5432}
    mock_get.return_value = mock_response

    response = client.get("/counts/posts.json?tags=cat")
    assert response.status_code == 200
    data = response.get_json()
    # Ensure Danbooru-compatible structure: {"counts": {"posts": 5432}}
    assert "counts" in data
    assert "posts" in data["counts"]
    assert data["counts"]["posts"] == 5432


def test_favorites_empty_post_id_no_crash(client):
    # Verifies that empty search[post_id] does NOT crash with 500 ValueError
    response = client.get("/favorites.json")
    assert response.status_code == 200
    assert response.get_json() == []


def test_auth_extraction_with_colon_in_password(app):
    # Test Basic Auth with username:password_with:colon
    credentials = "myuser:pass:word:123"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")

    with app.test_request_context(
        "/posts.json",
        headers={"Authorization": f"Basic {encoded}"},
    ):
        login, api_key = extract_auth_from_request()
        assert login == "myuser"
        assert api_key == "pass:word:123"
