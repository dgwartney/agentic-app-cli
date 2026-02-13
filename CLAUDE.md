# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an agentic application CLI tool built with Python 3.12+. The project uses `uv` for fast, reliable Python package management and dependency resolution.

## Development Setup

This project uses `uv` for Python package management. If you need to set up the environment:

```bash
# Create/activate virtual environment (uv handles this automatically)
uv venv
source .venv/bin/activate

# Install dependencies
uv sync

# Add new dependencies
uv add <package-name>

# Add development dependencies
uv add --dev <package-name>
```

## Running the Application

```bash
# Run the main application
uv run main.py

# Or activate the venv and run directly
source .venv/bin/activate
python main.py
```

## Project Configuration

- **Python Version**: 3.12+ (specified in `.python-version`)
- **Package Manager**: uv (modern, fast alternative to pip/poetry)
- **Project Config**: `pyproject.toml` contains all project metadata and dependencies
- **Virtual Environment**: `.venv` directory (automatically created by uv)

## Kore.ai API Integration

This CLI tool integrates with the Kore.ai Agentic App Platform API to execute and manage AI agent runs.

### API Documentation Locations

- **Comprehensive Documentation**: `/Users/dgwartney/.claude/projects/-Users-dgwartney-git-agentic-app-cli/memory/kore-ai-api.md`
  - Complete API reference with request/response schemas
  - Usage examples and best practices
  - Error handling guidelines

- **Type Definitions**: `api_reference.py` (project root)
  - Python type hints using TypedDict
  - Constants (BASE_URL, etc.)
  - Enums for valid values (StreamMode, DebugMode, RunStatus)
  - URL builder functions
  - Example request objects

### Key API Concepts

- **Base URL**: `https://agent-platform.kore.ai/api/v2`
- **Authentication**: API key via `x-api-key` header
- **Session Identity**: Maintains conversation continuity across requests
- **Execution Modes**: Synchronous (default) or asynchronous
- **Streaming**: Supports token-by-token, message, or custom event streaming

### API Endpoints

1. **Execute Run**: `POST /apps/<AppID>/environments/<EnvName>/runs/execute`
   - Execute agentic app with query or direct agent invocation
   - Supports streaming, debug modes, file attachments

2. **Find Run Status**: `POST /apps/<AppID>/environments/<EnvName>/runs/<runId>/status`
   - Check status of asynchronous runs
   - Returns pending/running/success/failed status

### Configuration Requirements

The following credentials must be configured (via environment variables or config file):
- API Key
- App ID
- Environment Name

**Security Note**: Never hardcode credentials in source code.

## Planned Features & Tasks

The following features are planned for future implementation:

*(No planned tasks at this time)*

## Completed Features

### ✅ Task 1: Python standard library logging
- Added comprehensive logging with Python's standard library
- Supports log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File output with `--log-file` option
- Console logging with proper formatting
- Masked sensitive data in logs

### ✅ Task 2: Profile-based configuration support
- Profile management commands (add, list, delete, set-default)
- Secure storage in `~/.kore/` with 0600/0700 permissions
- Configuration precedence: CLI args > Env vars > Profiles > Defaults
- Interactive and CLI-based profile creation
- API key masking in list output

### ✅ Task 3: Enhanced debug option with debugMode support
- Updated `DebugMode` enum with `ALL`, `FUNCTION_CALL`, and `THOUGHTS` values
- Added `debugMode` field to `DebugConfig` TypedDict
- Implemented `--debug-mode` CLI option with choices: "all", "function-call", "thoughts"
- `--debug` flag alone sends `{"debug": {"enable": true}}` (backward compatible, no debugMode field)
- `--debug --debug-mode <mode>` sends `{"debug": {"enable": true, "debugMode": "<mode>"}}`
- `--debug-mode` requires `--debug` to be set (CLI-level validation)
- Debug information display in CLI output (summary in normal mode, details in verbose)
- Comprehensive test coverage for all debug modes (128 tests passing)
- Type-safe implementation with ValidationError for invalid modes
- API validates debugMode values server-side; client passes through user choice
- **Note:** Based on testing, API may require "thoughts" mode; other modes available for future compatibility

### ✅ Task 4: Create interactive chat command
- Implemented `chat` command with interactive REPL-style interface
- Auto-generates session ID (UUID-based: `chat-{uuid4}`) - upgraded in Task 6
- Maintains conversation context throughout session
- Multiple exit options: 'exit', 'quit', 'q', Ctrl+D, Ctrl+C
- Welcome banner with session info display
- Support for all execute options (--stream, --debug, --user-id, --metadata)
- Error resilient: API errors display but don't end chat session
- Empty input handling: skips silently and re-prompts
- Clean shutdown with goodbye message
- 12 comprehensive tests covering all scenarios

### ✅ Task 5: Implement special commands in chat mode
- Added special commands with '#' prefix for in-chat control
- Commands: #help, #new, #info, #clear, #debug, #stream, #history (placeholder)
- Dict-based command dispatch with aliases (#new/#newsession, #info/#session)
- State management: toggle debug/stream modes during chat without restarting
- Session management: #new generates fresh session with new ID for new context
- Case-insensitive commands and arguments for better UX
- Graceful error handling for unknown commands (shows helpful message, continues chat)
- Exit chat using 'exit', 'quit', or 'q' (no # prefix for simplicity/REPL convention)
- 13 comprehensive tests covering all commands, state changes, and edge cases
- Integration: Special command check inserted into chat loop before exit check
- Updated welcome banner to mention '#help' for discoverability
- ~230 lines of implementation code across dispatcher and 7 command handlers

### ✅ Task 6: Auto-generate session ID for chat command
- UUID-based session ID generation with format: `chat-{uuid4}`
- Guaranteed uniqueness across all sessions
- Auto-generates session ID when chat command starts (no --session-id needed)
- User can override with `--session-id` option for custom IDs
- Session ID displayed in welcome banner
- Session ID consistent throughout chat session
- #new command generates new UUID-based session ID
- Updated from timestamp-based to UUID-based for better uniqueness guarantees
- Test updated to mock uuid.uuid4() instead of time.time()

### ✅ Task 7: Add #new command to start fresh session
- Implemented as part of Task 5 (Special commands)
- Command aliases: #new and #newsession
- Generates new UUID-based session ID
- Resets conversation context (agent doesn't remember previous conversation)
- Maintains same environment and configuration
- Shows confirmation banner with previous and new session IDs
- Clears conversation history for fresh start
- Logged for debugging purposes
