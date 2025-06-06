"""
Unit tests for Nord color scheme application to Python syntax highlighting.

This module tests that the Nord color scheme is properly applied to Python code
syntax elements through the CodeEditor and SyntaxManager integration.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from color_schemes import get_nord_color_scheme, NORD0, NORD3, NORD6, NORD7, NORD8, NORD9, NORD11, NORD12, NORD13, NORD14, NORD15
from syntax_manager import SyntaxManager
from code_editor import CodeEditor


class TestNordPythonSyntax(unittest.TestCase):
    """Test Nord color scheme application to Python syntax elements."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.syntax_manager = SyntaxManager()
        
        # Mock parent widget for CodeEditor
        self.mock_parent = MagicMock()
        
        # Create CodeEditor with Nord color scheme
        self.code_editor = CodeEditor(
            parent=self.mock_parent,
            syntax_manager=self.syntax_manager,
            color_scheme="nord"
        )
        
    def test_nord_color_scheme_availability(self):
        """Test that Nord color scheme is available and properly structured."""
        nord_scheme = get_nord_color_scheme()
        
        # Verify it's a dictionary with required sections
        self.assertIsInstance(nord_scheme, dict)
        
        # Test essential sections for Python syntax
        required_sections = ['editor', 'general', 'keyword', 'name', 'string', 'number', 'comment']
        for section in required_sections:
            self.assertIn(section, nord_scheme)
            
        # Test specific Python-relevant color mappings
        self.assertEqual(nord_scheme['general']['comment'], NORD3)  # Comments
        self.assertEqual(nord_scheme['general']['keyword'], NORD9)  # Keywords  
        self.assertEqual(nord_scheme['general']['string'], NORD14)  # Strings
        self.assertEqual(nord_scheme['name']['function'], NORD8)    # Functions
        self.assertEqual(nord_scheme['name']['class'], NORD7)       # Classes (using calm blue NORD7)
        self.assertEqual(nord_scheme['number']['integer'], NORD15)  # Numbers
        
    def test_python_lexer_detection(self):
        """Test that Python lexer is correctly detected for Python files."""
        # Test .py extension
        python_lexer = self.syntax_manager.get_lexer_for_file("test.py")
        self.assertIsNotNone(python_lexer)
        self.assertEqual(python_lexer.name, "Python")
        
    def test_code_editor_nord_initialization(self):
        """Test that CodeEditor properly initializes with Nord color scheme."""
        self.assertEqual(self.code_editor.color_scheme, "nord")
        
        # Test that Nord scheme is recognized as custom scheme
        from color_schemes import get_color_scheme
        nord_scheme = get_color_scheme("nord")
        self.assertIsNotNone(nord_scheme)
        
    @patch('code_editor.CodeView')
    def test_widget_creation_with_nord_scheme(self, mock_codeview):
        """Test that CodeView widget is created with Nord color scheme."""
        # Get Python lexer
        python_lexer = self.syntax_manager.get_lexer_for_file("test.py")
        
        # Create widget with Python lexer
        self.code_editor.create_widget(lexer=python_lexer)
        
        # Verify CodeView was called with Nord scheme
        mock_codeview.assert_called_once()
        call_args, call_kwargs = mock_codeview.call_args
        
        # Should have lexer and color scheme
        self.assertEqual(call_kwargs['lexer'], python_lexer)
        self.assertIn('color_scheme', call_kwargs)
        
        # Color scheme should be the Nord scheme dictionary
        nord_scheme = get_nord_color_scheme()
        self.assertEqual(call_kwargs['color_scheme'], nord_scheme)
        
    def test_python_syntax_color_mapping(self):
        """Test that Python syntax elements map to correct Nord colors."""
        nord_scheme = get_nord_color_scheme()
        
        # Test keyword colors (if, def, class, import, etc.)
        self.assertEqual(nord_scheme['keyword']['declaration'], NORD9)  # def, class
        self.assertEqual(nord_scheme['keyword']['reserved'], NORD9)     # if, else, for
        self.assertEqual(nord_scheme['general']['keyword'], NORD9)      # General keywords
        
        # Test name colors (functions, classes, variables)
        self.assertEqual(nord_scheme['name']['function'], NORD8)        # Function names
        self.assertEqual(nord_scheme['name']['class'], NORD7)           # Class names (calm blue)
        self.assertEqual(nord_scheme['name']['builtin'], NORD8)         # Built-in functions
        
        # Test string colors
        self.assertEqual(nord_scheme['string']['single'], NORD14)       # Single quotes
        self.assertEqual(nord_scheme['string']['double'], NORD14)       # Double quotes
        self.assertEqual(nord_scheme['string']['doc'], NORD3)           # Docstrings (subtle)
        
        # Test number colors
        self.assertEqual(nord_scheme['number']['integer'], NORD15)      # Integers
        self.assertEqual(nord_scheme['number']['float'], NORD15)        # Floats
        
        # Test comment colors
        self.assertEqual(nord_scheme['comment']['single'], NORD3)       # # comments
        self.assertEqual(nord_scheme['comment']['hashbang'], NORD3)     # Shebang lines
        
        # Test decorator colors
        self.assertEqual(nord_scheme['name']['decorator'], NORD12)      # @property, etc.
        
    def test_nord_python_color_contrast(self):
        """Test that Nord colors provide good contrast for Python syntax."""
        nord_scheme = get_nord_color_scheme()
        
        # Background should be dark
        bg_color = nord_scheme['editor']['bg']
        self.assertEqual(bg_color, NORD0)  # Dark background
        
        # Text should be light for good contrast
        fg_color = nord_scheme['editor']['fg']
        self.assertEqual(fg_color, NORD6)  # Bright text
        
        # Comments should be subtle but readable
        comment_color = nord_scheme['comment']['single']
        self.assertEqual(comment_color, NORD3)  # Subtle gray
        
        # Keywords should be prominent
        keyword_color = nord_scheme['keyword']['declaration']
        self.assertEqual(keyword_color, NORD9)  # Blue
        
        # Strings should be distinctive
        string_color = nord_scheme['string']['double']
        self.assertEqual(string_color, NORD14)  # Green
        
    def test_python_specific_syntax_elements(self):
        """Test that Python-specific syntax elements have appropriate colors."""
        nord_scheme = get_nord_color_scheme()
        
        # Test f-string and string interpolation
        self.assertEqual(nord_scheme['string']['interpol'], NORD13)     # Yellow
        
        # Test magic methods (__init__, __str__, etc.)
        self.assertEqual(nord_scheme['name']['magic_function'], NORD8)  # Bright blue
        
        # Test exceptions
        self.assertEqual(nord_scheme['name']['exception'], NORD11)      # Red
        
        # Test decorators (@property, @staticmethod, etc.)
        self.assertEqual(nord_scheme['name']['decorator'], NORD12)      # Orange
        
        # Test constants (CONSTANT_VALUE, etc.)
        self.assertEqual(nord_scheme['name']['constant'], NORD15)       # Purple
        
    @patch('code_editor.CodeView')
    def test_fallback_color_scheme_handling(self, mock_codeview):
        """Test that fallback works if Nord scheme fails to load."""
        # Mock CodeView to raise an exception on first call (simulating color scheme error)
        mock_codeview.side_effect = [
            Exception("color scheme error"),  # First call fails
            MagicMock()  # Second call succeeds with fallback
        ]
        
        # Try to create widget - should fallback to monokai
        python_lexer = self.syntax_manager.get_lexer_for_file("test.py")
        widget = self.code_editor.create_widget(lexer=python_lexer)
        
        # Should have been called twice (once failing, once succeeding)
        self.assertEqual(mock_codeview.call_count, 2)
        
        # Second call should use fallback scheme
        second_call_kwargs = mock_codeview.call_args[1]
        self.assertEqual(second_call_kwargs['color_scheme'], "monokai")


if __name__ == "__main__":
    unittest.main()
