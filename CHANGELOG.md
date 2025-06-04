# Changelog
## [Unreleased]
### Added
- Initial REST API with `FastAPI`: `POST /entries`, `GET /entries`, `GET /entries/{id}`
- Server-side SQLite database (`server.db`) and Pydantic models (`server.models`)
- Client-to-server push command (`client.core.cli.push`) and API integration
- Pytest-based test suite with full coverage of CLI, archiving, server routes, storage, and models
  - Includes marker-based organization (`cli`, `routes`, `db`, `crud`, etc.) and temporary test environments
  - External services like Wayback Machine are mocked
- Initial `jinja2` web frontend for Hyperindex Yellowpages with search and pagination features
### Changed
- Refactored project layout: 
  - Split root directory into `client/` and `server/` to clearly separate the local client application from the backend API server
  - Separated database logic between `client.core.storage` (local database) and `server.db` (server-side database)

## [1.0.0] - 2025-06-02
### Added
- Full `click` CLI interface with commands: `add`, `list`, `update`, `delete`, `restore`, `trash`, `purge`, `search`, `tags`, `view`, `export`
- Local webpage archiving using `pywebcopy` and remote backup via Wayback Machine (`waybackpy`)
- SQLite-backed persistent storage
- Trash system with soft-delete, restore, and purge support
- Human-readable entry formatting for CLI display
- Local snapshot viewer (`view` command) opens archived HTML in the browser
- Entry export in JSON and CSV formats with optional inclusion of deleted entries
- Tag parsing, normalization, frequency ranking, and tag-based search via CLI
- Input validation and ISO-formatted timestamps
- Modular architecture: `core.storage`, `core.models`, `core.archive`, `core.config`