# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-04-04

### Added
- **MCP Server** (`agxr-mcp`): FastMCP-based server exposing 9 MCP tools for Claude Code integration
  - `start_session`, `end_session`, `send_message`, `get_session_history`, `reset_session`
  - `execute_query`, `check_run_status`, `list_profiles`, `get_server_info`
- **Sessions API** support in `AgenticAPIClient`:
  - `create_session(user_reference, ...)` — `POST /sessions`
  - `terminate_session(session_reference)` — `POST /sessions/terminate`
- **`AgentSession`** class for MCP-level session state management
- **Interactive Chat Mode**: REPL-style chat interface with persistent sessions and auto-generated session IDs
- **Special Commands**: Runtime control with `#help`, `#new`, `#info`, `#clear`, `#debug`, `#stream`
- **Profile Management**: Store and manage multiple credential sets in `~/.kore/profiles`
- **Enhanced Debug Modes**: `all`, `function-call`, and `thoughts` debug modes via `--debug-mode`
- **Advanced Logging**: Python standard library logging with `--log-file` and `--log-level`
- `fastmcp>=2.0` dependency; `agxr-mcp` CLI entry point in `pyproject.toml`
- New `SessionStatus` enum, `SessionResponse`, `CreateSessionRequest`, `TerminateSessionRequest` TypedDicts in `api_reference.py`
- `build_sessions_url()` and `build_terminate_session_url()` URL builder functions
- Optional `is_async`, `callback_url`, `callback_token` parameters on `execute_run()`

### Changed
- **`AgentTestSession`**: now uses the Sessions API for proper server-side lifecycle
  - `__init__` calls `create_session()` to establish a real Kore.ai session
  - `session_id` property now returns the API-assigned `sessionReference` (not a local UUID)
  - `reset()` performs a true server-side context reset (terminate + recreate)
  - `close()` terminates the Kore.ai session before closing the HTTP client
  - `profile` parameter type changed from `str` to `Optional[str]` (env vars supported)
- Exports `AgentTestSession`, `AgentSession`, `AgenticMCPServer` from `agxr.__init__`

### Fixed
- `create_session()` now handles environments (e.g. UAT_Chat) that wrap the response under a
  `"session"` key and return `sessionReference: null` — falls back to `sessionId` automatically

## [0.1.0] - 2026-02-12

### Added
- Initial release
- Package structure with proper Python packaging
- API reference module with TypedDict definitions
- Enums for StreamMode, DebugMode, and RunStatus
- URL builder functions for API endpoints
- CLI entry point (placeholder implementation)
- Development tooling configuration (pytest, mypy, ruff, black)
- MIT License
- README with usage examples
- Type hints and comprehensive documentation

### Documentation
- API documentation in project memory
- Type reference in api_reference.py
- Usage examples in README
- Development setup instructions

[Unreleased]: https://github.com/dgwartney/agentic-app-cli/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/dgwartney/agentic-app-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/dgwartney/agentic-app-cli/releases/tag/v0.1.0
