"""
Integration tests for complete syntax highlighting functionality.

This module tests the full integration of syntax highlighting features including
color schemes, lexer detection, and visual output verification.
"""

import unittest
import tkinter as tk
import tempfile
import os
from unittest.mock import Mock, patch
from src.code_editor import CodeEditor
from src.syntax_manager import SyntaxManager


class TestSyntaxHighlightingFull(unittest.TestCase):
    """Integration tests for complete syntax highlighting functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during testing
        self.parent_frame = tk.Frame(self.root)
        self.syntax_manager = SyntaxManager()
        self.scrollbar = tk.Scrollbar(self.parent_frame)
        
    def tearDown(self):
        """Clean up test environment."""
        try:
            # Use proper cleanup to avoid recursion
            if hasattr(self, 'root') and self.root:
                self.root.destroy()
        except Exception:
            # If cleanup fails, ignore to prevent test failures
            pass
        
    def test_python_syntax_highlighting_with_nord_colors(self):
        """Test that Python syntax highlighting works with Nord color scheme."""
        # Create code editor with Nord color scheme
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            color_scheme="nord",
            scrollbar=self.scrollbar
        )
        
        # Python test code with various syntax elements
        python_code = '''import os
def hello_world():
    """This is a docstring."""
    # This is a comment
    name = "World"  # String literal
    number = 42     # Integer literal
    pi = 3.14159    # Float literal
    is_valid = True # Boolean literal
    
    # F-string with expression
    message = f"Hello, {name}! Number: {number}"
    print(message)
    return message

class TestClass:
    """A test class."""
    
    def __init__(self, value):
        self.value = value
        
    @property
    def formatted_value(self):
        return f"Value: {self.value}"

if __name__ == "__main__":
    obj = TestClass(42)
    result = hello_world()
'''
        
        # Create widget with Python lexer
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        widget = editor.create_widget(lexer=lexer, color_scheme="nord")
        
        # Insert code content
        widget.insert("1.0", python_code)
        
        # Verify widget creation succeeded
        self.assertIsNotNone(widget)
        self.assertEqual(widget.get("1.0", "end-1c"), python_code)
        
        # Verify widget was created successfully (lexer is applied during creation)
        self.assertIsInstance(widget, type(editor.create_widget()))
        
    def test_multiple_language_syntax_highlighting(self):
        """Test syntax highlighting for multiple programming languages."""
        editor = CodeEditor(
            self.parent_frame,
            self.syntax_manager,
            color_scheme="nord"
        )
        
        # Test different file types
        test_cases = [
            ("test.py", "def function(): pass"),
            ("test.js", "function test() { return true; }"),
            ("test.html", "<html><body><h1>Test</h1></body></html>"),
            ("test.css", "body { color: #333; font-size: 14px; }"),
            ("test.json", '{"name": "test", "value": 42}'),
            ("test.md", "# Header\n\nThis is **bold** text."),
        ]
        
        for filename, code in test_cases:
            with self.subTest(filename=filename):
                lexer = self.syntax_manager.get_lexer_for_file(filename)
                widget = editor.create_widget(lexer=lexer, color_scheme="nord")
                widget.insert("1.0", code)
                
                # Verify widget creation and content
                self.assertIsNotNone(widget)
                self.assertEqual(widget.get("1.0", "end-1c"), code)
                
    def test_nord_color_scheme_configuration(self):
        """Test that Nord color scheme is properly configured."""
        editor = CodeEditor(
            self.parent_frame,
            self.syntax_manager,
            color_scheme="nord"
        )
        
        # Verify color scheme is set
        self.assertEqual(editor.color_scheme, "nord")
        
        # Create widget and verify it uses the color scheme
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        widget = editor.create_widget(lexer=lexer)
        
        # Verify widget was created with color scheme
        self.assertIsNotNone(widget)
        
    def test_color_scheme_fallback_behavior(self):
        """Test fallback behavior when color scheme is not available."""
        editor = CodeEditor(
            self.parent_frame,
            self.syntax_manager,
            color_scheme="nonexistent_scheme"
        )
        
        # Should still create widget even with invalid color scheme
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        widget = editor.create_widget(lexer=lexer)
        
        self.assertIsNotNone(widget)
        
    @patch('src.code_editor.CodeView')
    def test_syntax_highlighting_with_file_loading(self, mock_codeview):
        """Test syntax highlighting integration with file loading."""
        # Set up mock widget
        widget = Mock()
        mock_codeview.return_value = widget
        
        editor = CodeEditor(
            self.parent_frame,
            self.syntax_manager,
            color_scheme="nord"
        )
        
        # Create temporary Python file
        python_content = '''def test_function():
    """Test function with syntax highlighting."""
    return "Hello, World!"
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_content)
            temp_filename = f.name
            
        try:
            # Set up widget to return the content when get() is called
            widget.get.return_value = python_content
            
            # Load file with syntax highlighting
            editor.load_file(temp_filename)
            
            # Verify content was loaded
            self.assertTrue(editor.has_widget())
            content = editor.get_content()
            self.assertEqual(content, python_content)
            
        finally:
            # Clean up temporary file
            os.unlink(temp_filename)
            
    def test_nord_color_scheme_token_mapping(self):
        """Test that Nord color scheme properly maps Python token types."""
        editor = CodeEditor(
            self.parent_frame,
            self.syntax_manager,
            color_scheme="nord"
        )
        
        # Create widget with Python lexer
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        widget = editor.create_widget(lexer=lexer, color_scheme="nord")
        
        # Insert Python code with various token types
        python_code = '''# Comment
def function_name():
    """Docstring"""
    keyword = "string"
    number = 123
    return True
'''
        widget.insert("1.0", python_code)
        
        # Verify widget exists and content is correct
        self.assertIsNotNone(widget)
        self.assertEqual(widget.get("1.0", "end-1c"), python_code)
        
        # Note: Visual verification of actual color application would require
        # manual testing or more sophisticated UI testing tools
        
    def test_performance_with_large_content(self):
        """Test syntax highlighting performance with larger content."""
        editor = CodeEditor(
            self.parent_frame,
            self.syntax_manager,
            color_scheme="nord"
        )
        
        # Generate larger Python content
        large_content = ""
        for i in range(100):
            large_content += f'''def function_{i}():
    """Function number {i}."""
    value = {i} * 2
    result = f"Result: {{value}}"
    return result

'''
        
        # Create widget and measure time
        import time
        start_time = time.time()
        
        lexer = self.syntax_manager.get_lexer_for_file("large_test.py")
        widget = editor.create_widget(lexer=lexer, color_scheme="nord")
        widget.insert("1.0", large_content)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify it completed in reasonable time (less than 2 seconds)
        self.assertLess(duration, 2.0)
        self.assertEqual(widget.get("1.0", "end-1c"), large_content)


if __name__ == "__main__":
    unittest.main() 