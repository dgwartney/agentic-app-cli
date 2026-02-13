"""
Configuration management for Agentic API CLI.

Loads configuration from environment variables or .env file.
"""

import os
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv

from agentic_api_cli.exceptions import ConfigurationError


class Config:
    """
    Configuration manager for Agentic API CLI.

    Loads configuration from environment variables with optional .env file support.
    """

    def __init__(self, env_file: Optional[str] = None) -> None:
        """
        Initialize configuration.

        Args:
            env_file: Path to .env file (optional). If not provided, will look for .env
                     in current directory.
        """
        # Load from .env file if it exists
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load from current directory
            env_path = Path.cwd() / ".env"
            if env_path.exists():
                load_dotenv(env_path)

        # Load configuration from environment variables
        self._api_key = os.getenv("KOREAI_API_KEY")
        self._app_id = os.getenv("KOREAI_APP_ID")
        self._env_name = os.getenv("KOREAI_ENV_NAME", "production")
        self._base_url = os.getenv("KOREAI_BASE_URL", "https://agent-platform.kore.ai/api/v2")
        self._timeout = int(os.getenv("KOREAI_TIMEOUT", "30"))

    @property
    def api_key(self) -> str:
        """
        Get API key.

        Returns:
            API key

        Raises:
            ConfigurationError: If API key is not set
        """
        if not self._api_key:
            raise ConfigurationError(
                "API key not configured. Set KOREAI_API_KEY environment variable or use --api-key option."
            )
        return self._api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        """Set API key."""
        self._api_key = value

    @property
    def app_id(self) -> str:
        """
        Get application ID.

        Returns:
            Application ID

        Raises:
            ConfigurationError: If app ID is not set
        """
        if not self._app_id:
            raise ConfigurationError(
                "App ID not configured. Set KOREAI_APP_ID environment variable or use --app-id option."
            )
        return self._app_id

    @app_id.setter
    def app_id(self, value: str) -> None:
        """Set application ID."""
        self._app_id = value

    @property
    def env_name(self) -> str:
        """
        Get environment name.

        Returns:
            Environment name (defaults to 'production')
        """
        return self._env_name

    @env_name.setter
    def env_name(self, value: str) -> None:
        """Set environment name."""
        self._env_name = value

    @property
    def base_url(self) -> str:
        """
        Get base URL.

        Returns:
            Base URL for API
        """
        return self._base_url

    @base_url.setter
    def base_url(self, value: str) -> None:
        """Set base URL."""
        self._base_url = value

    @property
    def timeout(self) -> int:
        """
        Get request timeout.

        Returns:
            Timeout in seconds
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value: int) -> None:
        """Set request timeout."""
        self._timeout = value

    def validate(self) -> None:
        """
        Validate that all required configuration is present.

        Raises:
            ConfigurationError: If any required configuration is missing
        """
        # This will raise ConfigurationError if not set
        _ = self.api_key
        _ = self.app_id

    def __repr__(self) -> str:
        """String representation (masks sensitive data)."""
        api_key_masked = f"{self._api_key[:8]}..." if self._api_key else "Not set"
        return (
            f"Config(api_key='{api_key_masked}', "
            f"app_id='{self._app_id}', "
            f"env_name='{self._env_name}', "
            f"base_url='{self._base_url}', "
            f"timeout={self._timeout})"
        )
