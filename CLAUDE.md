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
