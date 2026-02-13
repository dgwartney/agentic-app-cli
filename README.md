# Agentic API CLI

A Python command-line interface for interacting with the Kore.ai Agentic App Platform API.

## Features

- **Interactive Chat Mode**: REPL-style chat interface with session management and special commands
- **Special Commands**: Runtime control with `#help`, `#new`, `#info`, `#clear`, `#debug`, `#stream` commands
- **Profile Management**: Store and manage multiple configuration sets for different environments
- **Execute AI agent runs**: Synchronous or asynchronous execution modes
- **Real-time streaming**: Stream responses token-by-token, by message, or with custom events
- **Status checking**: Monitor and poll async run status
- **Enhanced debug modes**: Comprehensive debugging with `all`, `function-call`, and `thoughts` modes
- **Advanced logging**: Python standard library logging with file output and configurable log levels
- **File attachments**: Support for attaching files to requests
- **Session management**: Maintain conversation continuity across requests
- **Flexible configuration**: Multiple configuration methods with clear precedence rules
- **Secure storage**: Profiles stored with proper file permissions (0600/0700)

## Installation

### From PyPI

```bash
pip install agentic-api-cli
```

### From Source

```bash
git clone https://github.com/dgwartney/agentic-app-cli.git
cd agentic-app-cli
uv sync
```

## Quick Start

### 1. Install the CLI

```bash
# From source (development)
git clone https://github.com/dgwartney/agentic-app-cli.git
cd agentic-app-cli
uv sync
```

### 2. Configure a Profile

Create a profile with your credentials:

```bash
agentic-api-cli profile add \
  --name production \
  --api-key "your-api-key" \
  --app-id "your-app-id" \
  --env-name production
```

Set it as the default:

```bash
agentic-api-cli profile set-default production
```

### 3. Start Chatting (Interactive Mode)

```bash
agentic-api-cli chat
```

Type your messages and use special commands like `#help`, `#debug on`, or `#new` for runtime control. Type `exit` to quit.

### 4. Or Execute a Single Query

```bash
# Session ID auto-generated
agentic-api-cli execute --query "Hello! How can you help me today?"

# Or use a custom session ID
agentic-api-cli execute --query "Hello!" --session-id my-session-001
```

### 5. View Configuration

```bash
agentic-api-cli config
```

## Configuration

The CLI requires the following configuration:

- **API Key**: Your Kore.ai API key
- **App ID**: Your application identifier
- **Environment Name**: Target environment (e.g., "production", "staging")

Configuration can be provided via multiple methods with the following precedence (highest to lowest):

1. **Command-line arguments** (`--api-key`, `--app-id`, etc.)
2. **Environment variables** (`KOREAI_API_KEY`, `KOREAI_APP_ID`, etc.)
3. **Profile values** (from `--profile` or default profile)
4. **Built-in defaults**

### Configuration Profiles (Recommended)

Profiles allow you to store multiple configuration sets and easily switch between them. This is the recommended approach for managing different environments or accounts.

#### Create a Profile

Create a profile interactively:
```bash
agentic-api-cli profile add
```

Or provide all values via command-line arguments:
```bash
agentic-api-cli profile add \
  --name production \
  --api-key "kg-your-api-key" \
  --app-id "aa-your-app-id" \
  --env-name production \
  --timeout 30
```

#### List Profiles

View all configured profiles:
```bash
# List with masked API keys (default)
agentic-api-cli profile list

# Show full API keys
agentic-api-cli profile list --show-keys
```

#### Set Default Profile

Set a profile to be used automatically when `--profile` is not specified:
```bash
agentic-api-cli profile set-default production
```

#### Use a Profile

Use a specific profile:
```bash
agentic-api-cli --profile staging execute --query "Test query" --session-id s1
```

Or use the default profile (no `--profile` flag needed):
```bash
agentic-api-cli execute --query "Test query" --session-id s1
```

#### Delete a Profile

```bash
agentic-api-cli profile delete staging
```

#### Profile Storage

Profiles are stored securely in `~/.kore/`:
- **Location**: `~/.kore/profiles` (JSON file)
- **Permissions**: `0600` (owner read/write only)
- **Directory permissions**: `0700` (owner access only)

### Environment Variables

You can also configure via environment variables (overrides profile values):

```bash
export KOREAI_API_KEY="your-api-key"
export KOREAI_APP_ID="your-app-id"
export KOREAI_ENV_NAME="production"
export KOREAI_BASE_URL="https://agent-platform.kore.ai/api/v2"
export KOREAI_TIMEOUT="30"
```

### .env File

Create a `.env` file in your project directory:

```bash
KOREAI_API_KEY=your-api-key
KOREAI_APP_ID=your-app-id
KOREAI_ENV_NAME=production
```

Or specify a custom .env file location:
```bash
agentic-api-cli --env-file /path/to/.env execute --query "Hello" --session-id s1
```

## Usage

### Basic Examples

Execute a run with auto-generated session ID:
```bash
agentic-api-cli execute --query "What is the weather in San Francisco?"
```

Execute with a custom session ID:
```bash
agentic-api-cli execute --query "What is the weather?" --session-id my-session-001
```

Execute using a specific profile:
```bash
agentic-api-cli --profile production execute --query "Hello, how are you?"
```

Execute using the default profile:
```bash
agentic-api-cli execute --query "Explain quantum computing"
```

### Stream Responses

Stream responses token-by-token for real-time output:
```bash
agentic-api-cli execute \
  --query "Explain quantum computing" \
  --session-id session-001 \
  --stream tokens
```

Stream by messages:
```bash
agentic-api-cli execute \
  --query "Write a story" \
  --session-id session-001 \
  --stream messages
```

### Check Run Status

Check the status of an asynchronous run:
```bash
agentic-api-cli status --run-id run-xyz-789
```

Wait for completion with polling:
```bash
agentic-api-cli status \
  --run-id run-xyz-789 \
  --wait \
  --poll-interval 2 \
  --max-attempts 30
```

### Interactive Chat Mode

Start an interactive chat session:
```bash
agentic-api-cli chat
```

Chat with streaming enabled:
```bash
agentic-api-cli chat --stream tokens
```

Chat with debug mode:
```bash
agentic-api-cli chat --debug --debug-mode thoughts
```

**Special Commands in Chat:**

Once in chat mode, use special commands for runtime control:

```
You: #help
Available Commands:
  #help              - Show this help message
  #new               - Start a new session
  #info              - Show current session information
  #clear             - Clear the terminal screen
  #debug on|off      - Toggle debug mode
  #stream on|off|tokens|messages|custom - Toggle streaming

To exit chat, type: exit, quit, or q

You: #debug on
Debug mode enabled

You: What is Python?
Agent: [Response with debug information...]

You: #new
╔═══════════════════════════════════════╗
║         New Session Started           ║
╚═══════════════════════════════════════╝
Previous Session: chat-1234567890
New Session: chat-1234567920

You: exit
Goodbye! Session ended.
```

### Debug Mode

Enable debug output for development:
```bash
agentic-api-cli execute \
  --query "Test query" \
  --session-id session-001 \
  --debug
```

Enable specific debug modes:
```bash
# Show all debug information
agentic-api-cli execute \
  --query "Test query" \
  --session-id session-001 \
  --debug --debug-mode all

# Show only function calls
agentic-api-cli execute \
  --query "Test query" \
  --session-id session-001 \
  --debug --debug-mode function-call

# Show agent thoughts
agentic-api-cli execute \
  --query "Test query" \
  --session-id session-001 \
  --debug --debug-mode thoughts
```

### Logging

Enable file logging:
```bash
agentic-api-cli --log-file app.log execute \
  --query "Test query" \
  --session-id session-001
```

Set log level:
```bash
agentic-api-cli --log-level DEBUG execute \
  --query "Test query" \
  --session-id session-001
```

### Show Current Configuration

View the current configuration (with masked sensitive data):
```bash
agentic-api-cli config
```

View configuration for a specific profile:
```bash
agentic-api-cli config --profile staging
```

### Override Configuration

Override specific configuration values (highest precedence):
```bash
agentic-api-cli --profile production \
  --env-name staging \
  --timeout 60 \
  execute --query "Test" --session-id s1
```

## Development

This project uses `uv` for package management.

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/dgwartney/agentic-app-cli.git
cd agentic-app-cli

# Create virtual environment and install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Run in Development

```bash
uv run agentic-api-cli
```

### Run Tests

```bash
uv run pytest
```

## API Reference

The package includes comprehensive type definitions and constants for the Kore.ai API:

```python
from agentic_api_cli import (
    BASE_URL,
    StreamMode,
    DebugMode,
    RunStatus,
    Config,
    AgenticAPIClient,
    ProfileManager,
    build_execute_url,
    build_status_url,
    build_headers,
)

# Programmatic profile management
profile_manager = ProfileManager()
profile_manager.add_profile(
    name="production",
    api_key="your-api-key",
    app_id="your-app-id",
    env_name="production",
    base_url="https://agent-platform.kore.ai/api/v2",
    timeout=30
)

# Load configuration from profile
config = Config(profile="production")

# Create API client
client = AgenticAPIClient(config)

# Build API URLs
execute_url = build_execute_url(app_id="my-app", env_name="production")

# Build headers
headers = build_headers(api_key="your-api-key")
```

## Documentation

- [API Documentation](https://docs.kore.ai/agentic-platform/)
- [Type Reference](./agentic_api_cli/api_reference.py)

## Requirements

- Python 3.12+
- `uv` for package management (recommended)

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- GitHub Issues: https://github.com/dgwartney/agentic-app-cli/issues
- Kore.ai Documentation: https://docs.kore.ai/

## Changelog

### 0.5.0 (Chat Mode & Special Commands)

- **Interactive Chat Mode**: REPL-style chat interface with persistent sessions
- **Special Commands**: Runtime control commands (`#help`, `#new`, `#info`, `#clear`, `#debug`, `#stream`)
- **Session Management**: Auto-generated session IDs with ability to start fresh sessions
- **Toggle Settings**: Change debug and streaming modes without restarting chat
- **Improved UX**: Case-insensitive commands, helpful error messages, discoverable features

### 0.4.0 (Enhanced Debug & Logging)

- **Debug Modes**: Support for `all`, `function-call`, and `thoughts` debug modes
- **Advanced Logging**: Python standard library logging with file output
- **Log Levels**: Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Secure Logging**: Automatic masking of sensitive data in logs
- **Verbose Output**: Enhanced verbose mode with detailed debug information

### 0.3.0 (Profile Management)

- **Profile Management**: Add, list, delete, and manage configuration profiles
- **Default Profiles**: Set a default profile to use automatically
- **Secure Storage**: Profiles stored in `~/.kore/` with secure permissions (0600)
- **Configuration Precedence**: Clear precedence rules (CLI args > Env vars > Profiles > Defaults)
- **Interactive Profile Creation**: Create profiles interactively or via CLI arguments
- **Profile Display**: List profiles with masked or full API keys

### 0.2.0 (Streaming & Session Support)

- **Real-time Streaming**: Token-by-token, message, and custom event streaming
- **Session Identity**: Maintain conversation continuity across requests
- **Async Execution**: Asynchronous run execution with status polling
- **Enhanced Error Handling**: Better error messages and recovery

### 0.1.0 (Initial Release)

- Initial package structure
- API type definitions and reference implementation
- Basic CLI framework
- Execute and status commands
- Documentation and examples
