#!/usr/bin/env python3
"""
Test to verify that the line numbers fix works correctly.

This test verifies that the GUI now properly preserves line numbers 
when loading files through the update_file_content method.
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


class TestLineNumbersFixVerification(unittest.TestCase):
    """Test suite to verify the line numbers fix works correctly."""
    
    def setUp(self):
        """Set up test environment."""
        self.syntax_manager = SyntaxManager()
        
    def tearDown(self):
        """Clean up test environment."""
        pass
        
    @patch('code_editor.CodeView')
    def test_gui_fixed_update_file_content_preserves_line_numbers(self, mock_codeview):
        """Test that the fixed GUI update_file_content preserves line numbers."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create parent mock that won't cause arithmetic issues
        parent_frame = Mock()
        parent_frame._last_child_ids = {}
        
        # Create CodeEditor with line numbers enabled (as GUI does)
        editor = CodeEditor(
            parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1,
            color_scheme="monokai"
        )
        
        # Test the CodeEditor's update_file_content method (which GUI now uses)
        test_content = "def hello():\n    print('Hello, World!')\n    return 42"
        widget = editor.update_file_content(test_content, filename="test.py")
        
        # Verify that CodeView was called with line numbers enabled
        self.assertGreater(mock_codeview.call_count, 0)
        
        # Check that all calls had line numbers enabled
        for call in mock_codeview.call_args_list:
            call_kwargs = call[1]
            print(f"CodeView call kwargs: {call_kwargs}")
            self.assertIn('linenums_border', call_kwargs)
            self.assertEqual(call_kwargs['linenums_border'], 1)
        
        # Verify that a widget was returned
        self.assertIsNotNone(widget)
        
    @patch('code_editor.CodeView')
    def test_multiple_file_loads_with_different_languages(self, mock_codeview):
        """Test that line numbers are preserved across multiple file loads with different languages."""
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
        
        # Test loading different file types
        test_files = [
            ("print('Python code')", "test.py"),
            ("console.log('JavaScript');", "test.js"),
            ("<html><body>HTML</body></html>", "test.html"),
            ("body { color: red; }", "test.css"),
            ("# Python again", "another.py")
        ]
        
        for content, filename in test_files:
            with self.subTest(filename=filename):
                # Reset call count to track this specific call
                initial_count = mock_codeview.call_count
                
                # Load file content
                widget = editor.update_file_content(content, filename=filename)
                
                # Verify widget was returned
                self.assertIsNotNone(widget)
                
                # Verify new CodeView calls were made
                self.assertGreater(mock_codeview.call_count, initial_count)
                
                # Check that the most recent call had line numbers enabled
                last_call_kwargs = mock_codeview.call_args[1]
                self.assertIn('linenums_border', last_call_kwargs)
                self.assertEqual(last_call_kwargs['linenums_border'], 1)
                
    @patch('code_editor.CodeView')
    def test_line_numbers_with_custom_border_width(self, mock_codeview):
        """Test that custom line numbers border width is preserved."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create parent mock that won't cause arithmetic issues
        parent_frame = Mock()
        parent_frame._last_child_ids = {}
        
        # Create CodeEditor with custom border width
        editor = CodeEditor(
            parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=3  # Custom border width
        )
        
        # Load file content
        content = "def test():\n    pass"
        widget = editor.update_file_content(content, filename="test.py")
        
        # Verify that CodeView was called with custom border width
        self.assertGreater(mock_codeview.call_count, 0)
        
        # Check that the call had the correct custom border width
        last_call_kwargs = mock_codeview.call_args[1]
        self.assertIn('linenums_border', last_call_kwargs)
        self.assertEqual(last_call_kwargs['linenums_border'], 3)
        
    @patch('code_editor.CodeView')
    def test_line_numbers_disabled_when_setting_false(self, mock_codeview):
        """Test that line numbers can be disabled and stay disabled."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create parent mock that won't cause arithmetic issues
        parent_frame = Mock()
        parent_frame._last_child_ids = {}
        
        # Create CodeEditor with line numbers disabled
        editor = CodeEditor(
            parent_frame, 
            self.syntax_manager,
            show_line_numbers=False
        )
        
        # Load file content
        content = "def test():\n    pass"
        widget = editor.update_file_content(content, filename="test.py")
        
        # Verify that CodeView was called with line numbers disabled
        self.assertGreater(mock_codeview.call_count, 0)
        
        # Check that the call had line numbers disabled (border = 0)
        last_call_kwargs = mock_codeview.call_args[1]
        self.assertIn('linenums_border', last_call_kwargs)
        self.assertEqual(last_call_kwargs['linenums_border'], 0)
        
    @patch('code_editor.CodeView')
    def test_line_numbers_dynamic_enable_disable(self, mock_codeview):
        """Test that line numbers can be dynamically enabled/disabled."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create parent mock that won't cause arithmetic issues
        parent_frame = Mock()
        parent_frame._last_child_ids = {}
        
        # Create CodeEditor with line numbers enabled initially
        editor = CodeEditor(
            parent_frame, 
            self.syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Load initial file
        widget1 = editor.update_file_content("# Initial content", filename="test1.py")
        initial_call_count = mock_codeview.call_count
        
        # Disable line numbers
        editor.set_line_numbers_enabled(False)
        
        # Load another file
        widget2 = editor.update_file_content("# Second content", filename="test2.py")
        
        # Check that line numbers are now disabled in the most recent call
        self.assertGreater(mock_codeview.call_count, initial_call_count)
        last_call_kwargs = mock_codeview.call_args[1]
        self.assertIn('linenums_border', last_call_kwargs)
        self.assertEqual(last_call_kwargs['linenums_border'], 0)
        
        # Re-enable line numbers
        editor.set_line_numbers_enabled(True)
        
        # Load third file
        widget3 = editor.update_file_content("# Third content", filename="test3.py")
        
        # Check that line numbers are enabled again
        last_call_kwargs = mock_codeview.call_args[1]
        self.assertIn('linenums_border', last_call_kwargs)
        self.assertEqual(last_call_kwargs['linenums_border'], 1)
        
    def test_line_numbers_configuration_persistence(self):
        """Test that line numbers configuration persists correctly."""
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
        
        # Verify initial configuration
        config = editor.get_line_numbers_config()
        self.assertEqual(config['enabled'], True)
        self.assertEqual(config['border_width'], 2)
        
        # Change configuration
        editor.set_line_numbers_enabled(False)
        editor.set_line_numbers_border(5)
        
        # Verify configuration was updated
        config = editor.get_line_numbers_config()
        self.assertEqual(config['enabled'], False)
        self.assertEqual(config['border_width'], 5)


if __name__ == '__main__':
    unittest.main() 