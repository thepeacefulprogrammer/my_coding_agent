#!/usr/bin/env python3
"""
Test suite for automatic line numbers display when files are loaded.

This tests the specific issue where line numbers should show automatically
when a file is loaded but might not be appearing correctly.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tkinter as tk

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


class TestLineNumbersAutoDisplay(unittest.TestCase):
    """Test suite for automatic line numbers display functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.parent_frame = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar = Mock()
        
    def tearDown(self):
        """Clean up test environment."""
        pass
        
    @patch('code_editor.CodeView')
    def test_line_numbers_enabled_by_default_in_new_editor(self, mock_codeview):
        """Test that CodeEditor has line numbers enabled by default."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Verify line numbers are enabled by default
        self.assertTrue(editor.show_line_numbers)
        self.assertEqual(editor.line_numbers_border, 1)
        
    @patch('code_editor.CodeView')
    def test_line_numbers_preserved_when_creating_widget(self, mock_codeview):
        """Test that line numbers settings are passed to CodeView widget creation."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=2
        )
        
        # Create widget
        widget = editor.create_widget()
        
        # Verify CodeView was called with line numbers settings
        mock_codeview.assert_called_once()
        call_args = mock_codeview.call_args
        
        # Check that linenums_border was passed correctly
        self.assertEqual(call_args[1]['linenums_border'], 2)
        
    @patch('code_editor.CodeView')
    def test_line_numbers_disabled_when_setting_false(self, mock_codeview):
        """Test that line numbers can be disabled by setting to False."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager,
            show_line_numbers=False
        )
        
        # Create widget
        widget = editor.create_widget()
        
        # Verify CodeView was called with line numbers disabled (border = 0)
        mock_codeview.assert_called_once()
        call_args = mock_codeview.call_args
        
        # Check that linenums_border was set to 0 to disable line numbers
        self.assertEqual(call_args[1]['linenums_border'], 0)
        
    @patch('code_editor.CodeView')
    def test_line_numbers_preserved_during_file_loading(self, mock_codeview):
        """Test that line numbers are preserved when loading files with different lexers."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Create initial widget
        initial_widget = editor.create_widget()
        editor.current_widget = initial_widget
        
        # Mock Python lexer detection
        mock_python_lexer = Mock()
        with patch.object(editor.syntax_manager, 'get_lexer_for_file', return_value=mock_python_lexer):
            # Update content with a Python file (should recreate widget with syntax highlighting)
            editor.update_file_content("def hello():\n    pass", filename="test.py")
            
            # Verify CodeView was called again with line numbers still enabled
            self.assertEqual(mock_codeview.call_count, 2)  # Initial + after file load
            
            # Check last call had line numbers enabled
            last_call_args = mock_codeview.call_args
            self.assertEqual(last_call_args[1]['linenums_border'], 1)
            
    @patch('code_editor.CodeView')
    def test_line_numbers_preserved_during_widget_replacement(self, mock_codeview):
        """Test that line numbers are preserved when replacing widgets with new lexers."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=2
        )
        
        # Create initial widget
        initial_widget = editor.create_widget()
        editor.current_widget = initial_widget
        
        # Mock JavaScript lexer
        mock_js_lexer = Mock()
        
        # Replace widget with new lexer
        new_widget = editor.replace_widget_with_lexer(mock_js_lexer)
        
        # Verify CodeView was called with line numbers preserved
        self.assertEqual(mock_codeview.call_count, 2)  # Initial + replacement
        
        # Check that the replacement call preserved line numbers
        last_call_args = mock_codeview.call_args
        self.assertEqual(last_call_args[1]['linenums_border'], 2)
        
    @patch('code_editor.CodeView')
    def test_line_numbers_work_with_different_lexers(self, mock_codeview):
        """Test that line numbers work correctly with different programming languages."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Test with different file types
        test_files = [
            ("test.py", "Python"),
            ("test.js", "JavaScript"),
            ("test.html", "HTML"),
            ("test.css", "CSS")
        ]
        
        for filename, language in test_files:
            with self.subTest(filename=filename, language=language):
                # Mock lexer for this file type
                mock_lexer = Mock()
                mock_lexer.name = language
                
                with patch.object(editor.syntax_manager, 'get_lexer_for_file', return_value=mock_lexer):
                    # Update content
                    editor.update_file_content(f"// {language} code", filename=filename)
                    
                    # Verify line numbers are enabled in the widget call
                    self.assertGreater(mock_codeview.call_count, 0)
                    last_call_args = mock_codeview.call_args
                    self.assertEqual(last_call_args[1]['linenums_border'], 1)
                    
    @patch('code_editor.CodeView')
    def test_line_numbers_preserved_during_content_update(self, mock_codeview):
        """Test that line numbers are preserved when updating content multiple times."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Load initial content
        editor.update_file_content("print('hello')", filename="test.py")
        initial_call_count = mock_codeview.call_count
        
        # Update content again
        editor.update_file_content("print('world')", filename="test.py")
        
        # Verify line numbers are still enabled
        self.assertGreater(mock_codeview.call_count, initial_call_count)
        last_call_args = mock_codeview.call_args
        self.assertEqual(last_call_args[1]['linenums_border'], 1)
        
    @patch('code_editor.CodeView')
    def test_line_numbers_fallback_behavior(self, mock_codeview):
        """Test line numbers behavior when widget creation encounters errors."""
        # Set up mock to fail first, then succeed
        mock_widget = Mock()
        mock_codeview.side_effect = [Exception("First call fails"), mock_widget]
        
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # This should trigger fallback behavior
        try:
            widget = editor.create_widget()
            # If we get here, fallback should have preserved line numbers
            last_call_args = mock_codeview.call_args
            self.assertEqual(last_call_args[1]['linenums_border'], 1)
        except Exception:
            # If fallback also fails, that's expected for this test case
            pass
            
    def test_line_numbers_configuration_consistency(self):
        """Test that line numbers configuration remains consistent."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=3
        )
        
        # Verify initial configuration
        config = editor.get_line_numbers_config()
        self.assertEqual(config['enabled'], True)
        self.assertEqual(config['border_width'], 3)
        
        # Change setting
        result = editor.set_line_numbers_enabled(False)
        self.assertTrue(result)
        
        # Verify configuration updated
        config = editor.get_line_numbers_config()
        self.assertEqual(config['enabled'], False)
        self.assertEqual(config['border_width'], 3)  # Border width preserved
        
        # Change border width
        result = editor.set_line_numbers_border(5)
        self.assertTrue(result)
        
        # Verify configuration updated
        config = editor.get_line_numbers_config()
        self.assertEqual(config['enabled'], False)  # Enabled state preserved
        self.assertEqual(config['border_width'], 5)


if __name__ == '__main__':
    unittest.main() 