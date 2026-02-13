"""
Kore.ai Agentic App Platform API Reference

This module provides type definitions, constants, and reference documentation
for the Kore.ai Agentic App Platform REST API.

Base URL: https://agent-platform.kore.ai/api/v2

NOTE: This implementation is based on the ACTUAL API format discovered through
working curl commands, not the initial documentation which was inaccurate.
"""

from enum import Enum
from typing import TypedDict, Literal, Optional, Any


# ============================================================================
# Constants
# ============================================================================

BASE_URL = "https://agent-platform.kore.ai/api/v2"
"""Base URL for Kore.ai Agentic App Platform API"""


# ============================================================================
# Enums
# ============================================================================

class StreamMode(str, Enum):
    """Streaming mode for execute run endpoint"""
    TOKENS = "tokens"      # Stream individual tokens as they're generated
    MESSAGES = "messages"  # Stream complete messages
    CUSTOM = "custom"      # Stream custom events


class DebugMode(str, Enum):
    """Debug mode for execute run endpoint"""
    ALL = "all"                      # Full debug information
    FUNCTION_CALL = "function-call"  # Function call debugging
    THOUGHTS = "thoughts"            # Thought process debugging


class RunStatus(str, Enum):
    """Status of an agentic run"""
    PENDING = "pending"    # Run is queued
    RUNNING = "running"    # Run is in progress
    SUCCESS = "success"    # Run completed successfully
    FAILED = "failed"      # Run failed with error


class SessionIdentityType(str, Enum):
    """Type of session identity"""
    USER_REFERENCE = "userReference"
    SESSION_REFERENCE = "sessionReference"


class InputType(str, Enum):
    """Type of input content"""
    TEXT = "text"


# ============================================================================
# Type Definitions - Request Bodies
# ============================================================================

class SessionIdentityItem(TypedDict):
    """
    Session identity item.

    Attributes:
        type: Type of identity (userReference or sessionReference)
        value: The identity value
    """
    type: str  # "userReference" or "sessionReference"
    value: str


class InputItem(TypedDict):
    """
    Input content item.

    Attributes:
        type: Type of input (typically "text")
        content: The actual input content
    """
    type: str  # "text"
    content: str


class FileAttachment(TypedDict, total=False):
    """
    File attachment for execute run request.

    Attributes:
        fileUrl: URL to the file to attach
        fileName: Display name for the file
    """
    fileUrl: str
    fileName: str


class StreamConfig(TypedDict, total=False):
    """
    Streaming configuration for execute run.

    Attributes:
        enable: Enable streaming (true/false)
        streamMode: Streaming mode (tokens, messages, or custom)
    """
    enable: bool
    streamMode: str  # "tokens", "messages", or "custom"


class DebugConfig(TypedDict, total=False):
    """
    Debug configuration for execute run.

    Attributes:
        enable: Enable debug mode (true/false)
        debugMode: Debug mode level ("all", "function-call", or "thoughts")
    """
    enable: bool
    debugMode: str  # "all", "function-call", or "thoughts"


class ExecuteRunRequest(TypedDict, total=False):
    """
    Request body for POST /apps/<AppID>/environments/<EnvName>/runs/execute

    ACTUAL API FORMAT (different from initial documentation):

    Attributes:
        sessionIdentity: Array of session identity objects with type and value
        input: Array of input objects with type and content
        stream: Streaming configuration with enable and streamMode
        debug: Debug configuration with enable flag
        metaData: Custom metadata key-value pairs
    """
    sessionIdentity: list[SessionIdentityItem]  # Required
    input: list[InputItem]  # Required
    stream: StreamConfig
    debug: DebugConfig
    metaData: dict[str, Any]


class FindRunStatusRequest(TypedDict, total=False):
    """
    Request body for POST /apps/<AppID>/environments/<EnvName>/runs/<runId>/status

    This endpoint typically uses an empty request body or {}.
    """
    pass


# ============================================================================
# Type Definitions - Response Bodies
# ============================================================================

class ExecuteRunMetadata(TypedDict, total=False):
    """
    Metadata from execute run response.

    Attributes:
        executionTime: Execution time in milliseconds
        tokenCount: Number of tokens used
    """
    executionTime: int
    tokenCount: int


class ExecuteRunResponse(TypedDict, total=False):
    """
    Response from execute run endpoint (synchronous).

    Attributes:
        runId: Unique identifier for the run
        status: Run status (success or failed)
        response: Response text from the agent
        metadata: Execution metadata
    """
    runId: str
    status: Literal["success", "failed"]
    response: str
    metadata: ExecuteRunMetadata


class AsyncExecuteRunResponse(TypedDict):
    """
    Response from execute run endpoint (asynchronous).

    Attributes:
        runId: Unique identifier for the run
        status: Run status (pending or running)
        message: Status message
    """
    runId: str
    status: Literal["pending", "running"]
    message: str


class ErrorDetail(TypedDict):
    """
    Error details in response.

    Attributes:
        code: Error code
        message: Human-readable error message
    """
    code: str
    message: str


class RunStatusMetadata(TypedDict, total=False):
    """
    Metadata from run status response.

    Attributes:
        startTime: ISO timestamp when run started
        endTime: ISO timestamp when run ended
        executionTime: Execution time in milliseconds
    """
    startTime: str
    endTime: str
    executionTime: int


class FindRunStatusResponse(TypedDict, total=False):
    """
    Response from find run status endpoint.

    Attributes:
        runId: The run identifier
        status: Current status (pending, running, success, or failed)
        response: Final response (available when status is success)
        error: Error details (present when status is failed)
        metadata: Execution metadata including timing information
    """
    runId: str
    status: Literal["pending", "running", "success", "failed"]
    response: str
    error: ErrorDetail
    metadata: RunStatusMetadata


class ErrorResponse(TypedDict):
    """
    Standard error response format.

    Attributes:
        error: Error details object
    """
    error: dict[str, Any]


# ============================================================================
# URL Builders
# ============================================================================

def build_execute_url(app_id: str, env_name: str) -> str:
    """
    Build URL for execute run endpoint.

    Args:
        app_id: Unique identifier for the agentic application
        env_name: Environment name (e.g., "production", "staging", "draft")

    Returns:
        Full URL for execute run endpoint

    Example:
        >>> build_execute_url("my-app-123", "production")
        'https://agent-platform.kore.ai/api/v2/apps/my-app-123/environments/production/runs/execute'
    """
    return f"{BASE_URL}/apps/{app_id}/environments/{env_name}/runs/execute"


def build_status_url(app_id: str, env_name: str, run_id: str) -> str:
    """
    Build URL for find run status endpoint.

    Args:
        app_id: Unique identifier for the agentic application
        env_name: Environment name (e.g., "production", "staging", "draft")
        run_id: Run ID to check status for

    Returns:
        Full URL for find run status endpoint

    Example:
        >>> build_status_url("my-app-123", "production", "run-xyz-789")
        'https://agent-platform.kore.ai/api/v2/apps/my-app-123/environments/production/runs/run-xyz-789/status'
    """
    return f"{BASE_URL}/apps/{app_id}/environments/{env_name}/runs/{run_id}/status"


# ============================================================================
# Headers
# ============================================================================

def build_headers(api_key: str) -> dict[str, str]:
    """
    Build standard headers for API requests.

    Args:
        api_key: Kore.ai API key

    Returns:
        Dictionary of headers including authentication

    Example:
        >>> headers = build_headers("your-api-key")
        >>> headers
        {'x-api-key': 'your-api-key', 'Content-Type': 'application/json'}
    """
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }


# ============================================================================
# Helper Functions
# ============================================================================

def build_session_identity(user_ref: str, session_ref: Optional[str] = None) -> list[SessionIdentityItem]:
    """
    Build sessionIdentity array from user and session references.

    Args:
        user_ref: User reference value
        session_ref: Session reference value (optional)

    Returns:
        List of session identity items

    Example:
        >>> build_session_identity("user-123", "session-456")
        [
            {'type': 'userReference', 'value': 'user-123'},
            {'type': 'sessionReference', 'value': 'session-456'}
        ]
    """
    identity: list[SessionIdentityItem] = [
        {
            "type": SessionIdentityType.USER_REFERENCE.value,
            "value": user_ref
        }
    ]

    if session_ref:
        identity.append({
            "type": SessionIdentityType.SESSION_REFERENCE.value,
            "value": session_ref
        })

    return identity


def build_input(text: str) -> list[InputItem]:
    """
    Build input array from text content.

    Args:
        text: Input text content

    Returns:
        List of input items

    Example:
        >>> build_input("Hello world")
        [{'type': 'text', 'content': 'Hello world'}]
    """
    return [
        {
            "type": InputType.TEXT.value,
            "content": text
        }
    ]


# ============================================================================
# Usage Examples (for reference)
# ============================================================================

# Example 1: Basic synchronous request
EXAMPLE_SYNC_REQUEST: ExecuteRunRequest = {
    "sessionIdentity": [
        {"type": "userReference", "value": "user-001"},
        {"type": "sessionReference", "value": "session-001"}
    ],
    "input": [
        {"type": "text", "content": "What is the weather in San Francisco?"}
    ]
}

# Example 2: Streaming request with debug
EXAMPLE_STREAM_REQUEST: ExecuteRunRequest = {
    "sessionIdentity": [
        {"type": "userReference", "value": "user-002"},
        {"type": "sessionReference", "value": "session-002"}
    ],
    "input": [
        {"type": "text", "content": "Explain quantum computing"}
    ],
    "stream": {
        "enable": True,
        "streamMode": "tokens"
    },
    "debug": {
        "enable": True
    }
}

# Example 3: Request with metadata
EXAMPLE_METADATA_REQUEST: ExecuteRunRequest = {
    "sessionIdentity": [
        {"type": "userReference", "value": "user-003"}
    ],
    "input": [
        {"type": "text", "content": "Analyze this data"}
    ],
    "metaData": {
        "userId": "user-123",
        "requestSource": "cli"
    }
}
