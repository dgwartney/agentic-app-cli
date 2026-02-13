"""
Unit tests for CLI.
"""

import json
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
