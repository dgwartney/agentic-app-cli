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
    DebugMode,
    RunStatus,
    StreamMode,
    build_execute_url,
    build_headers,
    build_status_url,
)
from agentic_api_cli.client import AgenticAPIClient
from agentic_api_cli.config import Config
from agentic_api_cli.exceptions import (
    AgenticAPIError,
    APIRequestError,
    APIResponseError,
    AuthenticationError,
    ConfigurationError,
    RunNotFoundError,
    TimeoutError,
    ValidationError,
)

__all__ = [
    "__version__",
    # API Reference
    "BASE_URL",
    "StreamMode",
    "DebugMode",
    "RunStatus",
    "build_execute_url",
    "build_status_url",
    "build_headers",
    # Core Classes
    "Config",
    "AgenticAPIClient",
    # Exceptions
    "AgenticAPIError",
    "AuthenticationError",
    "ConfigurationError",
    "APIRequestError",
    "APIResponseError",
    "TimeoutError",
    "RunNotFoundError",
    "ValidationError",
]
