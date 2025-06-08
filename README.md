# Hyperindex – Internet Rolodex and Yellow Pages
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Last Commit](https://img.shields.io/github/last-commit/finn-mo/hyperindex.svg)](https://github.com/finn-mo/hyperindex/commits/main)  
Hyperindex is a lightweight web app for curating and sharing independent websites. Inspired by the early internet, it lets users build a personal Rolodex and explore a shared Yellow Pages of user-submitted sites. Designed for the indie web and independent browsing. Built with FastAPI, Jinja2, and SQLite.

## Features
- **Personal Rolodex** (`/rolodex`) — view, add, edit, and delete your own bookmarks
- **Public Yellow Pages** (`/`) — browse entries shared by all users
- **User authentication** — register and log in to manage your own entries
- **Tagging and search** — with fast filtering and pagination
- **Submission system** — users submit entries for admin review
- **Paginated directory** — browse entries in a classic "directory" format
- **Moderation model** — Admins approve submissions by forking them into public copies; users retain control over their original entries
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
Start the server:
```bash
uvicorn server.main:app --reload
```
Once running, visit `http://localhost:8000/` in your browser to access the web interface.

## File Structure
```
server/
├── main.py               # Entry point
├── views/                # HTML-facing routes
│   ├── rolodex.py
│   ├── directory.py
│   └── admin.py
├── api/                  # JSON-only APIs
│   ├── auth.py
│   └── user.py
├── services/             # Core business logic
│   ├── entries.py
│   └── users.py
├── models/
│   ├── entities.py       # SQLAlchemy models
│   └── schemas.py        # Pydantic DTOs
├── templates/
└── static/
```

## Testing
Hyperindex includes a [pytest](https://docs.pytest.org/) suite covering server routes.

To run tests:
```bash
pytest
```

## Environment
- SQLite by default (`hyperindex.db`)
- Configurable via `HYPERINDEX_SERVER_DB`
- `.env` supported if using with deployment

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License
Licensed under the [MIT License](LICENSE).