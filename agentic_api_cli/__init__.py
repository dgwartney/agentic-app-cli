"""
Agentic API CLI - Command-line interface for Kore.ai Agentic App Platform

A Python CLI tool for interacting with the Kore.ai Agentic App Platform API.
Supports executing AI agent runs, streaming responses, and managing async operations.
"""

__version__ = "0.1.0"
__author__ = "David Gwartney"
__email__ = "david.gwartney@gmail.com"

from agentic_api_cli.api_reference import (
    BASE_URL,
    DebugMode,
    InputType,
    RunStatus,
    SessionIdentityType,
    StreamMode,
    build_execute_url,
    build_headers,
    build_input,
    build_session_identity,
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
from agentic_api_cli.profiles import ProfileManager

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
    "ProfileManager",
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
