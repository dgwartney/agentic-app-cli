"""
Unit tests for CLI.
"""

import json
import os
import uuid
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from agentic_api_cli.cli import CLI
from agentic_api_cli.exceptions import AgenticAPIError, ConfigurationError


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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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


class TestStatusCommand:
    """Test status command."""

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.config.load_dotenv")
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
        with patch("agentic_api_cli.cli.AgenticAPIClient") as mock_client_class:
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    def test_client_closed_on_success(self, mock_client_class, cli, mock_env):
        """Test that client is closed on successful execution."""
        mock_client = Mock()
        mock_client.execute_run.return_value = {"output": [], "sessionInfo": {}}
        mock_client_class.return_value = mock_client

        cli.run(["execute", "--session-id", "session-123", "--query", "Hello"])

        mock_client.close.assert_called_once()

    @patch("agentic_api_cli.cli.AgenticAPIClient")
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_basic_conversation(self, mock_input, mock_client_class, cli, mock_env):
        """Test basic chat conversation with exit command."""
        # Setup mock inputs: two queries then exit
        mock_input.side_effect = ["Hello", "How are you?", "exit"]

        mock_client = Mock()
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_quit_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat exits with 'quit' command."""
        mock_input.side_effect = ["Hello", "quit"]

        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])
        assert exit_code == 0

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_q_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat exits with 'q' command."""
        mock_input.side_effect = ["test", "Q"]  # Test case insensitivity

        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])
        assert exit_code == 0

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_eof(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat handles Ctrl+D (EOFError)."""
        mock_input.side_effect = ["Hello", EOFError()]

        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        assert "Goodbye!" in fake_out.getvalue()

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_keyboard_interrupt(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat handles Ctrl+C (KeyboardInterrupt)."""
        mock_input.side_effect = ["Hello", KeyboardInterrupt()]

        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])
        assert exit_code == 130

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_empty_input_skipped(self, mock_input, mock_client_class, cli, mock_env):
        """Test empty input is skipped in chat."""
        mock_input.side_effect = ["Hello", "", "  ", "World", "exit"]

        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])

        assert exit_code == 0
        # Only "Hello" and "World" should trigger execute_run
        assert mock_client.execute_run.call_count == 2

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_api_error_continues(self, mock_input, mock_client_class, cli, mock_env):
        """Test API error doesn't break chat loop."""
        mock_input.side_effect = ["error query", "success query", "exit"]

        mock_client = Mock()
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_custom_session_id(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat uses provided session ID."""
        mock_input.side_effect = ["Hello", "exit"]

        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat", "--session-id", "my-custom-session"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "my-custom-session" in output

        # Verify session ID passed to execute_run
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["session_identity"] == "my-custom-session"

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_streaming(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat passes streaming flag."""
        mock_input.side_effect = ["Hello", "exit"]

        mock_client = Mock()
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_with_debug(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat passes debug flags."""
        mock_input.side_effect = ["Hello", "exit"]

        mock_client = Mock()
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_chat_session_id_auto_generation(self, mock_input, mock_client_class, cli, mock_env):
        """Test chat auto-generates session ID."""
        mock_input.side_effect = ["Hello", "exit"]

        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Hi"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        # Check for chat- prefix in session ID
        assert "Session ID: chat-" in output

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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_help_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test #help command displays available commands."""
        mock_input.side_effect = ["#help", "exit"]

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Available Commands:" in output
        assert "#help" in output
        assert "#debug" in output
        # Should NOT call execute_run for special commands
        mock_client.execute_run.assert_not_called()

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_debug_toggle_on(self, mock_input, mock_client_class, cli, mock_env):
        """Test #debug on enables debug mode."""
        mock_input.side_effect = ["#debug on", "#info", "exit"]

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Debug mode enabled" in output
        assert "Debug: enabled" in output

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_debug_affects_api_calls(self, mock_input, mock_client_class, cli, mock_env):
        """Test that #debug on affects subsequent API calls."""
        mock_input.side_effect = ["#debug on", "test query", "exit"]

        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["debug_enabled"] is True

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_stream_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test #stream tokens enables token streaming."""
        mock_input.side_effect = ["#stream tokens", "test", "exit"]

        mock_client = Mock()
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

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    @patch("uuid.uuid4")
    def test_new_command_changes_session(self, mock_uuid, mock_input, mock_client_class, cli, mock_env):
        """Test #new command generates new session ID."""
        # Mock uuid to return different values for session IDs
        from uuid import UUID
        mock_uuid.side_effect = [
            UUID("12345678-1234-5678-1234-567812345678"),
            UUID("87654321-4321-8765-4321-876543218765")
        ]

        mock_input.side_effect = ["test1", "#new", "test2", "exit"]

        mock_client = Mock()
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

        # Verify different session IDs
        assert mock_client.execute_run.call_count == 2
        session_1 = mock_client.execute_run.call_args_list[0][1]["session_identity"]
        session_2 = mock_client.execute_run.call_args_list[1][1]["session_identity"]
        assert session_1 != session_2

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_info_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test #info displays session information."""
        mock_input.side_effect = ["#info", "exit"]

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Session Information:" in output
        assert "Session ID:" in output
        assert "Environment:" in output

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    @patch("os.system")
    def test_clear_command(self, mock_system, mock_input, mock_client_class, cli, mock_env):
        """Test #clear command clears screen."""
        mock_input.side_effect = ["#clear", "exit"]

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat"])

        assert exit_code == 0
        mock_system.assert_called_once()
        call_arg = mock_system.call_args[0][0]
        assert call_arg in ['clear', 'cls']

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_unknown_command(self, mock_input, mock_client_class, cli, mock_env):
        """Test unknown special command shows error."""
        mock_input.side_effect = ["#unknown", "exit"]

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Unknown command: #unknown" in output
        assert "#help" in output

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_case_insensitive_commands(self, mock_input, mock_client_class, cli, mock_env):
        """Test special commands are case-insensitive."""
        mock_input.side_effect = ["#HELP", "#Debug ON", "exit"]

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Available Commands:" in output
        assert "Debug mode enabled" in output

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_command_aliases(self, mock_input, mock_client_class, cli, mock_env):
        """Test command aliases work."""
        mock_input.side_effect = ["#newsession", "#session", "exit"]

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "New Session Started" in output
        assert "Session Information:" in output

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_debug_query_state(self, mock_input, mock_client_class, cli, mock_env):
        """Test #debug without args shows current state."""
        mock_input.side_effect = ["#debug", "exit"]

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "Debug mode is currently" in output

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_stream_toggle_off(self, mock_input, mock_client_class, cli, mock_env):
        """Test #stream off disables streaming."""
        mock_input.side_effect = ["#stream off", "test", "exit"]

        mock_client = Mock()
        mock_client.execute_run.return_value = {
            "output": [{"type": "text", "content": "Response"}],
            "sessionInfo": {},
        }
        mock_client_class.return_value = mock_client

        exit_code = cli.run(["chat", "--stream", "tokens"])  # Start with streaming on

        assert exit_code == 0
        call_kwargs = mock_client.execute_run.call_args[1]
        assert call_kwargs["stream_enabled"] is False

    @patch("agentic_api_cli.cli.AgenticAPIClient")
    @patch("builtins.input")
    def test_history_placeholder(self, mock_input, mock_client_class, cli, mock_env):
        """Test #history shows placeholder message."""
        mock_input.side_effect = ["#history", "exit"]

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        with patch("sys.stdout", new=StringIO()) as fake_out:
            exit_code = cli.run(["chat"])

        assert exit_code == 0
        output = fake_out.getvalue()
        assert "History feature not yet implemented" in output
