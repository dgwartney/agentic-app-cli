# Usage Guide

Comprehensive guide for using the Agentic API CLI.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Commands](#commands)
  - [Execute Command](#execute-command)
  - [Status Command](#status-command)
  - [Config Command](#config-command)
- [Examples](#examples)
- [Python API](#python-api)

## Installation

```bash
pip install agentic-api-cli
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
agentic-api-cli --env-file /path/to/.env execute --query "Hello" --session-id session-1
```

### Command-line Arguments

Override any configuration using command-line flags:

```bash
agentic-api-cli --api-key YOUR_KEY --app-id YOUR_APP execute --query "Hello" --session-id session-1
```

## Commands

### Execute Command

Execute an agentic run with a query.

**Basic Usage:**

```bash
agentic-api-cli execute --query "What is the weather?" --session-id session-001
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
agentic-api-cli execute \
  --query "Explain quantum computing" \
  --session-id session-001

# With streaming
agentic-api-cli execute \
  --query "Write a story" \
  --session-id session-002 \
  --stream tokens

# Asynchronous execution
agentic-api-cli execute \
  --query "Analyze large dataset" \
  --session-id session-003 \
  --async

# Async with automatic waiting
agentic-api-cli execute \
  --query "Process data" \
  --session-id session-004 \
  --async \
  --wait

# With metadata
agentic-api-cli execute \
  --query "Hello" \
  --session-id session-005 \
  --metadata '{"userId": "user123", "source": "cli"}'

# With debug mode
agentic-api-cli execute \
  --query "Test query" \
  --session-id session-006 \
  --debug all \
  --verbose
```

### Status Command

Check the status of an asynchronous run.

**Basic Usage:**

```bash
agentic-api-cli status --run-id run-xyz-789
```

**Options:**

- `--run-id, -r ID` - Run ID to check status for (required)
- `--wait` - Wait for run to complete
- `--poll-interval SECONDS` - Polling interval when waiting (default: 2)
- `--max-attempts N` - Maximum polling attempts (default: 30)

**Examples:**

```bash
# Check status once
agentic-api-cli status --run-id run-abc-123

# Poll until completion
agentic-api-cli status \
  --run-id run-abc-123 \
  --wait \
  --poll-interval 3 \
  --max-attempts 20

# JSON output
agentic-api-cli status --run-id run-abc-123 --json
```

### Config Command

Display current configuration (with sensitive data masked).

**Usage:**

```bash
# Human-readable output
agentic-api-cli config

# JSON output
agentic-api-cli config --json
```

## Examples

### Basic Workflow

```bash
# 1. Configure environment
export KOREAI_API_KEY="your-api-key"
export KOREAI_APP_ID="your-app-id"

# 2. Execute a simple query
agentic-api-cli execute \
  --query "What is artificial intelligence?" \
  --session-id session-001

# 3. Continue the conversation
agentic-api-cli execute \
  --query "Can you explain more about machine learning?" \
  --session-id session-001
```

### Async Workflow

```bash
# 1. Start an async run
agentic-api-cli execute \
  --query "Generate a comprehensive report" \
  --session-id session-002 \
  --async

# Output: Run ID: run-xyz-789

# 2. Check status periodically
agentic-api-cli status --run-id run-xyz-789

# 3. Or wait for completion
agentic-api-cli status --run-id run-xyz-789 --wait
```

### Advanced Usage

```bash
# Streaming with debug and metadata
agentic-api-cli execute \
  --query "Explain the solar system" \
  --session-id session-003 \
  --stream tokens \
  --debug summary \
  --metadata '{"topic": "astronomy", "level": "beginner"}' \
  --verbose

# Async execution with auto-wait
agentic-api-cli execute \
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
agentic-api-cli --env-name development execute \
  --query "Test query" \
  --session-id dev-session-001

# Staging environment
agentic-api-cli --env-name staging execute \
  --query "Test query" \
  --session-id staging-session-001

# Production (default)
agentic-api-cli execute \
  --query "Production query" \
  --session-id prod-session-001
```

### JSON Output for Scripting

```bash
# Execute and parse JSON output
result=$(agentic-api-cli execute \
  --query "What is 2+2?" \
  --session-id script-001 \
  --json)

# Extract fields using jq
echo "$result" | jq '.response'
echo "$result" | jq '.runId'
```

## Python API

You can also use the classes directly in Python:

```python
from agentic_api_cli import Config, AgenticAPIClient

# Create configuration
config = Config()
config.api_key = "your-api-key"
config.app_id = "your-app-id"
config.env_name = "production"

# Create client
client = AgenticAPIClient(config)

# Execute a run
response = client.execute_run(
    query="What is the weather?",
    session_identity="session-001"
)

print(f"Response: {response['response']}")

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
from agentic_api_cli import Config, AgenticAPIClient

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
from agentic_api_cli import (
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
agentic-api-cli config

# Use verbose mode to see what's happening
agentic-api-cli --verbose execute --query "test" --session-id test
```

### Authentication Errors

```bash
# Verify API key is set
echo $KOREAI_API_KEY

# Try with explicit API key
agentic-api-cli --api-key YOUR_KEY execute --query "test" --session-id test
```

### Timeout Issues

```bash
# Increase timeout
agentic-api-cli --timeout 60 execute --query "complex query" --session-id test

# Or use async mode
agentic-api-cli execute --query "complex query" --session-id test --async --wait
```

## Getting Help

```bash
# General help
agentic-api-cli --help

# Command-specific help
agentic-api-cli execute --help
agentic-api-cli status --help
agentic-api-cli config --help
```
