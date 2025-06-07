"""Test module to verify required dependencies are available.

This test ensures that PyQt6 and Pygments are properly installed
and can be imported for the code viewer application.
"""

import pytest


def test_pyqt6_available() -> None:
    """Test that PyQt6 is available and can be imported.
    
    This test verifies that the PyQt6 GUI framework is properly
    installed and its core modules can be imported.
    """
    try:
        import PyQt6.QtWidgets
        import PyQt6.QtCore
        import PyQt6.QtGui
        # If we get here, PyQt6 is available
        assert True
    except ImportError as e:
        pytest.fail(f"PyQt6 not available: {e}")


def test_pygments_available() -> None:
    """Test that Pygments is available and can be imported.
    
    This test verifies that the Pygments syntax highlighting
    library is properly installed and functional.
    """
    try:
        import pygments
        from pygments.lexers import get_lexer_by_name
        from pygments.formatters import get_formatter_by_name
        
        # Test that we can get lexers for our target languages
        python_lexer = get_lexer_by_name("python")
        javascript_lexer = get_lexer_by_name("javascript")
        
        # Test that we can get a formatter
        html_formatter = get_formatter_by_name("html")
        
        assert python_lexer is not None
        assert javascript_lexer is not None
        assert html_formatter is not None
        
    except ImportError as e:
        pytest.fail(f"Pygments not available: {e}")
    except Exception as e:
        pytest.fail(f"Pygments functionality test failed: {e}")


def test_pygments_syntax_highlighting() -> None:
    """Test that Pygments can perform basic syntax highlighting.
    
    This test verifies that Pygments can actually highlight code,
    not just that it's importable.
    """
    try:
        from pygments import highlight
        from pygments.lexers import PythonLexer
        from pygments.formatters import HtmlFormatter
        
        code = "def hello():\n    print('Hello, World!')"
        lexer = PythonLexer()
        formatter = HtmlFormatter()
        
        result = highlight(code, lexer, formatter)
        
        # Should contain HTML tags indicating syntax highlighting
        assert "<span" in result
        assert "hello" in result
        assert "print" in result
        
    except Exception as e:
        pytest.fail(f"Pygments syntax highlighting test failed: {e}") 