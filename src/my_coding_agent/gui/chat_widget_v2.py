"""Clean, simplified chat widget implementation."""

from typing import Any

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QKeyEvent,
    QPainter,
    QPaintEvent,
    QPen,
)
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .chat_message_model import (
    ChatMessage,
    ChatMessageModel,
    MessageRole,
    MessageStatus,
)


class EnhancedTextEdit(QTextEdit):
    """Text edit widget with enhanced Enter key handling for chat input."""

    enter_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, e: QKeyEvent | None) -> None:
        """Handle key press events, especially Enter key."""
        if e is None:
            return

        if e.key() == Qt.Key.Key_Return or e.key() == Qt.Key.Key_Enter:
            # Check modifiers
            if e.modifiers() == Qt.KeyboardModifier.NoModifier:
                # Plain Enter: send message
                text = self.toPlainText().strip()
                if text:  # Only send if there's actual content
                    self.enter_pressed.emit()
                    return  # Don't process the key event further
            elif e.modifiers() == Qt.KeyboardModifier.ControlModifier:
                # Ctrl+Enter: also send message
                text = self.toPlainText().strip()
                if text:
                    self.enter_pressed.emit()
                    return
            # Shift+Enter or other modifiers: let default behavior handle (newline)

        # For all other keys or Shift+Enter, use default behavior
        super().keyPressEvent(e)


class SimplifiedMessageBubble(QWidget):
    """Clean, simple message bubble with proper sizing."""

    def __init__(self, message: ChatMessage, parent=None):
        super().__init__(parent)
        self.message = message
        self.role = message.role
        self._current_theme = "dark"
        self.setup_ui()
        self.apply_styling()

    def setup_ui(self) -> None:
        """Set up the UI with minimal nesting."""
        # Single layout, no nested containers
        layout = QVBoxLayout(self)
        # PADDING FIX: Restore proper padding inside bubbles for text spacing
        self._base_padding = (
            12,
            8,
            12,
            8,
        )  # Store base padding for responsive adjustments
        layout.setContentsMargins(*self._base_padding)
        layout.setSpacing(4)

        # Content display - use QLabel for better sizing behavior
        self.content_display = QLabel()
        self.content_display.setText(self.message.content)
        self.content_display.setWordWrap(True)  # Enable word wrapping
        self.content_display.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )  # Allow text selection like QTextEdit
        self.content_display.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        # Make the label size to content properly
        self.content_display.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )

        # FULL WIDTH: All messages should span the full width of the window
        # Set size policy to allow full width expansion with content-based height
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # Remove width constraints to allow full window width for all message types
        self.setMaximumWidth(16777215)  # No width limit
        self.setMinimumWidth(0)  # Allow natural minimum width

        layout.addWidget(self.content_display)

        # Error display (hidden by default)
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

    def apply_styling(self) -> None:
        """Apply role-based styling."""
        if self._current_theme == "dark":
            if self.role == MessageRole.USER:
                bg_color = "#444444"
                text_color = "#ffffff"
                border_color = "#555555"
            elif self.role == MessageRole.ASSISTANT:
                bg_color = "#2d2d2d"
                text_color = "#ffffff"
                border_color = "#444444"
            else:  # SYSTEM
                bg_color = "#1a1a1a"
                text_color = "#aaaaaa"
                border_color = "#333333"
        else:  # light theme
            if self.role == MessageRole.USER:
                bg_color = "#e3f2fd"
                text_color = "#000000"
                border_color = "#bbdefb"
            elif self.role == MessageRole.ASSISTANT:
                bg_color = "#f5f5f5"
                text_color = "#000000"
                border_color = "#e0e0e0"
            else:  # SYSTEM
                bg_color = "#fff3e0"
                text_color = "#666666"
                border_color = "#ffcc02"

        self.setStyleSheet(f"""
            SimplifiedMessageBubble {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                margin: 4px 0px;
            }}
        """)

        # Apply text color to the label
        self.content_display.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background-color: transparent;
                border: none;
                padding: 0px;
            }}
        """)

    def apply_theme(self, theme: str) -> None:
        """Apply theme to the message bubble."""
        self._current_theme = theme
        self.apply_styling()

    def update_content(self, content: str) -> None:
        """Update the message content."""
        self.content_display.setText(content)

    def set_error(self, error_message: str) -> None:
        """Display error message in the bubble."""
        self.content_display.setText(f"Error: {error_message}")
        self.setStyleSheet(f"""
            SimplifiedMessageBubble {{
                background-color: {"#4a1a1a" if self._current_theme == "dark" else "#ffebee"};
                border: 1px solid {"#ff4444" if self._current_theme == "dark" else "#e57373"};
                border-radius: 8px;
                margin: 4px 0px;
            }}
        """)

    def clear_error(self) -> None:
        """Clear error message."""
        self.error_label.hide()

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Custom paint event to ensure backgrounds and borders are visible."""
        if a0 is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get widget rectangle
        rect = self.rect()

        if self.role == MessageRole.USER:
            # User messages: light grey border and slightly lighter background
            bg_color = QColor("#3a3a3a" if self._current_theme == "dark" else "#f0f0f0")
            border_color = QColor(
                "#666666" if self._current_theme == "dark" else "#cccccc"
            )

            # Draw background with smaller rounded corners
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 2))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)

        elif self.role == MessageRole.SYSTEM:
            # System messages: gray background and border
            bg_color = QColor("#404040" if self._current_theme == "dark" else "#fff3cd")
            border_color = QColor(
                "#666666" if self._current_theme == "dark" else "#ffeaa7"
            )

            # Draw background with rounded corners
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 1))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)

        # For ASSISTANT messages, we don't draw any background (transparent)

        # Call parent paint event to handle text and other elements
        super().paintEvent(a0)

    def resizeEvent(self, a0) -> None:
        """Handle resize events for responsive padding adjustments."""
        super().resizeEvent(a0)

        # RESPONSIVE DESIGN: Adjust padding based on available width
        if hasattr(self, "_base_padding"):
            width = self.width()

            # Reduce padding on narrow screens
            if width < 400:
                # Smaller padding for narrow screens
                padding_factor = 0.5
            elif width < 600:
                # Medium padding for medium screens
                padding_factor = 0.75
            else:
                # Full padding for wide screens
                padding_factor = 1.0

            # Apply adaptive padding
            base_left, base_top, base_right, base_bottom = self._base_padding
            adaptive_padding = (
                int(base_left * padding_factor),
                int(base_top * padding_factor),
                int(base_right * padding_factor),
                int(base_bottom * padding_factor),
            )

            layout = self.layout()
            if layout:
                layout.setContentsMargins(*adaptive_padding)


class SimplifiedMessageDisplayArea(QScrollArea):
    """Clean message display area with proper layout."""

    def __init__(self, message_model: ChatMessageModel, parent=None):
        super().__init__(parent)
        self.message_model = message_model
        self._message_bubbles: dict[str, SimplifiedMessageBubble] = {}
        self._current_theme = "dark"
        self._typing_indicator: QLabel | None = None
        self._base_margin = 16
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        """Set up the display area."""
        # Configure scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create container widget
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)

        # RESPONSIVE DESIGN: Adaptive margins based on available space
        self.container_layout.setContentsMargins(
            self._base_margin, self._base_margin, self._base_margin, self._base_margin
        )
        self.container_layout.setSpacing(12)  # Add proper spacing between messages

        # HEIGHT FIX: Add spacer at the bottom to absorb extra vertical space
        # This prevents message bubbles from expanding to fill available height
        self.bottom_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.container_layout.addItem(self.bottom_spacer)

        self.setWidget(self.container)

        # Apply theme styling
        self.apply_theme(self._current_theme)

    def connect_signals(self) -> None:
        """Connect to message model signals."""
        self.message_model.message_added.connect(self.add_message)
        self.message_model.message_updated.connect(self.update_message)
        self.message_model.message_removed.connect(self.remove_message)
        self.message_model.modelReset.connect(self.clear_all_messages)

    def add_message(self, message: ChatMessage) -> None:
        """Add a new message bubble."""
        bubble = SimplifiedMessageBubble(message)
        bubble.apply_theme(self._current_theme)

        self._message_bubbles[message.message_id] = bubble

        # FULL WIDTH: Add bubble directly to layout without container wrapper
        # This ensures messages span full width and size properly to content
        # HEIGHT FIX: Insert before the bottom spacer to maintain proper spacing
        spacer_index = self.container_layout.indexOf(self.bottom_spacer)
        self.container_layout.insertWidget(spacer_index, bubble)

        # Auto-scroll to bottom
        QTimer.singleShot(10, self.scroll_to_bottom)

    def update_message(self, message: ChatMessage) -> None:
        """Update an existing message."""
        if message.message_id in self._message_bubbles:
            bubble = self._message_bubbles[message.message_id]
            bubble.update_content(message.content)

            if message.has_error():
                bubble.set_error(message.error_message or "Unknown error")
            else:
                bubble.clear_error()

    def remove_message(self, message_id: str) -> None:
        """Remove a message bubble."""
        if message_id in self._message_bubbles:
            bubble = self._message_bubbles[message_id]
            self.container_layout.removeWidget(bubble)
            bubble.deleteLater()
            del self._message_bubbles[message_id]

    def clear_all_messages(self) -> None:
        """Clear all messages."""
        for bubble in self._message_bubbles.values():
            self.container_layout.removeWidget(bubble)
            bubble.deleteLater()
        self._message_bubbles.clear()

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom."""
        scrollbar = self.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def show_typing_indicator(self, text: str = "AI is typing...") -> None:
        """Show typing indicator."""
        if self._typing_indicator is None:
            self._typing_indicator = QLabel(text)
            self._typing_indicator.setObjectName("typing_indicator")
            self._typing_indicator.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self._typing_indicator.setWordWrap(True)
            self._typing_indicator.setStyleSheet(f"""
                QLabel {{
                    color: {"#aaaaaa" if self._current_theme == "dark" else "#666666"};
                    font-style: italic;
                    padding: 8px;
                    background-color: transparent;
                    border: none;
                }}
            """)
            # HEIGHT FIX: Insert typing indicator before the bottom spacer
            # This maintains proper layout with spacer at the bottom
            spacer_index = self.container_layout.indexOf(self.bottom_spacer)
            self.container_layout.insertWidget(spacer_index, self._typing_indicator)

        self._typing_indicator.setText(text)
        self._typing_indicator.show()

        # Auto scroll after adding indicator
        QTimer.singleShot(10, self.scroll_to_bottom)

    def hide_typing_indicator(self) -> None:
        """Hide typing indicator."""
        if self._typing_indicator:
            self._typing_indicator.hide()
            # Remove from layout to avoid layout issues
            self.container_layout.removeWidget(self._typing_indicator)
            self._typing_indicator.deleteLater()
            self._typing_indicator = None

    def is_typing_indicator_visible(self) -> bool:
        """Check if typing indicator is visible."""
        return self._typing_indicator is not None and self._typing_indicator.isVisible()

    def apply_theme(self, theme: str) -> None:
        """Apply theme to the display area."""
        self._current_theme = theme

        if theme == "dark":
            self.setStyleSheet("""
                QScrollArea {
                    background-color: #2b2b2b;
                    border: none;
                }
                QWidget {
                    background-color: #2b2b2b;
                }
            """)
        else:
            self.setStyleSheet("""
                QScrollArea {
                    background-color: #ffffff;
                    border: none;
                }
                QWidget {
                    background-color: #ffffff;
                }
            """)

        # Update all existing bubbles
        for bubble in self._message_bubbles.values():
            bubble.apply_theme(self._current_theme)

    def _on_app_theme_changed(self, theme: str) -> None:
        """Handle theme change."""
        self.apply_theme(theme)

    def deleteLater(self) -> None:
        """Clean up theme manager connection when widget is deleted."""
        if self._auto_adapt_theme and self.theme_manager:
            self.theme_manager.unregister_widget(self)
        super().deleteLater()

    def resizeEvent(self, a0) -> None:
        """Handle resize events for responsive layout adjustments."""
        super().resizeEvent(a0)

        # RESPONSIVE DESIGN: Adjust margins based on container width
        if hasattr(self, "container_layout"):
            container_width = self.width()

            # Reduce margins on narrow screens
            if container_width < 500:
                adaptive_margin = max(8, self._base_margin // 2)
            else:
                adaptive_margin = self._base_margin

            self.container_layout.setContentsMargins(
                adaptive_margin, adaptive_margin, adaptive_margin, adaptive_margin
            )


class SimplifiedChatWidget(QWidget):
    """Clean, simplified chat widget."""

    message_sent = pyqtSignal(str)
    stream_interrupted = pyqtSignal(str)

    def __init__(self, parent=None, auto_adapt_theme: bool = False, theme_manager=None):
        """Initialize the simplified chat widget.

        Args:
            parent: Parent widget
            auto_adapt_theme: Whether to automatically adapt to application theme changes
            theme_manager: ThemeManager instance for automatic theme updates
        """
        super().__init__(parent)
        self._current_theme = "dark"
        self._auto_adapt_theme = auto_adapt_theme
        self.theme_manager = theme_manager

        # Initialize message model
        self.message_model = ChatMessageModel()

        # Streaming state
        self._is_streaming = False
        self._current_stream_id: str | None = None
        self._streaming_message_id: str | None = None
        self._retry_count = 0

        # Visual indicator components
        self._streaming_indicator: QLabel | None = None
        self._interrupt_button: QPushButton | None = None
        self._streaming_container: QWidget | None = None
        self._animation_timer: QTimer | None = None
        self._animation_dots = 0

        # Initialize UI and connections
        self.setup_ui()

        # Apply theme if auto-adaptation is enabled
        if self._auto_adapt_theme and self.theme_manager:
            self.theme_manager.theme_changed.connect(self._on_app_theme_changed)
            current_theme = self.theme_manager.get_current_theme()
            self.apply_theme(current_theme)

    def setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # RESPONSIVE DESIGN: Set minimum size for usability
        self.setMinimumSize(320, 240)  # Minimum usable size

        # Message display area - give it stretch to fill available space
        self.display_area = SimplifiedMessageDisplayArea(self.message_model)
        layout.addWidget(self.display_area, 1)  # stretch factor 1 to fill space

        # Input area - fixed size at bottom
        self.setup_input_area(layout)

    def setup_input_area(self, main_layout: QVBoxLayout) -> None:
        """Set up the input area with full-width text box and embedded send icon."""
        # Create container for input area
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)

        # RESPONSIVE DESIGN: Adaptive margins based on window size
        base_margin = 8
        input_layout.setContentsMargins(
            base_margin, base_margin, base_margin, base_margin
        )
        input_layout.setSpacing(0)

        # Create text input - full width
        self.input_text = EnhancedTextEdit()
        self.input_text.setPlaceholderText(
            "Type your message... (Enter to send, Shift+Enter for new line)"
        )

        # RESPONSIVE DESIGN: Adaptive input height based on available space
        self.input_text.setMinimumHeight(32)  # Reduced minimum for small screens
        self.input_text.setMaximumHeight(100)  # Reduced maximum to save space

        # Connect enter key to send message
        self.input_text.enter_pressed.connect(self.send_message)

        # Create send icon button positioned inside the text box
        self.send_icon = QPushButton("→")
        self.send_icon.setFixedSize(
            28, 20
        )  # Slightly smaller for better responsiveness
        self.send_icon.clicked.connect(self.send_message)
        self.send_icon.setParent(self.input_text)

        # Position the send icon in the bottom right of the text input
        # Use a timer to periodically update position
        self._position_timer = QTimer()
        self._position_timer.timeout.connect(self._update_send_icon_position)
        self._position_timer.start(100)  # Update every 100ms

        input_layout.addWidget(self.input_text)

        # RESPONSIVE DESIGN: Set size policy for input container
        input_container.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )

        main_layout.addWidget(input_container)

        # Apply initial theme
        self.apply_input_theme(self._current_theme)

    def _update_send_icon_position(self) -> None:
        """Update send icon position to stay in bottom right of input text."""
        if hasattr(self, "send_icon") and hasattr(self, "input_text"):
            # RESPONSIVE DESIGN: Adaptive positioning based on input size
            padding = 6  # Consistent padding from edges
            new_x = max(0, self.input_text.width() - self.send_icon.width() - padding)
            new_y = max(0, self.input_text.height() - self.send_icon.height() - padding)
            self.send_icon.move(new_x, new_y)

    def apply_input_theme(self, theme: str) -> None:
        """Apply theme to input area."""
        if theme == "dark":
            self.input_text.setStyleSheet("""
                QTextEdit {
                    background-color: #3a3a3a;
                    border: 1px solid #555555;
                    border-radius: 6px;
                    color: white;
                    padding: 8px;
                    font-size: 14px;
                }
            """)
            self.send_icon.setStyleSheet("""
                QPushButton {
                    background-color: #4285F4;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5A9BFF;
                }
                QPushButton:pressed {
                    background-color: #2D5AA0;
                }
            """)
        else:
            self.input_text.setStyleSheet("""
                QTextEdit {
                    background-color: white;
                    border: 1px solid #cccccc;
                    border-radius: 6px;
                    color: #333;
                    padding: 8px;
                    font-size: 14px;
                }
            """)
            self.send_icon.setStyleSheet("""
                QPushButton {
                    background-color: #4285F4;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5A9BFF;
                }
                QPushButton:pressed {
                    background-color: #2D5AA0;
                }
            """)

    def send_message(self) -> None:
        """Send the current message."""
        text = self.input_text.toPlainText().strip()
        if text:
            # Add user message first and wait for it to be fully processed
            self.add_user_message(text)

            # Use a short delay to ensure message is rendered before emitting signal
            QTimer.singleShot(50, lambda: self.message_sent.emit(text))

            # Clear input immediately
            self.input_text.clear()

    def add_user_message(
        self, content: str, metadata: "dict[str, Any] | None" = None
    ) -> str:
        """Add a user message."""
        message = ChatMessage.create_user_message(content, metadata)
        self.message_model.add_message(message)
        return message.message_id

    def add_assistant_message(
        self, content: str, metadata: "dict[str, Any] | None" = None
    ) -> str:
        """Add an assistant message."""
        message = ChatMessage.create_assistant_message(content, metadata)
        self.message_model.add_message(message)
        return message.message_id

    def add_system_message(
        self, content: str, metadata: "dict[str, Any] | None" = None
    ) -> str:
        """Add a system message."""
        message = ChatMessage.create_system_message(content, metadata)
        self.message_model.add_message(message)
        return message.message_id

    def clear_conversation(self) -> None:
        """Clear the conversation."""
        self.message_model.clear_all_messages()

    def apply_theme(self, theme: str) -> None:
        """Apply theme to the entire widget."""
        self.display_area.apply_theme(theme)
        self.apply_input_theme(theme)

        # Apply theme to streaming indicators if they exist
        if self._streaming_container:
            self._apply_streaming_indicator_theme()

    def update_message_content(self, message_id: str, content: str) -> None:
        """Update message content (for streaming)."""
        message = self.message_model.get_message_by_id(message_id)
        if message:
            message.content = content
            self.display_area.update_message(message)

    # Streaming methods required by the main application

    def is_streaming(self) -> bool:
        """Check if currently streaming a response."""
        return getattr(self, "_is_streaming", False)

    def start_streaming_response(self, stream_id: str, retry_count: int = 0) -> str:
        """Start a new streaming response."""
        if self._is_streaming:
            raise RuntimeError("Stream already active")

        # Create assistant message
        assistant_msg_id = self.add_assistant_message("", {"stream_id": stream_id})

        # Update streaming state
        self._is_streaming = True
        self._current_stream_id = stream_id
        self._streaming_message_id = assistant_msg_id
        self._retry_count = retry_count

        # Show streaming indicators
        self._show_streaming_indicators()

        # Show typing indicator
        self.display_area.show_typing_indicator("AI is responding...")

        return assistant_msg_id

    def complete_streaming_response(self) -> None:
        """Complete the current streaming response."""
        if not self._is_streaming:
            return

        # Update message status to delivered
        if self._streaming_message_id:
            message = self.message_model.get_message_by_id(self._streaming_message_id)
            if message:
                self.message_model.update_message_status(
                    self._streaming_message_id, MessageStatus.DELIVERED
                )

        # Clear streaming state
        self._is_streaming = False
        self._current_stream_id = None
        self._streaming_message_id = None
        self._retry_count = 0

        # Hide streaming indicators
        self._hide_streaming_indicators()

        # Hide typing indicator
        self.display_area.hide_typing_indicator()

    def handle_streaming_error(self, error: Exception) -> None:
        """Handle streaming error."""
        if not self._is_streaming:
            return

        # Update message with error
        if self._streaming_message_id:
            message = self.message_model.get_message_by_id(self._streaming_message_id)
            if message:
                self.message_model.update_message_status(
                    self._streaming_message_id, MessageStatus.ERROR
                )
                # Note: ChatMessageModel doesn't have error_message field, so we'll handle this differently

        # Clear streaming state
        self._is_streaming = False
        self._current_stream_id = None
        self._streaming_message_id = None
        self._retry_count = 0

        # Hide streaming indicators
        self._hide_streaming_indicators()

        # Hide typing indicator
        self.display_area.hide_typing_indicator()

    def _show_streaming_indicators(self) -> None:
        """Show streaming visual indicators."""
        if self._streaming_container is None:
            self._create_streaming_indicators()

        # Update indicator text based on retry count
        if self._retry_count > 0:
            indicator_text = f"AI is responding... (attempt {self._retry_count + 1})"
        else:
            indicator_text = "AI is responding..."

        if self._streaming_indicator:
            self._streaming_indicator.setText(indicator_text)

        # Ensure container is visible - use both methods for reliability
        if self._streaming_container:
            self._streaming_container.show()
            self._streaming_container.setVisible(True)

        # Start subtle animation
        self._start_streaming_animation()

    def _hide_streaming_indicators(self) -> None:
        """Hide streaming visual indicators."""
        if self._streaming_container:
            self._streaming_container.hide()

        # Stop animation
        self._stop_streaming_animation()

    def _create_streaming_indicators(self) -> None:
        """Create streaming indicator UI components."""
        # Create container for streaming indicators
        self._streaming_container = QWidget()
        self._streaming_container.setObjectName("streaming_container")

        # Create horizontal layout for indicators
        layout = QHBoxLayout(self._streaming_container)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Create streaming indicator label
        self._streaming_indicator = QLabel("AI is responding...")
        self._streaming_indicator.setObjectName("streaming_indicator")
        self._streaming_indicator.setAccessibleName(
            "AI is currently responding to your message"
        )

        # Create interrupt button
        self._interrupt_button = QPushButton("Stop")
        self._interrupt_button.setObjectName("interrupt_button")
        self._interrupt_button.setAccessibleName("Stop AI response")
        self._interrupt_button.clicked.connect(self._on_interrupt_clicked)
        self._interrupt_button.setMaximumWidth(60)
        self._interrupt_button.setMaximumHeight(24)

        # Add to layout
        layout.addWidget(self._streaming_indicator)
        layout.addStretch()  # Push button to the right
        layout.addWidget(self._interrupt_button)

        # Apply theme styling
        self._apply_streaming_indicator_theme()

        # Add to main layout (insert before input area)
        main_layout = self.layout()

        if main_layout and isinstance(main_layout, QVBoxLayout):
            # Insert before the last widget (input area)
            main_layout.insertWidget(main_layout.count() - 1, self._streaming_container)

        # Start hidden - will be shown when needed
        self._streaming_container.hide()

    def _apply_streaming_indicator_theme(self) -> None:
        """Apply theme styling to streaming indicators."""
        if not self._streaming_container:
            return

        if self._current_theme == "dark":
            bg_color = "#2a2a2a"
            text_color = "#cccccc"
            border_color = "#444444"
            button_bg = "#3a3a3a"
            button_hover = "#4a4a4a"
        else:  # light theme
            bg_color = "#f8f8f8"
            text_color = "#666666"
            border_color = "#e0e0e0"
            button_bg = "#ffffff"
            button_hover = "#f0f0f0"

        # Style the container
        if self._streaming_container:
            self._streaming_container.setStyleSheet(f"""
                QWidget#streaming_container {{
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    margin: 2px 0px;
                }}
            """)

        # Style the indicator label
        if self._streaming_indicator:
            self._streaming_indicator.setStyleSheet(f"""
                QLabel#streaming_indicator {{
                    color: {text_color};
                    background-color: transparent;
                    border: none;
                    font-size: 12px;
                    padding: 2px 4px;
                }}
            """)

        # Style the interrupt button
        if self._interrupt_button:
            self._interrupt_button.setStyleSheet(f"""
                QPushButton#interrupt_button {{
                    background-color: {button_bg};
                    border: 1px solid {border_color};
                    border-radius: 3px;
                    color: {text_color};
                    font-size: 11px;
                    padding: 2px 8px;
                }}
                QPushButton#interrupt_button:hover {{
                    background-color: {button_hover};
                }}
                QPushButton#interrupt_button:pressed {{
                    background-color: {border_color};
                }}
            """)

    def _start_streaming_animation(self) -> None:
        """Start subtle animation for streaming indicator."""
        if self._animation_timer is None:
            self._animation_timer = QTimer()
            self._animation_timer.timeout.connect(self._update_animation)

        self._animation_dots = 0
        self._animation_timer.start(500)  # Update every 500ms

    def _stop_streaming_animation(self) -> None:
        """Stop streaming animation."""
        if self._animation_timer:
            self._animation_timer.stop()

    def _update_animation(self) -> None:
        """Update animation dots."""
        if not self._streaming_indicator:
            return

        # Cycle through 0, 1, 2, 3 dots
        self._animation_dots = (self._animation_dots + 1) % 4
        dots = "." * self._animation_dots

        # Update text with animated dots
        base_text = "AI is responding"
        if self._retry_count > 0:
            base_text = f"AI is responding (attempt {self._retry_count + 1})"

        self._streaming_indicator.setText(f"{base_text}{dots}")

    def _on_interrupt_clicked(self) -> None:
        """Handle interrupt button click."""
        if self._is_streaming and self._current_stream_id:
            # Emit interrupt signal
            self.stream_interrupted.emit(self._current_stream_id)

            # Update streaming message to show interruption
            if self._streaming_message_id:
                message = self.message_model.get_message_by_id(
                    self._streaming_message_id
                )
                if message:
                    self.message_model.update_message_status(
                        self._streaming_message_id, MessageStatus.ERROR
                    )

            # Clear streaming state
            self._is_streaming = False
            self._current_stream_id = None
            self._streaming_message_id = None
            self._retry_count = 0

            # Hide indicators
            self._hide_streaming_indicators()
            self.display_area.hide_typing_indicator()

    # Public API methods for testing and external access

    def is_streaming_indicator_visible(self) -> bool:
        """Check if streaming indicator is visible."""
        return (
            self._streaming_container is not None
            and self._streaming_container.isVisible()
        )

    def is_interrupt_button_visible(self) -> bool:
        """Check if interrupt button is visible."""
        return self._interrupt_button is not None and self._interrupt_button.isVisible()

    def get_streaming_indicator_text(self) -> str:
        """Get current streaming indicator text."""
        if self._streaming_indicator:
            return self._streaming_indicator.text()
        return ""

    def get_streaming_indicator_widget(self) -> QWidget | None:
        """Get the streaming indicator widget for testing."""
        return self._streaming_container

    def trigger_interrupt_button(self) -> None:
        """Programmatically trigger interrupt button (for testing)."""
        if self._interrupt_button and self._interrupt_button.isVisible():
            self._interrupt_button.click()

    def is_streaming_animation_active(self) -> bool:
        """Check if streaming animation is currently active."""
        return self._animation_timer is not None and self._animation_timer.isActive()

    def _on_app_theme_changed(self, theme: str) -> None:
        """Handle theme change."""
        self.apply_theme(theme)

    def deleteLater(self) -> None:
        """Clean up theme manager connection when widget is deleted."""
        if self._auto_adapt_theme and self.theme_manager:
            self.theme_manager.unregister_widget(self)
        super().deleteLater()

    def resizeEvent(self, a0) -> None:
        """Handle resize events for responsive behavior."""
        super().resizeEvent(a0)

        # RESPONSIVE DESIGN: Adjust layout based on window size
        if hasattr(self, "display_area") and hasattr(self, "input_text"):
            window_width = self.width()
            window_height = self.height()

            # Adjust input area margins for very small screens
            if window_width < 400:
                # Reduce margins on small screens
                container = self.input_text.parent()
                if container and hasattr(container, "layout"):
                    layout = container.layout()
                    if layout:
                        layout.setContentsMargins(4, 4, 4, 4)

            # Adjust maximum input height based on available space
            available_height = window_height
            max_input_height = min(100, max(32, available_height // 6))
            self.input_text.setMaximumHeight(max_input_height)

            # Update send icon position immediately
            self._update_send_icon_position()

    def append_streaming_chunk(self, chunk: str) -> None:
        """Append a chunk of content to the streaming message."""
        if not self.is_streaming() or not self._streaming_message_id:
            return

        # Update the message content
        self.update_message_content(self._streaming_message_id, chunk)

        # Auto-scroll to show new content
        self.scroll_to_bottom()

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom."""
        self.display_area.scroll_to_bottom()

    def show_ai_thinking(self, animated: bool = False) -> None:
        """Show AI thinking indicator."""
        self.display_area.show_typing_indicator("AI is thinking...")

    def hide_typing_indicator(self) -> None:
        """Hide typing indicator."""
        self.display_area.hide_typing_indicator()
