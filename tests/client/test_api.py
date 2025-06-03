import pytest
import requests
from unittest.mock import patch
from client.core.models import Entry
from client.core.config import Config

@pytest.fixture
def sample_entry():
    return Entry(
        id=1,
        url="https://example.com",
        title="Example",
        tags=["test"],
        description="A test entry.",
        date_added="2024-01-01T00:00:00Z"
    )

@pytest.mark.client
@pytest.mark.api
def test_push_entry_success(sample_entry):
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.raise_for_status = lambda: None

        payload = {
            "url": sample_entry.url,
            "title": sample_entry.title,
            "tags": sample_entry.tags,
            "description": sample_entry.description
        }

        response = requests.post(f"{Config.API_URL}/entries", json=payload)
        response.raise_for_status()
        assert response.status_code == 201
        mock_post.assert_called_once_with(f"{Config.API_URL}/entries", json=payload)