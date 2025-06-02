# Hyperindex – CLI-based internet Rolodex
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Last Commit](https://img.shields.io/github/last-commit/finn-mo/hyperindex.svg)](https://github.com/finn-mo/hyperindex/commits/main)  
Hyperindex lets you build a personal web directory from the command line. Bookmark and tag important sites, archive full-page snapshots and Wayback Machine links, and browse your curated index offline.

## Features
- Save full-page offline snapshots with `pywebcopy`
- Backup URLs to the Wayback Machine using `waybackpy`
- Organize links with tags, descriptions, and timestamps
- Search entries by keywords or tags
- Soft-delete entries with restore and purge support
- Export entries to JSON or CSV (optionally including deleted)
- Browse snapshots locally via the `view` command
- Track tag usage frequency via `tags` report

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
*(Note: [pip-tools](https://github.com/jazzband/pip-tools) is required to modify dependencies.)*

## Usage
```bash
python main.py [COMMAND] [OPTIONS]
```

Entry management:
- `add <url> <title> [--tags TAGS] [--desc TEXT] [--strategy STRATEGY]`: Add and archive a new entry
  - `--strategy STRATEGY`: Archive methods (e.g. `pywebcopy`, `wayback`, or `none`)
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

Export:
- `export --format [json|csv] [--include-deleted]`: Export entries

## Data Storage
Hyperindex saves data to:
- `~/.hyperindex/rolodex.db`
- `~/.hyperindex/snapshots/`
- `~/.hyperindex/exports/`

## Roadmap
- Pytest-based test suite
- PDF/image archival support
- REST API exposure
- Web frontend for a curated "Internet Yellowpages" based on user submissions

## License
Licensed under the [MIT License](LICENSE).