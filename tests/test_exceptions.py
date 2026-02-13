"""
Unit tests for custom exceptions.
"""

import pytest

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


def test_agentic_api_error_base():
    """Test base AgenticAPIError."""
    error = AgenticAPIError("Test error")
    assert str(error) == "Test error"
    assert error.message == "Test error"
    assert error.status_code is None


def test_agentic_api_error_with_status():
    """Test AgenticAPIError with status code."""
    error = AgenticAPIError("Test error", status_code=500)
    assert error.message == "Test error"
    assert error.status_code == 500


def test_configuration_error():
    """Test ConfigurationError."""
    error = ConfigurationError("Config missing")
    assert isinstance(error, AgenticAPIError)
    assert str(error) == "Config missing"


def test_authentication_error():
    """Test AuthenticationError."""
    error = AuthenticationError("Invalid API key", status_code=401)
    assert isinstance(error, AgenticAPIError)
    assert error.status_code == 401


def test_validation_error():
    """Test ValidationError."""
    error = ValidationError("Invalid input")
    assert isinstance(error, AgenticAPIError)
    assert str(error) == "Invalid input"


def test_api_request_error():
    """Test APIRequestError."""
    error = APIRequestError("Request failed", status_code=500)
    assert isinstance(error, AgenticAPIError)
    assert error.status_code == 500


def test_api_response_error():
    """Test APIResponseError."""
    error = APIResponseError("Bad response", status_code=400)
    assert isinstance(error, AgenticAPIError)
    assert error.status_code == 400


def test_timeout_error():
    """Test TimeoutError."""
    error = TimeoutError("Request timed out")
    assert isinstance(error, AgenticAPIError)
    assert str(error) == "Request timed out"


def test_run_not_found_error():
    """Test RunNotFoundError."""
    error = RunNotFoundError("Run not found", status_code=404)
    assert isinstance(error, AgenticAPIError)
    assert error.status_code == 404
