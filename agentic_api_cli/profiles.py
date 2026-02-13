"""
Profile management for Agentic API CLI.

Manages configuration profiles stored in ~/.kore directory.
"""

import json
import os
from pathlib import Path
from typing import Optional

from agentic_api_cli.exceptions import ConfigurationError
from agentic_api_cli.logging_config import get_logger


class ProfileManager:
    """
    Manages configuration profiles stored in ~/.kore directory.

    Profiles allow users to store and switch between different configuration
    sets for different environments or accounts.
    """

    def __init__(self) -> None:
        """Initialize the ProfileManager."""
        self.profiles_dir = Path.home() / ".kore"
        self.profiles_file = self.profiles_dir / "profiles"
        self.config_file = self.profiles_dir / "config"
        self.logger = get_logger('profiles')

    def ensure_profiles_dir(self) -> None:
        """
        Create ~/.kore directory with secure permissions if it doesn't exist.

        Creates directory with 0700 permissions to ensure privacy.
        """
        if not self.profiles_dir.exists():
            self.logger.debug(f"Creating profiles directory: {self.profiles_dir}")
            self.profiles_dir.mkdir(mode=0o700, parents=True)
            self.logger.info(f"Created profiles directory: {self.profiles_dir}")
        else:
            # Ensure correct permissions on existing directory
            self.profiles_dir.chmod(0o700)

    def load_profiles(self) -> dict:
        """
        Load all profiles from JSON file.

        Returns:
            Dictionary of profile name to profile data

        Raises:
            ConfigurationError: If profiles file is corrupted or invalid
        """
        if not self.profiles_file.exists():
            self.logger.debug("No profiles file found, returning empty dict")
            return {}

        try:
            with open(self.profiles_file, 'r') as f:
                profiles = json.load(f)
                self.logger.debug(f"Loaded {len(profiles)} profiles")
                return profiles
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse profiles file: {e}")
            raise ConfigurationError(
                f"Corrupted profiles file at {self.profiles_file}. "
                f"Parse error: {e}. Consider backing up and removing the file."
            )
        except Exception as e:
            self.logger.error(f"Failed to load profiles: {e}")
            raise ConfigurationError(f"Failed to load profiles: {e}")

    def save_profiles(self, profiles: dict) -> None:
        """
        Save profiles to JSON file with secure permissions.

        Args:
            profiles: Dictionary of profile name to profile data

        The file is created with 0600 permissions to prevent unauthorized access.
        """
        self.ensure_profiles_dir()

        try:
            # Write to temp file first for atomicity
            temp_file = self.profiles_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(profiles, f, indent=2)

            # Set secure permissions (0600 - owner read/write only)
            temp_file.chmod(0o600)

            # Atomic rename
            temp_file.replace(self.profiles_file)

            self.logger.info(f"Saved {len(profiles)} profiles to {self.profiles_file}")
        except Exception as e:
            self.logger.error(f"Failed to save profiles: {e}")
            raise ConfigurationError(f"Failed to save profiles: {e}")

    def add_profile(
        self,
        name: str,
        api_key: str,
        app_id: str,
        env_name: str,
        base_url: str,
        timeout: int,
    ) -> None:
        """
        Add or update a profile.

        Args:
            name: Profile name (must not be empty)
            api_key: API key
            app_id: Application ID
            env_name: Environment name
            base_url: Base URL
            timeout: Timeout in seconds

        Raises:
            ConfigurationError: If profile name is invalid
        """
        if not name or not name.strip():
            raise ConfigurationError("Profile name cannot be empty")

        name = name.strip()
        self.logger.debug(f"Adding profile: {name}")

        profiles = self.load_profiles()

        # Warn if overwriting existing profile
        if name in profiles:
            self.logger.warning(f"Overwriting existing profile: {name}")

        profiles[name] = {
            "api_key": api_key,
            "app_id": app_id,
            "env_name": env_name,
            "base_url": base_url,
            "timeout": timeout,
        }

        self.save_profiles(profiles)
        self.logger.info(f"Successfully added/updated profile: {name}")

    def get_profile(self, name: str) -> dict:
        """
        Get a specific profile by name.

        Args:
            name: Profile name

        Returns:
            Profile data dictionary

        Raises:
            ConfigurationError: If profile doesn't exist
        """
        profiles = self.load_profiles()

        if name not in profiles:
            available = list(profiles.keys())
            self.logger.error(f"Profile not found: {name}")
            raise ConfigurationError(
                f"Profile '{name}' not found. "
                f"Available profiles: {', '.join(available) if available else 'none'}"
            )

        self.logger.debug(f"Retrieved profile: {name}")
        return profiles[name]

    def list_profiles(self) -> list[str]:
        """
        List all profile names.

        Returns:
            List of profile names (sorted alphabetically)
        """
        profiles = self.load_profiles()
        profile_names = sorted(profiles.keys())
        self.logger.debug(f"Listing {len(profile_names)} profiles")
        return profile_names

    def delete_profile(self, name: str) -> None:
        """
        Delete a profile.

        Args:
            name: Profile name to delete

        Raises:
            ConfigurationError: If profile doesn't exist
        """
        profiles = self.load_profiles()

        if name not in profiles:
            self.logger.error(f"Cannot delete profile - not found: {name}")
            raise ConfigurationError(f"Profile '{name}' not found")

        del profiles[name]
        self.save_profiles(profiles)

        # Clear default if we just deleted it
        default = self.get_default_profile()
        if default == name:
            self.logger.warning(f"Deleted default profile '{name}', clearing default setting")
            self.clear_default_profile()

        self.logger.info(f"Deleted profile: {name}")

    def set_default_profile(self, name: str) -> None:
        """
        Set the default profile.

        Args:
            name: Profile name to set as default

        Raises:
            ConfigurationError: If profile doesn't exist
        """
        # Verify profile exists
        self.get_profile(name)  # Will raise if doesn't exist

        self.ensure_profiles_dir()

        config = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                self.logger.warning("Corrupted config file, creating new one")
                config = {}

        config["default_profile"] = name

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.config_file.chmod(0o600)
            self.logger.info(f"Set default profile to: {name}")
        except Exception as e:
            self.logger.error(f"Failed to set default profile: {e}")
            raise ConfigurationError(f"Failed to set default profile: {e}")

    def get_default_profile(self) -> Optional[str]:
        """
        Get the name of the default profile.

        Returns:
            Default profile name, or None if not set
        """
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                default = config.get("default_profile")
                if default:
                    self.logger.debug(f"Default profile: {default}")
                return default
        except (json.JSONDecodeError, KeyError):
            self.logger.warning("Failed to read default profile from config")
            return None

    def clear_default_profile(self) -> None:
        """Clear the default profile setting."""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            config = {}

        if "default_profile" in config:
            del config["default_profile"]

            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.logger.info("Cleared default profile setting")

    def mask_api_key(self, api_key: str) -> str:
        """
        Mask API key for display.

        Args:
            api_key: Full API key

        Returns:
            Masked API key (e.g., "kg-1234****")
        """
        if not api_key or len(api_key) <= 8:
            return "****"
        return f"{api_key[:8]}****"

    def get_profile_display(self, name: str, show_keys: bool = False) -> dict:
        """
        Get profile data formatted for display.

        Args:
            name: Profile name
            show_keys: Whether to show full API keys

        Returns:
            Profile data with masked or full API keys
        """
        profile = self.get_profile(name)
        display = profile.copy()

        if not show_keys:
            display["api_key"] = self.mask_api_key(profile["api_key"])

        return display
