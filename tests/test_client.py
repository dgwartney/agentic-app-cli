"""
Unit tests for API client.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from agxr.client import AgenticAPIClient
from agxr.config import Config
from agxr.exceptions import (
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
        # Streaming calls iter_lines(); return an empty iterator to avoid processing
        mock_response.iter_lines.return_value = iter([])
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


class TestCreateSession:
    """Test create_session method."""

    MOCK_SESSION_RESPONSE = {
        "sessionReference": "sr-abc123",
        "sessionId": "si-xyz789",
        "userReference": "user-001",
        "userId": "uid-001",
        "status": "idle",
        "allowedMimeTypes": ["application/pdf", "image/png"],
        "fileUploadConfig": {"enabled": True, "maxFileCount": 5, "maxFileSize": 10.0},
    }

    @patch("requests.Session.post")
    def test_success_returns_session_data(self, mock_post, client):
        """Test successful session creation returns session metadata."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_SESSION_RESPONSE
        mock_response.text = '{"sessionReference": "sr-abc123"}'
        mock_post.return_value = mock_response

        result = client.create_session("user-001")

        assert result["sessionReference"] == "sr-abc123"
        assert result["sessionId"] == "si-xyz789"
        assert result["status"] == "idle"

    def test_validation_empty_user_reference(self, client):
        """Test that empty user_reference raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            client.create_session("")
        assert "user_reference cannot be empty" in str(exc_info.value)

    def test_validation_whitespace_user_reference(self, client):
        """Test that whitespace-only user_reference raises ValidationError."""
        with pytest.raises(ValidationError):
            client.create_session("   ")

    @patch("requests.Session.post")
    def test_authentication_error_401(self, mock_post, client):
        """Test that 401 response raises AuthenticationError."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            client.create_session("user-001")

    @patch("requests.Session.post")
    def test_api_error_500(self, mock_post, client):
        """Test that 500 response raises APIResponseError."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": {"message": "Internal server error"}}
        mock_response.text = '{"error": {"message": "Internal server error"}}'
        mock_post.return_value = mock_response

        with pytest.raises(APIResponseError):
            client.create_session("user-001")

    @patch("requests.Session.post")
    def test_request_error_on_network_failure(self, mock_post, client):
        """Test that network errors raise APIRequestError."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection refused")

        with pytest.raises(APIRequestError):
            client.create_session("user-001")

    @patch("requests.Session.post")
    def test_timeout_error(self, mock_post, client):
        """Test that timeouts raise AgenticTimeoutError."""
        from agxr.exceptions import TimeoutError as AgenticTimeoutError

        mock_post.side_effect = requests.exceptions.Timeout()

        with pytest.raises(AgenticTimeoutError):
            client.create_session("user-001")

    @patch("requests.Session.post")
    def test_with_session_reference_included_in_body(self, mock_post, client):
        """Test that session_reference is included in request body when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_SESSION_RESPONSE
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.create_session("user-001", session_reference="sr-custom-123")

        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"]
        identity_types = [item["type"] for item in body["sessionIdentity"]]
        assert "sessionReference" in identity_types

    @patch("requests.Session.post")
    def test_with_source_included_in_body(self, mock_post, client):
        """Test that source is included in request body when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_SESSION_RESPONSE
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.create_session("user-001", source="AIS-AA")

        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"]
        assert body["source"] == "AIS-AA"

    @patch("requests.Session.post")
    def test_source_omitted_when_none(self, mock_post, client):
        """Test that source key is absent from body when not provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_SESSION_RESPONSE
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.create_session("user-001")

        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"]
        assert "source" not in body


class TestTerminateSession:
    """Test terminate_session method."""

    MOCK_TERMINATE_RESPONSE = {
        "status": "idle",
        "sessionReference": "sr-abc123",
        "userReference": "user-001",
        "userId": "uid-001",
        "appId": "app-001",
        "attachments": [],
    }

    @patch("requests.Session.post")
    def test_success_returns_response(self, mock_post, client):
        """Test successful session termination returns metadata."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_TERMINATE_RESPONSE
        mock_response.text = "success"
        mock_post.return_value = mock_response

        result = client.terminate_session("sr-abc123")

        assert result["sessionReference"] == "sr-abc123"

    def test_validation_empty_session_reference(self, client):
        """Test that empty session_reference raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            client.terminate_session("")
        assert "session_reference cannot be empty" in str(exc_info.value)

    def test_validation_whitespace_session_reference(self, client):
        """Test that whitespace-only session_reference raises ValidationError."""
        with pytest.raises(ValidationError):
            client.terminate_session("   ")

    @patch("requests.Session.post")
    def test_authentication_error_401(self, mock_post, client):
        """Test that 401 response raises AuthenticationError."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            client.terminate_session("sr-abc123")

    @patch("requests.Session.post")
    def test_not_found_404(self, mock_post, client):
        """Test that 404 response raises RunNotFoundError."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": {"message": "Session not found"}}
        mock_response.text = "not found"
        mock_post.return_value = mock_response

        with pytest.raises(RunNotFoundError):
            client.terminate_session("sr-nonexistent")

    @patch("requests.Session.post")
    def test_api_error_500(self, mock_post, client):
        """Test that 500 response raises APIResponseError."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": {"message": "Internal server error"}}
        mock_response.text = "error"
        mock_post.return_value = mock_response

        with pytest.raises(APIResponseError):
            client.terminate_session("sr-abc123")

    @patch("requests.Session.post")
    def test_request_error_on_network_failure(self, mock_post, client):
        """Test that network errors raise APIRequestError."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        with pytest.raises(APIRequestError):
            client.terminate_session("sr-abc123")

    @patch("requests.Session.post")
    def test_timeout_error(self, mock_post, client):
        """Test that timeouts raise AgenticTimeoutError."""
        from agxr.exceptions import TimeoutError as AgenticTimeoutError

        mock_post.side_effect = requests.exceptions.Timeout()

        with pytest.raises(AgenticTimeoutError):
            client.terminate_session("sr-abc123")

    @patch("requests.Session.post")
    def test_body_uses_session_reference_type(self, mock_post, client):
        """Test that request body uses sessionReference identity type."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_TERMINATE_RESPONSE
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.terminate_session("sr-abc123")

        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"]
        assert body["sessionIdentity"][0]["type"] == "sessionReference"
        assert body["sessionIdentity"][0]["value"] == "sr-abc123"


class TestExecuteRunExtensions:
    """Test new optional parameters added to execute_run."""

    MOCK_EXECUTE_RESPONSE = {
        "output": [{"type": "text", "content": "Hello!"}],
        "sessionInfo": {"runId": "r-001", "status": "idle"},
    }

    @patch("requests.Session.post")
    def test_is_async_true_adds_field_to_body(self, mock_post, client):
        """Test that is_async=True adds isAsync: True to request body."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_EXECUTE_RESPONSE
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.execute_run("Hello", "session-1", is_async=True)

        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"]
        assert body.get("isAsync") is True

    @patch("requests.Session.post")
    def test_is_async_false_omits_field_from_body(self, mock_post, client):
        """Test that is_async=False (default) does not add isAsync to body."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_EXECUTE_RESPONSE
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.execute_run("Hello", "session-1")

        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"]
        assert "isAsync" not in body

    @patch("requests.Session.post")
    def test_callback_url_included_in_body(self, mock_post, client):
        """Test that callback_url is included in body when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_EXECUTE_RESPONSE
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.execute_run(
            "Hello", "session-1",
            is_async=True,
            callback_url="https://example.com/callback",
        )

        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"]
        assert body.get("callbackUrl") == "https://example.com/callback"

    @patch("requests.Session.post")
    def test_callback_token_included_in_body(self, mock_post, client):
        """Test that callback_token is included in body when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_EXECUTE_RESPONSE
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.execute_run(
            "Hello", "session-1",
            is_async=True,
            callback_token="my-secret-token",
        )

        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"]
        assert body.get("callbackToken") == "my-secret-token"

    @patch("requests.Session.post")
    def test_callback_omitted_when_none(self, mock_post, client):
        """Test that callbackUrl and callbackToken are absent when not provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_EXECUTE_RESPONSE
        mock_response.text = "success"
        mock_post.return_value = mock_response

        client.execute_run("Hello", "session-1")

        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"]
        assert "callbackUrl" not in body
        assert "callbackToken" not in body
