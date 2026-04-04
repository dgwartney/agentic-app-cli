# Usage Guide

Comprehensive guide for using the Agentic API CLI.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Commands](#commands)
  - [Execute Command](#execute-command)
  - [Status Command](#status-command)
  - [Config Command](#config-command)
- [MCP Server](#mcp-server)
- [Examples](#examples)
- [Python API](#python-api)

## Installation

```bash
pip install agxr
```

## Configuration

The CLI requires authentication credentials and configuration. These can be provided via:

1. **Environment Variables** (recommended)
2. **`.env` file**
3. **Command-line arguments**

### Environment Variables

```bash
export KOREAI_API_KEY="your-api-key"
export KOREAI_APP_ID="your-app-id"
export KOREAI_ENV_NAME="production"  # Optional, defaults to "production"
```

### Using .env File

Create a `.env` file in your project directory:

```env
KOREAI_API_KEY=your-api-key-here
KOREAI_APP_ID=your-app-id-here
KOREAI_ENV_NAME=production
```

Or specify a custom location:

```bash
agxr --env-file /path/to/.env execute --query "Hello" --session-id session-1
```

### Command-line Arguments

Override any configuration using command-line flags:

```bash
agxr --api-key YOUR_KEY --app-id YOUR_APP execute --query "Hello" --session-id session-1
```

## Commands

### Execute Command

Execute an agentic run with a query.

**Basic Usage:**

```bash
agxr execute --query "What is the weather?" --session-id session-001
```

**Options:**

- `--query, -q TEXT` - Query or input text for the agent (required)
- `--session-id, -s ID` - Session identity for conversation continuity (required)
- `--async` - Execute asynchronously (returns immediately with run ID)
- `--stream MODE` - Enable streaming mode (`tokens`, `messages`, or `custom`)
- `--debug LEVEL` - Debug mode (`all`, `summary`, or `off`)
- `--stream-debug` - Stream debug data in real-time
- `--skip-cache` - Bypass cache for fresh responses
- `--metadata JSON` - JSON string of metadata key-value pairs
- `--wait` - Wait for async run to complete
- `--poll-interval SECONDS` - Polling interval when waiting (default: 2)
- `--max-attempts N` - Maximum polling attempts (default: 30)

**Examples:**

```bash
# Synchronous execution
agxr execute \
  --query "Explain quantum computing" \
  --session-id session-001

# With streaming
agxr execute \
  --query "Write a story" \
  --session-id session-002 \
  --stream tokens

# Asynchronous execution
agxr execute \
  --query "Analyze large dataset" \
  --session-id session-003 \
  --async

# Async with automatic waiting
agxr execute \
  --query "Process data" \
  --session-id session-004 \
  --async \
  --wait

# With metadata
agxr execute \
  --query "Hello" \
  --session-id session-005 \
  --metadata '{"userId": "user123", "source": "cli"}'

# With debug mode
agxr execute \
  --query "Test query" \
  --session-id session-006 \
  --debug all \
  --verbose
```

### Status Command

Check the status of an asynchronous run.

**Basic Usage:**

```bash
agxr status --run-id run-xyz-789
```

**Options:**

- `--run-id, -r ID` - Run ID to check status for (required)
- `--wait` - Wait for run to complete
- `--poll-interval SECONDS` - Polling interval when waiting (default: 2)
- `--max-attempts N` - Maximum polling attempts (default: 30)

**Examples:**

```bash
# Check status once
agxr status --run-id run-abc-123

# Poll until completion
agxr status \
  --run-id run-abc-123 \
  --wait \
  --poll-interval 3 \
  --max-attempts 20

# JSON output
agxr status --run-id run-abc-123 --json
```

### Config Command

Display current configuration (with sensitive data masked).

**Usage:**

```bash
# Human-readable output
agxr config

# JSON output
agxr config --json
```

## MCP Server

`agxr-mcp` exposes your Kore.ai agent as MCP tools for use with Claude Code and other MCP clients.

### Starting the server

```bash
# With a named profile
agxr-mcp --profile my-profile

# With environment variables
agxr-mcp
```

### Claude Code integration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "agxr": {
      "command": "uv",
      "args": ["run", "agxr-mcp", "--profile", "my-profile"],
      "cwd": "/path/to/agentic-app-cli"
    }
  }
}
```

### Tools

#### `start_session(user_reference?)`

Create a new conversation session. Returns an `mcp_session_id` for use in subsequent calls.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_reference` | str | No | Stable user identifier. Auto-generated if omitted. |

**Returns (success):**
```json
{
  "status": "success",
  "mcp_session_id": "mcp-xxxxxxxx-...",
  "session_reference": "sr-...",
  "user_reference": "mcp-user-..."
}
```

#### `end_session(mcp_session_id)`

Terminate a session and free server-side agent memory.

**Returns (success):** `{"status": "terminated", "mcp_session_id": "..."}`

#### `send_message(mcp_session_id, message)`

Send a message to the agent and receive its response. Maintains conversation context.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mcp_session_id` | str | Yes | Session ID from `start_session` |
| `message` | str | Yes | The user message |

**Returns (success):**
```json
{
  "status": "success",
  "response": "Agent reply text",
  "mcp_session_id": "mcp-...",
  "turn_count": 1
}
```

#### `get_session_history(mcp_session_id)`

Return the full conversation history for a session.

**Returns:**
```json
{
  "mcp_session_id": "mcp-...",
  "history": [
    {"role": "user", "text": "Hello"},
    {"role": "agent", "text": "Hi there"}
  ],
  "turn_count": 1
}
```

#### `reset_session(mcp_session_id)`

Clear the local conversation history. The Kore.ai session remains active on the server.
To also reset server-side agent memory, use `end_session` + `start_session`.

**Returns (success):** `{"status": "reset", "mcp_session_id": "..."}`

#### `execute_query(query, user_reference?)`

Send a one-shot query without creating a persistent session. No history is maintained.

**Returns (success):**
```json
{
  "status": "success",
  "response": "Agent reply text",
  "run_id": "r-..."
}
```

#### `check_run_status(run_id)`

Poll the status of an asynchronous run (from `sessionInfo.runId` in a prior response).

**Returns (success):**
```json
{
  "status": "success",
  "run_id": "r-...",
  "output": [{"type": "text", "content": "..."}]
}
```

#### `list_profiles()`

List all configuration profiles stored in `~/.kore/profiles`.

**Returns:** `{"profiles": ["prod", "staging"], "count": 2}`

#### `get_server_info()`

Return connection details for the active server configuration.

**Returns:** `{"app_id": "...", "env_name": "...", "base_url": "...", "active_sessions": 0}`

### Error responses

All tools return a structured error dict on failure rather than raising an exception:

```json
{
  "status": "error",
  "error_type": "authentication",
  "error": "Human-readable error message"
}
```

| `error_type` | Cause |
|-------------|-------|
| `session_not_found` | Unknown `mcp_session_id` — call `start_session` first |
| `authentication` | Invalid or missing API key |
| `configuration` | Missing required configuration |
| `not_found` | Unknown run ID |
| `api_error` | Kore.ai API returned an error |
| `unexpected` | Unexpected runtime error |

### Python API (`AgenticMCPServer`)

You can also use `AgenticMCPServer` directly in Python:

```python
from agxr import AgenticMCPServer

server = AgenticMCPServer(profile="my-profile")

# Start a session
result = server.start_session(user_reference="user-alice")
mcp_id = result["mcp_session_id"]

# Chat
reply = server.send_message(mcp_id, "Hello, what can you do?")
print(reply["response"])

# End the session
server.end_session(mcp_id)
```

## Examples

### Basic Workflow

```bash
# 1. Configure environment
export KOREAI_API_KEY="your-api-key"
export KOREAI_APP_ID="your-app-id"

# 2. Execute a simple query
agxr execute \
  --query "What is artificial intelligence?" \
  --session-id session-001

# 3. Continue the conversation
agxr execute \
  --query "Can you explain more about machine learning?" \
  --session-id session-001
```

### Async Workflow

```bash
# 1. Start an async run
agxr execute \
  --query "Generate a comprehensive report" \
  --session-id session-002 \
  --async

# Output: Run ID: run-xyz-789

# 2. Check status periodically
agxr status --run-id run-xyz-789

# 3. Or wait for completion
agxr status --run-id run-xyz-789 --wait
```

### Advanced Usage

```bash
# Streaming with debug and metadata
agxr execute \
  --query "Explain the solar system" \
  --session-id session-003 \
  --stream tokens \
  --debug summary \
  --metadata '{"topic": "astronomy", "level": "beginner"}' \
  --verbose

# Async execution with auto-wait
agxr execute \
  --query "Complex analysis task" \
  --session-id session-004 \
  --async \
  --wait \
  --poll-interval 5 \
  --max-attempts 20 \
  --skip-cache
```

### Using Different Environments

```bash
# Development environment
agxr --env-name development execute \
  --query "Test query" \
  --session-id dev-session-001

# Staging environment
agxr --env-name staging execute \
  --query "Test query" \
  --session-id staging-session-001

# Production (default)
agxr execute \
  --query "Production query" \
  --session-id prod-session-001
```

### JSON Output for Scripting

```bash
# Execute and parse JSON output
result=$(agxr execute \
  --query "What is 2+2?" \
  --session-id script-001 \
  --json)

# Extract fields using jq
echo "$result" | jq '.response'
echo "$result" | jq '.runId'
```

## Python API

### `AgentTestSession` — End-to-End Testing

Use `AgentTestSession` for integration tests that make real API calls:

```python
from agxr import AgentTestSession

# Use a named profile
with AgentTestSession(profile="staging") as session:
    response = session.send("Hello")
    assert len(response) > 0

# Or use environment variables (no profile argument)
with AgentTestSession() as session:
    session.send("My name is Alice")
    reply = session.send("What is my name?")
    assert "Alice" in reply

    # Reset server-side memory mid-test
    session.reset()
    reply = session.send("What is my name?")
    # Agent should not remember

print(f"Session ID: {session.session_id}")  # API-assigned sessionReference
```

See [TESTING.md](./TESTING.md) for the full testing guide.

### `AgenticAPIClient` — Low-Level Client

You can also use the classes directly in Python:

```python
from agxr import Config, AgenticAPIClient

# Create configuration
config = Config()
config.api_key = "your-api-key"
config.app_id = "your-app-id"
config.env_name = "production"

# Create client
client = AgenticAPIClient(config)

# Create a session
session_data = client.create_session("user-alice")
session_ref = session_data["sessionReference"]

# Execute a run within the session
response = client.execute_run(
    query="What is the weather?",
    session_identity=session_ref
)

print(f"Response text: {response['output'][0]['content']}")

# Terminate the session when done
client.terminate_session(session_ref)

# Check status of async run
status = client.get_run_status("run-xyz-789")
print(f"Status: {status['status']}")

# Poll for completion
final_status = client.poll_run_status(
    run_id="run-xyz-789",
    max_attempts=30,
    interval=2
)

# Or execute and wait in one call
result = client.execute_and_wait(
    query="Analyze data",
    session_identity="session-002"
)

# Close the client
client.close()
```

### Using Context Manager

```python
from agxr import Config, AgenticAPIClient

config = Config()
config.api_key = "your-api-key"
config.app_id = "your-app-id"

# Client automatically closes when done
with AgenticAPIClient(config) as client:
    response = client.execute_run(
        query="Hello world",
        session_identity="session-001"
    )
    print(response)
```

### Error Handling

```python
from agxr import (
    Config,
    AgenticAPIClient,
    AgenticAPIError,
    AuthenticationError,
    ValidationError,
)

config = Config()
config.api_key = "your-api-key"
config.app_id = "your-app-id"

try:
    with AgenticAPIClient(config) as client:
        response = client.execute_run(
            query="Test query",
            session_identity="session-001"
        )
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
except ValidationError as e:
    print(f"Validation error: {e.message}")
except AgenticAPIError as e:
    print(f"API error: {e.message}")
    if e.status_code:
        print(f"Status code: {e.status_code}")
```

## Global Options

Available for all commands:

- `--version` - Show version and exit
- `--api-key KEY` - Override API key
- `--app-id ID` - Override app ID
- `--env-name NAME` - Override environment name
- `--base-url URL` - Override base URL
- `--timeout SECONDS` - Override request timeout
- `--env-file FILE` - Load configuration from specific .env file
- `--json` - Output in JSON format
- `--verbose, -v` - Verbose output with request/response details

## Exit Codes

- `0` - Success
- `1` - Error (API error, validation error, etc.)
- `130` - Interrupted by user (Ctrl+C)

## Troubleshooting

### Configuration Errors

```bash
# Check your configuration
agxr config

# Use verbose mode to see what's happening
agxr --verbose execute --query "test" --session-id test
```

### Authentication Errors

```bash
# Verify API key is set
echo $KOREAI_API_KEY

# Try with explicit API key
agxr --api-key YOUR_KEY execute --query "test" --session-id test
```

### Timeout Issues

```bash
# Increase timeout
agxr --timeout 60 execute --query "complex query" --session-id test

# Or use async mode
agxr execute --query "complex query" --session-id test --async --wait
```

## Getting Help

```bash
# General help
agxr --help

# Command-specific help
agxr execute --help
agxr status --help
agxr config --help
```
