"""
Unit tests for MCP tool call visualization component.

Tests the MCPToolCallWidget component that displays tool calls with expandable details.
"""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QVBoxLayout,
)

from my_coding_agent.core.theme_manager import ThemeManager
from my_coding_agent.gui.components.mcp_tool_visualization import MCPToolCallWidget


class TestMCPToolCallWidget:
    """Test cases for MCPToolCallWidget component."""

    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def theme_manager(self, app):
        """Create a ThemeManager instance for testing."""
        return ThemeManager(app)

    @pytest.fixture
    def sample_tool_call(self):
        """Create a sample tool call for testing."""
        return {
            "id": "call_123",
            "name": "read_file",
            "parameters": {
                "file_path": "/home/user/test.py",
                "start_line": 1,
                "end_line": 10,
            },
            "status": "pending",
        }

    @pytest.fixture
    def sample_tool_result(self):
        """Create a sample tool result for testing."""
        return {
            "success": True,
            "content": "def hello_world():\n    print('Hello, World!')\n",
            "error": None,
            "execution_time": 0.125,
        }

    @pytest.fixture
    def sample_python_code_result(self):
        """Create a sample tool result with Python code."""
        return {
            "success": True,
            "content": '''def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Example usage
result = calculate_fibonacci(10)
print(f"Fibonacci(10) = {result}")
''',
            "error": None,
            "execution_time": 0.250,
            "content_type": "python",
        }

    @pytest.fixture
    def sample_javascript_code_result(self):
        """Create a sample tool result with JavaScript code."""
        return {
            "success": True,
            "content": """function calculateFactorial(n) {
    // Calculate factorial using recursion
    if (n <= 1) {
        return 1;
    }
    return n * calculateFactorial(n - 1);
}

const result = calculateFactorial(5);
console.log(`Factorial of 5 is: ${result}`);
""",
            "error": None,
            "execution_time": 0.180,
            "content_type": "javascript",
        }

    @pytest.fixture
    def sample_json_result(self):
        """Create a sample tool result with JSON content."""
        return {
            "success": True,
            "content": """{
    "status": "success",
    "data": {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ],
        "total": 2,
        "page": 1
    },
    "timestamp": "2024-01-15T10:30:00Z"
}""",
            "error": None,
            "execution_time": 0.095,
            "content_type": "json",
        }

    def test_widget_creation_with_tool_call(self, app, theme_manager, sample_tool_call):
        """Test that widget is created properly with tool call data."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        assert widget is not None
        assert widget.tool_call == sample_tool_call
        assert widget.theme_manager == theme_manager
        assert widget.is_collapsed is True  # Should start collapsed
        assert widget.result is None  # No result initially

    def test_widget_structure_creation(self, app, theme_manager, sample_tool_call):
        """Test that widget creates proper UI structure."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Check main layout exists
        assert widget.layout() is not None
        assert isinstance(widget.layout(), QVBoxLayout)

        # Check header components exist
        assert hasattr(widget, "header_frame")
        assert hasattr(widget, "expand_button")
        assert hasattr(widget, "tool_name_label")
        assert hasattr(widget, "status_label")

        # Check content components exist
        assert hasattr(widget, "content_widget")
        assert hasattr(widget, "parameters_text")
        assert hasattr(widget, "result_text")

    def test_expand_collapse_functionality(self, app, theme_manager, sample_tool_call):
        """Test expand/collapse functionality."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Show the widget so visibility tests work properly
        widget.show()

        # Should start collapsed
        assert widget.is_collapsed is True
        assert widget.content_widget.isVisible() is False

        # Expand
        widget.toggle_expand_collapse()
        assert widget.is_collapsed is False
        assert widget.content_widget.isVisible() is True

        # Collapse again
        widget.toggle_expand_collapse()
        assert widget.is_collapsed is True
        assert widget.content_widget.isVisible() is False

    def test_expand_button_click(self, app, theme_manager, sample_tool_call, qtbot):
        """Test that clicking expand button toggles visibility."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        initial_state = widget.is_collapsed

        # Click the expand button
        qtbot.mouseClick(widget.expand_button, Qt.MouseButton.LeftButton)

        assert widget.is_collapsed != initial_state
        assert widget.content_widget.isVisible() == (not initial_state)

    def test_tool_call_display(self, app, theme_manager, sample_tool_call):
        """Test that tool call information is displayed correctly."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Check tool name is displayed
        assert sample_tool_call["name"] in widget.tool_name_label.text()

        # Check status is displayed (status gets formatted with emoji, so check for formatted version)
        assert sample_tool_call["status"].title() in widget.status_label.text()

        # Check parameters are formatted and displayed
        widget.toggle_expand_collapse()  # Expand to see content
        parameters_text = widget.parameters_text.toPlainText()
        assert "file_path" in parameters_text
        assert "/home/user/test.py" in parameters_text

    def test_status_indicators(self, app, theme_manager):
        """Test different status indicators."""
        statuses = ["pending", "success", "error", "timeout"]

        for status in statuses:
            tool_call = {
                "id": f"call_{status}",
                "name": "test_tool",
                "parameters": {},
                "status": status,
            }

            widget = MCPToolCallWidget(tool_call=tool_call, theme_manager=theme_manager)

            # Check that status is reflected in the label
            assert status in widget.status_label.text().lower()

            # Check that status affects styling (we'll implement this)
            assert widget.status_label.styleSheet() != ""

    def test_update_result(
        self, app, theme_manager, sample_tool_call, sample_tool_result
    ):
        """Test updating widget with tool execution result."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Initially no result
        assert widget.result is None

        # Update with result
        widget.update_result(sample_tool_result)

        # Check result is stored
        assert widget.result == sample_tool_result

        # Check status is updated
        assert widget.tool_call["status"] == "success"

        # Check result is displayed when expanded
        widget.toggle_expand_collapse()
        result_text = widget.result_text.toPlainText()
        assert "Hello, World!" in result_text

    def test_error_result_handling(self, app, theme_manager, sample_tool_call):
        """Test handling of error results."""
        error_result = {
            "success": False,
            "content": None,
            "error": "File not found: /invalid/path.py",
            "execution_time": 0.050,
        }

        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        widget.update_result(error_result)

        # Check status is updated to error
        assert widget.tool_call["status"] == "error"

        # Check error is displayed when expanded
        widget.toggle_expand_collapse()
        result_text = widget.result_text.toPlainText()
        assert "File not found" in result_text

    # Task 8.5: Syntax highlighting tests
    def test_syntax_highlighting_python_code(
        self, app, theme_manager, sample_tool_call, sample_python_code_result
    ):
        """Test syntax highlighting for Python code in tool results."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Update with Python code result
        widget.update_result(sample_python_code_result)

        # Check that syntax highlighter is created and configured
        assert hasattr(widget, "result_syntax_highlighter")
        assert widget.result_syntax_highlighter is not None

        # Check that syntax highlighting is enabled
        assert widget.result_syntax_highlighter.is_enabled() is True

        # Check that correct lexer is detected for Python
        from pygments.lexers import PythonLexer

        assert isinstance(widget.result_syntax_highlighter.lexer, PythonLexer)

        # Expand to see highlighted content
        widget.toggle_expand_collapse()
        result_text = widget.result_text.toPlainText()
        assert "def calculate_fibonacci" in result_text

    def test_syntax_highlighting_javascript_code(
        self, app, theme_manager, sample_tool_call, sample_javascript_code_result
    ):
        """Test syntax highlighting for JavaScript code in tool results."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Update with JavaScript code result
        widget.update_result(sample_javascript_code_result)

        # Check that syntax highlighter is created and configured
        assert hasattr(widget, "result_syntax_highlighter")
        assert widget.result_syntax_highlighter is not None

        # Check that correct lexer is detected for JavaScript
        from pygments.lexers import JavascriptLexer

        assert isinstance(widget.result_syntax_highlighter.lexer, JavascriptLexer)

        # Expand to see highlighted content
        widget.toggle_expand_collapse()
        result_text = widget.result_text.toPlainText()
        assert "function calculateFactorial" in result_text

    def test_syntax_highlighting_json_content(
        self, app, theme_manager, sample_tool_call, sample_json_result
    ):
        """Test syntax highlighting for JSON content in tool results."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Update with JSON result
        widget.update_result(sample_json_result)

        # Check that syntax highlighter is created and configured
        assert hasattr(widget, "result_syntax_highlighter")
        assert widget.result_syntax_highlighter is not None

        # Check that correct lexer is detected for JSON
        from pygments.lexers import JsonLexer

        assert isinstance(widget.result_syntax_highlighter.lexer, JsonLexer)

        # Expand to see highlighted content
        widget.toggle_expand_collapse()
        result_text = widget.result_text.toPlainText()
        assert '"status": "success"' in result_text

    def test_syntax_highlighting_auto_detection(
        self, app, theme_manager, sample_tool_call
    ):
        """Test automatic language detection for syntax highlighting."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Test Python code detection without explicit content_type
        python_result = {
            "success": True,
            "content": "def hello():\n    print('Hello, World!')",
            "execution_time": 0.1,
        }

        widget.update_result(python_result)

        # Should detect Python from content patterns
        from pygments.lexers import PythonLexer

        assert isinstance(widget.result_syntax_highlighter.lexer, PythonLexer)

        # Test JavaScript code detection
        js_result = {
            "success": True,
            "content": "function hello() {\n    console.log('Hello, World!');\n}",
            "execution_time": 0.1,
        }

        widget.update_result(js_result)

        # Should detect JavaScript from content patterns
        from pygments.lexers import JavascriptLexer

        assert isinstance(widget.result_syntax_highlighter.lexer, JavascriptLexer)

    def test_syntax_highlighting_plain_text_fallback(
        self, app, theme_manager, sample_tool_call
    ):
        """Test fallback to plain text when language cannot be detected."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Result with plain text content
        plain_result = {
            "success": True,
            "content": "This is just plain text without any code patterns.",
            "execution_time": 0.05,
        }

        widget.update_result(plain_result)

        # Should fallback to TextLexer
        from pygments.lexers import TextLexer

        assert isinstance(widget.result_syntax_highlighter.lexer, TextLexer)

    def test_syntax_highlighting_disable_enable(
        self, app, theme_manager, sample_tool_call, sample_python_code_result
    ):
        """Test enabling and disabling syntax highlighting."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Update with code result
        widget.update_result(sample_python_code_result)

        # Should be enabled by default
        assert widget.result_syntax_highlighter.is_enabled() is True

        # Disable syntax highlighting
        widget.set_syntax_highlighting_enabled(False)
        assert widget.result_syntax_highlighter.is_enabled() is False

        # Re-enable syntax highlighting
        widget.set_syntax_highlighting_enabled(True)
        assert widget.result_syntax_highlighter.is_enabled() is True

    def test_syntax_highlighting_theme_adaptation(
        self, app, theme_manager, sample_tool_call, sample_python_code_result
    ):
        """Test that syntax highlighting adapts to theme changes."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Update with code result
        widget.update_result(sample_python_code_result)

        # Check that syntax highlighter has theme-aware colors
        token_styles = widget.result_syntax_highlighter.token_styles
        assert len(token_styles) > 0

        # Verify that colors are appropriate for the theme
        for _token_type, color in token_styles.items():
            assert color.isValid()

        # Simulate theme change
        widget._on_theme_changed("light")

        # Colors should be updated for light theme
        updated_styles = widget.result_syntax_highlighter.token_styles
        assert updated_styles is not None

    def test_syntax_highlighting_error_handling(
        self, app, theme_manager, sample_tool_call
    ):
        """Test error handling in syntax highlighting."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Result with potentially problematic content
        problematic_result = {
            "success": True,
            "content": "Content with unicode: \u0001\u0002\u0003",
            "execution_time": 0.05,
        }

        # Should not raise exceptions
        try:
            widget.update_result(problematic_result)
            assert widget.result_syntax_highlighter is not None
        except Exception as e:
            pytest.fail(
                f"Syntax highlighting should handle problematic content gracefully: {e}"
            )

    def test_theme_application(self, app, theme_manager, sample_tool_call):
        """Test that theme is applied correctly to widget."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Widget should have styling applied
        assert widget.styleSheet() != ""

        # Should be able to apply theme manually
        widget.apply_theme()
        assert widget.styleSheet() != ""

    def test_theme_change_handling(self, app, theme_manager, sample_tool_call):
        """Test handling of theme changes."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call,
            theme_manager=theme_manager,
            auto_adapt_theme=True,
        )

        # Simulate theme change
        widget._on_theme_changed("light")

        # Style should be updated
        assert widget.styleSheet() != ""
        # Note: We can't easily compare exact styles, but we can ensure it's not empty

    def test_execution_timing_display(
        self, app, theme_manager, sample_tool_call, sample_tool_result
    ):
        """Test that execution timing is displayed correctly."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        widget.update_result(sample_tool_result)

        # Expand to see timing information
        widget.toggle_expand_collapse()
        result_text = widget.result_text.toPlainText()

        # Should show execution time
        assert "125.0ms" in result_text or "0.125s" in result_text

    def test_accessibility_features(self, app, theme_manager, sample_tool_call):
        """Test accessibility features of the widget."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Check accessibility names and descriptions
        assert widget.accessibleName() != ""
        assert widget.accessibleDescription() != ""
        assert widget.expand_button.accessibleName() != ""
        assert widget.expand_button.accessibleDescription() != ""
        assert widget.parameters_text.accessibleName() != ""
        assert widget.result_text.accessibleName() != ""

    def test_multiple_widgets_independence(self, app, theme_manager):
        """Test that multiple widgets operate independently."""
        tool_call_1 = {
            "id": "call_1",
            "name": "tool_1",
            "parameters": {},
            "status": "pending",
        }
        tool_call_2 = {
            "id": "call_2",
            "name": "tool_2",
            "parameters": {},
            "status": "success",
        }

        widget_1 = MCPToolCallWidget(tool_call=tool_call_1, theme_manager=theme_manager)
        widget_2 = MCPToolCallWidget(tool_call=tool_call_2, theme_manager=theme_manager)

        # Both should start collapsed
        assert widget_1.is_collapsed is True
        assert widget_2.is_collapsed is True

        # Expand one widget
        widget_1.toggle_expand_collapse()

        # Only the first widget should be expanded
        assert widget_1.is_collapsed is False
        assert widget_2.is_collapsed is True

    def test_widget_cleanup(self, app, theme_manager, sample_tool_call):
        """Test proper cleanup when widget is deleted."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call,
            theme_manager=theme_manager,
            auto_adapt_theme=True,
        )

        # Should not raise exceptions during cleanup
        try:
            widget.deleteLater()
        except Exception as e:
            pytest.fail(f"Widget cleanup should not raise exceptions: {e}")

    def test_update_result_nested_structure(self, app, theme_manager, sample_tool_call):
        """Test update_result method with nested result structure from AI agent."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # AI agent signal data structure
        result_data = {
            "id": "test_call_123",
            "status": "success",
            "result": {
                "success": True,
                "content": "This is nested result content",
                "execution_time": 1.5,
                "content_type": "text",
            },
            "execution_time": 2.0,
        }

        widget.update_result(result_data)

        # Verify status is success
        assert widget.tool_call["status"] == "success"
        assert "Success: True" in widget.result_text.toPlainText()
        assert "This is nested result content" in widget.result_text.toPlainText()

    def test_update_result_direct_structure(self, app, theme_manager, sample_tool_call):
        """Test update_result method with direct result structure."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Direct result data structure
        result_data = {
            "success": True,
            "content": "This is direct result content",
            "execution_time": 1.2,
        }

        widget.update_result(result_data)

        # Verify status is success
        assert widget.tool_call["status"] == "success"
        assert "Success: True" in widget.result_text.toPlainText()
        assert "This is direct result content" in widget.result_text.toPlainText()

    def test_update_result_error_nested(self, app, theme_manager, sample_tool_call):
        """Test update_result method with nested error structure."""
        widget = MCPToolCallWidget(
            tool_call=sample_tool_call, theme_manager=theme_manager
        )

        # Error result with nested structure
        result_data = {
            "id": "test_call_456",
            "status": "error",
            "result": {
                "success": False,
                "error": "This is a nested error message",
                "execution_time": 0.5,
            },
            "execution_time": 0.8,
        }

        widget.update_result(result_data)

        # Verify status is error
        assert widget.tool_call["status"] == "error"
        assert "Success: False" in widget.result_text.toPlainText()
        assert "This is a nested error message" in widget.result_text.toPlainText()
