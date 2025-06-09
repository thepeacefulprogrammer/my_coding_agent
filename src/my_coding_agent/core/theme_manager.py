"""Theme management for the Simple Code Viewer application.

This module provides the ThemeManager class for handling application themes,
including dark mode styling and theme persistence.
"""

from typing import List, Optional

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication, QWidget

from my_coding_agent.assets import get_theme_file


class ThemeManager:
    """Manages application themes including dark mode styling."""

    def __init__(self, app: QApplication):
        """Initialize the ThemeManager.

        Args:
            app: The QApplication instance to apply themes to
        """
        self.app = app
        self._available_themes = ["light", "dark"]

        # Load saved theme or default to light
        self._settings = QSettings("my_coding_agent", "Simple Code Viewer")
        saved_theme = self._settings.value("theme/current", "light")

        # Validate saved theme
        if saved_theme not in self._available_themes:
            saved_theme = "light"

        self._current_theme = saved_theme

        # Apply the initial theme
        self.set_theme(self._current_theme)

    def get_current_theme(self) -> str:
        """Get the currently active theme.

        Returns:
            Current theme name ('light' or 'dark')
        """
        return self._current_theme

    def get_available_themes(self) -> List[str]:
        """Get list of available themes.

        Returns:
            List of available theme names
        """
        return self._available_themes.copy()

    def set_theme(self, theme_name: str) -> bool:
        """Set the application theme.

        Args:
            theme_name: Name of the theme to apply ('light' or 'dark')

        Returns:
            True if theme was successfully applied, False otherwise
        """
        if theme_name not in self._available_themes:
            return False

        try:
            # Load and apply stylesheet
            stylesheet = self._load_stylesheet(theme_name)
            self.app.setStyleSheet(stylesheet)

            # Update current theme
            self._current_theme = theme_name

            # Save to settings
            self._settings.setValue("theme/current", theme_name)

            return True
        except Exception:
            # If theme loading fails, fall back to previous theme
            return False

    def toggle_theme(self) -> str:
        """Toggle between light and dark themes.

        Returns:
            The new theme name after toggling
        """
        new_theme = "dark" if self._current_theme == "light" else "light"
        self.set_theme(new_theme)
        return self._current_theme

    def apply_theme_to_widget(
        self, widget: QWidget, theme_name: Optional[str] = None
    ) -> bool:
        """Apply theme to a specific widget.

        Args:
            widget: Widget to apply theme to
            theme_name: Theme to apply, or None to use current theme

        Returns:
            True if theme was successfully applied, False otherwise
        """
        if theme_name is None:
            theme_name = self._current_theme

        if theme_name not in self._available_themes:
            return False

        try:
            stylesheet = self._load_stylesheet(theme_name)
            widget.setStyleSheet(stylesheet)
            return True
        except Exception:
            return False

    def _load_stylesheet(self, theme_name: str) -> str:
        """Load stylesheet for the given theme.

        Args:
            theme_name: Name of the theme to load

        Returns:
            Stylesheet content as string

        Raises:
            FileNotFoundError: If theme file doesn't exist
        """
        if theme_name == "light":
            # For light theme, we can use minimal styling or load light.qss
            try:
                theme_path = get_theme_file("light.qss")
                with open(theme_path, encoding="utf-8") as f:
                    return f.read()
            except (FileNotFoundError, OSError):
                # Fall back to empty stylesheet for light theme
                return ""

        elif theme_name == "dark":
            # Load dark theme stylesheet
            theme_path = get_theme_file("dark.qss")
            with open(theme_path, encoding="utf-8") as f:
                return f.read()

        else:
            raise ValueError(f"Unknown theme: {theme_name}")

    def refresh_theme(self) -> None:
        """Refresh the current theme by reloading and reapplying it."""
        current = self._current_theme
        self.set_theme(current)
