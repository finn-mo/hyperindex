import pytest

from fastapi.testclient import TestClient

from server.api.main import app


pytestmark = pytest.mark.security

client = TestClient(app)


def test_list_entries_unauthorized():
    response = client.get("/entries")
    assert response.status_code == 401


def test_list_entries_authorized():
    headers = {"Authorization": "Bearer example-token"}
    response = client.get("/entries", headers=headers)
    assert response.status_code == 200