from datetime import datetime, timezone
from pathlib import Path
import requests
from urllib.parse import urlparse
import webbrowser

import click

from client.core.archive import archive_url
from client.core.config import Config
from client.core.models import Entry
from client.core.storage import (
    add_entry,
    count_tags,
    delete_entry,
    export_entries_json,
    export_entries_csv,
    get_entry,
    list_entries,
    list_deleted_entries,
    purge_deleted_entries,
    restore_entry,
    search_entries,
    update_entry
)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("url")
@click.argument("title")
@click.option("--tags", help="Comma-separated tags")
@click.option("--desc", help="Description")
@click.option(
    "--strategy", type=str, default="pywebcopy", show_default=True,
    help="Comma-separated archive strategies: none, pywebcopy, wayback"
)
def add(url, title, tags, desc, strategy):
    """Add a new entry to the rolodex."""
    parsed = urlparse(url)
    if not (parsed.scheme in ("http", "https") and parsed.netloc):
        click.echo("Invalid URL")
        return
    tag_list = [t.strip().lower() for t in (tags or "").split(",") if t.strip()]
    strategy_list = [s.strip().lower() for s in strategy.split(",") if s.strip()]
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    try:
        result = archive_url(url, strategy_list)
    except RuntimeError as e:
        click.echo(str(e))
        return
    entry = Entry(
        url=url,
        title=title,
        tags=tag_list,
        description=desc or "",
        date_added=now,
        archived_url=result.get("archived_url", ""),
        snapshot_dir=result.get("snapshot_dir", "")
    )
    add_entry(entry)
    click.echo("Entry added.")


@cli.command()
@click.argument("entry_id", type=int)
@click.option("--title", help="New title")
@click.option("--tags", help="New tags (comma-separated)")
@click.option("--desc", help="New description")
@click.option("--add-tags", help="Tags to add (comma-separated)")
@click.option("--remove-tags", help="Tags to remove (comma-separated)")
def update(entry_id, title, tags, desc, add_tags, remove_tags):
    """Edit an existing Rolodex entry."""
    add_tags = add_tags.split(",") if add_tags else None
    remove_tags = remove_tags.split(",") if remove_tags else None
    success = update_entry(entry_id, title, tags, desc, add_tags, remove_tags)
    if success:
        click.echo(f"Updated entry ID {entry_id}.")
    else:
        click.echo("Invalid ID.")


@cli.command()
@click.argument("entry_id", type=int)
def delete(entry_id):
    """Delete an entry from the Rolodex."""
    entry = get_entry(entry_id)
    if not entry:
        click.echo("Invalid ID.")
        return
    deleted = delete_entry(entry_id)
    if deleted:
        click.echo(f"Deleted: {entry.title}")

@cli.command()
@click.argument("entry_id", type=int)
def restore(entry_id):
    """Restore a deleted entry from the trash."""
    success = restore_entry(entry_id)
    if success:
        click.echo(f"Restored entry ID {entry_id}.")
    else:
        click.echo("Invalid ID.")


@cli.command(name="list")
@click.option("--include-deleted", is_flag=True, help="Include deleted entries")
def list_command(include_deleted):
    """List all entries in the Rolodex."""
    entries = list_entries(include_deleted=include_deleted)
    if not entries:
        click.echo("Your Rolodex is empty.")
        return
    for entry in entries:
        click.echo(f"{entry}\n")


@cli.command()
@click.option("--query", help="Search term")
@click.option("--tag", help="Search tag")
def search(query, tag):
    """Search for entries by query or tag."""
    entries = search_entries(query, tag)
    if not entries:
        click.echo("No results found.")
        return
    for entry in entries:
        click.echo(f"{entry}\n")


@cli.command()
def tags():
    """List all entry tags ranked by use frequency."""
    tag_counts = count_tags()
    if not tag_counts:
        click.echo("No tags found.")
        return
    for tag, count in tag_counts.most_common():
        click.echo(f"{tag}: {count}")


@cli.command()
def trash():
    """List all entries in the trash."""
    entries = list_deleted_entries()
    if not entries:
        click.echo("Trash is empty.")
        return
    for entry in entries:
        click.echo(f"{entry}\n")


@cli.command()
def purge():
    """Permanently delete all entries in the trash."""
    purge_deleted_entries()
    click.echo("Purged deleted entries.")


@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]), default="json", show_default=True)
@click.option("--include-deleted", is_flag=True, help="Include deleted entries")
def export(format, include_deleted):
    """Export a JSON or CSV log of the Rolodex."""
    if format == "json":
        path = export_entries_json(include_deleted=include_deleted)
    else:
        path = export_entries_csv(include_deleted=include_deleted)
    click.echo(f"Exported to {path}")


@cli.command()
@click.argument("entry_id", type=int)
def view(entry_id):
    """View a local backup of an archived site in the web browser."""
    entry = get_entry(entry_id)
    if not entry or not entry.snapshot_dir:
        click.echo("Snapshot not found.")
        return
    if not Path(entry.snapshot_dir).is_dir():
        click.echo("Invalid snapshot directory.")
        return
    matches = list(Path(entry.snapshot_dir).rglob("index.html"))
    if not matches:
        click.echo("Snapshot file missing.")
        return
    snapshot_path = matches[0]
    webbrowser.open(snapshot_path.as_uri())
    click.echo("Opened in browser.")


@cli.command()
@click.argument("entry_id", type=int)
@click.option("--token", envvar="HYPERINDEX_TOKEN", help="Bearer token for authentication")
def push(entry_id, token):
    """Push a local entry to the remote Yellowpages server."""
    entry = get_entry(entry_id)
    if not entry:
        click.echo("Entry not found.")
        return

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "url": entry.url,
        "title": entry.title,
        "tags": entry.tags,
        "description": entry.description
    }

    try:
        response = requests.post(f"{Config.API_URL}/entries", json=payload, headers=headers)
        response.raise_for_status()
        click.echo(f"Pushed: {entry.title}")
    except requests.RequestException as e:
        click.echo(f"Failed to push entry: {e}")