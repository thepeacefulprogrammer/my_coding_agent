"""Configuration settings for My Coding Agent.

This module provides a centralized configuration system that supports:
- Environment variables
- Default values
- Type safety with dataclasses
- Theme and UI settings
- File handling preferences
"""

import contextlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Settings:
    """Application settings with type-safe configuration options.

    This class provides centralized configuration management with
    support for environment variables and sensible defaults.

    Attributes:
        window_width: Default main window width in pixels
        window_height: Default main window height in pixels
        splitter_position: Default splitter position (0.0 to 1.0)
        theme: UI theme name ('dark' or 'light')
        font_family: Code viewer font family
        font_size: Code viewer font size in points
        line_numbers: Whether to show line numbers by default
        word_wrap: Whether to enable word wrapping
        max_file_size_mb: Maximum file size to load in MB
        recent_files_count: Number of recent files to remember
        auto_detect_language: Whether to auto-detect file language
        highlight_current_line: Whether to highlight current line
        show_whitespace: Whether to show whitespace characters
        tab_width: Tab width in spaces
        config_dir: Directory for storing configuration files
        cache_dir: Directory for storing cache files
    """

    # Window settings
    window_width: int = 1200
    window_height: int = 800
    splitter_position: float = 0.3

    # Theme settings
    theme: str = "dark"
    font_family: str = "JetBrains Mono"
    font_size: int = 11

    # Editor settings
    line_numbers: bool = True
    word_wrap: bool = False
    highlight_current_line: bool = True
    show_whitespace: bool = False
    tab_width: int = 4

    # File handling
    max_file_size_mb: int = 10
    auto_detect_language: bool = True

    # Application settings
    recent_files_count: int = 10

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
        # Window settings
        if width := os.getenv("MCA_WINDOW_WIDTH"):
            with contextlib.suppress(ValueError):
                self.window_width = int(width)

        if height := os.getenv("MCA_WINDOW_HEIGHT"):
            with contextlib.suppress(ValueError):
                self.window_height = int(height)

        # Theme settings
        if (theme := os.getenv("MCA_THEME")) and theme.lower() in ("dark", "light"):
            self.theme = theme.lower()

        if font_family := os.getenv("MCA_FONT_FAMILY"):
            self.font_family = font_family

        if font_size := os.getenv("MCA_FONT_SIZE"):
            with contextlib.suppress(ValueError):
                self.font_size = int(font_size)

    def to_dict(self) -> Dict[str, Any]:
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
_settings_instance: Optional[Settings] = None


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
        config_path: Path to configuration file (TOML format)

    Returns:
        Settings instance with values from file

    Note:
        This function is planned for future implementation
        to support configuration files.
    """
    # Future implementation for loading from TOML/JSON files
    # For now, return default settings
    return Settings()


def save_settings_to_file(settings: Settings, config_path: Path) -> None:
    """Save settings to a configuration file.

    Args:
        settings: Settings instance to save
        config_path: Path where to save configuration file

    Note:
        This function is planned for future implementation
        to support configuration files.
    """
    # Future implementation for saving to TOML/JSON files
    pass
