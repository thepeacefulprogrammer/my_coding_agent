"""Configuration management for My Coding Agent.

This module provides type-safe configuration handling with support for:
- Environment variables
- Configuration files (TOML, JSON, YAML)
- Runtime configuration updates
- Theme and appearance settings
- Plugin configuration
"""

from .settings import Settings, get_settings
from .themes import ThemeConfig, get_theme_config
from .paths import get_app_dirs, get_config_path, get_data_path

__all__ = [
    "Settings",
    "ThemeConfig", 
    "get_settings",
    "get_theme_config",
    "get_app_dirs",
    "get_config_path",
    "get_data_path",
] 