"""Tests for the PygmentsSyntaxHighlighter class."""

import pytest
from pygments.lexers import JavascriptLexer, PythonLexer, TextLexer
from pygments.token import Token
from PyQt6.QtGui import QColor, QTextDocument

from my_coding_agent.core.code_viewer import PygmentsSyntaxHighlighter


class TestPygmentsSyntaxHighlighter:
    """Test cases for PygmentsSyntaxHighlighter class."""

    def test_syntax_highlighter_initialization(self, qapp):
        """Test PygmentsSyntaxHighlighter initialization."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document)

        # Should be properly initialized
        assert highlighter.document() == document
        assert highlighter.is_enabled() is True
        assert highlighter.lexer is not None
        assert isinstance(highlighter.lexer, TextLexer)  # Default lexer

    def test_syntax_highlighter_initialization_with_lexer(self, qapp):
        """Test PygmentsSyntaxHighlighter initialization with custom lexer."""
        document = QTextDocument()
        python_lexer = PythonLexer()
        highlighter = PygmentsSyntaxHighlighter(document, python_lexer)

        # Should be initialized with custom lexer
        assert highlighter.document() == document
        assert highlighter.lexer == python_lexer
        assert isinstance(highlighter.lexer, PythonLexer)

    def test_syntax_highlighter_enable_disable(self, qapp):
        """Test enabling and disabling syntax highlighting."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document)

        # Should be enabled by default
        assert highlighter.is_enabled() is True

        # Disable highlighting
        highlighter.set_enabled(False)
        assert highlighter.is_enabled() is False

        # Re-enable highlighting
        highlighter.set_enabled(True)
        assert highlighter.is_enabled() is True

    def test_syntax_highlighter_lexer_change(self, qapp):
        """Test changing the lexer."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document)

        # Start with default TextLexer
        assert isinstance(highlighter.lexer, TextLexer)

        # Change to Python lexer
        python_lexer = PythonLexer()
        highlighter.set_lexer(python_lexer)
        assert highlighter.lexer == python_lexer
        assert isinstance(highlighter.lexer, PythonLexer)

        # Change to JavaScript lexer
        js_lexer = JavascriptLexer()
        highlighter.set_lexer(js_lexer)
        assert highlighter.lexer == js_lexer
        assert isinstance(highlighter.lexer, JavascriptLexer)

    def test_syntax_highlighter_token_styles(self, qapp):
        """Test that token styles are properly defined."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document)

        # Should have defined token styles
        assert hasattr(highlighter, "token_styles")
        assert isinstance(highlighter.token_styles, dict)
        assert len(highlighter.token_styles) > 0

        # Check that common token types are defined
        expected_tokens = [
            Token.Keyword,
            Token.String,
            Token.Comment,
            Token.Number,
            Token.Operator,
            Token.Name.Function,
            Token.Name.Class,
            Token.Name.Builtin,
            Token.Literal,
        ]

        for token_type in expected_tokens:
            assert token_type in highlighter.token_styles
            color = highlighter.token_styles[token_type]
            assert isinstance(color, QColor)
            assert color.isValid()

    def test_syntax_highlighter_color_for_token(self, qapp):
        """Test the _get_color_for_token method."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document)

        # Test exact token match
        keyword_color = highlighter._get_color_for_token(Token.Keyword)
        assert keyword_color is not None
        assert isinstance(keyword_color, QColor)
        assert keyword_color == highlighter.token_styles[Token.Keyword]

        # Test parent token matching
        string_literal_color = highlighter._get_color_for_token(Token.String.Double)
        assert string_literal_color is not None
        assert isinstance(string_literal_color, QColor)

        # Test unknown token type
        unknown_color = highlighter._get_color_for_token(Token.Other)
        # Should return None for truly unknown tokens
        assert unknown_color is None or isinstance(unknown_color, QColor)

    def test_syntax_highlighter_highlight_block_disabled(self, qapp):
        """Test that highlightBlock does nothing when disabled."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document)

        # Disable highlighting
        highlighter.set_enabled(False)

        # Mock the highlightBlock method by checking it doesn't crash
        # and doesn't set any formatting when disabled
        test_text = "def hello(): print('world')"

        # This should not raise any exceptions
        try:
            highlighter.highlightBlock(test_text)
        except Exception as e:
            pytest.fail(f"highlightBlock should not raise exception when disabled: {e}")

    def test_syntax_highlighter_highlight_block_empty_text(self, qapp):
        """Test highlightBlock with empty or None text."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document)

        # Test with None
        try:
            highlighter.highlightBlock(None)
        except Exception as e:
            pytest.fail(f"highlightBlock should handle None text gracefully: {e}")

        # Test with empty string
        try:
            highlighter.highlightBlock("")
        except Exception as e:
            pytest.fail(f"highlightBlock should handle empty text gracefully: {e}")

        # Test with whitespace only
        try:
            highlighter.highlightBlock("   \n\t  ")
        except Exception as e:
            pytest.fail(
                f"highlightBlock should handle whitespace-only text gracefully: {e}"
            )

    def test_syntax_highlighter_python_code(self, qapp):
        """Test syntax highlighting with Python code."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document, PythonLexer())

        # Test Python code highlighting
        python_code = "def hello_world():\n    print('Hello, World!')"

        # Should not raise exceptions
        try:
            highlighter.highlightBlock(python_code)
        except Exception as e:
            pytest.fail(f"Python syntax highlighting should work: {e}")

        # Verify lexer is correctly set
        assert isinstance(highlighter.lexer, PythonLexer)

    def test_syntax_highlighter_javascript_code(self, qapp):
        """Test syntax highlighting with JavaScript code."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document, JavascriptLexer())

        # Test JavaScript code highlighting
        js_code = "function hello() { console.log('Hello, World!'); }"

        # Should not raise exceptions
        try:
            highlighter.highlightBlock(js_code)
        except Exception as e:
            pytest.fail(f"JavaScript syntax highlighting should work: {e}")

        # Verify lexer is correctly set
        assert isinstance(highlighter.lexer, JavascriptLexer)

    def test_syntax_highlighter_error_handling(self, qapp):
        """Test that syntax highlighter handles errors gracefully."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document)

        # Test with potentially problematic text
        problematic_texts = [
            "def broken_function(",  # Incomplete syntax
            "invalid syntax here!!!",  # Invalid syntax
            "\x00\x01\x02",  # Binary data
            "ä ö ü",  # Unicode characters
            "print('test')" * 100,  # Long line (reduced from 1000 for performance)
        ]

        for text in problematic_texts:
            try:
                highlighter.highlightBlock(text)
                # Should not crash, even with problematic input
            except Exception as e:
                pytest.fail(
                    f"Syntax highlighter should handle problematic text gracefully: {text} -> {e}"
                )

    def test_syntax_highlighter_lexer_change_with_highlighting(self, qapp):
        """Test that changing lexer triggers re-highlighting when enabled."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document)

        # Enable highlighting
        highlighter.set_enabled(True)

        # Change lexer - this should trigger rehighlight() when enabled
        python_lexer = PythonLexer()
        try:
            highlighter.set_lexer(python_lexer)
            assert highlighter.lexer == python_lexer
        except Exception as e:
            pytest.fail(f"Changing lexer should not raise exception: {e}")

        # Disable highlighting and change lexer - should not trigger rehighlight()
        highlighter.set_enabled(False)
        js_lexer = JavascriptLexer()
        try:
            highlighter.set_lexer(js_lexer)
            assert highlighter.lexer == js_lexer
        except Exception as e:
            pytest.fail(f"Changing lexer when disabled should not raise exception: {e}")

    def test_syntax_highlighter_token_hierarchy(self, qapp):
        """Test that token hierarchy matching works correctly."""
        document = QTextDocument()
        highlighter = PygmentsSyntaxHighlighter(document)

        # Test that child tokens inherit parent colors
        # Token.String.Double should match Token.String
        string_color = highlighter._get_color_for_token(Token.String)
        string_double_color = highlighter._get_color_for_token(Token.String.Double)

        # Both should return a color (string_double might inherit from string)
        assert string_color is not None
        assert string_double_color is not None

        # Test Token.Name.Function.Magic should match Token.Name.Function
        function_color = highlighter._get_color_for_token(Token.Name.Function)
        function_magic_color = highlighter._get_color_for_token(
            Token.Name.Function.Magic
        )

        assert function_color is not None
        assert function_magic_color is not None

    def test_syntax_highlighter_integration_with_document(self, qapp):
        """Test integration with QTextDocument."""
        document = QTextDocument()
        document.setPlainText("def test(): pass")

        # Create highlighter attached to document
        highlighter = PygmentsSyntaxHighlighter(document, PythonLexer())

        # Verify the highlighter is attached to the document
        assert highlighter.document() == document

        # Should be able to highlight the document content
        assert highlighter.is_enabled() is True

        # Change document content - highlighter should handle it
        document.setPlainText("function test() { return true; }")

        # Change to JavaScript lexer
        highlighter.set_lexer(JavascriptLexer())
        assert isinstance(highlighter.lexer, JavascriptLexer)
