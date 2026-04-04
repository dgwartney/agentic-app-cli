"""
Unit tests for AgentTestSession testing utility.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from agxr.testing import AgentTestSession


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_SESSION_RESPONSE = {
    "sessionReference": "sr-test-abc123",
    "sessionId": "si-test-xyz789",
    "userReference": "test-user-001",
    "userId": "uid-001",
    "status": "idle",
}

MOCK_EXECUTE_RESPONSE = {
    "output": [{"type": "text", "content": "Hello from agent"}],
    "sessionInfo": {"runId": "r-001", "status": "idle"},
}

MOCK_TERMINATE_RESPONSE = {
    "status": "idle",
    "sessionReference": "sr-test-abc123",
    "userReference": "test-user-001",
    "attachments": [],
}


@pytest.fixture
def mock_client():
    """Create a mock AgenticAPIClient with default return values."""
    client = Mock()
    client.create_session.return_value = MOCK_SESSION_RESPONSE.copy()
    client.execute_run.return_value = MOCK_EXECUTE_RESPONSE.copy()
    client.terminate_session.return_value = MOCK_TERMINATE_RESPONSE.copy()
    return client


@pytest.fixture
def session(mock_client, monkeypatch):
    """Create an AgentTestSession with a mocked API client."""
    monkeypatch.setenv("KOREAI_API_KEY", "test-key")
    monkeypatch.setenv("KOREAI_APP_ID", "test-app")
    monkeypatch.setenv("KOREAI_ENV_NAME", "test-env")
    with patch("agxr.testing.AgenticAPIClient", return_value=mock_client):
        sess = AgentTestSession()
    sess._mock_client = mock_client
    return sess


# ---------------------------------------------------------------------------
# Tests: __init__
# ---------------------------------------------------------------------------

class TestAgentTestSessionInit:
    """Test AgentTestSession initialization."""

    def test_calls_create_session_on_init(self, monkeypatch, mock_client):
        """Test that __init__ calls create_session to establish a server-side session."""
        monkeypatch.setenv("KOREAI_API_KEY", "key")
        monkeypatch.setenv("KOREAI_APP_ID", "app")
        monkeypatch.setenv("KOREAI_ENV_NAME", "env")
        with patch("agxr.testing.AgenticAPIClient", return_value=mock_client):
            AgentTestSession()
        mock_client.create_session.assert_called_once()

    def test_stores_session_reference_from_api(self, session):
        """Test that session_id returns the API-assigned sessionReference."""
        assert session.session_id == "sr-test-abc123"

    def test_history_empty_on_init(self, session):
        """Test that conversation history starts empty."""
        assert session.history == []

    def test_last_response_none_on_init(self, session):
        """Test that last_response_raw starts as None."""
        assert session.last_response_raw is None

    def test_user_reference_is_test_prefixed(self, monkeypatch, mock_client):
        """Test that the generated user_reference has the test- prefix."""
        monkeypatch.setenv("KOREAI_API_KEY", "key")
        monkeypatch.setenv("KOREAI_APP_ID", "app")
        monkeypatch.setenv("KOREAI_ENV_NAME", "env")
        with patch("agxr.testing.AgenticAPIClient", return_value=mock_client):
            AgentTestSession()
        call_args = mock_client.create_session.call_args
        user_ref = call_args[0][0]
        assert user_ref.startswith("test-")


# ---------------------------------------------------------------------------
# Tests: send
# ---------------------------------------------------------------------------

class TestAgentTestSessionSend:
    """Test AgentTestSession.send()."""

    def test_send_calls_execute_run_with_session_reference(self, session, mock_client):
        """Test that send() passes the stored sessionReference to execute_run."""
        session.send("Hello")
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["session_identity"] == "sr-test-abc123"

    def test_send_returns_extracted_text(self, session):
        """Test that send() returns the agent's text response."""
        result = session.send("Hello")
        assert result == "Hello from agent"

    def test_send_appends_user_and_agent_to_history(self, session):
        """Test that send() appends both user and agent turns to history."""
        session.send("Hello")
        assert len(session.history) == 2
        assert session.history[0] == {"role": "user", "text": "Hello"}
        assert session.history[1] == {"role": "agent", "text": "Hello from agent"}

    def test_send_accumulates_history_across_turns(self, session):
        """Test that history accumulates across multiple send() calls."""
        session.send("Turn 1")
        session.send("Turn 2")
        assert len(session.history) == 4

    def test_send_stores_raw_response(self, session, mock_client):
        """Test that send() stores the raw API response in last_response_raw."""
        session.send("Hello")
        assert session.last_response_raw == MOCK_EXECUTE_RESPONSE

    def test_send_with_multiple_text_items_joins_with_newline(self, session, mock_client):
        """Test that multiple text output items are joined with newlines."""
        mock_client.execute_run.return_value = {
            "output": [
                {"type": "text", "content": "Part 1"},
                {"type": "text", "content": "Part 2"},
            ]
        }
        result = session.send("Hello")
        assert result == "Part 1\nPart 2"

    def test_send_ignores_non_text_output_items(self, session, mock_client):
        """Test that non-text output items are ignored."""
        mock_client.execute_run.return_value = {
            "output": [
                {"type": "image", "content": "data:image/png;base64,..."},
                {"type": "text", "content": "Text only"},
            ]
        }
        result = session.send("Hello")
        assert result == "Text only"

    def test_send_returns_empty_string_for_no_output(self, session, mock_client):
        """Test that send() returns empty string when output array is empty."""
        mock_client.execute_run.return_value = {"output": []}
        result = session.send("Hello")
        assert result == ""


# ---------------------------------------------------------------------------
# Tests: reset
# ---------------------------------------------------------------------------

class TestAgentTestSessionReset:
    """Test AgentTestSession.reset()."""

    def test_reset_calls_terminate_session(self, session, mock_client):
        """Test that reset() terminates the current session."""
        session.reset()
        mock_client.terminate_session.assert_called_with("sr-test-abc123")

    def test_reset_calls_create_session_again(self, session, mock_client):
        """Test that reset() creates a new session after terminating the old one."""
        initial_call_count = mock_client.create_session.call_count
        session.reset()
        assert mock_client.create_session.call_count == initial_call_count + 1

    def test_reset_clears_history(self, session):
        """Test that reset() clears the conversation history."""
        session.send("Turn 1")
        assert len(session.history) == 2
        session.reset()
        assert session.history == []

    def test_reset_clears_last_response(self, session):
        """Test that reset() clears last_response_raw."""
        session.send("Hello")
        assert session.last_response_raw is not None
        session.reset()
        assert session.last_response_raw is None

    def test_reset_updates_session_reference(self, session, mock_client):
        """Test that reset() updates session_id with the new sessionReference."""
        mock_client.create_session.return_value = {
            "sessionReference": "sr-new-session-456",
            "sessionId": "si-new-456",
            "status": "idle",
        }
        session.reset()
        assert session.session_id == "sr-new-session-456"


# ---------------------------------------------------------------------------
# Tests: close
# ---------------------------------------------------------------------------

class TestAgentTestSessionClose:
    """Test AgentTestSession.close()."""

    def test_close_calls_terminate_session(self, session, mock_client):
        """Test that close() terminates the Kore.ai session."""
        session.close()
        mock_client.terminate_session.assert_called_with("sr-test-abc123")

    def test_close_calls_client_close(self, session, mock_client):
        """Test that close() closes the underlying HTTP client."""
        session.close()
        mock_client.close.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: context manager
# ---------------------------------------------------------------------------

class TestAgentTestSessionContextManager:
    """Test AgentTestSession context manager protocol."""

    def test_enter_returns_self(self, session):
        """Test that __enter__ returns the session instance."""
        result = session.__enter__()
        assert result is session

    def test_exit_calls_close(self, monkeypatch, mock_client):
        """Test that __exit__ calls close(), which terminates the session."""
        monkeypatch.setenv("KOREAI_API_KEY", "key")
        monkeypatch.setenv("KOREAI_APP_ID", "app")
        monkeypatch.setenv("KOREAI_ENV_NAME", "env")
        with patch("agxr.testing.AgenticAPIClient", return_value=mock_client):
            with AgentTestSession() as sess:
                pass
        mock_client.terminate_session.assert_called_once()
        mock_client.close.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: __repr__
# ---------------------------------------------------------------------------

class TestAgentTestSessionRepr:
    """Test AgentTestSession string representation."""

    def test_repr_contains_session_reference(self, session):
        """Test that repr includes the session reference."""
        r = repr(session)
        assert "sr-test-abc123" in r

    def test_repr_contains_env_name(self, session):
        """Test that repr includes the environment name."""
        r = repr(session)
        assert "test-env" in r
