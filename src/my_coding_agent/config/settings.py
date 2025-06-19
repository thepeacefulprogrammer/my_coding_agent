"""Simplified configuration settings for MCP Client Interface.

This module provides a simplified configuration system focused on:
- MCP server connection settings
- Essential UI preferences
- Configuration file management
"""

from __future__ import annotations

import contextlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


@dataclass
class Settings:
    """Simplified application settings focused on MCP server configuration.

    This class provides centralized configuration management for the MCP client,
    including server connection settings and essential UI preferences.

    Attributes:
        # Essential UI settings
        window_width: Default main window width in pixels
        window_height: Default main window height in pixels
        theme: UI theme name ('dark' or 'light')

        # MCP server configuration
        mcp_server_url: URL of the MCP server to connect to
        mcp_timeout: Connection timeout in seconds
        mcp_enable_streaming: Whether to enable streaming responses
        mcp_max_retries: Maximum number of connection retries
        mcp_auth_token: Authentication token for MCP server
        mcp_auth_type: Authentication type ('none', 'bearer', 'oauth2')

        # Directories
        config_dir: Directory for storing configuration files
        cache_dir: Directory for storing cache files
    """

    # Essential UI settings (preserved from original)
    window_width: int = 1200
    window_height: int = 800
    theme: str = "dark"

    # MCP server configuration
    mcp_server_url: str = "http://localhost:8080"
    mcp_timeout: float = 30.0
    mcp_enable_streaming: bool = True
    mcp_max_retries: int = 3
    mcp_auth_token: str = ""
    mcp_auth_type: str = "none"

    # Directories
    config_dir: Path = field(default_factory=lambda: _get_config_dir())
    cache_dir: Path = field(default_factory=lambda: _get_cache_dir())

    def __post_init__(self) -> None:
        """Initialize settings after dataclass creation.

        This method ensures that directories exist and
        applies any environment variable overrides.
        """
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Apply environment variable overrides
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to settings.

        This method checks for environment variables that can
        override default settings values.
        """
        # UI settings
        if width := os.getenv("MCA_WINDOW_WIDTH"):
            with contextlib.suppress(ValueError):
                self.window_width = int(width)

        if height := os.getenv("MCA_WINDOW_HEIGHT"):
            with contextlib.suppress(ValueError):
                self.window_height = int(height)

        if (theme := os.getenv("MCA_THEME")) and theme.lower() in ("dark", "light"):
            self.theme = theme.lower()

        # MCP server settings
        if server_url := os.getenv("MCP_SERVER_URL"):
            self.mcp_server_url = server_url

        if timeout := os.getenv("MCP_TIMEOUT"):
            with contextlib.suppress(ValueError):
                self.mcp_timeout = float(timeout)

        if streaming := os.getenv("MCP_ENABLE_STREAMING"):
            self.mcp_enable_streaming = streaming.lower() in ("true", "1", "yes")

        if retries := os.getenv("MCP_MAX_RETRIES"):
            with contextlib.suppress(ValueError):
                self.mcp_max_retries = int(retries)

        if auth_token := os.getenv("MCP_AUTH_TOKEN"):
            self.mcp_auth_token = auth_token

        if (auth_type := os.getenv("MCP_AUTH_TYPE")) and auth_type.lower() in (
            "none",
            "bearer",
            "oauth2",
        ):
            self.mcp_auth_type = auth_type.lower()

    def is_mcp_url_valid(self) -> bool:
        """Validate MCP server URL format.

        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(self.mcp_server_url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def is_mcp_timeout_valid(self) -> bool:
        """Validate MCP timeout value.

        Returns:
            True if timeout is valid, False otherwise
        """
        return self.mcp_timeout > 0

    def get_mcp_config(self) -> dict[str, Any]:
        """Get MCP configuration as dictionary.

        Returns:
            Dictionary containing MCP connection configuration
        """
        return {
            "server_url": self.mcp_server_url,
            "timeout": self.mcp_timeout,
            "enable_streaming": self.mcp_enable_streaming,
            "max_retries": self.mcp_max_retries,
            "auth_token": self.mcp_auth_token,
            "auth_type": self.mcp_auth_type,
        }

    def get_mcp_auth_config(self) -> dict[str, Any]:
        """Get MCP authentication configuration.

        Returns:
            Dictionary containing authentication settings
        """
        return {"type": self.mcp_auth_type, "token": self.mcp_auth_token}

    def validate_mcp_config(self) -> dict[str, Any]:
        """Validate complete MCP configuration.

        Returns:
            Dictionary with validation results and any errors
        """
        errors = []

        # Validate URL
        if not self.is_mcp_url_valid():
            errors.append("Invalid MCP server URL format")

        # Validate timeout
        if not self.is_mcp_timeout_valid():
            errors.append("MCP timeout must be greater than 0")

        # Validate max retries
        if self.mcp_max_retries < 0:
            errors.append("MCP max retries must be non-negative")

        # Validate auth type
        if self.mcp_auth_type not in ("none", "bearer", "oauth2"):
            errors.append("Invalid MCP authentication type")

        return {"valid": len(errors) == 0, "errors": errors}

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary format.

        Returns:
            Dictionary representation of settings with serializable values
        """
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value
        return result

    def update(self, **kwargs: Any) -> None:
        """Update settings with new values.

        Args:
            **kwargs: Settings to update with their new values
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


def _get_config_dir() -> Path:
    """Get the configuration directory for the application.

    Returns:
        Path to configuration directory, creating it if needed
    """
    if config_home := os.getenv("XDG_CONFIG_HOME"):
        return Path(config_home) / "my_coding_agent"
    else:
        return Path.home() / ".config" / "my_coding_agent"


def _get_cache_dir() -> Path:
    """Get the cache directory for the application.

    Returns:
        Path to cache directory, creating it if needed
    """
    if cache_home := os.getenv("XDG_CACHE_HOME"):
        return Path(cache_home) / "my_coding_agent"
    else:
        return Path.home() / ".cache" / "my_coding_agent"


# Global settings instance
_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance.

    This function provides a singleton pattern for accessing
    application settings throughout the codebase.

    Returns:
        Global Settings instance
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reset_settings() -> None:
    """Reset the global settings instance.

    This function is primarily useful for testing to ensure
    a clean settings state between tests.
    """
    global _settings_instance
    _settings_instance = None


def load_settings_from_file(config_path: Path) -> Settings:
    """Load settings from a configuration file.

    Args:
        config_path: Path to configuration file (JSON format)

    Returns:
        Settings instance with values from file
    """
    try:
        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)

            # Create settings instance
            settings = Settings()

            # Update with loaded data
            for key, value in data.items():
                if hasattr(settings, key):
                    # Convert string paths back to Path objects
                    if key in ("config_dir", "cache_dir"):
                        value = Path(value)
                    setattr(settings, key, value)

            return settings
        else:
            # Return default settings if file doesn't exist
            return Settings()
    except Exception:
        # Return default settings on any error
        return Settings()


def save_settings_to_file(settings: Settings, config_path: Path) -> None:
    """Save settings to a configuration file.

    Args:
        settings: Settings instance to save
        config_path: Path where to save configuration file
    """
    try:
        # Ensure config directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert settings to dictionary and save as JSON
        settings_dict = settings.to_dict()

        with open(config_path, "w") as f:
            json.dump(settings_dict, f, indent=2)
    except Exception:
        # Fail silently to avoid disrupting application
        pass
