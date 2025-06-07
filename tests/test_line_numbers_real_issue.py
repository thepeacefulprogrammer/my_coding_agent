#!/usr/bin/env python3
"""
Test to identify the real line numbers issue in practice.

This test will help identify if line numbers are actually showing when files are loaded.
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


class TestLineNumbersRealIssue(unittest.TestCase):
    """Test suite to identify the real line numbers issue."""
    
    def setUp(self):
        """Set up test environment."""
        self.syntax_manager = SyntaxManager()
        
    def tearDown(self):
        """Clean up test environment."""
        pass
        
    @patch('code_editor.CodeView')
    def test_line_numbers_in_widget_creation_calls(self, mock_codeview):
        """Test that line numbers are actually passed to widget creation."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create parent mock that won't cause arithmetic issues
        parent_frame = Mock()
        parent_frame._last_child_ids = {}
        
        # Create CodeEditor with line numbers enabled
        editor = CodeEditor(
            parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Create widget and check parameters
        widget = editor.create_widget()
        
        # Verify CodeView was called with correct line numbers parameter
        mock_codeview.assert_called_once()
        call_kwargs = mock_codeview.call_args[1]
        
        print(f"Widget creation kwargs: {call_kwargs}")
        
        # Check that linenums_border is set correctly
        self.assertIn('linenums_border', call_kwargs)
        self.assertEqual(call_kwargs['linenums_border'], 1)
        
    @patch('code_editor.CodeView')
    def test_line_numbers_disabled_when_false(self, mock_codeview):
        """Test that line numbers are disabled when set to False."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create parent mock that won't cause arithmetic issues
        parent_frame = Mock()
        parent_frame._last_child_ids = {}
        
        # Create CodeEditor with line numbers disabled
        editor = CodeEditor(
            parent_frame, 
            self.syntax_manager,
            show_line_numbers=False,
            line_numbers_border=1
        )
        
        # Create widget and check parameters
        widget = editor.create_widget()
        
        # Verify CodeView was called with line numbers disabled
        mock_codeview.assert_called_once()
        call_kwargs = mock_codeview.call_args[1]
        
        print(f"Widget creation kwargs (disabled): {call_kwargs}")
        
        # Check that linenums_border is set to 0 (disabled)
        self.assertIn('linenums_border', call_kwargs)
        self.assertEqual(call_kwargs['linenums_border'], 0)
        
    @patch('code_editor.CodeView')
    def test_line_numbers_preserved_during_lexer_replacement(self, mock_codeview):
        """Test that line numbers are preserved when replacing widget with new lexer."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create parent mock that won't cause arithmetic issues
        parent_frame = Mock()
        parent_frame._last_child_ids = {}
        
        # Create CodeEditor with line numbers enabled
        editor = CodeEditor(
            parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=2
        )
        
        # Set up initial widget
        initial_widget = editor.create_widget()
        editor.current_widget = initial_widget
        
        # Mock a Python lexer
        mock_lexer = Mock()
        mock_lexer.name = "Python"
        
        # Replace widget with new lexer
        new_widget = editor.replace_widget_with_lexer(mock_lexer)
        
        # Check that all CodeView calls had line numbers enabled
        self.assertEqual(mock_codeview.call_count, 2)  # Initial + replacement
        
        for call in mock_codeview.call_args_list:
            call_kwargs = call[1]
            print(f"CodeView call kwargs: {call_kwargs}")
            self.assertIn('linenums_border', call_kwargs)
            self.assertEqual(call_kwargs['linenums_border'], 2)
            
    @patch('code_editor.CodeView')
    def test_line_numbers_with_file_content_update(self, mock_codeview):
        """Test that line numbers work when updating file content."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create parent mock that won't cause arithmetic issues
        parent_frame = Mock()
        parent_frame._last_child_ids = {}
        
        # Create CodeEditor with line numbers enabled
        editor = CodeEditor(
            parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Update file content with a Python file
        python_content = "def hello():\n    print('Hello, World!')\n    return 42"
        widget = editor.update_file_content(python_content, filename="test.py")
        
        # Verify widget was created/updated
        self.assertIsNotNone(widget)
        
        # Check that CodeView was called with line numbers enabled
        self.assertGreater(mock_codeview.call_count, 0)
        
        # Check the most recent call
        last_call_kwargs = mock_codeview.call_args[1]
        print(f"File content update kwargs: {last_call_kwargs}")
        
        self.assertIn('linenums_border', last_call_kwargs)
        self.assertEqual(last_call_kwargs['linenums_border'], 1)
        
    def test_line_numbers_configuration_methods(self):
        """Test line numbers configuration methods work correctly."""
        # Create parent mock that won't cause arithmetic issues
        parent_frame = Mock()
        parent_frame._last_child_ids = {}
        
        # Create CodeEditor with line numbers enabled
        editor = CodeEditor(
            parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Test getting configuration
        config = editor.get_line_numbers_config()
        self.assertEqual(config['enabled'], True)
        self.assertEqual(config['border_width'], 1)
        
        # Test setting enabled state
        result = editor.set_line_numbers_enabled(False)
        self.assertTrue(result)
        
        config = editor.get_line_numbers_config()
        self.assertEqual(config['enabled'], False)
        self.assertEqual(config['border_width'], 1)
        
        # Test setting border width
        result = editor.set_line_numbers_border(3)
        self.assertTrue(result)
        
        config = editor.get_line_numbers_config()
        self.assertEqual(config['enabled'], False)
        self.assertEqual(config['border_width'], 3)
        
    def test_line_numbers_issue_investigation(self):
        """Investigate the specific line numbers display issue."""
        print("\n=== Line Numbers Issue Investigation ===")
        
        # Create parent mock that won't cause arithmetic issues
        parent_frame = Mock()
        parent_frame._last_child_ids = {}
        
        # Create CodeEditor as GUI would
        editor = CodeEditor(
            parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1,
            color_scheme="monokai"
        )
        
        print(f"CodeEditor initialized with line numbers: {editor.show_line_numbers}")
        print(f"Line numbers border width: {editor.line_numbers_border}")
        
        # Check if the issue is in the default widget creation
        with patch('code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            # Create initial widget
            widget = editor.create_widget()
            
            print(f"Initial widget creation called: {mock_codeview.called}")
            if mock_codeview.called:
                call_kwargs = mock_codeview.call_args[1]
                print(f"Initial widget kwargs: {call_kwargs}")
                print(f"linenums_border in kwargs: {'linenums_border' in call_kwargs}")
                if 'linenums_border' in call_kwargs:
                    print(f"linenums_border value: {call_kwargs['linenums_border']}")
        
        # Test the specific scenario: loading a file
        with patch('code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            # Load content like GUI would do
            content = "def test():\n    pass\n"
            widget = editor.update_file_content(content, filename="test.py")
            
            print(f"File loading widget creation calls: {mock_codeview.call_count}")
            if mock_codeview.call_count > 0:
                for i, call in enumerate(mock_codeview.call_args_list):
                    call_kwargs = call[1]
                    print(f"Call {i+1} kwargs: {call_kwargs}")
                    print(f"Call {i+1} linenums_border: {call_kwargs.get('linenums_border', 'NOT SET')}")
        
        print("=== End Investigation ===\n")


if __name__ == '__main__':
    unittest.main() 