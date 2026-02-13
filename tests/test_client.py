"""
Unit tests for API client.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from agentic_api_cli.client import AgenticAPIClient
from agentic_api_cli.config import Config
from agentic_api_cli.exceptions import (
    APIRequestError,
    APIResponseError,
    AuthenticationError,
    RunNotFoundError,
    TimeoutError,
    ValidationError,
)


@pytest.fixture
def mock_config(monkeypatch):
    """Create a mock configuration."""
    monkeypatch.setenv("KOREAI_API_KEY", "test-api-key")
    monkeypatch.setenv("KOREAI_APP_ID", "test-app-id")
    monkeypatch.setenv("KOREAI_ENV_NAME", "test-env")
    return Config()


@pytest.fixture
def client(mock_config):
    """Create a test client."""
    return AgenticAPIClient(mock_config)


class TestAgenticAPIClientInit:
    """Test client initialization."""

    def test_init_sets_config(self, mock_config):
        """Test that initialization sets configuration."""
        client = AgenticAPIClient(mock_config)
        assert client.config == mock_config

    def test_init_creates_session(self, mock_config):
        """Test that initialization creates requests session."""
        client = AgenticAPIClient(mock_config)
        assert isinstance(client.session, requests.Session)

    def test_init_sets_headers(self, mock_config):
        """Test that initialization sets headers."""
        client = AgenticAPIClient(mock_config)
        assert "x-api-key" in client.session.headers
        assert client.session.headers["x-api-key"] == "test-api-key"

    def test_repr(self, mock_config):
        """Test string representation."""
        client = AgenticAPIClient(mock_config)
        repr_str = repr(client)
        assert "test-app-id" in repr_str
        assert "test-env" in repr_str


class TestExecuteRun:
    """Test execute_run method."""

    def test_execute_run_validation_empty_query(self, client):
        """Test that empty query raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            client.execute_run(query="", session_identity="session-123")
        assert "Query cannot be empty" in str(exc_info.value)

    def test_execute_run_validation_empty_session(self, client):
        """Test that empty session identity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            client.execute_run(query="Hello", session_identity="")
        assert "Session identity cannot be empty" in str(exc_info.value)

    def test_execute_run_validation_invalid_stream_mode(self, client):
        """Test that invalid stream mode raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            client.execute_run(
                query="Hello",
                session_identity="session-123",
                stream_mode="invalid",
            )
        assert "Invalid stream mode" in str(exc_info.value)

    @patch("requests.Session.post")
    def test_execute_run_success(self, mock_post, client):
        """Test successful execute run."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "output": [{"type": "text", "content": "Hello!"}],
            "sessionInfo": {"runId": "run-123"},
        }
        mock_response.text = "success"
        mock_post.return_value = mock_response

        result = client.execute_run(query="Hello", session_identity="session-123")

        assert result["sessionInfo"]["runId"] == "run-123"
        mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_execute_run_with_streaming(self, mock_post, client):
        """Test execute run with streaming enabled."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"output": [], "sessionInfo": {}}
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.execute_run(
            query="Hello",
            session_identity="session-123",
            stream_enabled=True,
            stream_mode="tokens",
        )

        # Verify stream config was included in request
        call_args = mock_post.call_args
        request_body = call_args[1]["json"]
        assert "stream" in request_body
        assert request_body["stream"]["enable"] is True
        assert request_body["stream"]["streamMode"] == "tokens"

    @patch("requests.Session.post")
    def test_execute_run_with_debug(self, mock_post, client):
        """Test execute run with debug enabled."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"output": [], "sessionInfo": {}}
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.execute_run(
            query="Hello",
            session_identity="session-123",
            debug_enabled=True,
        )

        # Verify debug config was included in request
        call_args = mock_post.call_args
        request_body = call_args[1]["json"]
        assert "debug" in request_body
        assert request_body["debug"]["enable"] is True

    @patch("requests.Session.post")
    def test_execute_run_with_metadata(self, mock_post, client):
        """Test execute run with metadata."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"output": [], "sessionInfo": {}}
        mock_response.text = "success"
        mock_post.return_value = mock_response

        metadata = {"key1": "value1", "key2": "value2"}
        client.execute_run(
            query="Hello",
            session_identity="session-123",
            metadata=metadata,
        )

        # Verify metadata was included in request
        call_args = mock_post.call_args
        request_body = call_args[1]["json"]
        assert "metaData" in request_body
        assert request_body["metaData"] == metadata

    @patch("requests.Session.post")
    def test_execute_run_with_debug_mode(self, mock_post, client):
        """Test execute run with debug mode."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"output": [], "sessionInfo": {}}
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.execute_run(
            query="Hello",
            session_identity="session-123",
            debug_enabled=True,
            debug_mode="thoughts",
        )

        # Verify debug config with debugMode was included in request
        call_args = mock_post.call_args
        request_body = call_args[1]["json"]
        assert "debug" in request_body
        assert request_body["debug"]["enable"] is True
        assert request_body["debug"]["debugMode"] == "thoughts"

    @patch("requests.Session.post")
    def test_execute_run_debug_without_mode(self, mock_post, client):
        """Test execute run with debug but no mode specified."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"output": [], "sessionInfo": {}}
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.execute_run(
            query="Hello",
            session_identity="session-123",
            debug_enabled=True,
        )

        # Verify debug config was included without debugMode
        call_args = mock_post.call_args
        request_body = call_args[1]["json"]
        assert "debug" in request_body
        assert request_body["debug"]["enable"] is True
        assert "debugMode" not in request_body["debug"]

    def test_execute_run_validation_invalid_debug_mode(self, client):
        """Test that invalid debug mode raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            client.execute_run(
                query="Hello",
                session_identity="session-123",
                debug_enabled=True,
                debug_mode="invalid",  # truly invalid mode
            )
        assert "Invalid debug mode" in str(exc_info.value)

    @patch("requests.Session.post")
    def test_execute_run_401_error(self, mock_post, client):
        """Test execute run with 401 authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError) as exc_info:
            client.execute_run(query="Hello", session_identity="session-123")
        assert "Authentication failed" in str(exc_info.value)

    @patch("requests.Session.post")
    def test_execute_run_404_error(self, mock_post, client):
        """Test execute run with 404 not found error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_post.return_value = mock_response

        with pytest.raises(APIRequestError) as exc_info:
            client.execute_run(query="Hello", session_identity="session-123")
        assert "Resource not found" in str(exc_info.value)

    @patch("requests.Session.post")
    def test_execute_run_429_error(self, mock_post, client):
        """Test execute run with 429 rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Too many requests"
        mock_post.return_value = mock_response

        with pytest.raises(APIRequestError) as exc_info:
            client.execute_run(query="Hello", session_identity="session-123")
        assert "Rate limit exceeded" in str(exc_info.value)

    @patch("requests.Session.post")
    def test_execute_run_timeout(self, mock_post, client):
        """Test execute run with timeout."""
        mock_post.side_effect = requests.Timeout()

        with pytest.raises(TimeoutError) as exc_info:
            client.execute_run(query="Hello", session_identity="session-123")
        assert "timed out" in str(exc_info.value)

    @patch("requests.Session.post")
    def test_execute_run_request_exception(self, mock_post, client):
        """Test execute run with request exception."""
        mock_post.side_effect = requests.RequestException("Connection error")

        with pytest.raises(APIRequestError) as exc_info:
            client.execute_run(query="Hello", session_identity="session-123")
        assert "Request failed" in str(exc_info.value)


class TestGetRunStatus:
    """Test get_run_status method."""

    def test_get_run_status_validation_empty_run_id(self, client):
        """Test that empty run ID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            client.get_run_status("")
        assert "Run ID cannot be empty" in str(exc_info.value)

    @patch("requests.Session.post")
    def test_get_run_status_success(self, mock_post, client):
        """Test successful get run status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "runId": "run-123",
        }
        mock_response.text = "success"
        mock_post.return_value = mock_response

        result = client.get_run_status("run-123")

        assert result["status"] == "success"
        assert result["runId"] == "run-123"

    @patch("requests.Session.post")
    def test_get_run_status_404_error(self, mock_post, client):
        """Test get run status with 404 not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_post.return_value = mock_response

        with pytest.raises(RunNotFoundError) as exc_info:
            client.get_run_status("run-123")
        assert "not found" in str(exc_info.value)


class TestPollRunStatus:
    """Test poll_run_status method."""

    @patch("requests.Session.post")
    def test_poll_run_status_immediate_success(self, mock_post, client):
        """Test polling that completes immediately."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = "success"
        mock_post.return_value = mock_response

        result = client.poll_run_status("run-123", max_attempts=5, interval=1)

        assert result["status"] == "success"
        assert mock_post.call_count == 1

    @patch("requests.Session.post")
    @patch("time.sleep")
    def test_poll_run_status_eventual_success(self, mock_sleep, mock_post, client):
        """Test polling that eventually succeeds."""
        # First two calls return running, third returns success
        responses = [
            Mock(status_code=200, json=lambda: {"status": "running"}, text="ok"),
            Mock(status_code=200, json=lambda: {"status": "running"}, text="ok"),
            Mock(status_code=200, json=lambda: {"status": "success"}, text="ok"),
        ]
        mock_post.side_effect = responses

        result = client.poll_run_status("run-123", max_attempts=5, interval=1)

        assert result["status"] == "success"
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep called between attempts

    @patch("requests.Session.post")
    def test_poll_run_status_failed(self, mock_post, client):
        """Test polling with failed run."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "failed",
            "error": {"message": "Run failed"},
        }
        mock_response.text = "success"
        mock_post.return_value = mock_response

        with pytest.raises(APIResponseError) as exc_info:
            client.poll_run_status("run-123", max_attempts=5, interval=1)
        assert "Run failed" in str(exc_info.value)

    @patch("requests.Session.post")
    @patch("time.sleep")
    def test_poll_run_status_timeout(self, mock_sleep, mock_post, client):
        """Test polling timeout."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "running"}
        mock_response.text = "success"
        mock_post.return_value = mock_response

        with pytest.raises(TimeoutError) as exc_info:
            client.poll_run_status("run-123", max_attempts=3, interval=1)
        assert "did not complete" in str(exc_info.value)


class TestClientContextManager:
    """Test context manager functionality."""

    def test_context_manager_enter(self, mock_config):
        """Test context manager __enter__."""
        with AgenticAPIClient(mock_config) as client:
            assert isinstance(client, AgenticAPIClient)

    def test_context_manager_exit(self, mock_config):
        """Test context manager __exit__ closes session."""
        client = AgenticAPIClient(mock_config)
        with patch.object(client.session, "close") as mock_close:
            with client:
                pass
            mock_close.assert_called_once()

    def test_close_method(self, client):
        """Test close method."""
        with patch.object(client.session, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()
