"""ThemeAwareWidget base class for automatic theme adaptation (Task 3.5)."""

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget

from ...core.theme_manager import ThemeManager


class ThemeAwareWidget(QWidget):
    """Base class for widgets that automatically adapt to application theme changes."""

    def __init__(
        self, theme_manager: ThemeManager | None = None, parent: QWidget | None = None
    ):
        """Initialize ThemeAwareWidget.

        Args:
            theme_manager: ThemeManager instance for automatic theme updates
            parent: Parent widget
        """
        super().__init__(parent)

        self.theme_manager = theme_manager

        if self.theme_manager:
            # Connect to theme change signals
            self.theme_manager.theme_changed.connect(self._on_theme_changed)
            # Register with theme manager
            self.theme_manager.register_widget(self)

    @pyqtSlot(str)
    def _on_theme_changed(self, theme_name: str):
        """Handle theme change signal.

        Args:
            theme_name: New theme name
        """
        try:
            self._apply_theme(theme_name)
        except Exception as e:
            # Gracefully handle theme adaptation errors
            print(f"Theme adaptation failed for {self.__class__.__name__}: {e}")

    def _apply_theme(self, theme_name: str):
        """Apply theme to the widget. Override in subclasses.

        Args:
            theme_name: Theme name to apply ('light' or 'dark')
        """
        # Default implementation - subclasses should override
        pass

    def deleteLater(self):
        """Clean up theme manager connection when widget is deleted."""
        if self.theme_manager:
            self.theme_manager.unregister_widget(self)
        super().deleteLater()
