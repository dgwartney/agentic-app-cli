"""
Configuration management for Agentic API CLI.

Loads configuration from environment variables or .env file.
"""

import os
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv

from agentic_api_cli.exceptions import ConfigurationError
from agentic_api_cli.logging_config import get_logger


class Config:
    """
    Configuration manager for Agentic API CLI.

    Loads configuration from environment variables with optional .env file support.
    """

    def __init__(self, env_file: Optional[str] = None, profile: Optional[str] = None) -> None:
        """
        Initialize configuration.

        Configuration precedence (highest to lowest):
        1. Command-line arguments (applied in CLI._load_config)
        2. Environment variables
        3. Profile values
        4. Built-in defaults

        Args:
            env_file: Path to .env file (optional). If not provided, will look for .env
                     in current directory.
            profile: Profile name to load configuration from (optional)
        """
        logger = get_logger('config')

        # Start with built-in defaults
        self._api_key = None
        self._app_id = None
        self._env_name = "production"
        self._base_url = "https://agent-platform.kore.ai/api/v2"
        self._timeout = 30

        # Load from profile if specified (precedence: 3)
        if profile:
            logger.debug(f"Loading configuration from profile: {profile}")
            self._load_from_profile(profile)

        # Load from .env file if it exists (will be overridden by env vars)
        if env_file:
            logger.debug(f"Loading environment from file: {env_file}")
            load_dotenv(env_file)
        else:
            # Try to load from current directory
            env_path = Path.cwd() / ".env"
            if env_path.exists():
                logger.debug(f"Loading environment from: {env_path}")
                load_dotenv(env_path)

        # Load configuration from environment variables (precedence: 2)
        # These override profile values
        if os.getenv("KOREAI_API_KEY"):
            self._api_key = os.getenv("KOREAI_API_KEY")
        if os.getenv("KOREAI_APP_ID"):
            self._app_id = os.getenv("KOREAI_APP_ID")
        if os.getenv("KOREAI_ENV_NAME"):
            self._env_name = os.getenv("KOREAI_ENV_NAME")
        if os.getenv("KOREAI_BASE_URL"):
            self._base_url = os.getenv("KOREAI_BASE_URL")
        if os.getenv("KOREAI_TIMEOUT"):
            self._timeout = int(os.getenv("KOREAI_TIMEOUT"))

        logger.debug(f"Configuration initialized: env_name={self._env_name}, base_url={self._base_url}, timeout={self._timeout}")

    def _load_from_profile(self, profile_name: str) -> None:
        """
        Load configuration from a profile.

        Args:
            profile_name: Name of the profile to load

        Raises:
            ConfigurationError: If profile doesn't exist or can't be loaded
        """
        from agentic_api_cli.profiles import ProfileManager

        logger = get_logger('config')
        manager = ProfileManager()

        try:
            profile = manager.get_profile(profile_name)
            self._api_key = profile.get("api_key")
            self._app_id = profile.get("app_id")
            self._env_name = profile.get("env_name", "production")
            self._base_url = profile.get("base_url", "https://agent-platform.kore.ai/api/v2")
            self._timeout = profile.get("timeout", 30)
            logger.info(f"Loaded configuration from profile: {profile_name}")
        except Exception as e:
            logger.error(f"Failed to load profile '{profile_name}': {e}")
            raise

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
        logger = get_logger('config')
        logger.debug("Validating configuration...")

        # This will raise ConfigurationError if not set
        _ = self.api_key
        _ = self.app_id

        logger.info("Configuration validated successfully")

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
