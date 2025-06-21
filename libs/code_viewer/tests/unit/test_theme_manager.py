"""Tests for the ThemeManager class and dark mode functionality."""

from __future__ import annotations

from pathlib import Path

import pytest
from code_viewer.core.theme_manager import ThemeManager
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication, QMainWindow


@pytest.mark.qt
class TestThemeManager:
    """Test suite for ThemeManager class."""

    def test_theme_manager_initialization(self, qtbot):
        """Test ThemeManager initializes correctly."""
        app = QApplication.instance()
        theme_manager = ThemeManager(app)

        assert theme_manager.app is app
        assert hasattr(theme_manager, "_current_theme")
        assert hasattr(theme_manager, "_available_themes")
        assert "light" in theme_manager._available_themes
        assert "dark" in theme_manager._available_themes

    def test_theme_manager_get_current_theme(self, qtbot):
        """Test getting current theme."""
        app = QApplication.instance()
        theme_manager = ThemeManager(app)

        current_theme = theme_manager.get_current_theme()
        assert current_theme in ["light", "dark"]

    def test_theme_manager_get_available_themes(self, qtbot):
        """Test getting available themes list."""
        app = QApplication.instance()
        theme_manager = ThemeManager(app)

        themes = theme_manager.get_available_themes()
        assert isinstance(themes, list)
        assert "light" in themes
        assert "dark" in themes
        assert len(themes) >= 2

    def test_theme_manager_set_theme_light(self, qtbot):
        """Test setting light theme."""
        app = QApplication.instance()
        theme_manager = ThemeManager(app)

        # Set to light theme
        result = theme_manager.set_theme("light")
        assert result is True
        assert theme_manager.get_current_theme() == "light"

        # Application should have minimal or no stylesheet for light theme
        stylesheet = app.styleSheet()
        # Light theme might have empty stylesheet or minimal styling
        assert isinstance(stylesheet, str)

    def test_theme_manager_set_theme_dark(self, qtbot):
        """Test setting dark theme."""
        app = QApplication.instance()
        theme_manager = ThemeManager(app)

        # Set to dark theme
        result = theme_manager.set_theme("dark")
        assert result is True
        assert theme_manager.get_current_theme() == "dark"

        # Application should have dark theme stylesheet applied
        stylesheet = app.styleSheet()
        assert len(stylesheet) > 0
        # Check for common dark theme properties
        assert "background-color" in stylesheet.lower()

    def test_theme_manager_set_invalid_theme(self, qtbot):
        """Test setting invalid theme returns False."""
        app = QApplication.instance()
        theme_manager = ThemeManager(app)

        result = theme_manager.set_theme("invalid_theme")
        assert result is False
        # Current theme should remain unchanged
        current = theme_manager.get_current_theme()
        assert current in ["light", "dark"]

    def test_theme_manager_toggle_theme(self, qtbot):
        """Test toggling between themes."""
        app = QApplication.instance()
        theme_manager = ThemeManager(app)

        # Get initial theme
        initial_theme = theme_manager.get_current_theme()

        # Toggle theme
        theme_manager.toggle_theme()
        new_theme = theme_manager.get_current_theme()

        # Should be different from initial
        assert new_theme != initial_theme
        assert new_theme in ["light", "dark"]

        # Toggle back
        theme_manager.toggle_theme()
        final_theme = theme_manager.get_current_theme()
        assert final_theme == initial_theme

    def test_theme_manager_load_dark_stylesheet(self, qtbot):
        """Test loading dark theme stylesheet."""
        app = QApplication.instance()
        theme_manager = ThemeManager(app)

        # This should load the dark stylesheet
        stylesheet = theme_manager._load_stylesheet("dark")
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

        # Should contain typical dark theme styling
        stylesheet_lower = stylesheet.lower()
        assert any(
            keyword in stylesheet_lower
            for keyword in ["background-color", "color", "#", "dark", "black", "white"]
        )

    def test_theme_manager_load_light_stylesheet(self, qtbot):
        """Test loading light theme stylesheet."""
        app = QApplication.instance()
        theme_manager = ThemeManager(app)

        # Light theme might return empty string or minimal styling
        stylesheet = theme_manager._load_stylesheet("light")
        assert isinstance(stylesheet, str)

    def test_theme_manager_persistence_settings(self, qtbot):
        """Test theme persistence through QSettings."""
        app = QApplication.instance()

        # Clear any existing settings for clean test
        settings = QSettings("my_coding_agent", "Simple Code Viewer")
        settings.remove("theme/current")

        # Create theme manager and set theme
        theme_manager = ThemeManager(app)
        theme_manager.set_theme("dark")

        # Create new instance to test persistence
        theme_manager2 = ThemeManager(app)
        assert theme_manager2.get_current_theme() == "dark"

    def test_theme_manager_apply_to_widget(self, qtbot):
        """Test applying theme to specific widget."""
        app = QApplication.instance()
        theme_manager = ThemeManager(app)

        # Create a test widget
        widget = QMainWindow()
        qtbot.addWidget(widget)

        # Apply dark theme to widget
        theme_manager.apply_theme_to_widget(widget, "dark")

        # Widget should have stylesheet applied
        stylesheet = widget.styleSheet()
        if theme_manager.get_current_theme() == "dark":
            assert len(stylesheet) > 0

    def test_theme_manager_stylesheet_file_exists(self, qtbot):
        """Test that dark theme stylesheet file exists."""
        from code_viewer.assets import get_theme_file

        # Should be able to get dark theme file path
        dark_theme_path = get_theme_file("dark.qss")
        assert dark_theme_path is not None
        assert Path(dark_theme_path).exists()

        # File should contain CSS content
        with open(dark_theme_path, encoding="utf-8") as f:
            content = f.read()
        assert len(content) > 0
        assert any(
            keyword in content.lower()
            for keyword in ["background-color", "color", "qwidget", "qtextedit"]
        )

def test_get_theme_file_integration():
    """Test integration with assets get_theme_file function."""
    theme_manager = ThemeManager()

    # Test that get_theme_file is called correctly
    with patch("code_viewer.assets.get_theme_file") as mock_get_theme_file:
        mock_get_theme_file.return_value = "/path/to/dark.qss"

        result = theme_manager._get_theme_file("dark.qss")

        mock_get_theme_file.assert_called_once_with("dark.qss")
        assert result == "/path/to/dark.qss"
