"""
Agentic API CLI - Command-line interface for Kore.ai Agentic App Platform

A Python CLI tool for interacting with the Kore.ai Agentic App Platform API.
Supports executing AI agent runs, streaming responses, and managing async operations.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from agentic_api_cli.api_reference import (
    BASE_URL,
    StreamMode,
    DebugMode,
    RunStatus,
    build_execute_url,
    build_status_url,
    build_headers,
)

__all__ = [
    "__version__",
    "BASE_URL",
    "StreamMode",
    "DebugMode",
    "RunStatus",
    "build_execute_url",
    "build_status_url",
    "build_headers",
]
