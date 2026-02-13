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
