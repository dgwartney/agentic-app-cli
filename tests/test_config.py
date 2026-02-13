"""
Unit tests for configuration management.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from agentic_api_cli.config import Config
from agentic_api_cli.exceptions import ConfigurationError


@pytest.fixture(autouse=True)
def prevent_dotenv_autoload(monkeypatch):
    """Prevent automatic .env loading in tests."""
    # Clear all KORE AI environment variables before each test
    for key in ["KOREAI_API_KEY", "KOREAI_APP_ID", "KOREAI_ENV_NAME", "KOREAI_BASE_URL", "KOREAI_TIMEOUT"]:
        monkeypatch.delenv(key, raising=False)

    # Mock load_dotenv to prevent loading project .env file
    with patch('agentic_api_cli.config.load_dotenv'):
        yield


class TestConfig:
    """Test Config class."""

    def test_init_with_env_vars(self, monkeypatch):
        """Test initialization with environment variables."""
        monkeypatch.setenv("KOREAI_API_KEY", "test-key")
        monkeypatch.setenv("KOREAI_APP_ID", "test-app")
        monkeypatch.setenv("KOREAI_ENV_NAME", "test-env")

        config = Config()

        assert config._api_key == "test-key"
        assert config._app_id == "test-app"
        assert config._env_name == "test-env"

    def test_init_with_defaults(self, monkeypatch):
        """Test initialization with default values."""
        # Clear environment variables
        monkeypatch.delenv("KOREAI_API_KEY", raising=False)
        monkeypatch.delenv("KOREAI_APP_ID", raising=False)
        monkeypatch.delenv("KOREAI_ENV_NAME", raising=False)
        monkeypatch.delenv("KOREAI_BASE_URL", raising=False)
        monkeypatch.delenv("KOREAI_TIMEOUT", raising=False)

        config = Config()

        assert config._api_key is None
        assert config._app_id is None
        assert config._env_name == "production"
        assert config._base_url == "https://agent-platform.kore.ai/api/v2"
        assert config._timeout == 30

    def test_init_with_env_file(self, monkeypatch, prevent_dotenv_autoload):
        """Test initialization with .env file."""
        # Clear environment variables first so .env file takes precedence
        monkeypatch.delenv("KOREAI_API_KEY", raising=False)
        monkeypatch.delenv("KOREAI_APP_ID", raising=False)
        monkeypatch.delenv("KOREAI_ENV_NAME", raising=False)

        # Import the real load_dotenv for this test
        from dotenv import load_dotenv as real_load_dotenv

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "KOREAI_API_KEY=file-key\n"
                "KOREAI_APP_ID=file-app\n"
                "KOREAI_ENV_NAME=file-env\n"
            )

            # Temporarily unpatch to allow real dotenv loading
            with patch('agentic_api_cli.config.load_dotenv', real_load_dotenv):
                config = Config(env_file=str(env_file))

            assert config._api_key == "file-key"
            assert config._app_id == "file-app"
            assert config._env_name == "file-env"

    def test_api_key_property(self, monkeypatch):
        """Test api_key property."""
        monkeypatch.setenv("KOREAI_API_KEY", "test-key")
        config = Config()
        assert config.api_key == "test-key"

    def test_api_key_raises_when_not_set(self, monkeypatch):
        """Test api_key raises ConfigurationError when not set."""
        monkeypatch.delenv("KOREAI_API_KEY", raising=False)
        config = Config()

        with pytest.raises(ConfigurationError) as exc_info:
            _ = config.api_key

        assert "API key not configured" in str(exc_info.value)

    def test_api_key_setter(self, monkeypatch):
        """Test api_key setter."""
        monkeypatch.delenv("KOREAI_API_KEY", raising=False)
        config = Config()
        config.api_key = "new-key"
        assert config.api_key == "new-key"

    def test_app_id_property(self, monkeypatch):
        """Test app_id property."""
        monkeypatch.setenv("KOREAI_APP_ID", "test-app")
        config = Config()
        assert config.app_id == "test-app"

    def test_app_id_raises_when_not_set(self, monkeypatch):
        """Test app_id raises ConfigurationError when not set."""
        monkeypatch.delenv("KOREAI_APP_ID", raising=False)
        config = Config()

        with pytest.raises(ConfigurationError) as exc_info:
            _ = config.app_id

        assert "App ID not configured" in str(exc_info.value)

    def test_app_id_setter(self, monkeypatch):
        """Test app_id setter."""
        monkeypatch.delenv("KOREAI_APP_ID", raising=False)
        config = Config()
        config.app_id = "new-app"
        assert config.app_id == "new-app"

    def test_env_name_property(self, monkeypatch):
        """Test env_name property."""
        monkeypatch.delenv("KOREAI_ENV_NAME", raising=False)
        config = Config()
        assert config.env_name == "production"

    def test_env_name_setter(self):
        """Test env_name setter."""
        config = Config()
        config.env_name = "staging"
        assert config.env_name == "staging"

    def test_base_url_property(self):
        """Test base_url property."""
        config = Config()
        assert config.base_url == "https://agent-platform.kore.ai/api/v2"

    def test_base_url_setter(self):
        """Test base_url setter."""
        config = Config()
        config.base_url = "https://custom.example.com"
        assert config.base_url == "https://custom.example.com"

    def test_timeout_property(self):
        """Test timeout property."""
        config = Config()
        assert config.timeout == 30

    def test_timeout_setter(self):
        """Test timeout setter."""
        config = Config()
        config.timeout = 60
        assert config.timeout == 60

    def test_timeout_from_env(self, monkeypatch):
        """Test timeout from environment variable."""
        monkeypatch.setenv("KOREAI_TIMEOUT", "45")
        config = Config()
        assert config.timeout == 45

    def test_validate_success(self, monkeypatch):
        """Test validate with valid configuration."""
        monkeypatch.setenv("KOREAI_API_KEY", "test-key")
        monkeypatch.setenv("KOREAI_APP_ID", "test-app")

        config = Config()
        config.validate()  # Should not raise

    def test_validate_missing_api_key(self, monkeypatch):
        """Test validate with missing API key."""
        monkeypatch.delenv("KOREAI_API_KEY", raising=False)
        monkeypatch.setenv("KOREAI_APP_ID", "test-app")

        config = Config()

        with pytest.raises(ConfigurationError):
            config.validate()

    def test_validate_missing_app_id(self, monkeypatch):
        """Test validate with missing app ID."""
        monkeypatch.setenv("KOREAI_API_KEY", "test-key")
        monkeypatch.delenv("KOREAI_APP_ID", raising=False)

        config = Config()

        with pytest.raises(ConfigurationError):
            config.validate()

    def test_repr(self, monkeypatch):
        """Test string representation."""
        monkeypatch.setenv("KOREAI_API_KEY", "kg-12345678-abcd")
        monkeypatch.setenv("KOREAI_APP_ID", "test-app")
        monkeypatch.delenv("KOREAI_ENV_NAME", raising=False)

        config = Config()
        repr_str = repr(config)

        assert "kg-12345" in repr_str  # First 5-8 chars
        assert "..." in repr_str  # Masking indicator
        assert "test-app" in repr_str
        assert "production" in repr_str
        assert "abcd" not in repr_str  # API key should be masked

    def test_repr_no_api_key(self, monkeypatch):
        """Test repr with no API key."""
        monkeypatch.delenv("KOREAI_API_KEY", raising=False)

        config = Config()
        repr_str = repr(config)

        assert "Not set" in repr_str
