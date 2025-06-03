import pytest
from client.core.models import Entry

pytestmark = pytest.mark.unit

def test_entry_str_formatting():
    entry = Entry(
        id=123,
        url="https://example.com",
        title="Test",
        tags=["a", "b"],
        description="desc",
        date_added="2024-01-01",
        archived_url="https://archive.org/123",
        snapshot_dir="/path/to/snapshot"
    )
    output = str(entry)
    assert "ID: 123" in output
    assert "Title: Test" in output
    assert "Tags: a, b" in output
    assert "Archived URL: https://archive.org/123" in output