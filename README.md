# Hyperindex – Internet Rolodex and Yellowpages
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Last Commit](https://img.shields.io/github/last-commit/finn-mo/hyperindex.svg)](https://github.com/finn-mo/hyperindex/commits/main)  
Hyperindex lets you build a personal web directory from the command line. Bookmark and tag important sites, archive full-page snapshots and Wayback Machine links, browse your curated index offline or push to the Hyperindex server powered by the built-in REST API.

## Features
Hyperindex consists of:
- A local CLI client (`client/`) for bookmarking, archiving, and managing entries
- REST API server (`server/`) for syncing and retrieving entries remotely

### CLI Client
- Save full-page offline snapshots with `pywebcopy`
- Backup URLs to the Wayback Machine using `waybackpy`
- Organize links with tags, descriptions, and timestamps
- Search entries by keywords or tags
- Soft-delete entries with restore and purge support
- Export entries to JSON or CSV (optionally including deleted)
- Browse snapshots locally via the `view` command
- Track tag usage frequency via `tags` report
- Push a local entry to the server via the REST API

### REST API Server
- Built with [`FastAPI`](https://fastapi.tiangolo.com/)
- Accepts entries from CLI (`POST /entries`)
- Lists all entries (`GET /entries`)
- Retrieves specific entries (`GET /entries/{id}`)

## Installation
```bash
git clone https://github.com/finn-mo/hyperindex.git
cd hyperindex
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

To update `requirements.txt`, modify `requirements.in` and run:
```bash
pip-compile
```
*(Requires [pip-tools](https://github.com/jazzband/pip-tools))*

## Usage
### CLI
From the `client/` directory or via `python -m client.main`:
```bash
python -m client.main [COMMAND] [OPTIONS]
```

Entry management:
- `add <url> <title> [--tags TAGS] [--desc TEXT] [--strategy STRATEGY]`: Add and archive a new entry (`STRATEGY` can be `pywebcopy`, `wayback`, or `none`)
- `update <id> [--title TEXT] [--tags TAGS] [--desc TEXT] [--add-tags TAGS] [--remove-tags TAGS]`: Modify an entry
- `delete <id>`: Soft-delete an entry
- `restore <id>`: Restore a soft-deleted entry
- `list [--include-deleted]`: List all active entries
- `view <id>`: Open the local archived snapshot

Search and metadata:
- `search [--query TEXT] [--tag TAG]`
- `tags`: List all tags with usage counts

Trash handling:
- `trash`: View deleted entries
- `purge`: Permanently delete all soft-deleted entries

Export and share:
- `export --format [json|csv] [--include-deleted]`: Export entries
- `push <id>`: Push local entry to the Hyperindex server (`POST /entries`)

### API
Start the server:
```bash
uvicorn server.main:app --reload
```

Example requests:
```bash
curl http://localhost:8000/entries            # List entries
curl http://localhost:8000/entries/1          # View one entry
http POST http://localhost:8000/entries \     # Add a new entry
    url="https://example.com" \
    title="Example Site" \
    tags:='["reference", "sample"]' \
    description="A sample entry"
```

## Data Storage
### Client
Hyperindex saves data to:
- `~/.hyperindex/rolodex.db`
- `~/.hyperindex/snapshots/`
- `~/.hyperindex/exports/`

### Server
- `server/data/yellowpages.db` (configurable via `HYPERINDEX_SERVER_DB`)

## Roadmap
- Web frontend for a curated "Internet Yellowpages" based on user submissions
- Client-side PDF/image archival support
- Advanced REST API auth (OAuth, user-specific roles)
- Server-side tag management enhancements

## Testing
Hyperindex includes a comprehensive [pytest](https://docs.pytest.org/) suite covering the CLI client, server routes, database logic, and archiving utilities.

### Running Tests
```bash
pytest                           # Run all tests
pytest -m cli                    # Run only CLI tests
pytest -m routes                 # API route tests
```

### Test Structure
Tests are organized with `pytest.ini` markers:
- `cli`, `client`, `storage`: Local CLI functionality
- `db`, `crud`, `routes`: Server-side components
- `unit`, `slow`, `security`: Misc categories
Tests run in temporary environments and mock all external services.

## License
Licensed under the [MIT License](LICENSE).