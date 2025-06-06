# Hyperindex – Internet Rolodex and Yellowpages
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Last Commit](https://img.shields.io/github/last-commit/finn-mo/hyperindex.svg)](https://github.com/finn-mo/hyperindex/commits/main)  
Hyperindex lets you build a personal internet directory and browse a shared, user-curated index through a lightweight web interface. It features a personal dashboard and public directory powered by FastAPI and Jinja2. Add, tag, and annotate bookmarks, then browse or search them from your browser. Hyperindex supports multi-user login, and fast, tag-aware filtering.

## Features
- **User authentication** — register and log in to manage your own entries
- **Personal dashboard** (`/dashboard`) — view, add, edit, and delete your own bookmarks
- **Public Yellowpages** (`/`) — browse entries shared by all users
- **Taggable, searchable entries** — filter results by tag and keyword
- **Paginated directory** — browse entries in a classic "directory" format
- **Fast and lightweight** — built with FastAPI + Jinja2 + SQLite

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
### API
Start the server:
```bash
uvicorn server.main:app --reload
```
Once running, visit `http://localhost:8000/` in your browser to access the web interface.

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
- SQLite database: `hyperindex.db` (default)
- Configurable via `HYPERINDEX_SERVER_DB` environment variable

## Roadmap
- PDF/image archival support
- OAuth or token-based API access
- Tag insights, summaries, and filtering tools

## Testing
Hyperindex includes a comprehensive [pytest](https://docs.pytest.org/) suite covering the CLI client, server routes, database logic, and archiving utilities.

### Running Tests
```bash
pytest                           # Run all tests
pytest -m routes                 # API route tests
```

### Test Structure
Tests are organized with `pytest.ini` markers:
- `db`, `crud`, `routes`: Server-side components
- `unit`, `slow`, `security`: Misc categories
Tests run in temporary environments and mock all external services.

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License
Licensed under the [MIT License](LICENSE).