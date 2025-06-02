# Changelog
## [Unreleased]
### Planned
- PDF/image archival support
- REST API exposure
- Web frontend for a curated "Internet Yellowpages" based on user submissions
- Pytest-based test suite

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