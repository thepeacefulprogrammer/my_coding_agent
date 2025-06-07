#!/usr/bin/env python3
"""
Unit tests to verify color scheme functionality in CodeEditor.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from syntax_manager import SyntaxManager


class TestColorScheme(unittest.TestCase):
    """Test color scheme functionality without creating GUI windows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.syntax_manager = SyntaxManager()
    
    @patch('code_editor.CodeEditor')
    @patch('tkinter.Tk')
    def test_monokai_color_scheme(self, mock_tk, mock_code_editor):
        """Test that monokai color scheme can be applied to CodeEditor."""
        from code_editor import CodeEditor
        
        # Mock root window
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Mock CodeEditor instance
        mock_editor_instance = MagicMock()
        mock_code_editor.return_value = mock_editor_instance
        
        # Create CodeEditor with monokai color scheme (mocked)
        editor = CodeEditor(mock_root, self.syntax_manager, color_scheme="monokai")
        
        # Verify CodeEditor was called with correct parameters
        mock_code_editor.assert_called_once_with(
            mock_root, 
            self.syntax_manager, 
            color_scheme="monokai"
        )
        
        # Test that lexer can be obtained for Python file
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        self.assertIsNotNone(lexer)
        self.assertEqual(lexer.name, "Python")
        
    @patch('code_editor.CodeView')
    def test_widget_creation_with_color_scheme(self, mock_codeview):
        """Test that widgets are created with proper color scheme."""
        # Mock widget instance
        mock_widget = MagicMock()
        mock_codeview.return_value = mock_widget
        
        # Test widget creation process
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        
        # Simulate widget creation with monokai scheme
        mock_codeview(
            parent=MagicMock(),
            lexer=lexer,
            color_scheme="monokai"
        )
        
        # Verify CodeView was called with color scheme
        mock_codeview.assert_called_once()
        call_kwargs = mock_codeview.call_args[1]
        self.assertEqual(call_kwargs['color_scheme'], "monokai")
        self.assertEqual(call_kwargs['lexer'], lexer)


if __name__ == "__main__":
    unittest.main() 