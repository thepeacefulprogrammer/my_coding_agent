"""Configuration management for My Coding Agent.

This module provides type-safe configuration handling with support for:
- Environment variables
- Configuration files (TOML, JSON, YAML)
- Runtime configuration updates
- Theme and appearance settings
- Plugin configuration
"""

from .settings import Settings, get_settings

__all__ = [
    "Settings",
    "get_settings",
]
