"""MessageDisplay component for consistent AI and user message rendering (Task 3.4)."""

from enum import Enum

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ...core.theme_manager import ThemeManager
from ..chat_message_model import ChatMessage, MessageRole


class MessageDisplayTheme(Enum):
    """Theme options for MessageDisplay component."""

    LIGHT = "light"
    DARK = "dark"


class MessageDisplay(QWidget):
    """Reusable component for rendering chat messages with consistent styling."""

    content_changed = pyqtSignal(str)

    def __init__(
        self,
        message: ChatMessage,
        theme: MessageDisplayTheme = MessageDisplayTheme.DARK,
        auto_adapt_theme: bool = False,
        theme_manager: ThemeManager | None = None,
        parent: QWidget | None = None,
    ):
        """Initialize MessageDisplay component.

        Args:
            message: The chat message to display
            theme: Theme for styling (light or dark)
            auto_adapt_theme: Whether to automatically adapt to application theme changes
            theme_manager: ThemeManager instance for automatic theme updates
            parent: Parent widget
        """
        super().__init__(parent)

        self._message = message
        self._error_message = ""
        self._has_error = False
        self._auto_adapt_theme = auto_adapt_theme
        self.theme_manager = theme_manager
        self._custom_stylesheet = ""  # Track custom styling added by user

        # Set initial theme
        if auto_adapt_theme and theme_manager:
            # Use theme from theme manager
            theme_name = theme_manager.get_current_theme()
            self._theme = (
                MessageDisplayTheme.DARK
                if theme_name == "dark"
                else MessageDisplayTheme.LIGHT
            )
            # Connect to theme changes
            theme_manager.theme_changed.connect(self._on_app_theme_changed)
            theme_manager.register_widget(self)
        else:
            self._theme = theme

        self._setup_ui()
        self._apply_theme_colors()
        self._update_styling()

        # Set accessibility
        self.setAccessibleName(f"{message.role.value} message")
        self.setAccessibleDescription(
            f"Message from {message.role.value}: {message.content[:50]}..."
        )

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Main content area
        self._content_label = QLabel()
        self._content_label.setWordWrap(True)
        self._content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._content_label.setText(self._message.content)

        # Error display area (initially hidden)
        self._error_label = QLabel()
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(
            "color: #ff6b6b; font-style: italic; margin-top: 4px;"
        )
        self._error_label.hide()

        layout.addWidget(self._content_label)
        layout.addWidget(self._error_label)

    def _on_app_theme_changed(self, theme_name: str):
        """Handle application theme change signal.

        Args:
            theme_name: New theme name from ThemeManager
        """
        if self._auto_adapt_theme:
            new_theme = (
                MessageDisplayTheme.DARK
                if theme_name == "dark"
                else MessageDisplayTheme.LIGHT
            )
            if new_theme != self._theme:
                self._theme = new_theme
                self._apply_theme_colors()
                self._update_styling()

    def _apply_theme_colors(self):
        """Apply theme-specific colors and styling."""
        if self._theme == MessageDisplayTheme.DARK:
            self._theme_colors = {
                "user_bg": "#2a2a2a",
                "user_border": "#1E88E5",
                "user_text": "#ffffff",
                "assistant_bg": "transparent",
                "assistant_text": "#ffffff",
                "system_bg": "#404040",
                "system_text": "#ffffff",
                "error_color": "#ff6b6b",
            }
        else:  # LIGHT theme
            self._theme_colors = {
                "user_bg": "#f8f9fa",
                "user_border": "#4285F4",
                "user_text": "#333",
                "assistant_bg": "transparent",
                "assistant_text": "#333",
                "system_bg": "#666666",
                "system_text": "#ffffff",
                "error_color": "#d73527",
            }

    def _update_styling(self):
        """Update component styling based on message role and theme."""
        role = self._message.role

        if role == MessageRole.USER:
            style = f"""
                MessageDisplay {{
                    background-color: {self._theme_colors["user_bg"]};
                    border: 2px solid {self._theme_colors["user_border"]};
                    border-radius: 8px;
                    max-width: 500px;
                    margin: 4px;
                }}
                QLabel {{
                    color: {self._theme_colors["user_text"]};
                    background-color: transparent;
                    padding: 4px;
                }}
            """
        elif role == MessageRole.ASSISTANT:
            style = f"""
                MessageDisplay {{
                    background-color: {self._theme_colors["assistant_bg"]};
                    border: none;
                    margin: 4px 0px;
                }}
                QLabel {{
                    color: {self._theme_colors["assistant_text"]};
                    background-color: transparent;
                    padding: 4px;
                }}
            """
        else:  # SYSTEM
            style = f"""
                MessageDisplay {{
                    background-color: {self._theme_colors["system_bg"]};
                    border-radius: 4px;
                    margin: 4px;
                }}
                QLabel {{
                    color: {self._theme_colors["system_text"]};
                    background-color: transparent;
                    font-style: italic;
                    padding: 4px;
                }}
            """

        # Combine theme styling with any custom styling
        combined_style = style
        if self._custom_stylesheet:
            combined_style += "\n" + self._custom_stylesheet

        self.setStyleSheet(combined_style)

    def setStyleSheet(self, styleSheet: str | None):
        """Override setStyleSheet to track custom styling.

        Args:
            styleSheet: The stylesheet to apply
        """
        if styleSheet is None:
            styleSheet = ""

        # If this contains our theme styling, extract any additional custom styling
        current_theme_style = (
            self._get_current_theme_style() if hasattr(self, "_theme_colors") else ""
        )

        if current_theme_style and styleSheet.startswith(current_theme_style):
            # This is theme styling + custom styling
            self._custom_stylesheet = styleSheet[len(current_theme_style) :].strip()
        elif current_theme_style and current_theme_style in styleSheet:
            # Find where theme styling ends and custom styling begins
            theme_end = styleSheet.find(current_theme_style) + len(current_theme_style)
            self._custom_stylesheet = styleSheet[theme_end:].strip()
        elif not current_theme_style:
            # No theme styling yet, this might be custom styling
            self._custom_stylesheet = styleSheet
        else:
            # This is completely new styling, treat as custom
            self._custom_stylesheet = styleSheet

        super().setStyleSheet(styleSheet)

    def _get_current_theme_style(self) -> str:
        """Get the current theme-based styling without custom additions."""
        if not hasattr(self, "_theme_colors"):
            return ""

        role = self._message.role

        if role == MessageRole.USER:
            return f"""
                MessageDisplay {{
                    background-color: {self._theme_colors["user_bg"]};
                    border: 2px solid {self._theme_colors["user_border"]};
                    border-radius: 8px;
                    max-width: 500px;
                    margin: 4px;
                }}
                QLabel {{
                    color: {self._theme_colors["user_text"]};
                    background-color: transparent;
                    padding: 4px;
                }}
            """
        elif role == MessageRole.ASSISTANT:
            return f"""
                MessageDisplay {{
                    background-color: {self._theme_colors["assistant_bg"]};
                    border: none;
                    margin: 4px 0px;
                }}
                QLabel {{
                    color: {self._theme_colors["assistant_text"]};
                    background-color: transparent;
                    padding: 4px;
                }}
            """
        else:  # SYSTEM
            return f"""
                MessageDisplay {{
                    background-color: {self._theme_colors["system_bg"]};
                    border-radius: 4px;
                    margin: 4px;
                }}
                QLabel {{
                    color: {self._theme_colors["system_text"]};
                    background-color: transparent;
                    font-style: italic;
                    padding: 4px;
                }}
            """

    def set_theme(self, theme: MessageDisplayTheme):
        """Change the theme of the component.

        Args:
            theme: New theme to apply
        """
        self._theme = theme
        self._apply_theme_colors()
        self._update_styling()

    def update_content(self, content: str):
        """Update the message content.

        Args:
            content: New content to display
        """
        self._message.content = content
        self._content_label.setText(content)
        self.content_changed.emit(content)

    def get_content(self) -> str:
        """Get the current message content.

        Returns:
            Current message content
        """
        return self._message.content

    def set_message(self, message: ChatMessage):
        """Set a new message for display.

        Args:
            message: New message to display
        """
        self._message = message
        self._content_label.setText(message.content)
        self._update_styling()

        # Update accessibility
        self.setAccessibleName(f"{message.role.value} message")
        self.setAccessibleDescription(
            f"Message from {message.role.value}: {message.content[:50]}..."
        )

    def set_error(self, error_message: str):
        """Display an error message.

        Args:
            error_message: Error message to display
        """
        self._error_message = error_message
        self._has_error = True
        self._error_label.setText(f"Error: {error_message}")
        self._error_label.show()

    def clear_error(self):
        """Clear any displayed error message."""
        self._error_message = ""
        self._has_error = False
        self._error_label.hide()

    def has_error(self) -> bool:
        """Check if component is displaying an error.

        Returns:
            True if there is an error being displayed
        """
        return self._has_error

    def get_error_text(self) -> str:
        """Get the current error message text.

        Returns:
            Current error message, empty string if no error
        """
        return self._error_message

    def get_message(self) -> ChatMessage:
        """Get the current chat message.

        Returns:
            The chat message object
        """
        return self._message

    def apply_theme(self):
        """Apply theme to message display."""
        # Apply theme to message display
        self._apply_theme_colors()
        self._update_styling()

    def deleteLater(self) -> None:
        """Clean up theme manager connection when widget is deleted."""
        if self._auto_adapt_theme and self.theme_manager:
            self.theme_manager.unregister_widget(self)
        super().deleteLater()
