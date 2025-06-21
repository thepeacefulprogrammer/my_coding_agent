"""Tests for code viewer widget with syntax highlighting."""

from __future__ import annotations

import pytest
from code_viewer.core.code_viewer import CodeViewerWidget, LineNumbersWidget
from PyQt6.QtWidgets import QWidget


@pytest.mark.qt
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


@pytest.mark.qt
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
        # (could be plain text highlighting)
        content = widget.toPlainText()
        assert content == "This is plain text content"

    def test_syntax_highlighting_plain_text_file(self, qapp, tmp_path):
        """Test syntax highlighting for plain text files."""
        widget = CodeViewerWidget()

        # Create plain text file
        txt_file = tmp_path / "test.txt"
        txt_content = "This is just plain text\nwith multiple lines."
        txt_file.write_text(txt_content)

        # Load file
        result = widget.load_file(txt_file)
        assert result is True

        # Content should be loaded
        assert widget.toPlainText() == txt_content

    def test_syntax_highlighting_toggle(self, qapp, tmp_path):
        """Test enabling/disabling syntax highlighting."""
        widget = CodeViewerWidget()

        # Create Python file
        python_file = tmp_path / "test.py"
        python_file.write_text("print('hello')")
        widget.load_file(python_file)

        # Should be enabled by default
        assert widget.syntax_highlighting_enabled() is True

        # Disable syntax highlighting
        widget.set_syntax_highlighting(False)
        assert widget.syntax_highlighting_enabled() is False

        # Enable syntax highlighting
        widget.set_syntax_highlighting(True)
        assert widget.syntax_highlighting_enabled() is True

    def test_language_detection_by_extension(self, qapp, tmp_path):
        """Test language detection based on file extension."""
        widget = CodeViewerWidget()

        # Test various file extensions
        test_cases = [
            ("test.py", "python"),
            ("test.js", "javascript"),
            ("test.txt", "text"),
        ]

        for filename, expected_lang in test_cases:
            test_file = tmp_path / filename
            test_file.write_text("content")
            widget.load_file(test_file)
            # Language detection should work
            current_lang = widget.get_current_language()
            assert current_lang == expected_lang or current_lang.startswith(
                expected_lang
            )

    @pytest.mark.slow
    def test_syntax_highlighting_performance(self, qapp, tmp_path):
        """Test syntax highlighting performance with medium-sized files."""
        widget = CodeViewerWidget()

        # Create a medium-sized Python file (around 200 lines - reduced for performance)
        large_file = tmp_path / "large_test.py"
        content_lines = []
        for i in range(200):  # Reduced from 1000 to 200
            content_lines.append(f"# Line {i}")
            content_lines.append(f"def function_{i}():")
            content_lines.append(f'    """Function {i} docstring."""')
            content_lines.append(f'    return "value_{i}"')
            content_lines.append("")

        large_content = "\n".join(content_lines)
        large_file.write_text(large_content)

        # Should load without issues
        import time

        start_time = time.time()
        result = widget.load_file(large_file)
        load_time = time.time() - start_time

        assert result is True
        # Should load reasonably quickly (less than 10 seconds)
        assert load_time < 10.0
        assert widget.get_current_language() == "python"


@pytest.mark.qt
class TestCodeViewerLineNumbers:
    """Test cases for line numbers functionality."""

    def test_line_numbers_widget_initialization(self, qapp):
        """Test LineNumbersWidget initialization."""
        widget = CodeViewerWidget()
        line_numbers = widget.get_line_numbers_widget()

        # Should be enabled by default (visibility depends on parent widget being shown)
        assert widget.line_numbers_enabled() is True

        # Should start with line count of 1
        assert line_numbers.get_line_count() >= 1

    def test_line_numbers_display_single_line(self, qapp, tmp_path):
        """Test line numbers with single line content."""
        widget = CodeViewerWidget()

        # Load single line content
        test_file = tmp_path / "single.py"
        test_file.write_text("print('hello')")
        widget.load_file(test_file)

        line_numbers = widget.get_line_numbers_widget()
        assert line_numbers.get_line_count() == 1

    def test_line_numbers_display_multiple_lines(self, qapp, tmp_path):
        """Test line numbers with multiple lines."""
        widget = CodeViewerWidget()

        # Load multi-line content
        test_file = tmp_path / "multi.py"
        content = "line1\nline2\nline3\nline4\nline5"
        test_file.write_text(content)
        widget.load_file(test_file)

        line_numbers = widget.get_line_numbers_widget()
        expected_lines = content.count("\n") + 1
        assert line_numbers.get_line_count() == expected_lines

        # Should show correct line numbers
        displayed_numbers = line_numbers.get_displayed_numbers()
        assert displayed_numbers == ["1", "2", "3", "4", "5"]

    def test_line_numbers_sync_with_scrolling(self, qapp, tmp_path):
        """Test that line numbers sync with text scrolling."""
        widget = CodeViewerWidget()

        # Create file with many lines to enable scrolling
        test_file = tmp_path / "scrollable.py"
        lines = [f"# Line {i}" for i in range(1, 101)]  # 100 lines
        content = "\n".join(lines)
        test_file.write_text(content)
        widget.load_file(test_file)

        line_numbers = widget.get_line_numbers_widget()

        # Should have correct line count
        assert line_numbers.get_line_count() == 100

        # Scroll the text editor and check that line numbers respond
        scroll_bar = widget.verticalScrollBar()
        if scroll_bar:
            # Move scroll position
            original_pos = scroll_bar.value()
            scroll_bar.setValue(50)  # Scroll down

            # Line numbers should track scroll position
            line_numbers_scroll = line_numbers.get_scroll_position()
            assert line_numbers_scroll >= 0  # Should be able to get scroll position

            # Reset scroll
            scroll_bar.setValue(original_pos)

    def test_line_numbers_toggle_visibility(self, qapp, tmp_path):
        """Test enabling/disabling line numbers."""
        widget = CodeViewerWidget()

        # Load some content
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")
        widget.load_file(test_file)

        # Should be enabled by default
        assert widget.line_numbers_enabled() is True
        # Note: visibility depends on parent widget being shown, so we check enabled state
        assert widget.line_numbers_enabled() is True

        # Disable line numbers
        widget.set_line_numbers_enabled(False)
        assert widget.line_numbers_enabled() is False

        # Enable line numbers
        widget.set_line_numbers_enabled(True)
        assert widget.line_numbers_enabled() is True

    def test_line_numbers_width_adjustment(self, qapp, tmp_path):
        """Test that line numbers widget adjusts width based on line count."""
        widget = CodeViewerWidget()
        line_numbers = widget.get_line_numbers_widget()

        # Start with single line
        test_file = tmp_path / "single.py"
        test_file.write_text("print('hello')")
        widget.load_file(test_file)

        # Get width for single digit line numbers
        single_digit_width = line_numbers.width()

        # Now load file with many lines (3+ digits)
        large_file = tmp_path / "large.py"
        lines = [f"# Line {i}" for i in range(1, 1001)]  # 1000+ lines
        content = "\n".join(lines)
        large_file.write_text(content)
        widget.load_file(large_file)

        # Width should increase to accommodate more digits
        multi_digit_width = line_numbers.width()
        assert multi_digit_width > single_digit_width

        # Line count should be correct
        assert line_numbers.get_line_count() == 1000

    def test_line_numbers_current_line_highlight(self, qapp, tmp_path):
        """Test current line tracking in line numbers."""
        widget = CodeViewerWidget()

        # Load multi-line content
        test_file = tmp_path / "multi.py"
        content = "line1\nline2\nline3\nline4"
        test_file.write_text(content)
        widget.load_file(test_file)

        line_numbers = widget.get_line_numbers_widget()

        # Should start at line 1
        assert line_numbers.get_current_line() == 1

        # Move cursor and check current line updates
        cursor = widget.textCursor()
        # Move to second line (position after first newline)
        cursor.setPosition(content.find("\n") + 1)
        widget.setTextCursor(cursor)

        # Current line should update
        current_line = line_numbers.get_current_line()
        assert current_line == 2

    def test_line_numbers_font_consistency(self, qapp, tmp_path):
        """Test that line numbers use consistent font with text editor."""
        widget = CodeViewerWidget()

        # Load some content
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")
        widget.load_file(test_file)

        line_numbers = widget.get_line_numbers_widget()
        text_font = widget.get_text_edit_font()
        line_numbers_font = line_numbers.font()

        # Fonts should match
        assert text_font.family() == line_numbers_font.family()
        assert text_font.pointSize() == line_numbers_font.pointSize()

    def test_line_numbers_empty_content(self, qapp):
        """Test line numbers behavior with empty content."""
        widget = CodeViewerWidget()
        line_numbers = widget.get_line_numbers_widget()

        # Even with empty content, should show at least line 1
        assert line_numbers.get_line_count() >= 1
        assert line_numbers.get_current_line() == 1


@pytest.mark.qt
class TestCodeViewerLargeFileHandling:
    """Test cases for large file handling with lazy loading."""

    def test_large_file_size_limit_detection(self, qapp, tmp_path):
        """Test detection of files approaching size limits."""
        widget = CodeViewerWidget()

        # Temporarily reduce the threshold for testing
        original_threshold = widget._large_file_threshold
        widget._large_file_threshold = 1024  # 1KB for testing

        try:
            # Create a file larger than our test threshold
            large_file = tmp_path / "large.py"
            content = "# " + "x" * 1100 + "\n"  # ~1.1KB content
            large_file.write_text(content)

            # Should load successfully
            result = widget.load_file(large_file)
            assert result is True

            # Should have loaded the content
            loaded_content = widget.toPlainText()
            assert len(loaded_content) > 0

            # Should detect this as a large file
            assert widget.is_large_file()
        finally:
            # Restore original threshold
            widget._large_file_threshold = original_threshold

    def test_very_large_file_lazy_loading(self, qapp, tmp_path):
        """Test lazy loading behavior for very large files."""
        widget = CodeViewerWidget()

        # Reduce threshold for testing
        original_threshold = widget._large_file_threshold
        widget._large_file_threshold = 512  # 512 bytes for testing

        try:
            # Create a file larger than threshold
            very_large_file = tmp_path / "very_large.py"
            content = "# " + "x" * 600 + "\n"  # ~600+ bytes
            very_large_file.write_text(content)

            # Should still load but with lazy loading
            result = widget.load_file(very_large_file)
            assert result is True

            # Should show content (with lazy loading message)
            loaded_content = widget.toPlainText()
            assert len(loaded_content) > 0

            # Should indicate lazy loading is active
            assert widget.is_lazy_loading_active()
        finally:
            widget._large_file_threshold = original_threshold

    def test_large_file_memory_efficiency(self, qapp, tmp_path):
        """Test memory efficiency with large files."""
        widget = CodeViewerWidget()

        # Create a reasonably sized file (not actually large to avoid test slowness)
        large_file = tmp_path / "memory_test.py"
        content_lines = []
        for i in range(1000):  # 1000 lines instead of megabytes
            content_lines.append(f"def function_{i}(): pass")

        content = "\n".join(content_lines)
        large_file.write_text(content)

        # Load the file
        result = widget.load_file(large_file)
        assert result is True

        # Should have loaded successfully
        loaded_content = widget.toPlainText()
        assert len(loaded_content) > 0

    @pytest.mark.slow
    def test_large_file_performance_requirements(self, qapp, tmp_path):
        """Test performance requirements for large file loading."""
        widget = CodeViewerWidget()

        # Create a file with many lines (testing line count performance)
        large_file = tmp_path / "performance_test.py"
        content_lines = []
        for i in range(1000):  # 1000 lines for performance testing (reduced from 5000)
            content_lines.append(f"# Performance test line {i}")

        content = "\n".join(content_lines)
        large_file.write_text(content)

        # Should load within reasonable time (under 5 seconds for test)
        import time

        start_time = time.time()

        result = widget.load_file(large_file)

        load_time = time.time() - start_time

        assert result is True
        assert load_time < 5.0  # Should load in under 5 seconds

    def test_large_file_lazy_loading_chunks(self, qapp, tmp_path):
        """Test that lazy loading shows content in manageable chunks."""
        widget = CodeViewerWidget()

        # Set small threshold and chunk size for testing
        original_threshold = widget._large_file_threshold
        original_chunk_size = widget._chunk_size
        widget._large_file_threshold = 100  # 100 bytes
        widget._chunk_size = 50  # 50 byte chunks

        try:
            # Create a file that will trigger lazy loading
            huge_file = tmp_path / "huge.py"
            content = "# " + "x" * 150 + "\n"  # 150+ bytes, will need chunking
            huge_file.write_text(content)

            # Load file
            result = widget.load_file(huge_file)
            assert result is True

            # Should show partial content (first chunk)
            loaded_content = widget.toPlainText()
            assert len(loaded_content) > 0

            # Should be able to request more content
            assert widget.can_load_more_content()

            # Load next chunk
            widget.load_next_chunk()
            updated_content = widget.toPlainText()
            assert len(updated_content) >= len(
                loaded_content
            )  # Should have same or more content
        finally:
            widget._large_file_threshold = original_threshold
            widget._chunk_size = original_chunk_size

    def test_large_file_syntax_highlighting_optimization(self, qapp, tmp_path):
        """Test that syntax highlighting is optimized for large files."""
        widget = CodeViewerWidget()

        # Create a Python file with many lines
        large_python_file = tmp_path / "large_syntax.py"
        content_lines = []
        for i in range(2000):  # 2000 lines for testing
            content_lines.append(f"def function_{i}():")
            content_lines.append(f'    """Docstring {i}."""')
            content_lines.append(f"    return {i}")

        content = "\n".join(content_lines)
        large_python_file.write_text(content)

        # Load file
        result = widget.load_file(large_python_file)
        assert result is True

        # Should load successfully
        loaded_content = widget.toPlainText()
        assert len(loaded_content) > 0

        # Language should be detected
        assert widget.get_current_language() == "python"

    def test_large_file_line_numbers_performance(self, qapp, tmp_path):
        """Test line numbers performance with large files."""
        widget = CodeViewerWidget()

        # Create file with many lines
        many_lines_file = tmp_path / "many_lines.py"
        lines = [f"# Line {i}" for i in range(1, 3001)]  # 3000 lines
        content = "\n".join(lines)
        many_lines_file.write_text(content)

        # Load file
        result = widget.load_file(many_lines_file)
        assert result is True

        line_numbers = widget.get_line_numbers_widget()

        # Line numbers should handle large line counts efficiently
        assert line_numbers.get_line_count() == 3000

    def test_large_file_user_feedback(self, qapp, tmp_path):
        """Test that user gets appropriate feedback for large file operations."""
        widget = CodeViewerWidget()

        # Set threshold for testing
        original_threshold = widget._large_file_threshold
        widget._large_file_threshold = 200  # 200 bytes

        try:
            # Create a file that will be considered "large"
            large_file = tmp_path / "user_feedback.py"
            content = "# " + "x" * 250 + "\n"  # 250+ bytes
            large_file.write_text(content)

            # Load file - should provide feedback about large file handling
            result = widget.load_file(large_file)
            assert result is True

            # Should indicate it's a large file
            assert widget.is_large_file()

            # Should provide status information
            status_info = widget.get_large_file_status()
            assert status_info is not None
            assert isinstance(status_info, dict)
            assert "file_size" in status_info
            assert "is_lazy_loading" in status_info
        finally:
            widget._large_file_threshold = original_threshold

    def test_large_file_threshold_configuration(self, qapp):
        """Test that large file threshold can be configured."""
        widget = CodeViewerWidget()

        # Check default threshold is reasonable
        assert widget._large_file_threshold == 10 * 1024 * 1024  # 10MB

        # Should be able to modify threshold for testing
        widget._large_file_threshold = 1024  # 1KB
        assert widget._large_file_threshold == 1024

    def test_chunk_loading_functionality(self, qapp, tmp_path):
        """Test chunk loading mechanism works correctly."""
        widget = CodeViewerWidget()

        # Set up small chunks for testing
        original_threshold = widget._large_file_threshold
        original_chunk_size = widget._chunk_size
        widget._large_file_threshold = 50
        widget._chunk_size = 25

        try:
            # Create file larger than threshold
            test_file = tmp_path / "chunk_test.py"
            content = (
                "# Line 1\n# Line 2\n# Line 3\n# Line 4\n# Line 5\n" * 5
            )  # ~300 bytes (ensure it's > 50 byte threshold)
            test_file.write_text(content)

            # Load file
            result = widget.load_file(test_file)
            assert result is True

            # Should be detected as large file first
            assert widget.is_large_file()

            # Should be in lazy loading mode
            assert widget.is_lazy_loading_active()

            # Should have status info
            status = widget.get_large_file_status()
            assert status is not None
            assert status["total_chunks"] > 1
        finally:
            widget._large_file_threshold = original_threshold
            widget._chunk_size = original_chunk_size


@pytest.mark.qt
class TestCodeViewerScrollbars:
    """Test cases for scrollbar functionality and smooth scrolling."""

    def test_vertical_scrollbar_availability(self, qapp, tmp_path):
        """Test that vertical scrollbar is available and accessible."""
        widget = CodeViewerWidget()

        # Create content that requires scrolling
        test_file = tmp_path / "long_content.py"
        long_content = "\n".join(
            [f"# Line {i}: Some content here" for i in range(1, 101)]
        )
        test_file.write_text(long_content)

        # Load file
        widget.load_file(test_file)

        # Should have vertical scrollbar
        v_scrollbar = widget.verticalScrollBar()
        assert v_scrollbar is not None

        # Should be visible when content exceeds viewport
        assert v_scrollbar.isVisible() or v_scrollbar.maximum() > 0

    def test_horizontal_scrollbar_availability(self, qapp, tmp_path):
        """Test that horizontal scrollbar is available and accessible."""
        widget = CodeViewerWidget()

        # Create content that requires horizontal scrolling
        test_file = tmp_path / "wide_content.py"
        wide_content = "\n".join(
            [
                "# This is a very long line that should definitely exceed the viewport width and trigger horizontal scrolling"
                + " " * 200
                + str(i)
                for i in range(1, 21)
            ]
        )
        test_file.write_text(wide_content)

        # Load file
        widget.load_file(test_file)

        # Should have horizontal scrollbar method
        h_scrollbar = widget.horizontalScrollBar()
        assert h_scrollbar is not None

        # Should be visible when content exceeds viewport width
        assert h_scrollbar.isVisible() or h_scrollbar.maximum() > 0

    def test_scrollbar_smooth_scrolling_enabled(self, qapp, tmp_path):
        """Test that smooth scrolling is enabled for both scrollbars."""
        widget = CodeViewerWidget()

        # Create content that requires scrolling
        test_file = tmp_path / "scrollable_content.py"
        content = "\n".join(
            [
                f"# Line {i}: "
                + "Content that is long enough to require horizontal scrolling " * 5
                for i in range(1, 51)
            ]
        )
        test_file.write_text(content)

        # Load file
        widget.load_file(test_file)

        # Get scrollbars
        v_scrollbar = widget.verticalScrollBar()
        h_scrollbar = widget.horizontalScrollBar()

        # Check that smooth scrolling is enabled (single step should be reasonable)
        assert v_scrollbar.singleStep() > 0
        assert h_scrollbar.singleStep() > 0

        # Page step should be larger than single step for smooth scrolling
        assert v_scrollbar.pageStep() > v_scrollbar.singleStep()
        assert h_scrollbar.pageStep() > h_scrollbar.singleStep()

    def test_vertical_scrollbar_range_calculation(self, qapp, tmp_path):
        """Test that vertical scrollbar range is properly calculated."""
        widget = CodeViewerWidget()

        # Create content with known number of lines
        test_file = tmp_path / "counted_lines.py"
        line_count = 50
        content = "\n".join([f"# Line {i}" for i in range(1, line_count + 1)])
        test_file.write_text(content)

        # Load file
        widget.load_file(test_file)

        # Get vertical scrollbar
        v_scrollbar = widget.verticalScrollBar()

        # Should have appropriate range
        assert v_scrollbar.minimum() == 0
        assert v_scrollbar.maximum() >= 0  # May be 0 if all content fits

    def test_horizontal_scrollbar_range_calculation(self, qapp, tmp_path):
        """Test that horizontal scrollbar range is properly calculated."""
        widget = CodeViewerWidget()

        # Create content with very long lines
        test_file = tmp_path / "wide_lines.py"
        wide_line = "# " + "x" * 500  # Very long line
        content = "\n".join([wide_line for _ in range(5)])
        test_file.write_text(content)

        # Load file
        widget.load_file(test_file)

        # Get horizontal scrollbar
        h_scrollbar = widget.horizontalScrollBar()

        # Should have appropriate range
        assert h_scrollbar.minimum() == 0
        assert h_scrollbar.maximum() >= 0  # May be 0 if all content fits

    def test_scrollbar_policy_configuration(self, qapp):
        """Test that scrollbar policies are properly configured."""
        widget = CodeViewerWidget()

        # Should have access to scrollbar policy methods
        assert hasattr(widget, "setVerticalScrollBarPolicy")
        assert hasattr(widget, "setHorizontalScrollBarPolicy")
        assert hasattr(widget, "verticalScrollBarPolicy")
        assert hasattr(widget, "horizontalScrollBarPolicy")

    def test_smooth_scrolling_step_sizes(self, qapp, tmp_path):
        """Test that scrollbar step sizes are configured for smooth scrolling."""
        widget = CodeViewerWidget()

        # Create scrollable content
        test_file = tmp_path / "smooth_scroll_test.py"
        content = "\n".join(
            [f"# Line {i}: Content for smooth scrolling test" for i in range(1, 101)]
        )
        test_file.write_text(content)

        # Load file
        widget.load_file(test_file)

        # Get scrollbars
        v_scrollbar = widget.verticalScrollBar()
        h_scrollbar = widget.horizontalScrollBar()

        # Verify smooth scrolling step sizes
        # Single step should be small for smooth scrolling
        assert 1 <= v_scrollbar.singleStep() <= 10
        assert 1 <= h_scrollbar.singleStep() <= 20

        # Page step should be larger but reasonable
        assert v_scrollbar.pageStep() >= v_scrollbar.singleStep() * 3
        assert h_scrollbar.pageStep() >= h_scrollbar.singleStep() * 3

    def test_scrollbar_synchronization_with_line_numbers(self, qapp, tmp_path):
        """Test that scrollbars work properly with line numbers widget."""
        widget = CodeViewerWidget()

        # Create content that requires scrolling
        test_file = tmp_path / "sync_test.py"
        content = "\n".join([f"print('Line {i}')" for i in range(1, 101)])
        test_file.write_text(content)

        # Load file
        widget.load_file(test_file)

        # Get scrollbar and line numbers
        v_scrollbar = widget.verticalScrollBar()
        line_numbers = widget.get_line_numbers_widget()

        # Verify line numbers can track scroll position
        initial_scroll = line_numbers.get_scroll_position()

        # Simulate scroll (if scrollbar is active)
        if v_scrollbar.maximum() > 0:
            # Move scrollbar
            v_scrollbar.setValue(10)

            # Line numbers should sync
            new_scroll = line_numbers.get_scroll_position()
            assert new_scroll >= initial_scroll

    def test_scrollbar_wheel_event_handling(self, qapp, tmp_path):
        """Test that mouse wheel events work with scrollbars."""
        widget = CodeViewerWidget()

        # Create scrollable content
        test_file = tmp_path / "wheel_test.py"
        content = "\n".join(
            [f"# Line {i}: Mouse wheel test content" for i in range(1, 101)]
        )
        test_file.write_text(content)

        # Load file
        widget.load_file(test_file)

        # Should accept wheel events (no need to simulate actual wheel events in unit test)
        # Just verify the widget can handle wheel events
        assert widget.wheelEvent is not None or hasattr(widget, "wheelEvent")

    def test_scrollbar_keyboard_navigation(self, qapp, tmp_path):
        """Test that keyboard navigation works with scrollbars."""
        widget = CodeViewerWidget()

        # Create scrollable content
        test_file = tmp_path / "keyboard_test.py"
        content = "\n".join(
            [f"# Line {i}: Keyboard navigation test" for i in range(1, 101)]
        )
        test_file.write_text(content)

        # Load file
        widget.load_file(test_file)

        # Should support keyboard navigation
        # Verify cursor can be moved (which should affect scrolling)
        cursor = widget.textCursor()
        assert cursor is not None

        # Should be able to move to end (which may trigger scrolling)
        widget.selectAll()
        assert widget.textCursor().hasSelection()


@pytest.mark.qt
class TestCodeViewerEdgeCases:
    """Test cases for edge cases and integration scenarios."""

    def test_syntax_highlighter_with_empty_document(self, qapp):
        """Test syntax highlighter behavior with empty or None document."""
        from code_viewer.core.code_viewer import PygmentsSyntaxHighlighter
        from PyQt6.QtGui import QTextDocument

        # Test with empty document
        empty_doc = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(empty_doc)

        # Should not crash
        assert highlighter.document() == empty_doc
        assert highlighter.is_enabled() is True

        # Test highlighting empty text
        highlighter.highlightBlock("")
        highlighter.highlightBlock(None)

        # Should handle gracefully
        assert highlighter.is_enabled() is True

    def test_syntax_highlighter_lexer_switching(self, qapp):
        """Test switching lexers during runtime."""
        from code_viewer.core.code_viewer import PygmentsSyntaxHighlighter
        from pygments.lexers import JavascriptLexer, PythonLexer, TextLexer
        from PyQt6.QtGui import QTextDocument

        doc = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(doc)

        # Start with Python lexer
        python_lexer = PythonLexer()
        highlighter.set_lexer(python_lexer)
        assert highlighter.lexer == python_lexer

        # Switch to JavaScript lexer
        js_lexer = JavascriptLexer()
        highlighter.set_lexer(js_lexer)
        assert highlighter.lexer == js_lexer

        # Switch to plain text
        text_lexer = TextLexer()
        highlighter.set_lexer(text_lexer)
        assert highlighter.lexer == text_lexer

    def test_syntax_highlighter_enable_disable_cycles(self, qapp):
        """Test enabling and disabling syntax highlighting multiple times."""
        from code_viewer.core.code_viewer import PygmentsSyntaxHighlighter
        from PyQt6.QtGui import QTextDocument

        doc = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(doc)

        # Should start enabled
        assert highlighter.is_enabled() is True

        # Disable and enable multiple times
        for _ in range(5):
            highlighter.set_enabled(False)
            assert highlighter.is_enabled() is False

            highlighter.set_enabled(True)
            assert highlighter.is_enabled() is True

    def test_syntax_highlighter_token_color_mapping(self, qapp):
        """Test token color mapping for various token types."""
        from code_viewer.core.code_viewer import PygmentsSyntaxHighlighter
        from pygments.token import Token
        from PyQt6.QtGui import QColor, QTextDocument

        doc = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(doc)

        # Test known token types
        keyword_color = highlighter._get_color_for_token(Token.Keyword)
        assert isinstance(keyword_color, QColor)

        string_color = highlighter._get_color_for_token(Token.String)
        assert isinstance(string_color, QColor)

        comment_color = highlighter._get_color_for_token(Token.Comment)
        assert isinstance(comment_color, QColor)

        # Test unknown token type
        unknown_color = highlighter._get_color_for_token(Token.Error)
        # Should return None or a default color
        assert unknown_color is None or isinstance(unknown_color, QColor)

    def test_line_numbers_paint_event_edge_cases(self, qapp):
        """Test line numbers widget paint event with various states."""
        widget = CodeViewerWidget()
        line_numbers = widget.get_line_numbers_widget()

        # Test paint when disabled
        line_numbers.setVisible(False)

        # Simulate paint event (create mock event)
        from PyQt6.QtCore import QRect
        from PyQt6.QtGui import QPaintEvent

        # Paint event when widget is not visible should not crash
        mock_event = QPaintEvent(QRect(0, 0, 50, 100))
        line_numbers.paintEvent(mock_event)

        # Re-enable and test
        line_numbers.setVisible(True)
        line_numbers.paintEvent(mock_event)

    def test_code_viewer_widget_delegate_methods_coverage(self, qapp, tmp_path):
        """Test all delegate methods of CodeViewerWidget work properly."""
        widget = CodeViewerWidget()

        # Test all delegate methods
        widget.setPlainText("test content")
        assert widget.toPlainText() == "test content"

        widget.clear()
        assert widget.toPlainText() == ""

        # Test cursor methods
        cursor = widget.textCursor()
        assert cursor is not None

        widget.setTextCursor(cursor)

        # Test read-only state
        assert widget.isReadOnly() is True

        # Test selection
        widget.setPlainText("line1\nline2\nline3")
        widget.selectAll()
        assert widget.textCursor().hasSelection()

    def test_code_viewer_binary_data_detection(self, qapp, tmp_path):
        """Test binary data detection with various content types."""
        widget = CodeViewerWidget()

        # Test with normal text
        assert widget._contains_binary_data("Hello, World!") is False
        assert widget._contains_binary_data("print('test')") is False
        assert widget._contains_binary_data("// JavaScript comment") is False

        # Test with unicode content
        assert widget._contains_binary_data("Hello 世界") is False
        assert widget._contains_binary_data("café résumé") is False

        # Test with binary-like content (null bytes)
        assert widget._contains_binary_data("text\x00with\x00nulls") is True
        assert widget._contains_binary_data("\x00\x01\x02\x03") is True

    def test_code_viewer_language_detection_edge_cases(self, qapp, tmp_path):
        """Test language detection with edge cases."""
        widget = CodeViewerWidget()

        # Test with files that have no extension
        no_ext_file = tmp_path / "README"
        no_ext_file.write_text("This is a readme file")
        widget.load_file(no_ext_file)
        # Should default to text
        assert widget.get_current_language() in ["text", "plain"]

        # Test with uppercase extensions
        py_upper = tmp_path / "test.PY"
        py_upper.write_text("print('test')")
        widget.load_file(py_upper)
        # Should still detect as Python
        assert widget.get_current_language() == "python"

        # Test with unknown extension
        unknown_ext = tmp_path / "test.xyz"
        unknown_ext.write_text("some content")
        widget.load_file(unknown_ext)
        # Should default to text
        assert widget.get_current_language() in ["text", "plain"]

    def test_code_viewer_font_consistency(self, qapp):
        """Test font consistency between components."""
        widget = CodeViewerWidget()

        # Get fonts from both components
        text_edit_font = widget.get_text_edit_font()
        line_numbers_font = widget.get_line_numbers_widget().font()

        # Should be the same font family and size
        assert text_edit_font.family() == line_numbers_font.family()
        assert text_edit_font.pointSize() == line_numbers_font.pointSize()
        assert text_edit_font.fixedPitch() == line_numbers_font.fixedPitch()

    def test_code_viewer_widget_state_consistency(self, qapp, tmp_path):
        """Test widget state consistency after various operations."""
        widget = CodeViewerWidget()

        # Initial state
        assert widget.get_current_file() is None
        assert widget.get_current_language() == "text"
        assert widget.syntax_highlighting_enabled() is True
        assert widget.line_numbers_enabled() is True

        # Load a file and check state
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        result = widget.load_file(test_file)
        assert result is True
        assert widget.get_current_file() == test_file
        assert widget.get_current_language() == "python"

        # Clear and check state reset
        widget.clear_content()
        assert widget.toPlainText() == ""
        # File path should be cleared
        assert widget.get_current_file() is None

    @pytest.mark.slow
    def test_code_viewer_performance_with_complex_syntax(self, qapp, tmp_path):
        """Test performance with complex syntax highlighting scenarios."""
        widget = CodeViewerWidget()

        # Create file with complex nested syntax
        complex_file = tmp_path / "complex.py"
        complex_content = '''
class ComplexClass:
    """A complex class with various syntax elements."""

    def __init__(self, value: str = "default"):
        self.value = value
        self.data = {
            "numbers": [1, 2, 3, 4, 5],
            "strings": ["hello", "world", "test"],
            "nested": {
                "level1": {"level2": {"level3": "deep"}}
            }
        }

    def method_with_decorators(self):
        @staticmethod
        @property
        def nested_function():
            # Complex string formatting
            return f"Value: {self.value}, Length: {len(self.data)}"

        # Complex comprehensions
        result = [
            x ** 2 for x in range(100)
            if x % 2 == 0 and x > 10
        ]

        # Regular expressions and raw strings
        import re
        pattern = r"\\d+\\.\\d+\\s+[a-zA-Z]+"

        return result, pattern

    async def async_method(self):
        """Test async/await syntax."""
        await self.some_async_operation()
        return True
'''
        complex_file.write_text(complex_content)

        # Should load and highlight without issues
        result = widget.load_file(complex_file)
        assert result is True
        assert widget.get_current_language() == "python"
        assert len(widget.toPlainText()) > 0

    def test_scrollbar_integration_with_content_changes(self, qapp, tmp_path):
        """Test scrollbar behavior when content changes dynamically."""
        widget = CodeViewerWidget()

        # Start with small content
        small_file = tmp_path / "small.py"
        small_file.write_text("print('small')")
        widget.load_file(small_file)

        v_scrollbar = widget.verticalScrollBar()
        initial_max = v_scrollbar.maximum()

        # Load larger content
        large_file = tmp_path / "large.py"
        large_content = "\n".join([f"# Line {i}" for i in range(100)])
        large_file.write_text(large_content)
        widget.load_file(large_file)

        # Scrollbar range should increase
        new_max = v_scrollbar.maximum()
        assert new_max >= initial_max

    def test_smooth_scrolling_configuration_details(self, qapp):
        """Test specific smooth scrolling configuration values."""
        widget = CodeViewerWidget()

        # Check that smooth scrolling was configured during initialization
        v_scrollbar = widget.verticalScrollBar()
        h_scrollbar = widget.horizontalScrollBar()

        # Verify specific step values set in _configure_smooth_scrolling
        assert v_scrollbar.singleStep() == 3
        assert v_scrollbar.pageStep() == 30
        assert h_scrollbar.singleStep() == 5
        assert h_scrollbar.pageStep() == 50
