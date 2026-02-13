"""
Kore.ai Agentic App Platform API Reference

This module provides type definitions, constants, and reference documentation
for the Kore.ai Agentic App Platform REST API.

Base URL: https://agent-platform.kore.ai/api/v2
Documentation: See memory/kore-ai-api.md for detailed API documentation
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
    """Debug verbosity level"""
    ALL = "all"          # Full debug information
    SUMMARY = "summary"  # Summary debug information
    OFF = "off"          # No debug information (default)


class RunStatus(str, Enum):
    """Status of an agentic run"""
    PENDING = "pending"    # Run is queued
    RUNNING = "running"    # Run is in progress
    SUCCESS = "success"    # Run completed successfully
    FAILED = "failed"      # Run failed with error


# ============================================================================
# Type Definitions - Request Bodies
# ============================================================================

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
        mode: Streaming mode (tokens, messages, or custom)
        customEventNames: List of custom event names to stream (when mode is custom)
    """
    mode: Literal["tokens", "messages", "custom"]
    customEventNames: list[str]


class DebugConfig(TypedDict, total=False):
    """
    Debug configuration for execute run.

    Attributes:
        mode: Debug verbosity level (all, summary, or off)
        streamDebugData: Whether to stream debug data in real-time
    """
    mode: Literal["all", "summary", "off"]
    streamDebugData: bool


class AgentSpecificInput(TypedDict):
    """
    Direct agent invocation input.

    Attributes:
        agentId: ID of the specific agent to invoke
        input: Input text for the agent
    """
    agentId: str
    input: str


class ExecuteRunRequest(TypedDict, total=False):
    """
    Request body for POST /apps/<AppID>/environments/<EnvName>/runs/execute

    Attributes:
        sessionIdentity: Unique session identifier for conversation continuity (required)
        async: Execute asynchronously (default: false)
        query: User query/input (required unless agentSpecificInput provided)
        stream: Streaming configuration
        debug: Debug configuration
        files: Array of file attachments
        metaData: Custom metadata key-value pairs
        agentSpecificInput: Direct agent invocation
        triggerToolIds: Specific tool IDs to trigger
        skipCache: Bypass cache for fresh responses (default: false)
    """
    sessionIdentity: str  # Required
    async_: bool  # Using async_ to avoid Python keyword conflict
    query: str
    stream: StreamConfig
    debug: DebugConfig
    files: list[FileAttachment]
    metaData: dict[str, Any]
    agentSpecificInput: AgentSpecificInput
    triggerToolIds: list[str]
    skipCache: bool


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
        env_name: Environment name (e.g., "production", "staging")

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
        env_name: Environment name (e.g., "production", "staging")
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
# Usage Examples (for reference)
# ============================================================================

# Example 1: Basic synchronous request
EXAMPLE_SYNC_REQUEST: ExecuteRunRequest = {
    "sessionIdentity": "user-session-001",
    "query": "What is the weather in San Francisco?"
}

# Example 2: Streaming request with debug
EXAMPLE_STREAM_REQUEST: ExecuteRunRequest = {
    "sessionIdentity": "user-session-002",
    "query": "Explain quantum computing",
    "stream": {
        "mode": "tokens"
    },
    "debug": {
        "mode": "all",
        "streamDebugData": True
    }
}

# Example 3: Asynchronous request with metadata
EXAMPLE_ASYNC_REQUEST: ExecuteRunRequest = {
    "sessionIdentity": "user-session-003",
    "async_": True,
    "query": "Analyze this large dataset",
    "metaData": {
        "userId": "user-123",
        "requestSource": "cli"
    },
    "skipCache": True
}

# Example 4: Request with file attachments
EXAMPLE_FILE_REQUEST: ExecuteRunRequest = {
    "sessionIdentity": "user-session-004",
    "query": "Analyze this document",
    "files": [
        {
            "fileUrl": "https://example.com/document.pdf",
            "fileName": "document.pdf"
        }
    ]
}
