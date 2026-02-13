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

### Task 4: Create interactive chat command

Implement a new `chat` command that provides an interactive REPL-style chat session with the agentic app.

**Requirements:**
- New command: `agentic-api-cli chat [OPTIONS]`
- Maintains conversation context using same session throughout
- Interactive loop: prompt user for input, send query, display response, repeat
- Clean, user-friendly prompt (e.g., "You: ")
- Clear display of agent responses (e.g., "Agent: ")
- Support all execute options: `--env-name`, `--stream`, `--debug`, `--user-id`, etc.
- Exit commands: 'exit', 'quit', 'q', Ctrl+D, Ctrl+C
- Show welcome message on start
- Display session info (session ID, environment) at start

**Example session:**
```
$ agentic-api-cli chat --env-name draft
╔═══════════════════════════════════════╗
║   Agentic API Chat Session Started   ║
╚═══════════════════════════════════════╝
Session ID: chat-1234-5678
Environment: draft

Type your message or '#help' for commands. Type 'exit' to quit.

You: Hello
Agent: Hi there! Welcome! How can I help you today?

You: What is 2+2?
Agent: 2 + 2 equals 4.

You: exit
Goodbye! Session ended.
```

**Implementation:**
- Add chat command to CLI parser
- Create interactive input loop
- Handle keyboard interrupts gracefully
- Support input history (using readline if available)
- Display loading indicator for long requests (optional)
- Save chat history to file (optional, with `--save-history` flag)

### Task 5: Implement special commands in chat mode

Add special commands with '#' prefix for chat mode to control session and display information.

**Special commands (all start with #):**
- `#help` - Show available special commands
- `#new` or `#newsession` - Start a new session (new session ID)
- `#info` or `#session` - Display current session information
- `#clear` - Clear the terminal screen
- `#history` - Show conversation history (if history tracking enabled)
- `#debug on|off` - Toggle debug mode
- `#stream on|off` - Toggle streaming mode
- `#exit` or `#quit` - Exit chat (same as 'exit')

**Example usage in chat:**
```
You: #help
Available commands:
  #help           - Show this help
  #new            - Start a new session
  #info           - Show session information
  #clear          - Clear screen
  #history        - Show conversation history
  #debug on|off   - Toggle debug mode
  #stream on|off  - Toggle streaming
  #exit           - Exit chat

You: #info
Session Information:
  Session ID: chat-1234-5678
  User ID: chat-1234-5678
  Environment: draft
  App ID: aa-c1bcf7e2-3c10-4c67-9b8a-4d79be0110af
  Debug: off
  Streaming: off

You: #debug on
Debug mode enabled
```

**Implementation:**
- Add command parser for lines starting with '#'
- Implement handler for each special command
- Track session state (debug, stream settings)
- Allow toggling options during chat
- Show helpful feedback for each command
- Handle invalid commands gracefully

**Depends on:** Task 4 (Create interactive chat command)

### Task 6: Auto-generate session ID for chat command

Automatically generate unique session IDs when starting chat mode if not provided by user.

**Requirements:**
- Generate unique session ID when chat command starts
- Use format: `chat-{uuid4}` for guaranteed uniqueness
- Allow user to override with `--session-id` option
- Display generated session ID in welcome banner
- Ensure session ID is consistent throughout chat session
- Generate new session ID when #new command is used

**Example implementation:**
```python
import uuid

def generate_chat_session_id() -> str:
    """Generate unique session ID for chat."""
    return f"chat-{uuid.uuid4()}"
```

**CLI behavior:**
- `chat` - Auto-generates session ID
- `chat --session-id custom-123` - Uses provided session ID
- Display session ID in welcome message
- Log session ID for debugging

**Implementation:**
- Add session ID generation function to utils module
- Update chat command to generate ID if not provided
- Pass session ID to execute_run calls
- Update #new command to generate new session ID

**Depends on:** Task 4 (Create interactive chat command)

### Task 7: Add #new command to start fresh session

Implement the #new/#newsession special command to start a fresh conversation session in chat mode.

**Requirements:**
- Command aliases: `#new`, `#newsession`
- Generates new session ID
- Resets conversation context
- Maintains same environment and configuration
- Shows confirmation with new session ID
- Clears any local conversation history tracking

**Example:**
```
You: Tell me about quantum computing
Agent: [Long response about quantum computing]

You: #new
╔═══════════════════════════════════════╗
║      New Session Started              ║
╚═══════════════════════════════════════╝
Previous Session: chat-1234-5678
New Session: chat-9876-5432

You: Hello
Agent: Hi! Welcome! How can I help you?
[Agent doesn't remember quantum computing conversation]
```

**Implementation:**
- Add #new command handler in chat special commands
- Call generate_session_id() to create new ID
- Update chat state with new session ID
- Clear any conversation history tracking
- Display banner or message confirming new session
- Log session change for debugging

**Optional enhancements:**
- Ask for confirmation before starting new session
- Offer to save previous session history
- Allow naming sessions for later recall

**Depends on:**
- Task 5 (Implement special commands in chat mode)
- Task 6 (Auto-generate session ID for chat command)

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
