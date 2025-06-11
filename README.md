# Hyperindex – Internet Rolodex and Yellow Pages
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Last Commit](https://img.shields.io/github/last-commit/finn-mo/hyperindex?cacheSeconds=3600)](https://github.com/finn-mo/hyperindex/commits/main)  
Hyperindex is a lightweight web app for curating and sharing independent websites. Inspired by the early internet, it lets users build a personal Rolodex and explore a shared Yellow Pages of user-submitted sites. Designed for the indie web and independent browsing. Built with FastAPI, Jinja2, and SQLite.

## Features
- **Personal Rolodex** (`/rolodex`) — view, add, edit, and delete your own bookmarks
- **Public Yellow Pages** (`/`) — browse entries shared by all users
- **User authentication** — register and log in to manage personal entries
- **Tagging and full-text search** — fast, SQLite FTS-backed search on both personal and public entries, with filtering and pagination
- **Submission system** — users submit entries for admin review
- **Paginated directory** — browse entries in a classic "directory" format
- **Moderation model** — admins approve submissions by forking them into public copies; users retain control over their original entries
- **Unified navigation bar** — easily switch between public, personal, and admin views
- **Fast and lightweight** — built with FastAPI + Jinja2 + SQLite

## Roles
| Role  | Add/Edit/Delete Own  | Submit to Public  | Edit Approved Public  | Approve/Reject |
|-------|----------------------|-------------------|-----------------------|----------------|
| User  | Yes                  | Yes               | No                    | No             |
| Admin | Yes                  | Yes               | Yes (forked copy only)| Yes            |


## Installation
```bash
git clone https://github.com/finn-mo/hyperindex.git
cd hyperindex
python -m venv venv                     # Requires Python 3.12+
source venv/bin/activate                # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

To update `requirements.txt`, modify `requirements.in` and run:
```bash
pip-compile
```
*(Requires [pip-tools](https://github.com/jazzband/pip-tools))*

## Usage
Start the server:
```bash
uvicorn server.api.main:app --reload   # Entry point: FastAPI app
```
Once running, visit `http://localhost:8000/` in your browser to access the web interface.

## File Structure
```
server/
├── api/            # API entrypoint (main FastAPI app)
├── views/          # Web routes (auth, rolodex, yellowpages, admin)
├── templates/      # Jinja2 templates for HTML rendering
├── static/         # CSS and other frontend assets
├── models/         # SQLAlchemy + Pydantic models (entities, schemas)
├── services/       # Business logic (e.g., EntryService, FTS-backed search)
├── utils/          # Shared helpers (e.g., tag parsing)
├── db/             # Database connection setup
├── security.py     # Auth + token creation/verification
└── settings.py     # Environment config (uses pydantic-settings)

tests/
├── conftest.py     # Pytest fixtures (DB, user, token, client)
├── test_auth.py    # Login, logout, registration tests
├── test_entries.py # Entry creation, filtering, tag logic tests
└── test_routes.py  # Route-level behavior tests (access, redirects)
```

## Testing
Hyperindex includes a [pytest](https://docs.pytest.org/) suite covering server routes. Coverage reporting is handled via `pytest-cov` (automatically configured via `pytest.ini`).

To run tests:
```bash
pytest
```
The suite includes:
- Fixtures for test database, users, and tokens
- Authentication flow tests (login, logout, protected access)
- Full coverage of core services (EntryService, tag filtering, etc.)
- Enforces a minimum 70% coverage threshold via `pytest.ini`

## Environment
- SQLite by default (`./server/db/hyperindex.db`)
- `.env` supported for environment overrides (e.g. `DATABASE_URL`, `SECRET_KEY`)

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License
Licensed under the [MIT License](LICENSE).