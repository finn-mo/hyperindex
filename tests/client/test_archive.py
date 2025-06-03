import pytest
from unittest.mock import patch

from client.core.archive import archive_url


pytestmark = pytest.mark.client


def test_archive_url_none():
    result = archive_url("https://example.com", ["none"])
    assert result["archived_url"] == ""
    assert result["snapshot_dir"] == ""


def test_archive_url_invalid_strategy():
    with pytest.raises(RuntimeError, match="Invalid archiving strategies"):
        archive_url("https://example.com", ["invalid"])


def test_archive_url_none_conflict():
    with pytest.raises(RuntimeError, match="'none' cannot be combined"):
        archive_url("https://example.com", ["none", "pywebcopy"])


@patch("client.core.archive.archive_with_pywebcopy")
def test_archive_url_pywebcopy(mock_archive):
    mock_archive.return_value = {"snapshot_dir": "/fake/path"}
    result = archive_url("https://example.com", ["pywebcopy"])
    assert result["snapshot_dir"] == "/fake/path"
    mock_archive.assert_called_once()


@patch("client.core.archive.archive_with_wayback")
def test_archive_url_wayback(mock_archive):
    mock_archive.return_value = {"archived_url": "https://archive.org/fake"}
    result = archive_url("https://example.com", ["wayback"])
    assert result["archived_url"] == "https://archive.org/fake"
    mock_archive.assert_called_once()


@patch("client.core.archive.archive_with_pywebcopy")
@patch("client.core.archive.archive_with_wayback")
def test_archive_url_both(mock_wayback, mock_pywebcopy):
    mock_pywebcopy.return_value = {"snapshot_dir": "/snap"}
    mock_wayback.return_value = {"archived_url": "https://archive.org/fake"}
    result = archive_url("https://example.com", ["pywebcopy", "wayback"])
    assert result["snapshot_dir"] == "/snap"
    assert result["archived_url"] == "https://archive.org/fake"