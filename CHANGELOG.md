# Changelog
## [2.0.0] - 2025-06-04
### Added
- Introduced REST API server using `FastAPI`, supporting `POST /entries`, `GET /entries`, and `GET /entries/{id}`
- Server-side SQLite database (`server.db`) and Pydantic models (`server.models`)
- Client-to-server push command (`client.core.cli.push`) and API integration
- Pytest-based test suite with full coverage of CLI, archiving, server routes, storage, and models
  - Includes marker-based organization (`cli`, `routes`, `db`, `crud`, etc.) and temporary test environments
  - External services like Wayback Machine are mocked
- Added lightweight `Jinja2` web frontend for Hyperindex Yellowpages with keyword search and pagination

### Changed
- Refactored project structure:
  - Moved CLI and server into separate directories (`client/` and `server/`) to isolate responsibilities
  - Split database logic: `client.core.storage` for local entries, `server.db` for shared/public entries

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

[2.0.0]: https://github.com/finn-mo/hyperindex/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/finn-mo/hyperindex/releases/tag/v1.0.0