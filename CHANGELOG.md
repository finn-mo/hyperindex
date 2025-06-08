## [Unreleased]
### Added
- Full web-first workflow:
  - New `/rolodex` dashboard for managing personal bookmarks
  - New `/` Yellowpages view for browsing admin-approved public entries
  - Entry submission system: users submit, admins approve for Yellowpages inclusion
- Role system:
  - Admin-only approval and editing of public entries via `/admin`
  - Admins manage Yellowpages entries via forks of user-submitted entries
- Forking logic for public entries:
  - Approved entries are cloned from user submissions
  - Public entries are marked with `is_public_copy=True`
  - Original user entry ID tracked in `original_id` for audit/history
- Tag-aware search:
  - Combined keyword + tag filtering
  - Tags now link to filtered views across index and dashboard
- Template and accessibility improvements:
  - Added ARIA attributes, `.sr-only`, and proper `:focus` state

### Changed
- Public index (`/`) now shows only admin-managed (approved) entries
- Distinct view styling:
  - `yellowpages.css` for public index
  - `rolodex.css` for personal dashboard
- Refactored project layout:
  - Separated views into `views/rolodex.py`, `views/directory.py`, `views/admin.py`
  - Moved business logic into `services/entries.py`, `services/users.py`
  - Created `utils/tags.py` for reusable tag parsing and cleaning
- Schema and ORM alignment:
  - Renamed `description` → `notes`
  - Converted notes field to `Text`
  - Enforced `url` and `title` as non-null
- Security & access control:
  - Prevented editing of already-submitted entries
  - Wrapped commits in `try/except` with rollback safety
- Deprecated CLI mode:
  - Removed CLI references from UI and documentation

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
  - Moved CLI and server into separate directories (`client/`, `server/`)
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