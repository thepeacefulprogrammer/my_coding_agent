"""Theme management for the Simple Code Viewer application.

This module provides the ThemeManager class for handling application themes,
including dark mode styling and theme persistence.
"""

from __future__ import annotations

import contextlib

from PyQt6.QtCore import QObject, QSettings, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget

from my_coding_agent.assets import get_theme_file


class ThemeManager(QObject):
    """Manages application themes including dark mode styling."""

    # Signal emitted when theme changes
    theme_changed = pyqtSignal(str)

    def __init__(self, app: QApplication):
        """Initialize the ThemeManager.

        Args:
            app: The QApplication instance to apply themes to
        """
        super().__init__()
        self.app = app
        self._available_themes = ["light", "dark"]
        self._connected_widgets: list[
            QWidget
        ] = []  # Track widgets for automatic theme updates

        # Load saved theme or default to dark
        self._settings = QSettings("my_coding_agent", "Simple Code Viewer")
        saved_theme = self._settings.value("theme/current", "dark")

        # Validate saved theme
        if saved_theme not in self._available_themes:
            saved_theme = "dark"

            # Initialize current theme
        self._current_theme = saved_theme

        # Apply the initial theme by forcing a stylesheet load
        self._apply_theme_stylesheet(saved_theme)

    def get_current_theme(self) -> str:
        """Get the currently active theme.

        Returns:
            Current theme name ('light' or 'dark')
        """
        return self._current_theme

    def get_available_themes(self) -> list[str]:
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

        # Check if we need to do anything (but still verify the theme is properly applied)
        if theme_name == self._current_theme:
            # Verify the stylesheet is actually applied
            if self.app and theme_name == "dark":
                current_stylesheet = self.app.styleSheet()
                if len(current_stylesheet) > 0:
                    return True
                # If stylesheet is empty but should be dark, re-apply
            elif theme_name == "light":
                return True

        return self._apply_theme_stylesheet(theme_name)

    def _apply_theme_stylesheet(self, theme_name: str) -> bool:
        """Apply the stylesheet for the given theme.

        Args:
            theme_name: Name of the theme to apply

        Returns:
            True if theme was successfully applied, False otherwise
        """
        try:
            # Load and apply stylesheet
            stylesheet = self._load_stylesheet(theme_name)

            # Apply stylesheet with error handling for CI environments
            if self.app:
                self.app.setStyleSheet(stylesheet)

            # Only update current theme after successful application
            self._current_theme = theme_name

            # Save to settings with error handling
            with contextlib.suppress(Exception):
                # Settings might fail in CI, but continue with theme change
                self._settings.setValue("theme/current", theme_name)

            # Emit signal for automatic theme adaptation with error handling
            with contextlib.suppress(Exception):
                # Signal emission might fail in CI, but theme is still changed
                self.theme_changed.emit(theme_name)

            return True
        except Exception:
            # If theme loading fails, keep the previous theme
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
        self, widget: QWidget, theme_name: str | None = None
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

    def register_widget(self, widget: QWidget) -> None:
        """Register a widget for automatic theme updates.

        Args:
            widget: Widget to register for theme updates
        """
        if widget not in self._connected_widgets:
            self._connected_widgets.append(widget)

    def unregister_widget(self, widget: QWidget) -> None:
        """Unregister a widget from automatic theme updates.

        Args:
            widget: Widget to unregister from theme updates
        """
        if widget in self._connected_widgets:
            self._connected_widgets.remove(widget)
