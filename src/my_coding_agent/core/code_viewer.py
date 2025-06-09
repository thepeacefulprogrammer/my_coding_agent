"""
Code viewer widget for displaying source code with syntax highlighting.
"""

from pathlib import Path
from typing import List, Optional

# Import pygments with type ignores for stub warnings
from pygments.lexers import (  # type: ignore
    JavascriptLexer,
    PythonLexer,
    TextLexer,
    get_lexer_for_filename,
)
from pygments.token import Token  # type: ignore
from PyQt6.QtCore import QRect, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)
from PyQt6.QtWidgets import QHBoxLayout, QTextEdit, QWidget


class PygmentsSyntaxHighlighter(QSyntaxHighlighter):
    """Qt syntax highlighter using Pygments for token parsing."""

    def __init__(self, document: QTextDocument, lexer=None):
        super().__init__(document)
        self.lexer = lexer if lexer else TextLexer()
        self._enabled = True

        # Define color scheme for different token types
        self.token_styles = {
            Token.Keyword: QColor(86, 156, 214),  # Blue
            Token.String: QColor(206, 145, 120),  # Orange
            Token.Comment: QColor(106, 153, 85),  # Green
            Token.Number: QColor(181, 206, 168),  # Light green
            Token.Operator: QColor(212, 212, 212),  # Light gray
            Token.Name.Function: QColor(220, 220, 170),  # Yellow
            Token.Name.Class: QColor(78, 201, 176),  # Cyan
            Token.Name.Builtin: QColor(86, 156, 214),  # Blue
            Token.Literal: QColor(206, 145, 120),  # Orange
        }

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable syntax highlighting."""
        self._enabled = enabled
        self.rehighlight()

    def is_enabled(self) -> bool:
        """Check if syntax highlighting is enabled."""
        return self._enabled

    def set_lexer(self, lexer) -> None:
        """Set the Pygments lexer for syntax highlighting."""
        self.lexer = lexer
        if self._enabled:
            self.rehighlight()

    def highlightBlock(self, text: str | None) -> None:
        """Highlight a block of text using Pygments."""
        if not self._enabled or not text or not text.strip():
            return

        try:
            # Get tokens from Pygments
            tokens = list(self.lexer.get_tokens(text))

            current_pos = 0
            for token_type, token_text in tokens:
                token_length = len(token_text)

                # Find matching style for token type or its parent types
                format = QTextCharFormat()
                color = self._get_color_for_token(token_type)
                if color:
                    format.setForeground(color)

                # Apply formatting
                self.setFormat(current_pos, token_length, format)
                current_pos += token_length

        except Exception:
            # If highlighting fails, just skip it
            pass

    def _get_color_for_token(self, token_type) -> Optional[QColor]:
        """Get color for a specific token type, checking parent types."""
        # Check exact match first
        if token_type in self.token_styles:
            return self.token_styles[token_type]

        # Check parent token types
        for style_token, color in self.token_styles.items():
            if token_type in style_token:
                return color

        return None


class LineNumbersWidget(QWidget):
    """Widget that displays line numbers for a text editor."""

    def __init__(self, text_editor: QTextEdit):
        super().__init__()
        self.text_editor = text_editor
        self._line_count = 1
        self._current_line = 1
        self._enabled = True

        # Set up the widget
        self.setFixedWidth(self._calculate_width())
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Set font to match text editor
        self.setFont(text_editor.font())

        # Connect to text editor signals for updates
        self.text_editor.textChanged.connect(self._update_line_count)
        self.text_editor.cursorPositionChanged.connect(self._update_current_line)

        # Connect scroll bar if available
        scroll_bar = self.text_editor.verticalScrollBar()
        if scroll_bar:
            scroll_bar.valueChanged.connect(self._sync_scroll)

        # Set background color - light theme to match the application
        self.setStyleSheet("""
            LineNumbersWidget {
                background-color: #f8f8f8;
                color: #666666;
                border-right: 1px solid #d0d0d0;
            }
        """)

        # Ensure widget is visible by default
        self.setVisible(True)
        self.show()

    def _calculate_width(self) -> int:
        """Calculate the width needed for line numbers based on line count."""
        # Calculate digits needed
        digits = len(str(max(1, self._line_count)))

        # Calculate width based on font metrics
        font_metrics = self.fontMetrics()
        digit_width = font_metrics.horizontalAdvance("9")  # Use widest digit
        padding = 10  # Left and right padding

        return (digits * digit_width) + padding

    def _update_line_count(self) -> None:
        """Update line count based on text editor content."""
        # Count lines by splitting content
        content = self.text_editor.toPlainText()
        new_count = max(1, content.count("\n") + 1)

        if new_count != self._line_count:
            self._line_count = new_count
            self.setFixedWidth(self._calculate_width())
            self.update()

    def _update_current_line(self) -> None:
        """Update current line number based on cursor position."""
        cursor = self.text_editor.textCursor()
        # Calculate line number from cursor position
        content = self.text_editor.toPlainText()
        cursor_pos = cursor.position()
        new_line = content[:cursor_pos].count("\n") + 1

        if new_line != self._current_line:
            self._current_line = new_line
            self.update()

    def _sync_scroll(self) -> None:
        """Sync scroll position with text editor."""
        self.update()

    def get_line_count(self) -> int:
        """Get the current line count."""
        return self._line_count

    def get_current_line(self) -> int:
        """Get the current line number (1-based)."""
        return self._current_line

    def get_scroll_position(self) -> int:
        """Get the current scroll position (synced with text editor)."""
        scroll_bar = self.text_editor.verticalScrollBar()
        return scroll_bar.value() if scroll_bar else 0

    def get_displayed_numbers(self) -> List[str]:
        """Get list of currently displayed line numbers as strings."""
        return [str(i) for i in range(1, self._line_count + 1)]

    def setVisible(self, visible: bool) -> None:
        """Override setVisible to control line numbers visibility."""
        super().setVisible(visible)
        self._enabled = visible

    def paintEvent(self, a0) -> None:
        """Paint the line numbers."""
        if not self._enabled:
            return

        painter = QPainter(self)
        painter.setFont(self.font())

        # Calculate line height and visible area
        font_metrics = self.fontMetrics()
        line_height = font_metrics.height()

        # Get scroll information from text editor
        scroll_bar = self.text_editor.verticalScrollBar()
        if not scroll_bar:
            return

        # Calculate which lines are visible
        scroll_value = scroll_bar.value()
        viewport = self.text_editor.viewport()
        if not viewport:
            return
        viewport_height = viewport.height()

        # Estimate visible line range based on scroll position
        # This is approximate since QTextEdit has variable line heights
        lines_per_page = max(1, viewport_height // line_height)

        # Get actual visible content from text editor
        content = self.text_editor.toPlainText()
        total_lines = content.count("\n") + 1 if content else 1

        # Calculate approximate first visible line based on scroll percentage
        if scroll_bar.maximum() > 0:
            scroll_percentage = scroll_value / scroll_bar.maximum()
            estimated_first_line = int(
                scroll_percentage * max(1, total_lines - lines_per_page)
            )
        else:
            estimated_first_line = 0

        # Ensure we don't go beyond available lines
        first_visible_line = max(1, estimated_first_line + 1)
        last_visible_line = min(
            total_lines, first_visible_line + lines_per_page + 2
        )  # +2 for buffer

        # Draw line numbers for visible range
        y = 5  # Start with small margin

        for line_number in range(first_visible_line, last_visible_line + 1):
            if line_number > total_lines:
                break

            # Highlight current line
            if line_number == self._current_line:
                painter.setPen(QPen(QColor(0, 0, 0)))  # Black for current line
            else:
                painter.setPen(QPen(QColor(102, 102, 102)))  # Gray for other lines

            # Draw the line number
            rect = QRect(0, y, self.width() - 5, line_height)
            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(line_number),
            )

            y += line_height

            # Don't draw beyond widget height
            if y > self.height():
                break


class CodeViewerWidget(QWidget):
    """
    A widget for viewing source code with syntax highlighting and line numbers.
    Provides read-only text display with Pygments-based syntax highlighting.
    """

    # Signal emitted when a file is loaded
    file_loaded = pyqtSignal(str)  # file_path

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create the text editor
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)

        # Set monospace font
        font = QFont("Courier New", 10)
        font.setFixedPitch(True)
        self._text_edit.setFont(font)

        # Configure text behavior
        self._text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._text_edit.setTabStopDistance(
            4 * self._text_edit.fontMetrics().horizontalAdvance(" ")
        )

        # Track current file and language
        self._current_file: Optional[Path] = None
        self._current_language = "text"

        # Initialize syntax highlighter
        document = self._text_edit.document()
        if document is not None:
            self._syntax_highlighter = PygmentsSyntaxHighlighter(document)
        else:
            # Create a new document if none exists
            document = QTextDocument()
            self._text_edit.setDocument(document)
            self._syntax_highlighter = PygmentsSyntaxHighlighter(document)

        # Create line numbers widget
        self._line_numbers = LineNumbersWidget(self._text_edit)
        self._line_numbers_enabled = True

        # Ensure line numbers widget has the correct font
        self._line_numbers.setFont(font)

        # Add widgets to layout
        layout.addWidget(self._line_numbers)
        layout.addWidget(self._text_edit)

    # Delegate text editor methods
    def setPlainText(self, text: str) -> None:
        """Set plain text content."""
        self._text_edit.setPlainText(text)

    def clear(self) -> None:
        """Clear content."""
        self._text_edit.clear()

    def textCursor(self):
        """Get text cursor."""
        return self._text_edit.textCursor()

    def setTextCursor(self, cursor) -> None:
        """Set text cursor."""
        self._text_edit.setTextCursor(cursor)

    def verticalScrollBar(self):
        """Get vertical scroll bar."""
        return self._text_edit.verticalScrollBar()

    def selectAll(self) -> None:
        """Select all text."""
        self._text_edit.selectAll()

    def toPlainText(self) -> str:
        """Get plain text content."""
        return self._text_edit.toPlainText()

    def isReadOnly(self) -> bool:
        """Check if text editor is read-only."""
        return self._text_edit.isReadOnly()

    def load_file(self, file_path) -> bool:
        """
        Load a file into the code viewer.

        Args:
            file_path: Path to the file to load (str or Path object)

        Returns:
            bool: True if file was loaded successfully, False otherwise
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            return False

        if not file_path.is_file():
            return False

        try:
            # Try multiple encodings
            encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
            content = None

            for encoding in encodings:
                try:
                    content = file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                return False

            # Set the content
            self.setPlainText(content)

            # Update current file and detect language
            self._current_file = file_path
            self._detect_and_set_language(file_path)

            # Emit signal
            self.file_loaded.emit(str(file_path))

            return True

        except (OSError, PermissionError):
            return False

    def _detect_and_set_language(self, file_path: Path) -> None:
        """Detect programming language from file extension and set appropriate lexer."""
        extension = file_path.suffix.lower()

        # Use extension-based detection for reliable results
        if extension in [".py", ".pyw"]:
            self._current_language = "python"
            lexer = PythonLexer()
        elif extension in [".js", ".jsx", ".ts", ".tsx"]:
            self._current_language = "javascript"
            lexer = JavascriptLexer()
        else:
            # For other extensions, try Pygments detection first
            try:
                lexer = get_lexer_for_filename(str(file_path))
                language_name = lexer.name.lower()

                # Map Pygments lexer names to our standard names
                if "python" in language_name:
                    self._current_language = "python"
                elif "javascript" in language_name or "typescript" in language_name:
                    self._current_language = "javascript"
                else:
                    self._current_language = "text"
                    lexer = TextLexer()

            except Exception:
                # If Pygments detection fails, treat as plain text
                self._current_language = "text"
                lexer = TextLexer()

        # Set the lexer in the syntax highlighter
        self._syntax_highlighter.set_lexer(lexer)

    def get_current_file(self) -> Optional[Path]:
        """Get the currently loaded file path."""
        return self._current_file

    def get_current_language(self) -> str:
        """Get the detected programming language of the current file."""
        return self._current_language

    def syntax_highlighting_enabled(self) -> bool:
        """Check if syntax highlighting is currently enabled."""
        return self._syntax_highlighter.is_enabled()

    def set_syntax_highlighting(self, enabled: bool) -> None:
        """Enable or disable syntax highlighting."""
        self._syntax_highlighter.set_enabled(enabled)

    def line_numbers_enabled(self) -> bool:
        """Check if line numbers are currently enabled."""
        return self._line_numbers_enabled

    def set_line_numbers_enabled(self, enabled: bool) -> None:
        """Enable or disable line numbers."""
        self._line_numbers_enabled = enabled
        self._line_numbers.setVisible(enabled)

    def get_line_numbers_widget(self) -> LineNumbersWidget:
        """Get the line numbers widget."""
        return self._line_numbers

    def get_text_edit_font(self):
        """Get the text editor's font."""
        return self._text_edit.font()

    def clear_content(self) -> None:
        """Clear the editor content and reset state."""
        self.clear()
        self._current_file = None
        self._current_language = "text"
        self._syntax_highlighter.set_lexer(TextLexer())
