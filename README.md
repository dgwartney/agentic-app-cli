# Agentic API CLI

A Python command-line interface for interacting with the Kore.ai Agentic App Platform API.

## Features

- Execute AI agent runs with synchronous or asynchronous execution
- Stream responses in real-time (tokens, messages, or custom events)
- Check status of async runs
- Debug mode support for development
- File attachment support
- Session management for conversation continuity

## Installation

### From PyPI

```bash
pip install agentic-api-cli
```

### From Source

```bash
git clone https://github.com/yourusername/agentic-app-cli.git
cd agentic-app-cli
uv sync
```

## Quick Start

```bash
# Run the CLI
agentic-api-cli

# Or with uv in development
uv run agentic-api-cli
```

## Configuration

The CLI requires the following configuration:

- **API Key**: Your Kore.ai API key
- **App ID**: Your application identifier
- **Environment Name**: Target environment (e.g., "production", "staging")

Configuration can be provided via:
- Environment variables
- Configuration file
- Command-line arguments

### Environment Variables

```bash
export KOREAI_API_KEY="your-api-key"
export KOREAI_APP_ID="your-app-id"
export KOREAI_ENV_NAME="production"
```

## Usage

### Execute a Run

```bash
agentic-api-cli execute --query "What is the weather in San Francisco?"
```

### Stream Responses

```bash
agentic-api-cli execute --query "Explain quantum computing" --stream tokens
```

### Async Execution

```bash
agentic-api-cli execute --async --query "Analyze this dataset"
agentic-api-cli status --run-id <run-id>
```

### Debug Mode

```bash
agentic-api-cli execute --query "Test query" --debug all
```

## Development

This project uses `uv` for package management.

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/agentic-app-cli.git
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
    build_execute_url,
    build_status_url,
    build_headers,
)

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
- GitHub Issues: https://github.com/yourusername/agentic-app-cli/issues
- Kore.ai Documentation: https://docs.kore.ai/

## Changelog

### 0.1.0 (Initial Release)

- Initial package structure
- API type definitions and reference implementation
- Basic CLI framework
- Documentation and examples
