"""
Unit tests for AgenticMCPServer and AgentSession.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from agxr.exceptions import (
    AgenticAPIError,
    APIResponseError,
    AuthenticationError,
    ConfigurationError,
    RunNotFoundError,
)
from agxr.mcp_server import AgentSession, AgenticMCPServer


# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

MOCK_SESSION_RESPONSE = {
    "sessionReference": "sr-mcp-abc123",
    "sessionId": "si-mcp-xyz789",
    "userReference": "mcp-user-001",
    "status": "idle",
}

MOCK_EXECUTE_RESPONSE = {
    "output": [{"type": "text", "content": "Agent reply"}],
    "sessionInfo": {"runId": "r-abc-001", "status": "idle"},
}

MOCK_RUN_STATUS_RESPONSE = {
    "run": {
        "status": "success",
        "kwargs": {
            "output": [{"type": "text", "content": "Run output"}]
        },
    }
}

MOCK_TERMINATE_RESPONSE = {
    "status": "idle",
    "sessionReference": "sr-mcp-abc123",
    "attachments": [],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    """Create a mock AgenticAPIClient."""
    client = Mock()
    client.create_session.return_value = MOCK_SESSION_RESPONSE.copy()
    client.execute_run.return_value = MOCK_EXECUTE_RESPONSE.copy()
    client.terminate_session.return_value = MOCK_TERMINATE_RESPONSE.copy()
    client.get_run_status.return_value = MOCK_RUN_STATUS_RESPONSE.copy()
    return client


@pytest.fixture
def server(mock_client, monkeypatch):
    """Create an AgenticMCPServer with mocked dependencies."""
    monkeypatch.setenv("KOREAI_API_KEY", "test-key")
    monkeypatch.setenv("KOREAI_APP_ID", "test-app")
    monkeypatch.setenv("KOREAI_ENV_NAME", "test-env")
    with patch("agxr.mcp_server.AgenticAPIClient", return_value=mock_client):
        srv = AgenticMCPServer()
    srv._mock_client = mock_client
    return srv


@pytest.fixture
def server_with_session(server, mock_client):
    """Server that already has one active session."""
    mock_client.create_session.return_value = MOCK_SESSION_RESPONSE.copy()
    result = server.start_session(user_reference="test-user")
    mcp_session_id = result["mcp_session_id"]
    return server, mcp_session_id


# ---------------------------------------------------------------------------
# Tests: AgentSession
# ---------------------------------------------------------------------------

class TestAgentSession:
    """Test AgentSession state management."""

    def test_init_sets_all_attributes(self):
        sess = AgentSession("mcp-1", "sr-ref-1", "si-id-1", "user-1")
        assert sess.mcp_session_id == "mcp-1"
        assert sess.session_reference == "sr-ref-1"
        assert sess.session_id == "si-id-1"
        assert sess.user_reference == "user-1"

    def test_history_starts_empty(self):
        sess = AgentSession("mcp-1", "sr-ref-1", "si-id-1", "user-1")
        assert sess.history == []

    def test_add_turn_appends_user_and_agent(self):
        sess = AgentSession("mcp-1", "sr-ref-1", "si-id-1", "user-1")
        sess.add_turn("Hello", "Hi there")
        assert sess.history[0] == {"role": "user", "text": "Hello"}
        assert sess.history[1] == {"role": "agent", "text": "Hi there"}

    def test_add_turn_accumulates(self):
        sess = AgentSession("mcp-1", "sr-ref-1", "si-id-1", "user-1")
        sess.add_turn("Turn 1", "Reply 1")
        sess.add_turn("Turn 2", "Reply 2")
        assert len(sess.history) == 4

    def test_reset_clears_history(self):
        sess = AgentSession("mcp-1", "sr-ref-1", "si-id-1", "user-1")
        sess.add_turn("Hello", "Hi")
        sess.reset()
        assert sess.history == []

    def test_repr_contains_session_id(self):
        sess = AgentSession("mcp-abc", "sr-ref-1", "si-id-1", "user-1")
        r = repr(sess)
        assert "mcp-abc" in r

    def test_repr_shows_turn_count(self):
        sess = AgentSession("mcp-1", "sr-ref-1", "si-id-1", "user-1")
        sess.add_turn("A", "B")
        assert "turns=1" in repr(sess)


# ---------------------------------------------------------------------------
# Tests: AgenticMCPServer.__init__
# ---------------------------------------------------------------------------

class TestAgenticMCPServerInit:
    """Test AgenticMCPServer initialization."""

    def test_sessions_dict_starts_empty(self, server):
        assert server._sessions == {}

    def test_mcp_instance_created(self, server):
        assert server.mcp is not None

    def test_config_validation_called(self, monkeypatch):
        monkeypatch.setenv("KOREAI_API_KEY", "key")
        monkeypatch.setenv("KOREAI_APP_ID", "app")
        monkeypatch.setenv("KOREAI_ENV_NAME", "env")
        mock_client = Mock()
        with patch("agxr.mcp_server.AgenticAPIClient", return_value=mock_client):
            with patch("agxr.mcp_server.Config") as mock_config_cls:
                mock_config = Mock()
                mock_config_cls.return_value = mock_config
                AgenticMCPServer()
        mock_config.validate.assert_called_once()

    def test_config_error_propagates(self, monkeypatch):
        monkeypatch.setenv("KOREAI_API_KEY", "key")
        monkeypatch.setenv("KOREAI_APP_ID", "app")
        monkeypatch.setenv("KOREAI_ENV_NAME", "env")
        with patch("agxr.mcp_server.AgenticAPIClient"):
            with patch("agxr.mcp_server.Config") as mock_config_cls:
                mock_config = Mock()
                mock_config.validate.side_effect = ConfigurationError("Missing API key")
                mock_config_cls.return_value = mock_config
                with pytest.raises(ConfigurationError):
                    AgenticMCPServer()


# ---------------------------------------------------------------------------
# Tests: get_server_info
# ---------------------------------------------------------------------------

class TestGetServerInfo:
    """Test get_server_info tool."""

    def test_returns_app_id(self, server):
        result = server.get_server_info()
        assert result["app_id"] == server._config.app_id

    def test_returns_env_name(self, server):
        result = server.get_server_info()
        assert result["env_name"] == server._config.env_name

    def test_returns_base_url(self, server):
        result = server.get_server_info()
        assert "base_url" in result

    def test_returns_active_sessions_count(self, server):
        result = server.get_server_info()
        assert result["active_sessions"] == 0

    def test_active_sessions_reflects_open_sessions(self, server_with_session):
        server, _ = server_with_session
        result = server.get_server_info()
        assert result["active_sessions"] == 1

    def test_does_not_return_api_key(self, server):
        result = server.get_server_info()
        result_str = str(result)
        assert "api_key" not in result_str
        assert "test-key" not in result_str


# ---------------------------------------------------------------------------
# Tests: list_profiles
# ---------------------------------------------------------------------------

class TestListProfiles:
    """Test list_profiles tool."""

    def test_returns_profile_list(self, server):
        with patch("agxr.mcp_server.ProfileManager") as mock_pm_cls:
            mock_pm = Mock()
            mock_pm.list_profiles.return_value = ["prod", "staging"]
            mock_pm_cls.return_value = mock_pm
            result = server.list_profiles()
        assert result["profiles"] == ["prod", "staging"]

    def test_returns_count(self, server):
        with patch("agxr.mcp_server.ProfileManager") as mock_pm_cls:
            mock_pm = Mock()
            mock_pm.list_profiles.return_value = ["prod", "staging"]
            mock_pm_cls.return_value = mock_pm
            result = server.list_profiles()
        assert result["count"] == 2

    def test_returns_empty_list_when_no_profiles(self, server):
        with patch("agxr.mcp_server.ProfileManager") as mock_pm_cls:
            mock_pm = Mock()
            mock_pm.list_profiles.return_value = []
            mock_pm_cls.return_value = mock_pm
            result = server.list_profiles()
        assert result == {"profiles": [], "count": 0}

    def test_returns_error_on_exception(self, server):
        with patch("agxr.mcp_server.ProfileManager") as mock_pm_cls:
            mock_pm = Mock()
            mock_pm.list_profiles.side_effect = Exception("disk error")
            mock_pm_cls.return_value = mock_pm
            result = server.list_profiles()
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# Tests: start_session
# ---------------------------------------------------------------------------

class TestStartSession:
    """Test start_session tool."""

    def test_returns_success_status(self, server):
        result = server.start_session(user_reference="user-a")
        assert result["status"] == "success"

    def test_returns_mcp_session_id(self, server):
        result = server.start_session(user_reference="user-a")
        assert result["mcp_session_id"].startswith("mcp-")

    def test_calls_create_session(self, server, mock_client):
        server.start_session(user_reference="user-a")
        mock_client.create_session.assert_called_once_with("user-a")

    def test_autogenerates_user_reference_when_none(self, server, mock_client):
        server.start_session()
        call_args = mock_client.create_session.call_args[0][0]
        assert call_args.startswith("mcp-user-")

    def test_stores_session_in_dict(self, server):
        result = server.start_session(user_reference="user-a")
        mcp_id = result["mcp_session_id"]
        assert mcp_id in server._sessions

    def test_stored_session_has_correct_session_reference(self, server):
        result = server.start_session(user_reference="user-a")
        mcp_id = result["mcp_session_id"]
        session = server._sessions[mcp_id]
        assert session.session_reference == "sr-mcp-abc123"

    def test_returns_session_reference(self, server):
        result = server.start_session(user_reference="user-a")
        assert result["session_reference"] == "sr-mcp-abc123"

    def test_authentication_error_returns_error_dict(self, server, mock_client):
        mock_client.create_session.side_effect = AuthenticationError("Unauthorized")
        result = server.start_session(user_reference="user-a")
        assert result["status"] == "error"
        assert result["error_type"] == "authentication"

    def test_api_error_returns_error_dict(self, server, mock_client):
        mock_client.create_session.side_effect = APIResponseError("Server error")
        result = server.start_session(user_reference="user-a")
        assert result["status"] == "error"
        assert result["error_type"] == "api_error"


# ---------------------------------------------------------------------------
# Tests: end_session
# ---------------------------------------------------------------------------

class TestEndSession:
    """Test end_session tool."""

    def test_returns_terminated_status(self, server_with_session):
        server, mcp_id = server_with_session
        result = server.end_session(mcp_id)
        assert result["status"] == "terminated"

    def test_returns_mcp_session_id(self, server_with_session):
        server, mcp_id = server_with_session
        result = server.end_session(mcp_id)
        assert result["mcp_session_id"] == mcp_id

    def test_calls_terminate_session(self, server_with_session, mock_client):
        server, mcp_id = server_with_session
        session_ref = server._sessions[mcp_id].session_reference
        server.end_session(mcp_id)
        mock_client.terminate_session.assert_called_with(session_ref)

    def test_removes_session_from_dict(self, server_with_session):
        server, mcp_id = server_with_session
        server.end_session(mcp_id)
        assert mcp_id not in server._sessions

    def test_unknown_session_id_returns_error(self, server):
        result = server.end_session("mcp-nonexistent")
        assert result["status"] == "error"
        assert result["error_type"] == "session_not_found"

    def test_api_error_returns_error_dict(self, server_with_session, mock_client):
        server, mcp_id = server_with_session
        mock_client.terminate_session.side_effect = APIResponseError("API error")
        result = server.end_session(mcp_id)
        assert result["status"] == "error"
        assert result["error_type"] == "api_error"


# ---------------------------------------------------------------------------
# Tests: send_message
# ---------------------------------------------------------------------------

class TestSendMessage:
    """Test send_message tool."""

    def test_returns_success_status(self, server_with_session):
        server, mcp_id = server_with_session
        result = server.send_message(mcp_id, "Hello")
        assert result["status"] == "success"

    def test_returns_agent_response_text(self, server_with_session):
        server, mcp_id = server_with_session
        result = server.send_message(mcp_id, "Hello")
        assert result["response"] == "Agent reply"

    def test_returns_mcp_session_id(self, server_with_session):
        server, mcp_id = server_with_session
        result = server.send_message(mcp_id, "Hello")
        assert result["mcp_session_id"] == mcp_id

    def test_calls_execute_run_with_session_reference(self, server_with_session, mock_client):
        server, mcp_id = server_with_session
        session_ref = server._sessions[mcp_id].session_reference
        server.send_message(mcp_id, "Hello")
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["session_identity"] == session_ref

    def test_increments_turn_count(self, server_with_session):
        server, mcp_id = server_with_session
        result1 = server.send_message(mcp_id, "Turn 1")
        assert result1["turn_count"] == 1
        result2 = server.send_message(mcp_id, "Turn 2")
        assert result2["turn_count"] == 2

    def test_appends_to_history(self, server_with_session):
        server, mcp_id = server_with_session
        server.send_message(mcp_id, "Hello")
        session = server._sessions[mcp_id]
        assert len(session.history) == 2
        assert session.history[0] == {"role": "user", "text": "Hello"}
        assert session.history[1] == {"role": "agent", "text": "Agent reply"}

    def test_unknown_session_id_returns_error(self, server):
        result = server.send_message("mcp-nonexistent", "Hello")
        assert result["status"] == "error"
        assert result["error_type"] == "session_not_found"

    def test_api_error_returns_error_dict(self, server_with_session, mock_client):
        server, mcp_id = server_with_session
        mock_client.execute_run.side_effect = APIResponseError("API error")
        result = server.send_message(mcp_id, "Hello")
        assert result["status"] == "error"
        assert result["error_type"] == "api_error"

    def test_authentication_error_returns_error_dict(self, server_with_session, mock_client):
        server, mcp_id = server_with_session
        mock_client.execute_run.side_effect = AuthenticationError("Unauthorized")
        result = server.send_message(mcp_id, "Hello")
        assert result["status"] == "error"
        assert result["error_type"] == "authentication"


# ---------------------------------------------------------------------------
# Tests: get_session_history
# ---------------------------------------------------------------------------

class TestGetSessionHistory:
    """Test get_session_history tool."""

    def test_returns_empty_history_for_new_session(self, server_with_session):
        server, mcp_id = server_with_session
        result = server.get_session_history(mcp_id)
        assert result["history"] == []

    def test_returns_history_after_messages(self, server_with_session):
        server, mcp_id = server_with_session
        server.send_message(mcp_id, "Hi")
        result = server.get_session_history(mcp_id)
        assert len(result["history"]) == 2

    def test_returns_mcp_session_id(self, server_with_session):
        server, mcp_id = server_with_session
        result = server.get_session_history(mcp_id)
        assert result["mcp_session_id"] == mcp_id

    def test_returns_correct_turn_count(self, server_with_session):
        server, mcp_id = server_with_session
        server.send_message(mcp_id, "Turn 1")
        server.send_message(mcp_id, "Turn 2")
        result = server.get_session_history(mcp_id)
        assert result["turn_count"] == 2

    def test_unknown_session_id_returns_error(self, server):
        result = server.get_session_history("mcp-nonexistent")
        assert result["status"] == "error"
        assert result["error_type"] == "session_not_found"

    def test_history_is_a_copy(self, server_with_session):
        """Modifying the returned history should not affect session state."""
        server, mcp_id = server_with_session
        server.send_message(mcp_id, "Hi")
        result = server.get_session_history(mcp_id)
        result["history"].clear()
        session = server._sessions[mcp_id]
        assert len(session.history) == 2


# ---------------------------------------------------------------------------
# Tests: reset_session
# ---------------------------------------------------------------------------

class TestResetSession:
    """Test reset_session tool."""

    def test_returns_reset_status(self, server_with_session):
        server, mcp_id = server_with_session
        result = server.reset_session(mcp_id)
        assert result["status"] == "reset"

    def test_returns_mcp_session_id(self, server_with_session):
        server, mcp_id = server_with_session
        result = server.reset_session(mcp_id)
        assert result["mcp_session_id"] == mcp_id

    def test_clears_history(self, server_with_session):
        server, mcp_id = server_with_session
        server.send_message(mcp_id, "Hello")
        server.reset_session(mcp_id)
        session = server._sessions[mcp_id]
        assert session.history == []

    def test_session_still_in_dict_after_reset(self, server_with_session):
        server, mcp_id = server_with_session
        server.reset_session(mcp_id)
        assert mcp_id in server._sessions

    def test_unknown_session_id_returns_error(self, server):
        result = server.reset_session("mcp-nonexistent")
        assert result["status"] == "error"
        assert result["error_type"] == "session_not_found"


# ---------------------------------------------------------------------------
# Tests: execute_query
# ---------------------------------------------------------------------------

class TestExecuteQuery:
    """Test execute_query tool."""

    def test_returns_success_status(self, server):
        result = server.execute_query("What is the weather?")
        assert result["status"] == "success"

    def test_returns_response_text(self, server):
        result = server.execute_query("What is the weather?")
        assert result["response"] == "Agent reply"

    def test_returns_run_id(self, server):
        result = server.execute_query("What is the weather?")
        assert result["run_id"] == "r-abc-001"

    def test_calls_execute_run(self, server, mock_client):
        server.execute_query("Hello", user_reference="user-x")
        mock_client.execute_run.assert_called_once()
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["query"] == "Hello"
        assert call_kwargs["user_reference"] == "user-x"

    def test_does_not_create_persistent_session(self, server):
        server.execute_query("Hello")
        assert len(server._sessions) == 0

    def test_autogenerates_session_identity(self, server, mock_client):
        server.execute_query("Hello")
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["session_identity"].startswith("mcp-adhoc-")

    def test_autogenerates_user_reference_when_none(self, server, mock_client):
        server.execute_query("Hello")
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["user_reference"].startswith("mcp-query-")

    def test_api_error_returns_error_dict(self, server, mock_client):
        mock_client.execute_run.side_effect = APIResponseError("API error")
        result = server.execute_query("Hello")
        assert result["status"] == "error"
        assert result["error_type"] == "api_error"


# ---------------------------------------------------------------------------
# Tests: check_run_status
# ---------------------------------------------------------------------------

class TestCheckRunStatus:
    """Test check_run_status tool."""

    def test_calls_get_run_status(self, server, mock_client):
        server.check_run_status("r-123")
        mock_client.get_run_status.assert_called_once_with("r-123")

    def test_returns_status(self, server):
        result = server.check_run_status("r-123")
        assert result["status"] == "success"

    def test_returns_run_id(self, server):
        result = server.check_run_status("r-123")
        assert result["run_id"] == "r-123"

    def test_returns_output(self, server):
        result = server.check_run_status("r-123")
        assert result["output"] == [{"type": "text", "content": "Run output"}]

    def test_not_found_error_returns_error_dict(self, server, mock_client):
        mock_client.get_run_status.side_effect = RunNotFoundError("Not found")
        result = server.check_run_status("r-unknown")
        assert result["status"] == "error"
        assert result["error_type"] == "not_found"

    def test_api_error_returns_error_dict(self, server, mock_client):
        mock_client.get_run_status.side_effect = APIResponseError("Server error")
        result = server.check_run_status("r-123")
        assert result["status"] == "error"
        assert result["error_type"] == "api_error"

    def test_handles_missing_run_data(self, server, mock_client):
        mock_client.get_run_status.return_value = {"status": "pending"}
        result = server.check_run_status("r-123")
        assert result["status"] == "pending"
        assert result["output"] == []


# ---------------------------------------------------------------------------
# Tests: _extract_text
# ---------------------------------------------------------------------------

class TestExtractText:
    """Test the static _extract_text helper."""

    def test_extracts_text_content(self):
        response = {"output": [{"type": "text", "content": "Hello"}]}
        assert AgenticMCPServer._extract_text(response) == "Hello"

    def test_joins_multiple_text_items_with_newline(self):
        response = {
            "output": [
                {"type": "text", "content": "Part 1"},
                {"type": "text", "content": "Part 2"},
            ]
        }
        assert AgenticMCPServer._extract_text(response) == "Part 1\nPart 2"

    def test_ignores_non_text_items(self):
        response = {
            "output": [
                {"type": "image", "content": "data:..."},
                {"type": "text", "content": "Text only"},
            ]
        }
        assert AgenticMCPServer._extract_text(response) == "Text only"

    def test_returns_empty_string_for_empty_output(self):
        assert AgenticMCPServer._extract_text({"output": []}) == ""

    def test_returns_empty_string_for_missing_output(self):
        assert AgenticMCPServer._extract_text({}) == ""

    def test_ignores_items_with_empty_content(self):
        response = {
            "output": [
                {"type": "text", "content": ""},
                {"type": "text", "content": "Real content"},
            ]
        }
        assert AgenticMCPServer._extract_text(response) == "Real content"


# ---------------------------------------------------------------------------
# Tests: _error_response
# ---------------------------------------------------------------------------

class TestErrorResponse:
    """Test the static _error_response helper."""

    def test_authentication_error_type(self):
        result = AgenticMCPServer._error_response(AuthenticationError("Unauthorized"))
        assert result["error_type"] == "authentication"
        assert result["status"] == "error"

    def test_configuration_error_type(self):
        result = AgenticMCPServer._error_response(ConfigurationError("Missing key"))
        assert result["error_type"] == "configuration"

    def test_not_found_error_type(self):
        result = AgenticMCPServer._error_response(RunNotFoundError("Not found"))
        assert result["error_type"] == "not_found"

    def test_generic_agentic_api_error_type(self):
        result = AgenticMCPServer._error_response(AgenticAPIError("API error"))
        assert result["error_type"] == "api_error"

    def test_unexpected_error_type(self):
        result = AgenticMCPServer._error_response(RuntimeError("unexpected"))
        assert result["error_type"] == "unexpected"

    def test_error_message_included(self):
        result = AgenticMCPServer._error_response(AuthenticationError("bad key"))
        assert "bad key" in result["error"]
