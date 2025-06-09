"""Assets management for My Coding Agent.

This module provides utilities for managing application assets including
icons, themes, and other resources. It offers a centralized way to access
and validate asset files.
"""

from pathlib import Path
from typing import List


def get_assets_dir() -> Path:
    """Get the assets directory path.

    Returns:
        Path to the assets directory
    """
    return Path(__file__).parent


def get_icon_path(category: str, filename: str) -> Path:
    """Get the path to an icon file.

    Args:
        category: Icon category (file_types, actions, ui)
        filename: Icon filename

    Returns:
        Path to the icon file

    Raises:
        ValueError: If category is invalid or filename is empty
    """
    if not filename:
        raise ValueError("Icon filename cannot be empty")

    valid_categories = ["file_types", "actions", "ui"]
    if category not in valid_categories:
        raise ValueError(
            f"Invalid icon category: {category}. Valid categories: {valid_categories}"
        )

    assets_dir = get_assets_dir()
    icon_path = assets_dir / "icons" / category / filename
    return icon_path


def get_theme_path(theme_name: str) -> Path:
    """Get the path to a theme file.

    Args:
        theme_name: Name of the theme (without .qss extension)

    Returns:
        Path to the theme file

    Raises:
        ValueError: If theme name is empty or theme not found
    """
    if not theme_name:
        raise ValueError("Theme name cannot be empty")

    assets_dir = get_assets_dir()
    theme_path = assets_dir / "themes" / f"{theme_name}.qss"

    if not theme_path.exists():
        available_themes = list_available_themes()
        raise ValueError(
            f"Theme '{theme_name}' not found. Available themes: {available_themes}"
        )

    return theme_path


def get_theme_file(filename: str) -> str:
    """Get the full path to a theme file.

    Args:
        filename: Theme filename (e.g., 'dark.qss')

    Returns:
        Full path to the theme file as a string

    Raises:
        ValueError: If filename is empty
        FileNotFoundError: If theme file doesn't exist
    """
    if not filename:
        raise ValueError("Theme filename cannot be empty")

    assets_dir = get_assets_dir()
    theme_path = assets_dir / "themes" / filename

    if not theme_path.exists():
        available_themes = list_available_themes()
        raise FileNotFoundError(
            f"Theme file '{filename}' not found. Available themes: {available_themes}"
        )

    return str(theme_path)


def list_available_themes() -> List[str]:
    """List all available theme names.

    Returns:
        List of available theme names (without .qss extension)
    """
    assets_dir = get_assets_dir()
    themes_dir = assets_dir / "themes"

    if not themes_dir.exists():
        return []

    theme_files = themes_dir.glob("*.qss")
    return [theme_file.stem for theme_file in theme_files]


def validate_assets_structure() -> bool:
    """Validate that the assets directory structure is correct.

    Returns:
        True if structure is valid, False otherwise
    """
    assets_dir = get_assets_dir()

    # Check main directories exist
    required_dirs = ["icons", "themes"]
    for dir_name in required_dirs:
        dir_path = assets_dir / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            return False

    # Check icon subdirectories
    icons_dir = assets_dir / "icons"
    required_icon_dirs = ["file_types", "actions", "ui"]
    for subdir in required_icon_dirs:
        subdir_path = icons_dir / subdir
        if not subdir_path.exists() or not subdir_path.is_dir():
            return False

    # Check theme files exist
    themes_dir = assets_dir / "themes"
    required_themes = ["dark.qss", "light.qss"]
    for theme_file in required_themes:
        theme_path = themes_dir / theme_file
        if not theme_path.exists() or not theme_path.is_file():
            return False

    return True


# Export public functions
__all__ = [
    "get_assets_dir",
    "get_icon_path",
    "get_theme_path",
    "get_theme_file",
    "list_available_themes",
    "validate_assets_structure",
]
