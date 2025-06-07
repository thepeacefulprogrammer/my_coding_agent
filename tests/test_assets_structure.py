"""Tests for assets directory structure and resource management.

This module tests the assets directory structure for icons and themes,
ensuring proper organization and accessibility of application resources.
"""

from pathlib import Path

import pytest
from src.my_coding_agent.assets import (
    get_icon_path,
    get_theme_path,
    list_available_themes,
)


class TestAssetsStructure:
    """Test cases for assets directory structure and organization."""

    def test_assets_module_exists(self):
        """Test that the assets module exists and is importable."""
        import src.my_coding_agent.assets

        assert src.my_coding_agent.assets is not None

    def test_assets_directory_exists(self):
        """Test that the assets directory exists in the package."""
        from src.my_coding_agent import assets

        assets_dir = Path(assets.__file__).parent
        assert assets_dir.exists()
        assert assets_dir.is_dir()
        assert assets_dir.name == "assets"

    def test_icons_directory_structure(self):
        """Test that the icons directory has proper structure."""
        from src.my_coding_agent import assets

        assets_dir = Path(assets.__file__).parent
        icons_dir = assets_dir / "icons"

        assert icons_dir.exists()
        assert icons_dir.is_dir()

        # Check for required icon categories
        expected_subdirs = ["file_types", "actions", "ui"]
        for subdir in expected_subdirs:
            subdir_path = icons_dir / subdir
            assert subdir_path.exists(), f"Missing icons subdirectory: {subdir}"
            assert subdir_path.is_dir()

    def test_themes_directory_structure(self):
        """Test that the themes directory has proper structure."""
        from src.my_coding_agent import assets

        assets_dir = Path(assets.__file__).parent
        themes_dir = assets_dir / "themes"

        assert themes_dir.exists()
        assert themes_dir.is_dir()

        # Check for required theme files
        expected_themes = ["dark.qss", "light.qss"]
        for theme_file in expected_themes:
            theme_path = themes_dir / theme_file
            assert theme_path.exists(), f"Missing theme file: {theme_file}"
            assert theme_path.is_file()

    def test_get_icon_path_function(self):
        """Test the get_icon_path utility function."""
        # Test valid icon path
        icon_path = get_icon_path("file_types", "python.png")
        assert isinstance(icon_path, Path)
        assert icon_path.name == "python.png"
        assert "file_types" in str(icon_path)

        # Test with different category
        action_icon = get_icon_path("actions", "open.png")
        assert isinstance(action_icon, Path)
        assert action_icon.name == "open.png"
        assert "actions" in str(action_icon)

    def test_get_theme_path_function(self):
        """Test the get_theme_path utility function."""
        # Test dark theme
        dark_theme = get_theme_path("dark")
        assert isinstance(dark_theme, Path)
        assert dark_theme.name == "dark.qss"
        assert "themes" in str(dark_theme)

        # Test light theme
        light_theme = get_theme_path("light")
        assert isinstance(light_theme, Path)
        assert light_theme.name == "light.qss"
        assert "themes" in str(light_theme)

    def test_list_available_themes_function(self):
        """Test the list_available_themes utility function."""
        themes = list_available_themes()
        assert isinstance(themes, list)
        assert len(themes) >= 2
        assert "dark" in themes
        assert "light" in themes

    def test_icon_path_validation(self):
        """Test that icon paths are validated properly."""
        # Test invalid category
        with pytest.raises(ValueError, match="Invalid icon category"):
            get_icon_path("invalid_category", "test.png")

        # Test empty filename
        with pytest.raises(ValueError, match="Icon filename cannot be empty"):
            get_icon_path("file_types", "")

    def test_theme_path_validation(self):
        """Test that theme paths are validated properly."""
        # Test invalid theme name
        with pytest.raises(ValueError, match="Theme 'invalid' not found"):
            get_theme_path("invalid")

        # Test empty theme name
        with pytest.raises(ValueError, match="Theme name cannot be empty"):
            get_theme_path("")

    def test_file_type_icons_exist(self):
        """Test that required file type icons exist."""
        required_icons = [
            "python.png",
            "javascript.png",
            "json.png",
            "text.png",
            "folder.png",
            "folder_open.png",
            "file.png",
        ]

        for icon_name in required_icons:
            icon_path = get_icon_path("file_types", icon_name)
            assert icon_path.exists(), f"Missing required icon: {icon_name}"
            assert icon_path.is_file()

    def test_action_icons_exist(self):
        """Test that required action icons exist."""
        required_icons = [
            "open.png",
            "refresh.png",
            "expand_all.png",
            "collapse_all.png",
        ]

        for icon_name in required_icons:
            icon_path = get_icon_path("actions", icon_name)
            assert icon_path.exists(), f"Missing required action icon: {icon_name}"
            assert icon_path.is_file()

    def test_ui_icons_exist(self):
        """Test that required UI icons exist."""
        required_icons = ["app_icon.png", "splitter_handle.png"]

        for icon_name in required_icons:
            icon_path = get_icon_path("ui", icon_name)
            assert icon_path.exists(), f"Missing required UI icon: {icon_name}"
            assert icon_path.is_file()

    def test_theme_files_valid_qss(self):
        """Test that theme files contain valid QSS content."""
        themes = list_available_themes()

        for theme_name in themes:
            theme_path = get_theme_path(theme_name)
            assert theme_path.exists()

            # Read and validate basic QSS structure
            content = theme_path.read_text(encoding="utf-8")
            assert len(content) > 0, f"Theme file {theme_name}.qss is empty"

            # Check for basic QSS selectors
            expected_selectors = ["QMainWindow", "QTreeView", "QTextEdit", "QSplitter"]
            for selector in expected_selectors:
                assert selector in content, f"Missing {selector} in {theme_name}.qss"


class TestAssetsResourceManagement:
    """Test cases for assets resource management and loading."""

    def test_icon_loading_performance(self):
        """Test that icon loading is performant."""
        import time

        start_time = time.time()
        for _ in range(100):
            get_icon_path("file_types", "python.png")
        end_time = time.time()

        # Should be very fast (under 0.1 seconds for 100 calls)
        assert (end_time - start_time) < 0.1

    def test_theme_loading_performance(self):
        """Test that theme loading is performant."""
        import time

        start_time = time.time()
        for _ in range(100):
            get_theme_path("dark")
        end_time = time.time()

        # Should be very fast (under 0.1 seconds for 100 calls)
        assert (end_time - start_time) < 0.1

    def test_missing_assets_handling(self):
        """Test handling of missing asset files."""
        # Test missing icon - should return path but not exist
        icon_path = get_icon_path("file_types", "nonexistent.png")
        assert isinstance(icon_path, Path)
        assert not icon_path.exists()

        # Test missing theme - should raise ValueError
        with pytest.raises(ValueError, match="Theme 'nonexistent' not found"):
            get_theme_path("nonexistent")

    def test_assets_package_integrity(self):
        """Test that the assets package maintains integrity."""
        from src.my_coding_agent import assets

        # Check that __init__.py exists and has required exports
        init_file = Path(assets.__file__)
        assert init_file.exists()

        # Check that required functions are exported
        required_functions = [
            "get_icon_path",
            "get_theme_path",
            "list_available_themes",
        ]
        for func_name in required_functions:
            assert hasattr(assets, func_name), f"Missing function: {func_name}"
