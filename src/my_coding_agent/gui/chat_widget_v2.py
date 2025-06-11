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
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .chat_message_model import (
    ChatMessage,
    ChatMessageModel,
    MessageRole,
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Content display - use QTextEdit for better sizing behavior
        self.content_display = QTextEdit()
        self.content_display.setPlainText(self.message.content)
        self.content_display.setReadOnly(True)
        self.content_display.setFrameStyle(QFrame.Shape.NoFrame)
        self.content_display.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.content_display.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Make the text edit size to content
        self.content_display.setMaximumHeight(16777215)  # Remove height constraints
        self.content_display.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        # Adjust height to content - connect signal safely
        doc = self.content_display.document()
        if doc and hasattr(doc, "documentLayout"):
            doc_layout = doc.documentLayout()
            if doc_layout and hasattr(doc_layout, "documentSizeChanged"):
                doc_layout.documentSizeChanged.connect(self.adjust_text_height)

        layout.addWidget(self.content_display)

        # Error display (hidden by default)
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

    def adjust_text_height(self) -> None:
        """Adjust text edit height to fit content."""
        doc = self.content_display.document()
        if doc:
            # Get the document height
            doc_height = int(doc.size().height())

            # Add padding based on role - user messages have 12px padding on QTextEdit
            padding = 24 if self.role == MessageRole.USER else 10

            # Set the height with padding included
            total_height = doc_height + padding
            self.content_display.setFixedHeight(total_height)

    def apply_styling(self) -> None:
        """Apply role-based styling."""
        if self.role == MessageRole.USER:
            # User messages: light grey border, slightly lighter background
            self.setStyleSheet(f"""
                SimplifiedMessageBubble {{
                    background-color: {"#3a3a3a" if self._current_theme == "dark" else "#f0f0f0"};
                    border: 2px solid {"#666666" if self._current_theme == "dark" else "#cccccc"};
                    border-radius: 6px;
                    margin: 8px 0px;
                    padding: 0px;
                }}
                QTextEdit {{
                    background-color: transparent;
                    border: none;
                    color: {"#ffffff" if self._current_theme == "dark" else "#333"};
                    font-size: 14px;
                    padding: 12px;
                }}
            """)
            # Force widget to have solid background
            self.setAutoFillBackground(True)

        elif self.role == MessageRole.ASSISTANT:
            # AI messages: full width, transparent
            self.setStyleSheet(f"""
                SimplifiedMessageBubble {{
                    background-color: transparent;
                    border: none;
                    margin: 8px 0px;
                    padding: 0px;
                }}
                QTextEdit {{
                    background-color: transparent;
                    border: none;
                    color: {"#ffffff" if self._current_theme == "dark" else "#333"};
                    font-size: 14px;
                }}
            """)
            # Ensure no background for AI messages
            self.setAutoFillBackground(False)

        else:  # SYSTEM
            # System messages: distinct styling
            self.setStyleSheet(f"""
                SimplifiedMessageBubble {{
                    background-color: {"#404040" if self._current_theme == "dark" else "#fff3cd"};
                    border: 1px solid {"#666666" if self._current_theme == "dark" else "#ffeaa7"};
                    border-radius: 8px;
                    margin: 8px 0px;
                    padding: 10px;
                    max-width: 600px;
                }}
                QTextEdit {{
                    background-color: transparent;
                    border: none;
                    color: {"#ffffff" if self._current_theme == "dark" else "#856404"};
                    font-size: 13px;
                    font-style: italic;
                }}
            """)
            # Force widget to have background for system messages
            self.setAutoFillBackground(True)

    def apply_theme(self, theme: str) -> None:
        """Apply theme to the bubble."""
        self._current_theme = theme
        self.apply_styling()

    def update_content(self, content: str) -> None:
        """Update the message content."""
        self.message.content = content
        self.content_display.setPlainText(content)

    def set_error(self, error_message: str) -> None:
        """Display error message."""
        self.error_label.setText(f"Error: {error_message}")
        self.error_label.setStyleSheet(
            "color: #ff6b6b; font-weight: bold; margin-top: 4px;"
        )
        self.error_label.show()

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


class SimplifiedMessageDisplayArea(QScrollArea):
    """Clean message display area with proper layout."""

    def __init__(self, message_model: ChatMessageModel, parent=None):
        super().__init__(parent)
        self.message_model = message_model
        self._message_bubbles: dict[str, SimplifiedMessageBubble] = {}
        self._current_theme = "dark"
        self._typing_indicator: QLabel | None = None
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
        self.container_layout.setContentsMargins(16, 16, 16, 16)
        self.container_layout.setSpacing(4)

        # Add stretch to push messages to top
        self.container_layout.addStretch()

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

        # Insert before the stretch
        self.container_layout.insertWidget(self.container_layout.count() - 1, bubble)

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
            self._typing_indicator = QLabel()
            self._typing_indicator.setWordWrap(True)
            self._typing_indicator.setStyleSheet(f"""
                QLabel {{
                    color: {"#aaaaaa" if self._current_theme == "dark" else "#666666"};
                    font-style: italic;
                    padding: 8px;
                    margin: 4px 0px;
                }}
            """)
            # Insert before the stretch
            self.container_layout.insertWidget(
                self.container_layout.count() - 1, self._typing_indicator
            )

        self._typing_indicator.setText(text)
        self._typing_indicator.show()
        QTimer.singleShot(10, self.scroll_to_bottom)

    def hide_typing_indicator(self) -> None:
        """Hide typing indicator."""
        if self._typing_indicator:
            self._typing_indicator.hide()

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
            bubble.apply_theme(theme)

    def show_typing_indicator(self, text: str = "AI is typing...") -> None:
        """Show typing indicator."""
        if self._typing_indicator is None:
            self._typing_indicator = QLabel()
            self._typing_indicator.setWordWrap(True)
            self._typing_indicator.setStyleSheet(f"""
                QLabel {{
                    color: {"#aaaaaa" if self._current_theme == "dark" else "#666666"};
                    font-style: italic;
                    padding: 8px;
                    margin: 4px 0px;
                }}
            """)
            # Insert before the stretch
            self.container_layout.insertWidget(
                self.container_layout.count() - 1, self._typing_indicator
            )

        self._typing_indicator.setText(text)
        self._typing_indicator.show()
        QTimer.singleShot(10, self.scroll_to_bottom)

    def hide_typing_indicator(self) -> None:
        """Hide typing indicator."""
        if self._typing_indicator:
            self._typing_indicator.hide()

    def is_typing_indicator_visible(self) -> bool:
        """Check if typing indicator is visible."""
        return self._typing_indicator is not None and self._typing_indicator.isVisible()

        # Update typing indicator style
        if self._typing_indicator:
            self._typing_indicator.setStyleSheet(f"""
                QLabel {{
                    color: {"#aaaaaa" if theme == "dark" else "#666666"};
                    font-style: italic;
                    padding: 8px;
                    margin: 4px 0px;
                }}
            """)


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

        self._auto_adapt_theme = auto_adapt_theme
        self.theme_manager = theme_manager

        # Connect to theme changes if auto adaptation is enabled
        if auto_adapt_theme and theme_manager:
            theme_manager.theme_changed.connect(self._on_app_theme_changed)
            theme_manager.register_widget(self)
            # Apply current theme immediately
            current_theme = theme_manager.get_current_theme()
            self._current_theme = current_theme
        else:
            self._current_theme = "dark"  # Default theme

        self.message_model = ChatMessageModel()
        self._is_streaming = False
        self._current_stream_id = None
        self._streaming_message_id = None
        self._streaming_content_buffer = ""
        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Message display area
        self.display_area = SimplifiedMessageDisplayArea(self.message_model)
        layout.addWidget(self.display_area)

        # Input area
        self.setup_input_area(layout)

    def setup_input_area(self, main_layout: QVBoxLayout) -> None:
        """Set up the input area with full-width text box and embedded send icon."""
        # Create container for input area
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(0)

        # Create text input - full width
        self.input_text = EnhancedTextEdit()
        self.input_text.setPlaceholderText("Type your message... (Enter to send, Shift+Enter for new line)")
        self.input_text.setMinimumHeight(40)
        self.input_text.setMaximumHeight(120)

        # Connect enter key to send message
        self.input_text.enter_pressed.connect(self.send_message)

        # Create send icon button positioned inside the text box
        self.send_icon = QPushButton("→")
        self.send_icon.setFixedSize(32, 24)
        self.send_icon.clicked.connect(self.send_message)
        self.send_icon.setParent(self.input_text)

        # Position the send icon in the bottom right of the text input
        # Use a timer to periodically update position
        self._position_timer = QTimer()
        self._position_timer.timeout.connect(self._update_send_icon_position)
        self._position_timer.start(100)  # Update every 100ms

        input_layout.addWidget(self.input_text)
        main_layout.addWidget(input_container)

        # Apply initial theme
        self.apply_input_theme("dark")

    def _update_send_icon_position(self) -> None:
        """Update send icon position to stay in bottom right of input text."""
        if hasattr(self, 'send_icon') and hasattr(self, 'input_text'):
            new_x = self.input_text.width() - 40
            new_y = self.input_text.height() - 32
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
            self.message_sent.emit(text)
            self.add_user_message(text)
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
        if self.is_streaming():
            raise RuntimeError(
                "Stream already active. Stop current stream before starting new one."
            )

        # Create new assistant message for streaming
        assistant_msg_id = self.add_assistant_message(
            "", metadata={"stream_id": stream_id}
        )

        # Update streaming state
        self._is_streaming = True
        self._current_stream_id = stream_id
        self._streaming_message_id = assistant_msg_id
        self._streaming_content_buffer = ""

        # Show typing indicator
        indicator_text = "AI is responding..."
        if retry_count > 0:
            indicator_text = f"AI is responding... (attempt {retry_count + 1})"
        self.show_ai_thinking()

        return assistant_msg_id

    def append_streaming_chunk(self, chunk: str) -> None:
        """Append a chunk of content to the streaming message."""
        if not self.is_streaming() or not getattr(self, "_streaming_message_id", None):
            return

        # Update content buffer (AI sends cumulative chunks)
        self._streaming_content_buffer = chunk

        # Update the message content
        self.update_message_content(
            self._streaming_message_id, self._streaming_content_buffer
        )

        # Auto-scroll to show new content
        self.scroll_to_bottom()

    def complete_streaming_response(self) -> None:
        """Complete the current streaming response."""
        if not self.is_streaming():
            return

        # Clear streaming state
        self._is_streaming = False
        self._current_stream_id = None
        self._streaming_message_id = None
        self._streaming_content_buffer = ""

        # Hide typing indicator
        self.hide_typing_indicator()

    def handle_streaming_error(self, error: Exception) -> None:
        """Handle an error during streaming."""
        if not self.is_streaming() or not getattr(self, "_streaming_message_id", None):
            return

        # Set error on the message
        message = self.message_model.get_message_by_id(self._streaming_message_id)
        if message:
            message.error_message = str(error)
            bubble = self.display_area._message_bubbles.get(self._streaming_message_id)
            if bubble:
                bubble.set_error(str(error))

        # Clear streaming state
        self._is_streaming = False
        self._current_stream_id = None
        self._streaming_message_id = None
        self._streaming_content_buffer = ""

        # Hide typing indicator
        self.hide_typing_indicator()

    def show_ai_thinking(self, animated: bool = False) -> None:
        """Show AI thinking indicator."""
        self.display_area.show_typing_indicator("AI is thinking...")

    def hide_typing_indicator(self) -> None:
        """Hide typing indicator."""
        self.display_area.hide_typing_indicator()

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom."""
        self.display_area.scroll_to_bottom()

    def is_streaming(self) -> bool:
        """Check if currently streaming a response."""
        return self._is_streaming

    def start_streaming_response(self, stream_id: str, retry_count: int = 0) -> str:
        """Start a new streaming response."""
        if self.is_streaming():
            raise RuntimeError(
                "Stream already active. Stop current stream before starting new one."
            )

        # Create new assistant message for streaming
        assistant_msg_id = self.add_assistant_message(
            "", metadata={"stream_id": stream_id}
        )

        # Update streaming state
        self._is_streaming = True
        self._current_stream_id = stream_id
        self._streaming_message_id = assistant_msg_id
        self._streaming_content_buffer = ""

        # Show typing indicator
        indicator_text = "AI is responding..."
        if retry_count > 0:
            indicator_text = f"AI is responding... (attempt {retry_count + 1})"
        self.show_ai_thinking()

        return assistant_msg_id

    def append_streaming_chunk(self, chunk: str) -> None:
        """Append a chunk of content to the streaming message."""
        if not self.is_streaming() or not self._streaming_message_id:
            return

        # Update content buffer (AI sends cumulative chunks)
        self._streaming_content_buffer = chunk

        # Update the message content
        self.update_message_content(
            self._streaming_message_id, self._streaming_content_buffer
        )

        # Auto-scroll to show new content
        self.scroll_to_bottom()

    def complete_streaming_response(self) -> None:
        """Complete the current streaming response."""
        if not self.is_streaming():
            return

        # Clear streaming state
        self._is_streaming = False
        self._current_stream_id = None
        self._streaming_message_id = None
        self._streaming_content_buffer = ""

        # Hide typing indicator
        self.hide_typing_indicator()

    def handle_streaming_error(self, error: Exception) -> None:
        """Handle an error during streaming."""
        if not self.is_streaming() or not self._streaming_message_id:
            return

        # Set error on the message
        message = self.message_model.get_message_by_id(self._streaming_message_id)
        if message:
            message.error_message = str(error)
            bubble = self.display_area._message_bubbles.get(self._streaming_message_id)
            if bubble:
                bubble.set_error(str(error))

        # Clear streaming state
        self._is_streaming = False
        self._current_stream_id = None
        self._streaming_message_id = None
        self._streaming_content_buffer = ""

        # Hide typing indicator
        self.hide_typing_indicator()

    def show_ai_thinking(self, animated: bool = False) -> None:
        """Show AI thinking indicator."""
        self.display_area.show_typing_indicator("AI is thinking...")

    def hide_typing_indicator(self) -> None:
        """Hide typing indicator."""
        self.display_area.hide_typing_indicator()

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom."""
        self.display_area.scroll_to_bottom()

    def _on_app_theme_changed(self, theme: str) -> None:
        """Handle theme change."""
        self.apply_theme(theme)

    def deleteLater(self) -> None:
        """Clean up theme manager connection when widget is deleted."""
        if self._auto_adapt_theme and self.theme_manager:
            self.theme_manager.unregister_widget(self)
        super().deleteLater()
