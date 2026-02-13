"""
Custom exceptions for Agentic API CLI.
"""


class AgenticAPIError(Exception):
    """Base exception for all Agentic API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(AgenticAPIError):
    """Raised when authentication fails (invalid API key)."""
    pass


class ConfigurationError(AgenticAPIError):
    """Raised when configuration is invalid or missing."""
    pass


class APIRequestError(AgenticAPIError):
    """Raised when an API request fails."""
    pass


class APIResponseError(AgenticAPIError):
    """Raised when the API returns an error response."""
    pass


class TimeoutError(AgenticAPIError):
    """Raised when a request times out."""
    pass


class RunNotFoundError(AgenticAPIError):
    """Raised when a run ID is not found."""
    pass


class ValidationError(AgenticAPIError):
    """Raised when input validation fails."""
    pass
