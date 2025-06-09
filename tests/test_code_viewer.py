"""Tests for code viewer widget with syntax highlighting."""

from PyQt6.QtWidgets import QWidget

from my_coding_agent.core.code_viewer import CodeViewerWidget, LineNumbersWidget


class TestCodeViewerWidget:
    """Test cases for CodeViewerWidget class."""

    def test_code_viewer_widget_initialization(self, qapp):
        """Test CodeViewerWidget initialization."""
        widget = CodeViewerWidget()

        # Should be a QWidget (not QTextEdit anymore due to line numbers)
        assert isinstance(widget, QWidget)

        # Should have line numbers enabled by default
        assert widget.line_numbers_enabled() is True

        # Should have a line numbers widget
        line_numbers_widget = widget.get_line_numbers_widget()
        assert line_numbers_widget is not None
        assert isinstance(line_numbers_widget, LineNumbersWidget)

    def test_code_viewer_widget_read_only_mode(self, qapp):
        """Test that the widget is properly configured in read-only mode."""
        widget = CodeViewerWidget()

        # Should be read-only
        assert widget.isReadOnly() is True

        # Should not accept text input
        widget.setPlainText("test content")
        assert widget.toPlainText() == "test content"

        # But should remain read-only
        assert widget.isReadOnly() is True

    def test_code_viewer_widget_load_file(self, qapp, tmp_path):
        """Test loading a file into the code viewer."""
        widget = CodeViewerWidget()

        # Create test file
        test_file = tmp_path / "test.py"
        test_content = "print('Hello, World!')\n# This is a comment"
        test_file.write_text(test_content)

        # Load file
        widget.load_file(test_file)

        # Should display file content
        assert widget.toPlainText() == test_content

    def test_code_viewer_widget_load_nonexistent_file(self, qapp, tmp_path):
        """Test loading a non-existent file."""
        widget = CodeViewerWidget()

        # Try to load non-existent file
        non_existent = tmp_path / "does_not_exist.py"

        # Should handle gracefully without crashing
        widget.load_file(non_existent)

        # Should remain empty or show error message
        content = widget.toPlainText()
        # Content could be empty or an error message
        assert isinstance(content, str)

    def test_code_viewer_widget_clear_content(self, qapp, tmp_path):
        """Test clearing the viewer content."""
        widget = CodeViewerWidget()

        # Load some content first
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")
        widget.load_file(test_file)

        # Verify content is loaded
        assert widget.toPlainText() != ""

        # Clear content
        widget.clear_content()

        # Should be empty
        assert widget.toPlainText() == ""

    def test_code_viewer_widget_get_current_file(self, qapp, tmp_path):
        """Test getting the currently loaded file path."""
        widget = CodeViewerWidget()

        # Initially no file
        assert widget.get_current_file() is None

        # Load a file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")
        widget.load_file(test_file)

        # Should return the file path
        assert widget.get_current_file() == test_file

    def test_code_viewer_widget_text_cursor_behavior(self, qapp, tmp_path):
        """Test text cursor and selection behavior."""
        widget = CodeViewerWidget()

        # Load content
        test_file = tmp_path / "test.py"
        test_content = "line1\nline2\nline3"
        test_file.write_text(test_content)
        widget.load_file(test_file)

        # Should be able to move cursor and select text
        cursor = widget.textCursor()
        assert cursor is not None

        # Should be able to select text even in read-only mode
        widget.selectAll()
        selected_text = widget.textCursor().selectedText()
        # Note: selectedText() may use different line separators
        assert len(selected_text) > 0


class TestCodeViewerSyntaxHighlighting:
    """Test cases for syntax highlighting functionality."""

    def test_syntax_highlighting_python_file(self, qapp, tmp_path):
        """Test syntax highlighting for Python files."""
        widget = CodeViewerWidget()

        # Create Python file with various syntax elements
        python_file = tmp_path / "test.py"
        python_content = '''
def hello_world():
    """A simple function."""
    print("Hello, World!")  # Comment
    x = 42
    return x

class MyClass:
    def __init__(self):
        self.value = "test"
'''
        python_file.write_text(python_content)

        # Load file
        result = widget.load_file(python_file)
        assert result is True

        # Check that syntax highlighting is enabled
        assert widget.syntax_highlighting_enabled() is True

        # Check that the correct lexer is detected
        assert widget.get_current_language() == "python"

    def test_syntax_highlighting_javascript_file(self, qapp, tmp_path):
        """Test syntax highlighting for JavaScript files."""
        widget = CodeViewerWidget()

        # Create JavaScript file
        js_file = tmp_path / "test.js"
        js_content = """
function helloWorld() {
    // This is a comment
    const message = "Hello, World!";
    console.log(message);
    return true;
}

class MyClass {
    constructor() {
        this.value = 42;
    }
}
"""
        js_file.write_text(js_content)

        # Load file
        result = widget.load_file(js_file)
        assert result is True

        # Check that syntax highlighting is enabled
        assert widget.syntax_highlighting_enabled() is True

        # Check that the correct lexer is detected
        assert widget.get_current_language() == "javascript"

    def test_syntax_highlighting_unsupported_file(self, qapp, tmp_path):
        """Test behavior with unsupported file types."""
        widget = CodeViewerWidget()

        # Create a file with unknown extension
        unknown_file = tmp_path / "test.unknown"
        unknown_file.write_text("This is plain text content")

        # Load file
        result = widget.load_file(unknown_file)
        assert result is True

        # Should still load but without syntax highlighting
        assert widget.get_current_language() == "text"

    def test_syntax_highlighting_plain_text_file(self, qapp, tmp_path):
        """Test plain text files without syntax highlighting."""
        widget = CodeViewerWidget()

        # Create plain text file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is plain text content\nWith multiple lines")

        # Load file
        result = widget.load_file(txt_file)
        assert result is True

        # Should be treated as plain text
        assert widget.get_current_language() == "text"

    def test_syntax_highlighting_toggle(self, qapp, tmp_path):
        """Test enabling/disabling syntax highlighting."""
        widget = CodeViewerWidget()

        # Create Python file
        python_file = tmp_path / "test.py"
        python_file.write_text("print('hello')")
        widget.load_file(python_file)

        # Initially should be enabled
        assert widget.syntax_highlighting_enabled() is True

        # Disable syntax highlighting
        widget.set_syntax_highlighting(False)
        assert widget.syntax_highlighting_enabled() is False

        # Re-enable syntax highlighting
        widget.set_syntax_highlighting(True)
        assert widget.syntax_highlighting_enabled() is True

    def test_language_detection_by_extension(self, qapp, tmp_path):
        """Test language detection based on file extension."""
        widget = CodeViewerWidget()

        # Test various file extensions
        test_cases = [
            ("test.py", "python"),
            ("test.pyw", "python"),
            ("test.js", "javascript"),
            ("test.jsx", "javascript"),
            ("test.ts", "javascript"),  # TypeScript treated as JavaScript
            ("test.tsx", "javascript"),
            ("test.txt", "text"),
            ("test.md", "text"),
            ("README", "text"),
        ]

        for filename, expected_language in test_cases:
            test_file = tmp_path / filename
            test_file.write_text("# Sample content")

            widget.load_file(test_file)
            assert widget.get_current_language() == expected_language, (
                f"Failed for {filename}"
            )

    def test_syntax_highlighting_performance(self, qapp, tmp_path):
        """Test syntax highlighting performance with medium-sized file."""
        widget = CodeViewerWidget()

        # Create a larger Python file
        python_file = tmp_path / "large.py"
        python_content = '''
def function_{i}():
    """Function number {i}."""
    value = {i} * 2
    print(f"Value: {{value}}")
    return value

class Class_{i}:
    def __init__(self):
        self.value = {i}
'''

        # Generate content with 100 functions and classes
        large_content = "\n".join([python_content.format(i=i) for i in range(100)])
        python_file.write_text(large_content)

        # Load file - should not take too long
        import time

        start_time = time.time()
        result = widget.load_file(python_file)
        load_time = time.time() - start_time

        assert result is True
        assert load_time < 2.0  # Should load within 2 seconds
        assert widget.syntax_highlighting_enabled() is True


class TestCodeViewerLineNumbers:
    """Test cases for line numbers widget functionality."""

    def test_line_numbers_widget_initialization(self, qapp):
        """Test line numbers widget is properly initialized."""
        widget = CodeViewerWidget()

        # Check that line numbers are enabled by default
        assert widget.line_numbers_enabled() is True

        # Check that line numbers widget exists
        line_numbers_widget = widget.get_line_numbers_widget()
        assert line_numbers_widget is not None

    def test_line_numbers_display_single_line(self, qapp, tmp_path):
        """Test line numbers display for single line content."""
        widget = CodeViewerWidget()

        # Create single line file
        test_file = tmp_path / "single_line.py"
        test_file.write_text("print('Hello, World!')")

        widget.load_file(test_file)

        # Should show line number 1
        line_numbers_widget = widget.get_line_numbers_widget()
        assert line_numbers_widget.get_line_count() == 1
        assert "1" in line_numbers_widget.get_displayed_numbers()

    def test_line_numbers_display_multiple_lines(self, qapp, tmp_path):
        """Test line numbers display for multiple lines."""
        widget = CodeViewerWidget()

        # Create multi-line file
        test_file = tmp_path / "multi_line.py"
        content = "\n".join([f"line_{i} = {i}" for i in range(1, 11)])  # 10 lines
        test_file.write_text(content)

        widget.load_file(test_file)

        # Should show line numbers 1-10
        line_numbers_widget = widget.get_line_numbers_widget()
        assert line_numbers_widget.get_line_count() == 10

        displayed_numbers = line_numbers_widget.get_displayed_numbers()
        for i in range(1, 11):
            assert str(i) in displayed_numbers

    def test_line_numbers_sync_with_scrolling(self, qapp, tmp_path):
        """Test line numbers sync with text editor scrolling."""
        widget = CodeViewerWidget()

        # Create file with many lines to enable scrolling
        test_file = tmp_path / "long_file.py"
        content = "\n".join([f"line_{i} = {i}" for i in range(1, 101)])  # 100 lines
        test_file.write_text(content)

        widget.load_file(test_file)

        line_numbers_widget = widget.get_line_numbers_widget()

        # Get initial scroll position
        initial_scroll = widget.verticalScrollBar().value()
        initial_line_scroll = line_numbers_widget.get_scroll_position()

        # Scroll down
        widget.verticalScrollBar().setValue(500)  # Scroll down

        # Line numbers should sync
        new_scroll = widget.verticalScrollBar().value()
        new_line_scroll = line_numbers_widget.get_scroll_position()

        assert new_scroll != initial_scroll
        assert new_line_scroll != initial_line_scroll
        assert new_line_scroll == new_scroll  # Should be synchronized

    def test_line_numbers_toggle_visibility(self, qapp, tmp_path):
        """Test toggling line numbers visibility."""
        widget = CodeViewerWidget()
        widget.show()  # Show the widget to make its children visible

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')\nprint('line 2')")
        widget.load_file(test_file)

        # Initially should be visible
        assert widget.line_numbers_enabled() is True
        line_numbers_widget = widget.get_line_numbers_widget()
        assert line_numbers_widget.isVisible() is True

        # Hide line numbers
        widget.set_line_numbers_enabled(False)
        assert widget.line_numbers_enabled() is False
        assert line_numbers_widget.isVisible() is False

        # Show line numbers again
        widget.set_line_numbers_enabled(True)
        assert widget.line_numbers_enabled() is True
        assert line_numbers_widget.isVisible() is True

    def test_line_numbers_width_adjustment(self, qapp, tmp_path):
        """Test line numbers widget width adjusts based on line count."""
        widget = CodeViewerWidget()
        line_numbers_widget = widget.get_line_numbers_widget()

        # Test with single digit line count (1-9)
        test_file = tmp_path / "small.py"
        content = "\n".join([f"line_{i}" for i in range(1, 6)])  # 5 lines
        test_file.write_text(content)
        widget.load_file(test_file)

        small_width = line_numbers_widget.width()

        # Test with double digit line count (10-99)
        test_file2 = tmp_path / "medium.py"
        content = "\n".join([f"line_{i}" for i in range(1, 51)])  # 50 lines
        test_file2.write_text(content)
        widget.load_file(test_file2)

        medium_width = line_numbers_widget.width()

        # Test with triple digit line count (100+)
        test_file3 = tmp_path / "large.py"
        content = "\n".join([f"line_{i}" for i in range(1, 151)])  # 150 lines
        test_file3.write_text(content)
        widget.load_file(test_file3)

        large_width = line_numbers_widget.width()

        # Width should increase with more digits
        assert medium_width >= small_width
        assert large_width >= medium_width

    def test_line_numbers_current_line_highlight(self, qapp, tmp_path):
        """Test current line highlighting in line numbers."""
        widget = CodeViewerWidget()

        # Create test file
        test_file = tmp_path / "highlight_test.py"
        content = "\n".join([f"line_{i}" for i in range(1, 11)])  # 10 lines
        test_file.write_text(content)
        widget.load_file(test_file)

        line_numbers_widget = widget.get_line_numbers_widget()

        # Initially should highlight line 1 (cursor at start)
        assert line_numbers_widget.get_current_line() == 1

        # Move cursor to line 5
        cursor = widget.textCursor()
        cursor.movePosition(
            cursor.MoveOperation.Down, cursor.MoveMode.MoveAnchor, 4
        )  # Move down 4 lines
        widget.setTextCursor(cursor)

        # Should now highlight line 5
        assert line_numbers_widget.get_current_line() == 5

    def test_line_numbers_font_consistency(self, qapp, tmp_path):
        """Test line numbers font matches text editor font."""
        widget = CodeViewerWidget()
        line_numbers_widget = widget.get_line_numbers_widget()

        # Create test file
        test_file = tmp_path / "font_test.py"
        test_file.write_text("print('test')")
        widget.load_file(test_file)

        # Line numbers should use same font family as text editor
        text_font = widget.get_text_edit_font()
        line_numbers_font = line_numbers_widget.font()

        assert text_font.family() == line_numbers_font.family()
        # Font size can be slightly different for readability
        assert abs(text_font.pointSize() - line_numbers_font.pointSize()) <= 1

    def test_line_numbers_empty_content(self, qapp):
        """Test line numbers behavior with empty content."""
        widget = CodeViewerWidget()
        line_numbers_widget = widget.get_line_numbers_widget()

        # With empty content, should still show line 1
        assert line_numbers_widget.get_line_count() >= 1
        assert line_numbers_widget.get_current_line() == 1
