import tempfile
from pathlib import Path
import pytest

from click.testing import CliRunner

from client.core.cli import cli
from client.core.config import Config
from client.core.storage import init_db


pytestmark = pytest.mark.cli


@pytest.fixture(scope="function")
def runner_with_temp_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tempdir:
        test_dir = Path(tempdir)
        Config.set_test_config(test_dir)
        init_db()
        runner = CliRunner()
        yield runner


def test_add_and_list_entry(runner_with_temp_db):
    result = runner_with_temp_db.invoke(cli, [
        "add", "https://example.com", "Example Title", "--tags", "news,tech", "--desc", "Example description", "--strategy", "none"
    ])
    assert "Entry added." in result.output

    list_result = runner_with_temp_db.invoke(cli, ["list"])
    assert "Example Title" in list_result.output


def test_update_entry(runner_with_temp_db):
    runner_with_temp_db.invoke(cli, [
        "add", "https://example.com", "Old Title", "--strategy", "none"
    ])
    result = runner_with_temp_db.invoke(cli, [
        "update", "1", "--title", "New Title"
    ])
    assert "Updated entry ID 1." in result.output


def test_delete_and_restore_entry(runner_with_temp_db):
    runner_with_temp_db.invoke(cli, [
        "add", "https://example.com", "Deletable", "--strategy", "none"
    ])
    delete_result = runner_with_temp_db.invoke(cli, ["delete", "1"])
    assert "Deleted" in delete_result.output

    trash_result = runner_with_temp_db.invoke(cli, ["trash"])
    assert "Deletable" in trash_result.output

    restore_result = runner_with_temp_db.invoke(cli, ["restore", "1"])
    assert "Restored entry ID 1." in restore_result.output


def test_tags_and_export(runner_with_temp_db):
    runner_with_temp_db.invoke(cli, [
        "add", "https://example.com", "Tagged", "--tags", "cli,test", "--strategy", "none"
    ])
    tags_result = runner_with_temp_db.invoke(cli, ["tags"])
    assert "cli: 1" in tags_result.output
    assert "test: 1" in tags_result.output

    export_result = runner_with_temp_db.invoke(cli, ["export", "--format", "json"])
    assert "export.json" in export_result.output


def test_search_and_purge(runner_with_temp_db):
    runner_with_temp_db.invoke(cli, [
        "add", "https://example.com", "Searchable", "--desc", "Find me", "--strategy", "none"
    ])
    search_result = runner_with_temp_db.invoke(cli, ["search", "--query", "Find"])
    assert "Searchable" in search_result.output

    runner_with_temp_db.invoke(cli, ["delete", "1"])
    purge_result = runner_with_temp_db.invoke(cli, ["purge"])
    assert "Purged deleted entries." in purge_result.output