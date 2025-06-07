#!/usr/bin/env python3

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


class TestLineNumbersScrollingFix(unittest.TestCase):
    """Test suite for line numbers scrolling synchronization fix."""
    
    def setUp(self):
        """Set up test environment."""
        self.parent_frame = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar = Mock()
        
    def tearDown(self):
        """Clean up test environment."""
        pass
    
    def test_configure_scrollbar_creates_custom_scroll_command(self):
        """Test that configure_scrollbar creates a custom scroll command."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            scrollbar=self.scrollbar,
            show_line_numbers=True
        )
        
        # Create a mock widget with scroll_line_update method
        mock_widget = Mock()
        mock_widget.yview = Mock(return_value=None)
        mock_widget.scroll_line_update = Mock()
        
        # Configure scrollbar
        editor.configure_scrollbar(mock_widget)
        
        # Verify scrollbar.config was called with a custom command
        self.assertTrue(self.scrollbar.config.called)
        call_args = self.scrollbar.config.call_args
        self.assertIn('command', call_args[1])
        
        # Verify widget.config was called with yscrollcommand
        mock_widget.config.assert_called_with(yscrollcommand=self.scrollbar.set)
    
    def test_custom_scroll_command_calls_line_numbers_redraw(self):
        """Test that the custom scroll command calls redraw on the line numbers widget."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            scrollbar=self.scrollbar,
            show_line_numbers=True
        )
        
        # Create a mock widget with _line_numbers attribute
        mock_widget = Mock()
        mock_widget.yview = Mock(return_value="scroll_result")
        mock_line_numbers = Mock()
        mock_widget._line_numbers = mock_line_numbers
        
        # Configure scrollbar to capture the custom command
        editor.configure_scrollbar(mock_widget)
        
        # Get the custom scroll command that was passed to scrollbar.config
        scroll_command = self.scrollbar.config.call_args[1]['command']
        
        # Call the custom scroll command
        result = scroll_command('moveto', '0.5')
        
        # Verify that yview was called with the correct arguments
        mock_widget.yview.assert_called_once_with('moveto', '0.5')
        
        # Verify that redraw was called on the line numbers widget
        mock_line_numbers.redraw.assert_called_once()
        
        # Verify the result is returned correctly
        self.assertEqual(result, "scroll_result")
    
    def test_custom_scroll_command_handles_missing_line_numbers(self):
        """Test that custom scroll command works even if _line_numbers doesn't exist."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            scrollbar=self.scrollbar,
            show_line_numbers=True
        )
        
        # Create a mock widget WITHOUT _line_numbers attribute
        mock_widget = Mock()
        mock_widget.yview = Mock(return_value="scroll_result")
        # Explicitly remove _line_numbers to simulate a regular Text widget
        if hasattr(mock_widget, '_line_numbers'):
            delattr(mock_widget, '_line_numbers')
        
        # Configure scrollbar
        editor.configure_scrollbar(mock_widget)
        
        # Get the custom scroll command
        scroll_command = self.scrollbar.config.call_args[1]['command']
        
        # Call the custom scroll command - should not raise an error
        result = scroll_command('moveto', '0.25')
        
        # Verify that yview was still called
        mock_widget.yview.assert_called_once_with('moveto', '0.25')
        
        # Verify the result is returned correctly
        self.assertEqual(result, "scroll_result")
    
    def test_custom_scroll_command_handles_line_numbers_redraw_errors(self):
        """Test that line numbers redraw errors don't break scrolling."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            scrollbar=self.scrollbar,
            show_line_numbers=True
        )
        
        # Create a mock widget with a failing redraw method
        mock_widget = Mock()
        mock_widget.yview = Mock(return_value="scroll_result")
        mock_line_numbers = Mock()
        mock_line_numbers.redraw = Mock(side_effect=Exception("Line redraw error"))
        mock_widget._line_numbers = mock_line_numbers
        
        # Configure scrollbar
        editor.configure_scrollbar(mock_widget)
        
        # Get the custom scroll command
        scroll_command = self.scrollbar.config.call_args[1]['command']
        
        # Call the custom scroll command - should not raise an error
        result = scroll_command('scroll', '5', 'units')
        
        # Verify that yview was still called
        mock_widget.yview.assert_called_once_with('scroll', '5', 'units')
        
        # Verify that redraw was called (even though it failed)
        mock_line_numbers.redraw.assert_called_once()
        
        # Verify the result is returned correctly despite the error
        self.assertEqual(result, "scroll_result")
    
    def test_custom_scroll_command_handles_yview_errors(self):
        """Test that custom scroll command handles yview errors gracefully."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            scrollbar=self.scrollbar,
            show_line_numbers=True
        )
        
        # Create a mock widget with failing yview
        mock_widget = Mock()
        mock_widget.yview = Mock(side_effect=Exception("Scroll error"))
        mock_line_numbers = Mock()
        mock_widget._line_numbers = mock_line_numbers
        
        # Configure scrollbar
        editor.configure_scrollbar(mock_widget)
        
        # Get the custom scroll command
        scroll_command = self.scrollbar.config.call_args[1]['command']
        
        # Call the custom scroll command - should not raise an error
        result = scroll_command('moveto', '0.75')
        
        # Verify that yview was called (might be called multiple times due to fallback)
        self.assertTrue(mock_widget.yview.called)
        
        # Verify that line numbers redraw was NOT called due to yview failure
        mock_line_numbers.redraw.assert_not_called()
        
        # Result should be None due to error handling
        self.assertIsNone(result)
    
    def test_configure_scrollbar_with_no_scrollbar(self):
        """Test that configure_scrollbar handles None scrollbar gracefully."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            scrollbar=None,  # No scrollbar
            show_line_numbers=True
        )
        
        mock_widget = Mock()
        
        # Should not raise an error
        editor.configure_scrollbar(mock_widget)
        
        # Widget should not be configured since there's no scrollbar
        mock_widget.config.assert_not_called()
    
    def test_line_numbers_scrolling_integration_without_widget_creation(self):
        """Test that line number scrolling integration works without creating real widgets."""
        editor = CodeEditor(
            self.parent_frame,
            self.syntax_manager,
            scrollbar=self.scrollbar,
            show_line_numbers=True
        )
        
        # Create a mock widget directly and configure it
        mock_widget = Mock()
        mock_widget.yview = Mock(return_value="scroll_result")
        mock_line_numbers = Mock()
        mock_widget._line_numbers = mock_line_numbers
        
        # Set it as the current widget and configure scrollbar
        editor.current_widget = mock_widget
        editor.configure_scrollbar(mock_widget)
        
        # Verify scrollbar was configured with custom command
        self.assertTrue(self.scrollbar.config.called)
        scroll_command = self.scrollbar.config.call_args[1]['command']
        
        # Test the scroll command
        scroll_command('moveto', '0.33')
        
        # Verify both yview and line numbers redraw were called
        mock_widget.yview.assert_called_with('moveto', '0.33')
        mock_line_numbers.redraw.assert_called_once()
    
    def test_multiple_scroll_commands_call_line_numbers_redraw_each_time(self):
        """Test that each scroll command calls line numbers redraw."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            scrollbar=self.scrollbar,
            show_line_numbers=True
        )
        
        # Create a mock widget
        mock_widget = Mock()
        mock_widget.yview = Mock(return_value=None)
        mock_line_numbers = Mock()
        mock_widget._line_numbers = mock_line_numbers
        
        # Configure scrollbar
        editor.configure_scrollbar(mock_widget)
        scroll_command = self.scrollbar.config.call_args[1]['command']
        
        # Call scroll command multiple times
        scroll_command('moveto', '0.1')
        scroll_command('moveto', '0.5')
        scroll_command('scroll', '3', 'units')
        
        # Verify line numbers redraw was called each time
        self.assertEqual(mock_line_numbers.redraw.call_count, 3)
        
        # Verify yview was called with correct arguments each time
        expected_calls = [
            call('moveto', '0.1'),
            call('moveto', '0.5'), 
            call('scroll', '3', 'units')
        ]
        mock_widget.yview.assert_has_calls(expected_calls)
    
    def test_scrollbar_configuration_error_handling(self):
        """Test that scrollbar configuration errors are handled gracefully."""
        # Create a scrollbar that raises an error on config
        error_scrollbar = Mock()
        error_scrollbar.config = Mock(side_effect=Exception("Scrollbar config error"))
        
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            scrollbar=error_scrollbar,
            show_line_numbers=True
        )
        
        mock_widget = Mock()
        
        # Should not raise an error despite scrollbar.config failing
        editor.configure_scrollbar(mock_widget)
        
        # Verify config was attempted
        error_scrollbar.config.assert_called_once()


if __name__ == '__main__':
    unittest.main() 