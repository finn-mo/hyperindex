import pytest

from fastapi.testclient import TestClient

from server.api.main import app


client = TestClient(app)
pytestmark = pytest.mark.routes


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_entries_requires_auth():
    response = client.get("/entries")
    assert response.status_code == 401


def test_create_entry_api():
    entry = {
        "url": "https://example.com",
        "title": "Example Site",
        "tags": ["tag1", "tag2"],
        "description": "An example"
    }
    headers = {"Authorization": "Bearer example-token"}
    response = client.post("/entries", json=entry, headers=headers)
    assert response.status_code == 200


def test_list_entries():
    headers = {"Authorization": "Bearer example-token"}
    response = client.get("/entries", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
