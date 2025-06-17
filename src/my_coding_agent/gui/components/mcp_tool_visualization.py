"""
MCP tool call visualization component.

This component provides a visual display for MCP tool calls with expandable details
showing parameters, results, execution time, and status indicators.
"""

import json
import re
from typing import Any

# Import pygments components for syntax highlighting
from pygments.lexers import (  # type: ignore
    JavascriptLexer,
    JsonLexer,
    PythonLexer,
    TextLexer,
    get_lexer_by_name,
)
from pygments.token import Token  # type: ignore
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...core.code_viewer import PygmentsSyntaxHighlighter
from ...core.theme_manager import ThemeManager


class MCPToolCallWidget(QWidget):
    """
    A widget that displays MCP tool calls with expandable details.

    Shows tool name, status, parameters, and results in a collapsible format.
    Supports theme-aware styling and accessibility features.
    """

    # Signals for tool call interactions
    tool_call_expanded = pyqtSignal(str)  # Emitted when tool call is expanded
    tool_call_collapsed = pyqtSignal(str)  # Emitted when tool call is collapsed

    def __init__(
        self,
        tool_call: dict[str, Any],
        theme_manager: ThemeManager | None = None,
        auto_adapt_theme: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the MCPToolCallWidget.

        Args:
            tool_call: Dictionary containing tool call information
            theme_manager: ThemeManager instance for automatic theme updates
            auto_adapt_theme: Whether to automatically adapt to theme changes
            parent: Parent widget
        """
        super().__init__(parent)

        self.tool_call = tool_call.copy()  # Store a copy to avoid mutations
        self.result: dict[str, Any] | None = None
        self.theme_manager = theme_manager
        self._auto_adapt_theme = auto_adapt_theme
        self.is_collapsed = True

        # Syntax highlighting components
        self.result_syntax_highlighter: PygmentsSyntaxHighlighter | None = None
        self._syntax_highlighting_enabled = True

        # UI components that will be created
        self.header_frame: QFrame
        self.expand_button: QPushButton
        self.tool_name_label: QLabel
        self.status_label: QLabel
        self.content_widget: QWidget
        self.parameters_text: QTextEdit
        self.result_text: QTextEdit

        self._setup_ui()
        self._apply_initial_theme()
        self._setup_accessibility()

        # Connect to theme changes if auto-adapt is enabled
        if auto_adapt_theme and theme_manager:
            theme_manager.theme_changed.connect(self._on_theme_changed)
            theme_manager.register_widget(self)

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(4)

        # Header frame (always visible)
        self.header_frame = QFrame()
        self.header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(8)

        # Expand/collapse button
        self.expand_button = QPushButton("▶")
        self.expand_button.setFixedSize(20, 20)
        self.expand_button.setFlat(True)
        self.expand_button.clicked.connect(self.toggle_expand_collapse)
        header_layout.addWidget(self.expand_button)

        # Tool name label
        self.tool_name_label = QLabel(
            f"🔧 {self.tool_call.get('name', 'Unknown Tool')}"
        )
        self.tool_name_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        header_layout.addWidget(self.tool_name_label)

        # Add stretch to push status to the right
        header_layout.addStretch()

        # Status label
        self.status_label = QLabel(
            self._format_status(self.tool_call.get("status", "unknown"))
        )
        self.status_label.setFont(QFont("Consolas", 9))
        header_layout.addWidget(self.status_label)

        main_layout.addWidget(self.header_frame)

        # Content widget (collapsible)
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 8, 8, 8)
        content_layout.setSpacing(8)

        # Parameters section
        params_label = QLabel("Parameters:")
        params_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        content_layout.addWidget(params_label)

        self.parameters_text = QTextEdit()
        self.parameters_text.setReadOnly(True)
        self.parameters_text.setMaximumHeight(120)
        self.parameters_text.setFont(QFont("Consolas", 8))
        self.parameters_text.setPlainText(self._format_parameters())
        content_layout.addWidget(self.parameters_text)

        # Result section
        result_label = QLabel("Result:")
        result_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        content_layout.addWidget(result_label)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(120)
        self.result_text.setFont(QFont("Consolas", 8))
        self.result_text.setPlainText("(No result yet)")
        content_layout.addWidget(self.result_text)

        main_layout.addWidget(self.content_widget)

        # Start collapsed
        self.content_widget.hide()

        # Set object name for styling
        self.setObjectName("MCPToolCallWidget")

    def _format_status(self, status: str) -> str:
        """Format status with appropriate emoji and text."""
        status_map = {
            "pending": "⏳ Pending",
            "success": "✅ Success",
            "error": "❌ Error",
            "timeout": "⏰ Timeout",
            "cancelled": "🚫 Cancelled",
        }
        return status_map.get(status.lower(), f"❓ {status.title()}")

    def _format_parameters(self) -> str:
        """Format tool call parameters for display."""
        params = self.tool_call.get("parameters", {})
        if not params:
            return "(No parameters)"

        try:
            return json.dumps(params, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(params)

    def _format_result(self, result: dict[str, Any]) -> str:
        """Format tool execution result for display."""
        if not result:
            return "(No result yet)"

        lines = []

        # Add execution time if available
        exec_time = result.get("execution_time")
        if exec_time:
            if exec_time < 1:
                lines.append(f"⏱️ Execution time: {exec_time * 1000:.1f}ms")
            else:
                lines.append(f"⏱️ Execution time: {exec_time:.2f}s")

        # Check for success status - handle both direct status and nested result
        success = False
        if (
            result.get("status") == "success"
            or result.get("success")
            or result.get("result", {}).get("success")
        ):
            success = True

        lines.append(f"✅ Success: {success}")

        # Add content or error - check both direct and nested locations
        error = result.get("error")
        if not error and "result" in result:
            error = result["result"].get("error")

        content = result.get("content")
        if not content and "result" in result:
            content = result["result"].get("content")

        if error:
            lines.append(f"\n❌ Error:\n{error}")
        elif content:
            if isinstance(content, str) and len(content) > 500:
                content = content[:500] + "... (truncated)"
            lines.append(f"\n📄 Content:\n{content}")

        return "\n".join(lines)

    def _detect_content_language(
        self, content: str, content_type: str | None = None
    ) -> str:
        """
        Detect the programming language of the content for syntax highlighting.

        Args:
            content: The content to analyze
            content_type: Explicit content type hint

        Returns:
            Language identifier for Pygments lexer
        """
        if not content or not isinstance(content, str):
            return "text"

        # Use explicit content type if provided
        if content_type:
            content_type = content_type.lower()
            if content_type in ["python", "py"]:
                return "python"
            elif content_type in ["javascript", "js", "typescript", "ts"]:
                return "javascript"
            elif content_type in ["json"]:
                return "json"
            elif content_type in ["html"]:
                return "html"
            elif content_type in ["css"]:
                return "css"
            elif content_type in ["yaml", "yml"]:
                return "yaml"
            elif content_type in ["xml"]:
                return "xml"
            elif content_type in ["bash", "shell", "sh"]:
                return "bash"
            elif content_type in ["sql"]:
                return "sql"

        # Auto-detect from content patterns
        content_lower = content.lower().strip()

        # Python detection
        python_patterns = [
            r"\bdef\s+\w+\s*\(",
            r"\bclass\s+\w+\s*[:\(]",
            r"\bimport\s+\w+",
            r"\bfrom\s+\w+\s+import",
            r"print\s*\(",
            r"__\w+__",
            r"self\.",
        ]

        if any(
            re.search(pattern, content, re.IGNORECASE) for pattern in python_patterns
        ):
            return "python"

        # JavaScript detection
        js_patterns = [
            r"\bfunction\s+\w+\s*\(",
            r"\bconst\s+\w+\s*=",
            r"\blet\s+\w+\s*=",
            r"\bvar\s+\w+\s*=",
            r"console\.log\s*\(",
            r"=>",
            r"\bclass\s+\w+\s*{",
        ]

        if any(re.search(pattern, content, re.IGNORECASE) for pattern in js_patterns):
            return "javascript"

        # JSON detection
        json_patterns = [
            r"^\s*[\{\[]",
            r":\s*[\"\'\d\[\{]",
            r"[\"\']:\s*[\"\']",
        ]

        if any(re.search(pattern, content_lower) for pattern in json_patterns):
            try:
                json.loads(content)
                return "json"
            except (json.JSONDecodeError, ValueError):
                pass

        # HTML detection
        if re.search(r"<\s*\w+[^>]*>", content, re.IGNORECASE):
            return "html"

        # CSS detection
        if re.search(r"\w+\s*\{[^}]*\}", content):
            return "css"

        # Fallback to plain text
        return "text"

    def _get_lexer_for_language(self, language: str) -> object | None:
        """Get appropriate Pygments lexer for the detected language."""
        try:
            if language == "python":
                return PythonLexer()
            elif language == "javascript":
                return JavascriptLexer()
            elif language == "json":
                return JsonLexer()
            elif language in ["html", "css", "yaml", "xml", "bash", "sql"]:
                return get_lexer_by_name(language)
            else:
                return TextLexer()
        except Exception:
            # Fallback to text lexer if anything goes wrong
            return TextLexer()

    def _setup_result_syntax_highlighting(
        self, content: str, content_type: str | None = None
    ) -> None:
        """
        Set up syntax highlighting for the result text.

        Args:
            content: The content to highlight
            content_type: Optional explicit content type
        """
        if not self._syntax_highlighting_enabled:
            return

        try:
            # Detect language and get appropriate lexer
            language = self._detect_content_language(content, content_type)
            lexer = self._get_lexer_for_language(language)

            # Create or update syntax highlighter
            if self.result_syntax_highlighter is None:
                document = self.result_text.document()
                if document is not None:
                    self.result_syntax_highlighter = PygmentsSyntaxHighlighter(
                        document, lexer
                    )
            else:
                self.result_syntax_highlighter.set_lexer(lexer)

            # Apply theme-aware colors
            self._apply_syntax_highlighting_theme()

        except Exception:
            # If syntax highlighting fails, continue without it
            self.result_syntax_highlighter = None

    def _apply_syntax_highlighting_theme(self) -> None:
        """Apply theme-appropriate colors to syntax highlighting."""
        if not self.result_syntax_highlighter:
            return

        try:
            # Get current theme
            current_theme = "dark"
            if self.theme_manager:
                current_theme = self.theme_manager.get_current_theme()

            # Update token styles based on theme
            if current_theme == "light":
                # Light theme colors
                self.result_syntax_highlighter.token_styles = {
                    Token.Keyword: self.palette().color(self.palette().ColorRole.Link),
                    Token.String: self.palette()
                    .color(self.palette().ColorRole.Text)
                    .darker(120),
                    Token.Comment: self.palette()
                    .color(self.palette().ColorRole.Text)
                    .lighter(150),
                    Token.Number: self.palette()
                    .color(self.palette().ColorRole.Link)
                    .darker(150),
                    Token.Operator: self.palette().color(self.palette().ColorRole.Text),
                    Token.Name.Function: self.palette()
                    .color(self.palette().ColorRole.Text)
                    .darker(130),
                    Token.Name.Class: self.palette()
                    .color(self.palette().ColorRole.Link)
                    .lighter(120),
                    Token.Name.Builtin: self.palette().color(
                        self.palette().ColorRole.Link
                    ),
                    Token.Literal: self.palette()
                    .color(self.palette().ColorRole.Text)
                    .darker(120),
                }
            else:
                # Dark theme colors (default from PygmentsSyntaxHighlighter)
                pass  # Use default dark theme colors

        except Exception:
            # If theme application fails, continue with defaults
            pass

    def set_syntax_highlighting_enabled(self, enabled: bool) -> None:
        """
        Enable or disable syntax highlighting for result content.

        Args:
            enabled: Whether to enable syntax highlighting
        """
        self._syntax_highlighting_enabled = enabled

        if self.result_syntax_highlighter:
            self.result_syntax_highlighter.set_enabled(enabled)

    def toggle_expand_collapse(self) -> None:
        """Toggle the expanded/collapsed state of the widget."""
        self.is_collapsed = not self.is_collapsed

        if self.is_collapsed:
            self.content_widget.hide()
            self.content_widget.setVisible(False)
            self.expand_button.setText("▶")
            self.tool_call_collapsed.emit(self.tool_call.get("id", ""))
        else:
            self.content_widget.show()
            self.content_widget.setVisible(True)
            self.expand_button.setText("▼")
            self.tool_call_expanded.emit(self.tool_call.get("id", ""))

    def update_result(self, result: dict[str, Any]) -> None:
        """
        Update the widget with tool execution result.

        Args:
            result: Dictionary containing execution result
        """
        self.result = result.copy()

        # Merge result data into tool_call
        self.tool_call.update(result)

        # Update status based on result - check both direct status and nested result
        if (
            result.get("status") == "success"
            or result.get("success")
            or result.get("result", {}).get("success")
        ):
            self.tool_call["status"] = "success"
        else:
            self.tool_call["status"] = "error"

        # Update status label
        self.status_label.setText(self._format_status(self.tool_call["status"]))

        # Update result text - handle nested result content
        formatted_result = self._format_result(result)
        self.result_text.setPlainText(formatted_result)

        # Set up syntax highlighting for the content if available
        # Check both direct content and nested result content
        content = result.get("content")
        if not content and "result" in result:
            content = result["result"].get("content")

        if content and isinstance(content, str):
            content_type = result.get("content_type")
            if not content_type and "result" in result:
                content_type = result["result"].get("content_type")
            self._setup_result_syntax_highlighting(content, content_type)

        # Apply status-specific styling
        self._apply_status_styling()

    def _apply_initial_theme(self) -> None:
        """Apply initial theme based on theme manager."""
        if self.theme_manager:
            current_theme = self.theme_manager.get_current_theme()
            self._apply_theme_for(current_theme)
        else:
            self._apply_theme_for("dark")  # Default to dark theme

    def _on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change signal from theme manager."""
        if self._auto_adapt_theme:
            self._apply_theme_for(theme_name)

    def _apply_theme_for(self, theme_name: str) -> None:
        """Apply theme-specific styling."""
        if theme_name == "dark":
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

        # Apply status-specific styling on top of theme
        self._apply_status_styling()

        # Update syntax highlighting theme
        self._apply_syntax_highlighting_theme()

    def _apply_dark_theme(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            MCPToolCallWidget {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 6px;
                margin: 2px 0px;
            }

            QFrame {
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 4px;
            }

            QLabel {
                color: #ffffff;
                background-color: transparent;
                border: none;
            }

            QPushButton {
                background-color: #555555;
                color: #ffffff;
                border: 1px solid #777777;
                border-radius: 3px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #666666;
            }

            QTextEdit {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
            }
        """)

    def _apply_light_theme(self) -> None:
        """Apply light theme styling."""
        self.setStyleSheet("""
            MCPToolCallWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin: 2px 0px;
            }

            QFrame {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 4px;
            }

            QLabel {
                color: #333333;
                background-color: transparent;
                border: none;
            }

            QPushButton {
                background-color: #e9ecef;
                color: #333333;
                border: 1px solid #ced4da;
                border-radius: 3px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #dee2e6;
            }

            QTextEdit {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #ced4da;
                border-radius: 3px;
                padding: 4px;
            }
        """)

    def _apply_status_styling(self) -> None:
        """Apply status-specific styling to the status label."""
        status = self.tool_call.get("status", "unknown").lower()

        status_styles = {
            "pending": "color: #ffc107; font-weight: bold;",
            "success": "color: #28a745; font-weight: bold;",
            "error": "color: #dc3545; font-weight: bold;",
            "timeout": "color: #fd7e14; font-weight: bold;",
            "cancelled": "color: #6c757d; font-weight: bold;",
        }

        style = status_styles.get(status, "color: #6c757d; font-weight: bold;")
        self.status_label.setStyleSheet(style)

    def _setup_accessibility(self) -> None:
        """Set up accessibility features."""
        tool_name = self.tool_call.get("name", "Unknown Tool")
        status = self.tool_call.get("status", "unknown")

        self.setAccessibleName(f"MCP tool call: {tool_name}")
        self.setAccessibleDescription(
            f"Tool call for {tool_name} with status {status}. "
            "Click expand button to view details."
        )

        self.expand_button.setAccessibleName("Expand tool call details")
        self.expand_button.setAccessibleDescription(
            "Click to show or hide tool call parameters and results"
        )

        self.parameters_text.setAccessibleName("Tool call parameters")
        self.result_text.setAccessibleName("Tool call results")

    def apply_theme(self) -> None:
        """Apply current theme - public method for external calls."""
        if self.theme_manager:
            current_theme = self.theme_manager.get_current_theme()
            self._apply_theme_for(current_theme)
        else:
            self._apply_theme_for("dark")

    def deleteLater(self) -> None:
        """Clean up theme manager connection when widget is deleted."""
        if self._auto_adapt_theme and self.theme_manager:
            self.theme_manager.unregister_widget(self)
        super().deleteLater()
