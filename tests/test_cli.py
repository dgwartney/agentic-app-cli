"""
Unit tests for CLI.
"""

import json
import os
import signal
import uuid
from io import StringIO
from unittest.mock import Mock, MagicMock, call, patch

import pytest

from agxr.cli import CLI
from agxr.exceptions import AgenticAPIError, ConfigurationError


@pytest.fixture
def cli():
    """Create a CLI instance."""
    return CLI()


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("KOREAI_API_KEY", "test-api-key")
    monkeypatch.setenv("KOREAI_APP_ID", "test-app-id")
    monkeypatch.setenv("KOREAI_ENV_NAME", "test-env")


class TestCLIInit:
    """Test CLI initialization."""

    def test_init_creates_parser(self, cli):
        """Test that initialization creates argument parser."""
        assert cli.parser is not None

    def test_init_config_none(self, cli):
        """Test that config starts as None."""
        assert cli.config is None

    def test_init_client_none(self, cli):
        """Test that client starts as None."""
        assert cli.client is None


class TestExecuteCommand:
    """Test execute command."""

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_basic(self, mock_client_class, cli, mock_env):
        """Test basic execute command."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hello!"}],
            "sessionInfo": {"runId": "run-123"},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(
                ["execute", "--session-id", "session-123", "--query", "Hello"]
            )

        assert exit_code == 0
        assert "Hello!" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_with_json_output(self, mock_client_class, cli, mock_env):
        """Test execute command with JSON output."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {"runId": "run-123"},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(
                [
                    "execute",
                    "--session-id",
                    "session-123",
                    "--query",
                    "Hello",
                    "--json",
                ]
            )

        assert exit_code == 0
        output = fake_out.getvalue()
        parsed = json.loads(output)
        assert "output" in parsed

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_with_user_id(self, mock_client_class, cli, mock_env):
        """Test execute command with user ID."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(
            [
                "execute",
                "--session-id",
                "session-123",
                "--user-id",
                "user-456",
                "--query",
                "Hello",
            ]
        )

        assert exit_code == 0
        mock_client.execute_run.assert_called_once()
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["user_reference"] == "user-456"

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_with_stream(self, mock_client_class, cli, mock_env):
        """Test execute command with streaming."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(
            [
                "execute",
                "--session-id",
                "session-123",
                "--query",
                "Hello",
                "--stream",
                "tokens",
            ]
        )

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["stream_enabled"] is True
        assert call_kwargs["stream_mode"] == "tokens"

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_with_debug(self, mock_client_class, cli, mock_env):
        """Test execute command with debug enabled."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(
            [
                "execute",
                "--session-id",
                "session-123",
                "--query",
                "Hello",
                "--debug",
            ]
        )

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["debug_enabled"] is True

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_with_debug_mode(self, mock_client_class, cli, mock_env):
        """Test execute command with debug mode."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(
            [
                "execute",
                "--session-id",
                "session-123",
                "--query",
                "Hello",
                "--debug",
                "--debug-mode",
                "thoughts",
            ]
        )

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["debug_enabled"] is True
        assert call_kwargs["debug_mode"] == "thoughts"

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_with_debug_mode_all(self, mock_client_class, cli, mock_env):
        """Test execute command with debug mode 'all'."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(
            [
                "execute",
                "--session-id",
                "session-123",
                "--query",
                "Hello",
                "--debug",
                "--debug-mode",
                "all",
            ]
        )

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["debug_enabled"] is True
        assert call_kwargs["debug_mode"] == "all"

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_with_debug_mode_function_call(self, mock_client_class, cli, mock_env):
        """Test execute command with debug mode 'function-call'."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(
            [
                "execute",
                "--session-id",
                "session-123",
                "--query",
                "Hello",
                "--debug",
                "--debug-mode",
                "function-call",
            ]
        )

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["debug_enabled"] is True
        assert call_kwargs["debug_mode"] == "function-call"

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_debug_without_mode(self, mock_client_class, cli, mock_env):
        """Test that --debug alone does not set debug_mode (backward compatible)."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(
            [
                "execute",
                "--session-id",
                "session-123",
                "--query",
                "Hello",
                "--debug",
            ]
        )

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["debug_enabled"] is True
        assert call_kwargs["debug_mode"] is None

    def test_execute_debug_mode_without_debug_flag(self, cli, mock_env):
        """Test that --debug-mode without --debug raises error."""
        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(
                [
                    "execute",
                    "--session-id",
                    "session-123",
                    "--query",
                    "Hello",
                    "--debug-mode",
                    "thoughts",
                ]
            )

        assert exit_code == 1
        assert "--debug-mode requires --debug" in fake_err.getvalue()

    def test_execute_invalid_debug_mode(self, cli, mock_env):
        """Test that invalid debug mode is rejected by argparse."""
        with patch("sys.stderr", new=StringIO()) as fake_err:
            with pytest.raises(SystemExit) as exc_info:
                cli.run(
                    [
                        "execute",
                        "--session-id",
                        "session-123",
                        "--query",
                        "Hello",
                        "--debug",
                        "--debug-mode",
                        "invalid",  # truly invalid mode
                    ]
                )

        assert exc_info.value.code == 2  # argparse exits with code 2 for argument errors
        stderr_output = fake_err.getvalue()
        assert "invalid choice" in stderr_output

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_with_metadata(self, mock_client_class, cli, mock_env):
        """Test execute command with metadata."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        metadata_json = '{"key1": "value1", "key2": "value2"}'
        exit_code = cli.run(
            [
                "execute",
                "--session-id",
                "session-123",
                "--query",
                "Hello",
                "--metadata",
                metadata_json,
            ]
        )

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["metadata"] == {"key1": "value1", "key2": "value2"}

    def test_execute_invalid_metadata_json(self, cli, mock_env):
        """Test execute command with invalid metadata JSON."""
        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(
                [
                    "execute",
                    "--session-id",
                    "session-123",
                    "--query",
                    "Hello",
                    "--metadata",
                    "invalid json",
                ]
            )

        assert exit_code == 1
        assert "Invalid JSON" in fake_err.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_api_error(self, mock_client_class, cli, mock_env):
        """Test execute command with API error."""
        mock_client = Mock()
        mock_client.execute_run.side_effect = AgenticAPIError(
            "API error", status_code=500
        )
        mock_client_class.return_value = mock_client

        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(
                ["execute", "--session-id", "session-123", "--query", "Hello"]
            )

        assert exit_code == 1
        assert "API error" in fake_err.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_auto_generates_session_id(self, mock_client_class, cli, mock_env):
        """Test execute command auto-generates session ID when not provided."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hello!"}],
            "sessionInfo": {"runId": "run-123"},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["execute", "--query", "Hello"])

        assert exit_code == 0
        # Verify execute_run was called
        assert mock_client.execute_run.called
        # Verify session_identity was provided (auto-generated)
        call_kwargs = mock_client.execute_run.call_args[1]
        session_id = call_kwargs["session_identity"]
        # Verify it's a UUID-based session ID
        assert session_id.startswith("chat-")
        assert len(session_id) > 10  # UUID makes it longer than just "chat-"

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_show_payloads_passes_flag(self, mock_client_class, cli, mock_env):
        """Test --show-payloads passes show_payloads=True to execute_run."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(
            ["execute", "--session-id", "session-123", "--query", "Hello", "--show-payloads"]
        )

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["show_payloads"] is True

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_no_show_payloads_defaults_false(self, mock_client_class, cli, mock_env):
        """Test show_payloads defaults to False when --show-payloads not set."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(
            ["execute", "--session-id", "session-123", "--query", "Hello"]
        )

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["show_payloads"] is False


class TestStatusCommand:
    """Test status command."""

    @patch("agxr.cli.AgenticAPIClient")
    def test_status_basic(self, mock_client_class, cli, mock_env):
        """Test basic status command."""
        mock_client = Mock()
        mock_client.get_run_status.return_value = {
            "status": "success",
            "runId": "run-123",
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["status", "--run-id", "run-123"])

        assert exit_code == 0
        mock_client.get_run_status.assert_called_once_with("run-123")

    @patch("agxr.cli.AgenticAPIClient")
    def test_status_with_wait(self, mock_client_class, cli, mock_env):
        """Test status command with wait."""
        mock_client = Mock()
        mock_client.poll_run_status.return_value = {
            "status": "success",
            "runId": "run-123",
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["status", "--run-id", "run-123", "--wait"])

        assert exit_code == 0
        mock_client.poll_run_status.assert_called_once()

    @patch("agxr.cli.AgenticAPIClient")
    def test_status_with_custom_poll_params(self, mock_client_class, cli, mock_env):
        """Test status command with custom polling parameters."""
        mock_client = Mock()
        mock_client.poll_run_status.return_value = {"status": "success"}
        mock_client_class.return_value = mock_client

        exit_code = cli.run(
            [
                "status",
                "--run-id",
                "run-123",
                "--wait",
                "--poll-interval",
                "5",
                "--max-attempts",
                "10",
            ]
        )

        assert exit_code == 0
        call_kwargs = mock_client.poll_run_status.call_args[1]
        assert call_kwargs["interval"] == 5
        assert call_kwargs["max_attempts"] == 10

    @patch("agxr.cli.AgenticAPIClient")
    def test_status_api_error(self, mock_client_class, cli, mock_env):
        """Test status command with API error."""
        mock_client = Mock()
        mock_client.get_run_status.side_effect = AgenticAPIError("Run not found")
        mock_client_class.return_value = mock_client

        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(["status", "--run-id", "run-123"])

        assert exit_code == 1
        assert "Run not found" in fake_err.getvalue()


class TestConfigCommand:
    """Test config command."""

    def test_config_basic(self, cli, mock_env):
        """Test basic config command."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["config"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Configuration" in output

    def test_config_json_output(self, cli, mock_env):
        """Test config command with JSON output."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["config", "--json"])

        assert exit_code == 0
        output = fake_out.getvalue()
        parsed = json.loads(output)
        assert "api_key" in parsed
        assert "app_id" in parsed


class TestConfigurationHandling:
    """Test configuration handling."""

    @patch("agxr.config.load_dotenv")
    def test_missing_api_key(self, mock_load_dotenv, cli, monkeypatch):
        """Test error when API key is missing."""
        monkeypatch.delenv("KOREAI_API_KEY", raising=False)
        monkeypatch.setenv("KOREAI_APP_ID", "test-app")
        monkeypatch.setenv("KOREAI_ENV_NAME", "test-env")

        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(["execute", "--session-id", "s123", "--query", "Hi"])

        assert exit_code == 1
        stderr_output = fake_err.getvalue()
        assert ("Configuration Error" in stderr_output
                or "API key not configured" in stderr_output
                or "Authentication failed" in stderr_output)

    def test_env_name_override(self, cli, mock_env):
        """Test env_name override with command-line argument."""
        with patch("agxr.cli.AgenticAPIClient") as mock_client_class:
            mock_client = Mock()
            mock_client.execute_run.return_value = {
                "output": [],
                "sessionInfo": {},
            }
            mock_client_class.return_value = mock_client

            cli.run(
                [
                    "execute",
                    "--env-name",
                    "staging",
                    "--session-id",
                    "s123",
                    "--query",
                    "Hi",
                ]
            )

            assert cli.config.env_name == "staging"


class TestVerboseMode:
    """Test verbose mode."""

    @patch("agxr.cli.AgenticAPIClient")
    def test_verbose_output(self, mock_client_class, cli, mock_env):
        """Test verbose mode shows extra output."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {"runId": "run-123"},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(
                [
                    "execute",
                    "--verbose",
                    "--session-id",
                    "session-123",
                    "--query",
                    "Hello",
                ]
            )

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Executing run" in output
        assert "Full Response" in output


class TestKeyboardInterrupt:
    """Test keyboard interrupt handling."""

    @patch("agxr.cli.AgenticAPIClient")
    def test_keyboard_interrupt(self, mock_client_class, cli, mock_env):
        """Test that keyboard interrupt is handled gracefully."""
        mock_client = Mock()
        mock_client.execute_run.side_effect = KeyboardInterrupt()
        mock_client_class.return_value = mock_client

        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(
                ["execute", "--session-id", "session-123", "--query", "Hello"]
            )

        assert exit_code == 130
        assert "Interrupted" in fake_err.getvalue()


class TestUnexpectedError:
    """Test unexpected error handling."""

    @patch("agxr.cli.AgenticAPIClient")
    def test_unexpected_error(self, mock_client_class, cli, mock_env):
        """Test that unexpected errors are handled."""
        mock_client = Mock()
        mock_client.execute_run.side_effect = RuntimeError("Unexpected")
        mock_client_class.return_value = mock_client

        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(
                ["execute", "--session-id", "session-123", "--query", "Hello"]
            )

        assert exit_code == 1
        assert "Unexpected error" in fake_err.getvalue()


class TestClientCleanup:
    """Test client cleanup."""

    @patch("agxr.cli.AgenticAPIClient")
    def test_client_closed_on_success(self, mock_client_class, cli, mock_env):
        """Test that client is closed on successful execution."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {"output": [], "sessionInfo": {}}
        mock_client_class.return_value = mock_client

        cli.run(["execute", "--session-id", "session-123", "--query", "Hello"])

        mock_client.close.assert_called_once()

    @patch("agxr.cli.AgenticAPIClient")
    def test_client_closed_on_error(self, mock_client_class, cli, mock_env):
        """Test that client is closed even when error occurs."""
        mock_client = Mock()
        mock_client.execute_run.side_effect = AgenticAPIError("Error")
        mock_client_class.return_value = mock_client

        with patch("sys.stderr", new=StringIO()):
            cli.run(["execute", "--session-id", "session-123", "--query", "Hello"])

        mock_client.close.assert_called_once()


class TestChatCommand:
    """Test chat command."""

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_basic_conversation(self, mock_input, mock_client_class, cli, mock_env):
        """Test basic chat conversation with exit command."""
        # Setup mock inputs: two queries then exit
        mock_input.side_effect = ["Hello", "How are you?", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "I'm doing well!"}],
            "sessionInfo": {"runId": "run-123"},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert mock_client.execute_run.call_count == 2
        output = fake_out.getvalue()
        assert "Agentic API Chat Session Started" in output
        assert "Goodbye!" in output
        mock_client.terminate_session.assert_called_once_with("s-aaaaaaaa-0000-0000-0000-000000000001")

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_quit_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat exits with 'quit' command."""
        mock_input.side_effect = ["Hello", "quit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])
        assert exit_code == 0
        mock_client.terminate_session.assert_called_once_with("s-aaaaaaaa-0000-0000-0000-000000000001")

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_q_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat exits with 'q' command."""
        mock_input.side_effect = ["test", "Q"]  # Test case insensitivity

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])
        assert exit_code == 0

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_eof(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat handles Ctrl+D (EOFError)."""
        mock_input.side_effect = ["Hello", EOFError()]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Goodbye!" in fake_out.getvalue()
        mock_client.terminate_session.assert_called_once_with("s-aaaaaaaa-0000-0000-0000-000000000001")

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_keyboard_interrupt(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat handles Ctrl+C (KeyboardInterrupt)."""
        mock_input.side_effect = ["Hello", KeyboardInterrupt()]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])
        assert exit_code == 130

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_empty_input_skipped(self, mock_input, mock_client_class, cli, mock_env):
        """Test empty input is skipped in chat."""
        mock_input.side_effect = ["Hello", "", "  ", "World", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])

        assert exit_code == 0
        # Only "Hello" and "World" should trigger execute_run
        assert mock_client.execute_run.call_count == 2

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_api_error_continues(self, mock_input, mock_client_class, cli, mock_env):
        """Test API error doesn't break chat loop."""
        mock_input.side_effect = ["error query", "success query", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        # First call raises error, second succeeds
        mock_client.execute_run.side_effect = [
            AgenticAPIError("API error", status_code=500),
            {"output": [{"type": "text", "content": "OK"}], "sessionInfo": {}},
        ]
        mock_client_class.return_value = mock_client

        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "API error" in fake_err.getvalue()
        assert mock_client.execute_run.call_count == 2

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_custom_session_id(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat passes --session-id to create_session and uses returned sessionReference."""
        mock_input.side_effect = ["Hello", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat", "--session-id", "my-custom-session"])

        assert exit_code == 0
        output = fake_out.getvalue()
        # Banner shows the server-assigned sessionReference
        assert "s-aaaaaaaa-0000-0000-0000-000000000001" in output

        # create_session was called with the custom value as session_reference
        create_kwargs = mock_client.create_session.call_args[1]
        assert create_kwargs.get("session_reference") == "my-custom-session"

        # execute_run uses the server-returned sessionReference
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["session_identity"] == "s-aaaaaaaa-0000-0000-0000-000000000001"

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_streaming(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat passes streaming flag."""
        mock_input.side_effect = ["Hello", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat", "--stream", "tokens"])

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["stream_enabled"] is True
        assert call_kwargs["stream_mode"] == "tokens"

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_debug(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat passes debug flags."""
        mock_input.side_effect = ["Hello", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat", "--debug", "--debug-mode", "thoughts"])

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["debug_enabled"] is True
        assert call_kwargs["debug_mode"] == "thoughts"

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_session_id_auto_generation(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat creates a server-side session and displays the returned sessionReference."""
        mock_input.side_effect = ["Hello", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        # Banner shows the server-assigned sessionReference
        assert "Session ID:" in output
        assert "s-aaaaaaaa-0000-0000-0000-000000000001" in output
        mock_client.create_session.assert_called_once()

    @patch("agxr.cli.AgenticAPIClient")
    def test_chat_session_creation_failure(self, mock_client_class, cli, mock_env):
        """Test chat exits gracefully if session creation fails."""
        mock_client = Mock()
        mock_client.create_session.side_effect = AgenticAPIError("Connection refused", status_code=500)
        mock_client_class.return_value = mock_client

        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(["chat"])

        assert exit_code == 1
        assert "Could not create session" in fake_err.getvalue()

    def test_chat_invalid_metadata_json(self, cli, mock_env):
        """Test chat rejects invalid metadata JSON before loop."""
        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(
                ["chat", "--metadata", "invalid json"]
            )

        assert exit_code == 1
        assert "Invalid JSON" in fake_err.getvalue()


class TestChatSpecialCommands:
    """Test special commands in chat mode."""

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_help_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test #help command displays available commands."""
        mock_input.side_effect = ["#help", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Available Commands:" in output
        assert "#help" in output
        assert "#debug" in output
        assert "#timing" in output
        # Should NOT call execute_run for special commands
        mock_client.execute_run.assert_not_called()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_debug_toggle_on(self, mock_input, mock_client_class, cli, mock_env):
        """Test #debug on enables debug mode."""
        mock_input.side_effect = ["#debug on", "#info", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Debug mode enabled" in output
        # Check for debug status (may have color codes between label and value)
        assert "Debug:" in output and "enabled" in output

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_debug_affects_api_calls(self, mock_input, mock_client_class, cli, mock_env):
        """Test that #debug on affects subsequent API calls."""
        mock_input.side_effect = ["#debug on", "test query", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["debug_enabled"] is True

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_stream_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test #stream tokens enables token streaming."""
        mock_input.side_effect = ["#stream tokens", "test", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["stream_enabled"] is True
        assert call_kwargs["stream_mode"] == "tokens"

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_new_command_changes_session(self, mock_input, mock_client_class, cli, mock_env):
        """Test #new command terminates old session and creates a new one via Sessions API."""
        mock_input.side_effect = ["test1", "#new", "test2", "exit"]

        mock_client = Mock()
        # create_session returns different sessionReferences on each call
        mock_client.create_session.side_effect = [
            {"sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001", "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001"},
            {"sessionReference": "s-bbbbbbbb-0000-0000-0000-000000000002", "sessionId": "s-bbbbbbbb-0000-0000-0000-000000000002"},
        ]
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "New Session Started" in output

        # Verify different server-assigned session references were used
        assert mock_client.execute_run.call_count == 2
        session_1 = mock_client.execute_run.call_args_list[0][1]["session_identity"]
        session_2 = mock_client.execute_run.call_args_list[1][1]["session_identity"]
        assert session_1 == "s-aaaaaaaa-0000-0000-0000-000000000001"
        assert session_2 == "s-bbbbbbbb-0000-0000-0000-000000000002"

        # #new terminates the old session before creating the new one
        assert mock_client.terminate_session.call_count >= 1

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_info_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test #info displays session information."""
        mock_input.side_effect = ["#info", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Session Information:" in output
        assert "Session ID:" in output
        assert "Environment:" in output

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    @patch("os.system")
    def test_clear_command(self, mock_system, mock_input, mock_client_class, cli, mock_env):
        """Test #clear command clears screen."""
        mock_input.side_effect = ["#clear", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])

        assert exit_code == 0
        mock_system.assert_called_once()
        call_arg = mock_system.call_args[0][0]
        assert call_arg in ['clear', 'cls']

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_unknown_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test unknown special command shows error."""
        mock_input.side_effect = ["#unknown", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Unknown command: #unknown" in output
        assert "#help" in output

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_case_insensitive_commands(self, mock_input, mock_client_class, cli, mock_env):
        """Test special commands are case-insensitive."""
        mock_input.side_effect = ["#HELP", "#Debug ON", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Available Commands:" in output
        assert "Debug mode enabled" in output

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_command_aliases(self, mock_input, mock_client_class, cli, mock_env):
        """Test command aliases work."""
        mock_input.side_effect = ["#newsession", "#session", "exit"]

        mock_client = Mock()
        mock_client.create_session.side_effect = [
            {"sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001", "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001"},
            {"sessionReference": "s-bbbbbbbb-0000-0000-0000-000000000002", "sessionId": "s-bbbbbbbb-0000-0000-0000-000000000002"},
        ]
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "New Session Started" in output
        assert "Session Information:" in output

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_debug_query_state(self, mock_input, mock_client_class, cli, mock_env):
        """Test #debug without args shows current state."""
        mock_input.side_effect = ["#debug", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Debug mode is currently" in output

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_stream_toggle_off(self, mock_input, mock_client_class, cli, mock_env):
        """Test #stream off disables streaming."""
        mock_input.side_effect = ["#stream off", "test", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat", "--stream", "tokens"])  # Start with streaming on

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["stream_enabled"] is False

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_history_empty(self, mock_input, mock_client_class, cli, mock_env):
        """Test #history with no prior turns shows empty message."""
        mock_input.side_effect = ["#history", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "No conversation history yet" in output

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_timing_toggle_on(self, mock_input, mock_client_class, cli, mock_env):
        """Test #timing on enables timing display."""
        mock_input.side_effect = ["#timing on", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Timing enabled" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_timing_toggle_off(self, mock_input, mock_client_class, cli, mock_env):
        """Test #timing off disables timing display."""
        mock_input.side_effect = ["#timing off", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Timing disabled" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_timing_show_state(self, mock_input, mock_client_class, cli, mock_env):
        """Test #timing without args shows current state."""
        mock_input.side_effect = ["#timing", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Timing is currently disabled" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_timing_invalid_arg(self, mock_input, mock_client_class, cli, mock_env):
        """Test #timing with invalid argument shows error."""
        mock_input.side_effect = ["#timing maybe", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Invalid argument" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_timing_output_after_response(self, mock_input, mock_client_class, cli, mock_env):
        """Test that timing is displayed after response when enabled."""
        mock_input.side_effect = ["#timing on", "hello", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi there"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "[timing]" in output

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_timing_not_shown_when_disabled(self, mock_input, mock_client_class, cli, mock_env):
        """Test that timing is not displayed when disabled (default)."""
        mock_input.side_effect = ["hello", "exit"]

        mock_client = Mock()
        mock_client.create_session.return_value = {
            "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
            "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
        }
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi there"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "[timing]" not in fake_out.getvalue()


class TestPayloadCommand:
    """Test #payload chat command."""

    SESSION_RESPONSE = {
        "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
        "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
    }
    EXECUTE_RESPONSE = {
        "output": [{"type": "text", "content": "Response"}],
        "sessionInfo": {},
    }

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_payload_toggle_on(self, mock_input, mock_client_class, cli, mock_env):
        """Test #payload on enables payload display."""
        mock_input.side_effect = ["#payload on", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = self.SESSION_RESPONSE
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Payload display enabled" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_payload_toggle_off(self, mock_input, mock_client_class, cli, mock_env):
        """Test #payload off disables payload display."""
        mock_input.side_effect = ["#payload off", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = self.SESSION_RESPONSE
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Payload display disabled" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_payload_show_state_disabled(self, mock_input, mock_client_class, cli, mock_env):
        """Test #payload without args shows current state (disabled by default)."""
        mock_input.side_effect = ["#payload", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = self.SESSION_RESPONSE
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Payload display is currently disabled" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_payload_show_state_enabled(self, mock_input, mock_client_class, cli, mock_env):
        """Test #payload after enabling shows state as enabled."""
        mock_input.side_effect = ["#payload on", "#payload", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = self.SESSION_RESPONSE
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Payload display is currently enabled" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_payload_invalid_arg(self, mock_input, mock_client_class, cli, mock_env):
        """Test #payload with invalid argument shows error."""
        mock_input.side_effect = ["#payload maybe", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = self.SESSION_RESPONSE
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Invalid argument" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_payload_affects_api_calls(self, mock_input, mock_client_class, cli, mock_env):
        """Test that #payload on passes show_payloads=True to subsequent execute_run calls."""
        mock_input.side_effect = ["#payload on", "test query", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = self.SESSION_RESPONSE
        mock_client.execute_run.return_value = self.EXECUTE_RESPONSE
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["show_payloads"] is True

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_payload_off_does_not_affect_api_calls(self, mock_input, mock_client_class, cli, mock_env):
        """Test that show_payloads defaults to False in execute_run calls."""
        mock_input.side_effect = ["test query", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = self.SESSION_RESPONSE
        mock_client.execute_run.return_value = self.EXECUTE_RESPONSE
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["show_payloads"] is False

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_payload_in_help_output(self, mock_input, mock_client_class, cli, mock_env):
        """Test that #help output includes #payload command."""
        mock_input.side_effect = ["#help", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = self.SESSION_RESPONSE
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "#payload" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_show_payloads_flag_wired(self, mock_input, mock_client_class, cli, mock_env):
        """Test that chat --show-payloads passes show_payloads=True to execute_run."""
        mock_input.side_effect = ["test query", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = self.SESSION_RESPONSE
        mock_client.execute_run.return_value = self.EXECUTE_RESPONSE
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat", "--show-payloads"])

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["show_payloads"] is True

# ---------------------------------------------------------------------------
# Helpers shared by new test classes
# ---------------------------------------------------------------------------
_SESSION_RESP = {
    "sessionReference": "s-aaaaaaaa-0000-0000-0000-000000000001",
    "sessionId": "s-aaaaaaaa-0000-0000-0000-000000000001",
}
_EXECUTE_RESP = {
    "output": [{"type": "text", "content": "Agent reply"}],
    "sessionInfo": {},
}


# ---------------------------------------------------------------------------
# TestReadlineSupport
# ---------------------------------------------------------------------------
class TestReadlineSupport:
    """Tests for readline setup, vi mode, history loading/saving."""

    def test_setup_readline_vi_mode_gnu(self, cli):
        """vi_mode=True on GNU readline calls set editing-mode vi."""
        with patch("agxr.cli._READLINE_AVAILABLE", True), \
             patch("agxr.cli._readline") as mock_rl, \
             patch("agxr.cli._CHAT_HISTORY_FILE") as mock_path:
            mock_path.exists.return_value = False
            mock_rl.__doc__ = "GNU readline"
            cli._setup_readline(vi_mode=True)
            mock_rl.parse_and_bind.assert_any_call("set editing-mode vi")

    def test_setup_readline_vi_mode_libedit(self, cli):
        """vi_mode=True on libedit calls bind -v (libedit syntax)."""
        with patch("agxr.cli._READLINE_AVAILABLE", True), \
             patch("agxr.cli._readline") as mock_rl, \
             patch("agxr.cli._CHAT_HISTORY_FILE") as mock_path:
            mock_path.exists.return_value = False
            mock_rl.__doc__ = "Importing this module enables command line editing using libedit readline."
            cli._setup_readline(vi_mode=True)
            mock_rl.parse_and_bind.assert_any_call("bind -v")

    def test_setup_readline_emacs_mode_no_vi_bind(self, cli):
        """vi_mode=False must not issue any vi bind."""
        with patch("agxr.cli._READLINE_AVAILABLE", True), \
             patch("agxr.cli._readline") as mock_rl, \
             patch("agxr.cli._CHAT_HISTORY_FILE") as mock_path:
            mock_path.exists.return_value = False
            mock_rl.__doc__ = "GNU readline"
            cli._setup_readline(vi_mode=False)
            vi_calls = [c for c in mock_rl.parse_and_bind.call_args_list
                        if "vi" in str(c)]
            assert vi_calls == []

    def test_setup_readline_libedit_tab_bind(self, cli):
        """macOS libedit path uses libedit-specific Tab binding."""
        with patch("agxr.cli._READLINE_AVAILABLE", True), \
             patch("agxr.cli._readline") as mock_rl, \
             patch("agxr.cli._CHAT_HISTORY_FILE") as mock_path:
            mock_path.exists.return_value = False
            mock_rl.__doc__ = "Wrapper module for libedit-based readline interface"
            cli._setup_readline()
            mock_rl.parse_and_bind.assert_any_call("bind ^I rl_complete")

    def test_setup_readline_gnu_tab_bind(self, cli):
        """GNU readline path uses tab: complete binding."""
        with patch("agxr.cli._READLINE_AVAILABLE", True), \
             patch("agxr.cli._readline") as mock_rl, \
             patch("agxr.cli._CHAT_HISTORY_FILE") as mock_path:
            mock_path.exists.return_value = False
            mock_rl.__doc__ = "GNU readline"
            cli._setup_readline()
            mock_rl.parse_and_bind.assert_any_call("tab: complete")

    def test_setup_readline_loads_history_when_file_exists(self, cli):
        """History file is read when it exists."""
        with patch("agxr.cli._READLINE_AVAILABLE", True), \
             patch("agxr.cli._readline") as mock_rl, \
             patch("agxr.cli._CHAT_HISTORY_FILE") as mock_path:
            mock_path.exists.return_value = True
            mock_rl.__doc__ = "GNU readline"
            cli._setup_readline()
            mock_rl.read_history_file.assert_called_once_with(str(mock_path))

    def test_setup_readline_os_error_on_read_silenced(self, cli):
        """OSError reading history file is silently ignored."""
        with patch("agxr.cli._READLINE_AVAILABLE", True), \
             patch("agxr.cli._readline") as mock_rl, \
             patch("agxr.cli._CHAT_HISTORY_FILE") as mock_path:
            mock_path.exists.return_value = True
            mock_rl.__doc__ = "GNU readline"
            mock_rl.read_history_file.side_effect = OSError("no perms")
            cli._setup_readline()  # must not raise

    def test_setup_readline_noop_when_unavailable(self, cli):
        """Nothing called when readline is not importable."""
        with patch("agxr.cli._READLINE_AVAILABLE", False), \
             patch("agxr.cli._readline") as mock_rl:
            cli._setup_readline()
            mock_rl.read_history_file.assert_not_called()
            mock_rl.parse_and_bind.assert_not_called()

    def test_save_readline_history_os_error_silenced(self, cli):
        """OSError writing history file is silently ignored."""
        with patch("agxr.cli._READLINE_AVAILABLE", True), \
             patch("agxr.cli._readline") as mock_rl:
            mock_rl.write_history_file.side_effect = OSError("read-only FS")
            cli._save_readline_history()  # must not raise

    def test_save_readline_history_noop_when_unavailable(self, cli):
        """Nothing called when readline is not importable."""
        with patch("agxr.cli._READLINE_AVAILABLE", False), \
             patch("agxr.cli._readline") as mock_rl:
            cli._save_readline_history()
            mock_rl.write_history_file.assert_not_called()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_vi_flag_passed_to_setup(self, mock_input, mock_client_class, cli, mock_env):
        """--vi CLI flag is wired to _setup_readline(vi_mode=True)."""
        mock_input.side_effect = ["exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client_class.return_value = mock_client
        with patch.object(cli, "_setup_readline") as mock_setup, \
             patch.object(cli, "_save_readline_history"):
            cli.run(["chat", "--vi"])
        mock_setup.assert_called_once_with(vi_mode=True)


# ---------------------------------------------------------------------------
# TestSignalHandler
# ---------------------------------------------------------------------------
class TestSignalHandler:
    """Tests for SIGTERM/SIGHUP handler installed during chat."""

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_sigterm_handler_saves_history_and_reraises(
        self, mock_input, mock_client_class, cli, mock_env
    ):
        """SIGTERM handler flushes history then re-raises the signal."""
        mock_input.side_effect = ["exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client_class.return_value = mock_client

        captured = {}
        real_signal = signal.signal

        def capture(signum, handler):
            if signum == signal.SIGTERM and "handler" not in captured:
                captured["handler"] = handler
            return real_signal(signum, handler)

        # Keep os.kill mocked throughout so calling the handler doesn't
        # actually deliver SIGTERM to the test process.
        with patch("agxr.cli.signal.signal", side_effect=capture), \
             patch.object(cli, "_save_readline_history") as mock_save, \
             patch("agxr.cli.os.kill") as mock_kill:
            cli.run(["chat"])

            assert "handler" in captured
            mock_save.reset_mock()
            mock_kill.reset_mock()

            # Call the handler directly (simulates receiving SIGTERM)
            captured["handler"](signal.SIGTERM, None)

        mock_save.assert_called_once()
        mock_kill.assert_called_once_with(os.getpid(), signal.SIGTERM)


# ---------------------------------------------------------------------------
# TestChatHistoryContent
# ---------------------------------------------------------------------------
class TestChatHistoryContent:
    """Tests for #history showing actual conversation turns."""

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_history_shows_conversation_turns(
        self, mock_input, mock_client_class, cli, mock_env
    ):
        """#history displays user/agent pairs from the current session."""
        mock_input.side_effect = ["hello agent", "#history", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client.execute_run.return_value = _EXECUTE_RESP
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "hello agent" in output
        assert "Agent reply" in output
        assert "[1]" in output

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_history_last_n_turns(self, mock_input, mock_client_class, cli, mock_env):
        """#history 1 shows only the most recent turn."""
        mock_input.side_effect = ["first message", "second message", "#history 1", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client.execute_run.return_value = _EXECUTE_RESP
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "second message" in output
        assert "[2]" in output

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_history_invalid_n_shows_usage(
        self, mock_input, mock_client_class, cli, mock_env
    ):
        """#history with non-integer arg shows usage message."""
        mock_input.side_effect = ["hello agent", "#history abc", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client.execute_run.return_value = _EXECUTE_RESP
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Usage: #history" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_history_resets_after_new_session(
        self, mock_input, mock_client_class, cli, mock_env
    ):
        """#new resets conversation history; #history shows empty."""
        mock_input.side_effect = ["hello agent", "#new", "#history", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client.execute_run.return_value = _EXECUTE_RESP
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "No conversation history yet" in fake_out.getvalue()


# ---------------------------------------------------------------------------
# TestPrintOutput
# ---------------------------------------------------------------------------
class TestPrintOutput:
    """Tests for _print_output format branches."""

    def test_session_info_format(self, cli, mock_env):
        """sessionInfo key with runId and status is printed."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            cli.config = Mock()
            cli._print_output({"sessionInfo": {"runId": "r-123", "status": "success"}})
        output = fake_out.getvalue()
        assert "r-123" in output
        assert "success" in output

    def test_response_format(self, cli, mock_env):
        """Old 'response' key is printed."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            cli.config = Mock()
            cli._print_output({"response": "some text"})
        assert "some text" in fake_out.getvalue()

    def test_message_format(self, cli, mock_env):
        """'message' key is printed."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            cli.config = Mock()
            cli._print_output({"message": "hello world"})
        assert "hello world" in fake_out.getvalue()

    def test_error_field_printed(self, cli, mock_env):
        """'error' field in response data is printed."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            cli.config = Mock()
            cli._print_output({"output": [{"type": "text", "content": "ok"}], "error": "oops"})
        assert "oops" in fake_out.getvalue()

    def test_debug_field_verbose(self, cli, mock_env):
        """debug field is shown in full when verbose=True."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            cli.config = Mock()
            cli._print_output(
                {"output": [{"type": "text", "content": "x"}], "debug": {"thoughts": "yes"}},
                verbose=True,
            )
        output = fake_out.getvalue()
        assert "thoughts" in output

    def test_debug_field_non_verbose_dict(self, cli, mock_env):
        """Non-verbose mode shows debug summary for dict debug info."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            cli.config = Mock()
            cli._print_output(
                {"output": [{"type": "text", "content": "x"}], "debug": {"k": "v"}},
                verbose=False,
            )
        assert "Debug" in fake_out.getvalue()


# ---------------------------------------------------------------------------
# TestPrintChatResponseVerbose
# ---------------------------------------------------------------------------
class TestPrintChatResponseVerbose:
    """Tests for _print_chat_response debug verbose path."""

    def test_verbose_shows_debug_info(self, cli):
        """Debug info is printed when verbose=True."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            cli._print_chat_response(
                {"output": [{"type": "text", "content": "hi"}], "debug": {"thought": "x"}},
                verbose=True,
            )
        assert "thought" in fake_out.getvalue()


# ---------------------------------------------------------------------------
# TestChatCommandBranches
# ---------------------------------------------------------------------------
class TestChatCommandBranches:
    """Coverage for chat command branches not hit by existing tests."""

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_debug_off_command(self, mock_input, mock_client_class, cli, mock_env):
        """#debug off disables debug mode."""
        mock_input.side_effect = ["#debug on", "#debug off", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Debug mode disabled" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_debug_invalid_arg(self, mock_input, mock_client_class, cli, mock_env):
        """#debug with invalid argument shows error."""
        mock_input.side_effect = ["#debug maybe", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Invalid argument" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_stream_no_args_shows_state(self, mock_input, mock_client_class, cli, mock_env):
        """#stream with no args shows current streaming state."""
        mock_input.side_effect = ["#stream", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "disabled" in fake_out.getvalue().lower()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_stream_on_shortcut_defaults_to_tokens(
        self, mock_input, mock_client_class, cli, mock_env
    ):
        """#stream on enables streaming with default tokens mode."""
        mock_input.side_effect = ["#stream on", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "tokens" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_stream_invalid_arg(self, mock_input, mock_client_class, cli, mock_env):
        """#stream with unknown mode shows error."""
        mock_input.side_effect = ["#stream badmode", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Invalid argument" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_new_command_api_error(self, mock_input, mock_client_class, cli, mock_env):
        """#new shows error and continues chat when session creation fails."""
        second_session = {**_SESSION_RESP}
        mock_input.side_effect = ["#new", "exit"]
        mock_client = Mock()
        mock_client.create_session.side_effect = [
            _SESSION_RESP,
            AgenticAPIError("server down", status_code=503),
        ]
        mock_client_class.return_value = mock_client

        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Error creating new session" in fake_err.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_api_error_verbose_shows_status_code(
        self, mock_input, mock_client_class, cli, mock_env
    ):
        """Verbose mode shows HTTP status code on API errors during chat."""
        mock_input.side_effect = ["bad query", "exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = _SESSION_RESP
        mock_client.execute_run.side_effect = AgenticAPIError("boom", status_code=500)
        mock_client_class.return_value = mock_client

        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(["chat", "--verbose"])

        assert exit_code == 0
        assert "500" in fake_err.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_session_initial_output_displayed(
        self, mock_input, mock_client_class, cli, mock_env
    ):
        """Initial agent message from create_session is displayed in the banner."""
        mock_input.side_effect = ["exit"]
        mock_client = Mock()
        mock_client.create_session.return_value = {
            **_SESSION_RESP,
            "output": [{"type": "text", "content": "Welcome!"}],
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Welcome!" in fake_out.getvalue()


# ---------------------------------------------------------------------------
# TestTerminateChatSession
# ---------------------------------------------------------------------------
class TestTerminateChatSession:
    """Tests for _terminate_chat_session error handling."""

    def test_api_error_silenced(self, cli, mock_env):
        """AgenticAPIError during session termination is silently ignored."""
        cli.client = Mock()
        cli.client.terminate_session.side_effect = AgenticAPIError("gone", status_code=404)
        cli._terminate_chat_session("s-ref")  # must not raise


# ---------------------------------------------------------------------------
# TestPrintOutput – execute/status verbose paths
# ---------------------------------------------------------------------------
class TestExecuteVerbose:
    """Covers verbose output paths in execute and status commands."""

    @patch("agxr.cli.AgenticAPIClient")
    def test_execute_verbose_shows_user_id(self, mock_client_class, cli, mock_env):
        """--verbose prints user-id when provided."""
        mock_client = Mock()
        mock_client.execute_run.return_value = _EXECUTE_RESP
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run([
                "execute", "--query", "hi", "--user-id", "u-abc", "--verbose"
            ])

        assert exit_code == 0
        assert "u-abc" in fake_out.getvalue()

    @patch("agxr.cli.AgenticAPIClient")
    def test_status_verbose_error_shows_status_code(self, mock_client_class, cli, mock_env):
        """Verbose mode shows HTTP status code on status command error."""
        mock_client = Mock()
        mock_client.get_run_status.side_effect = AgenticAPIError("not found", status_code=404)
        mock_client_class.return_value = mock_client

        with patch("sys.stderr", new=StringIO()) as fake_err:
            exit_code = cli.run(["status", "--run-id", "r-abc", "--verbose"])

        assert exit_code == 1
        assert "404" in fake_err.getvalue()


# ---------------------------------------------------------------------------
# TestRunCommandRouting
# ---------------------------------------------------------------------------
class TestRunCommandRouting:
    """Tests for run() routing logic (profile, unknown command, verbose error)."""

    @patch("agxr.profiles.ProfileManager")
    def test_run_profile_command_routes_to_handle_profile(
        self, mock_manager_class, cli, mock_env
    ):
        """run() routes 'profile' to _handle_profile without loading main config."""
        mock_manager = Mock()
        mock_manager.get_default_profile.return_value = None
        mock_manager.list_profiles.return_value = []
        mock_manager_class.return_value = mock_manager

        with patch("sys.stdout", new=StringIO()):
            exit_code = cli.run(["profile", "list"])

        assert exit_code == 0

    def test_run_unknown_command_returns_error(self, cli, mock_env):
        """An unrecognized command value returns exit code 1."""
        cli2 = CLI()
        # Directly call the internal routing after parsing
        import argparse
        args = argparse.Namespace(
            command="unknowncmd",
            log_level="WARNING",
            log_file=None,
            verbose=False,
            api_key=None,
            app_id=None,
            env_name=None,
            base_url=None,
            timeout=None,
            env_file=None,
            profile=None,
        )
        with patch("agxr.cli.setup_logging"), \
             patch("agxr.cli.get_logger", return_value=Mock()), \
             patch.object(cli2, "_load_config"), \
             patch.object(cli2, "config") as mock_config, \
             patch("agxr.cli.AgenticAPIClient"):
            mock_config.validate.return_value = None
            mock_config.env_name = "test"
            with patch("sys.stderr", new=StringIO()) as fake_err:
                # Reach the routing by setting config/client directly
                cli2.config = mock_config
                cli2.client = Mock()
                result = cli2._handle_config if False else None
                # Test the 'else' branch via run() with a patched parser
                with patch.object(cli2.parser, "parse_args", return_value=args):
                    exit_code = cli2.run([])
        assert exit_code == 1

    @patch("agxr.cli.AgenticAPIClient")
    def test_run_verbose_unexpected_error_prints_traceback(
        self, mock_client_class, cli, mock_env
    ):
        """Unexpected exception with --verbose prints traceback to stderr."""
        mock_client = Mock()
        mock_client.execute_run.side_effect = RuntimeError("unexpected!")
        mock_client_class.return_value = mock_client

        with patch("sys.stderr", new=StringIO()) as fake_err, \
             patch("traceback.print_exc"):
            exit_code = cli.run(["execute", "--query", "hi", "--verbose"])

        assert exit_code == 1


# ---------------------------------------------------------------------------
# TestMainEntryPoint
# ---------------------------------------------------------------------------
class TestMainEntryPoint:
    """Tests for the module-level main() function."""

    def test_main_calls_cli_run_and_exits(self):
        """main() creates a CLI, runs it, and calls sys.exit with the result."""
        from agxr.cli import main
        with patch("agxr.cli.CLI") as mock_cli_class, \
             patch("agxr.cli.sys.exit") as mock_exit:
            mock_cli_class.return_value.run.return_value = 0
            main()
        mock_exit.assert_called_once_with(0)


# ---------------------------------------------------------------------------
# TestProfileCommands
# ---------------------------------------------------------------------------
class TestProfileCommands:
    """Tests for profile sub-commands (list, add, delete, set-default)."""

    def _make_manager(self):
        m = Mock()
        m.get_default_profile.return_value = None
        m.list_profiles.return_value = []
        m.load_profiles.return_value = {}
        return m

    @patch("agxr.profiles.ProfileManager")
    def test_profile_list_empty(self, mock_manager_class, cli, mock_env):
        """profile list with no profiles shows the 'no profiles' message."""
        mock_manager_class.return_value = self._make_manager()
        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["profile", "list"])
        assert exit_code == 0
        assert "No profiles" in fake_out.getvalue()

    @patch("agxr.profiles.ProfileManager")
    def test_profile_list_with_profiles(self, mock_manager_class, cli, mock_env):
        """profile list shows profile names when profiles exist."""
        manager = self._make_manager()
        manager.list_profiles.return_value = ["prod"]
        manager.get_default_profile.return_value = "prod"
        manager.get_profile_display.return_value = {
            "api_key": "***",
            "app_id": "app-1",
            "env_name": "production",
            "base_url": "https://example.com",
            "timeout": 30,
        }
        mock_manager_class.return_value = manager
        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["profile", "list"])
        assert exit_code == 0
        assert "prod" in fake_out.getvalue()

    @patch("agxr.profiles.ProfileManager")
    def test_profile_set_default(self, mock_manager_class, cli, mock_env):
        """profile set-default sets the default profile."""
        manager = self._make_manager()
        mock_manager_class.return_value = manager
        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["profile", "set-default", "myprod"])
        assert exit_code == 0
        manager.set_default_profile.assert_called_once_with("myprod")
        assert "myprod" in fake_out.getvalue()

    @patch("agxr.profiles.ProfileManager")
    def test_profile_add_with_all_cli_args(self, mock_manager_class, cli, mock_env):
        """profile add with all args saves profile without interactive prompts."""
        manager = self._make_manager()
        mock_manager_class.return_value = manager
        with patch("sys.stdout", new=StringIO()):
            exit_code = cli.run([
                "profile", "add",
                "--name", "dev",
                "--api-key", "key-xxx",
                "--app-id", "app-yyy",
                "--env-name", "development",
            ])
        assert exit_code == 0
        manager.add_profile.assert_called_once()

    @patch("agxr.profiles.ProfileManager")
    def test_profile_delete_confirmed(self, mock_manager_class, cli, mock_env):
        """profile delete with 'y' confirmation deletes the profile."""
        manager = self._make_manager()
        manager.list_profiles.return_value = []  # empty after delete
        mock_manager_class.return_value = manager
        with patch("builtins.input", return_value="y"), \
             patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["profile", "delete", "dev"])
        assert exit_code == 0
        manager.delete_profile.assert_called_once_with("dev")

    @patch("agxr.profiles.ProfileManager")
    def test_profile_delete_cancelled(self, mock_manager_class, cli, mock_env):
        """profile delete with 'n' answer cancels without deleting."""
        manager = self._make_manager()
        mock_manager_class.return_value = manager
        with patch("builtins.input", return_value="n"), \
             patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["profile", "delete", "dev"])
        assert exit_code == 0
        manager.delete_profile.assert_not_called()
        assert "Cancelled" in fake_out.getvalue()
