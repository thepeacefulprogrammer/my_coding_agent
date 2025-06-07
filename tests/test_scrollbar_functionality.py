#!/usr/bin/env python3
"""
Tests for scrollbar functionality and state preservation in CodeEditor.

This module tests scrollbar behavior, connection/disconnection, state preservation
during widget replacement, and proper scrollbar synchronization with content.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager

class TestScrollbarConnection(unittest.TestCase):
    """Test scrollbar connection and disconnection functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_scrollbar_initial_connection(self, mock_codeview):
        """Test that scrollbar is properly connected during widget creation."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Create initial widget
        editor.setup_initial_widget()
        
        # Verify scrollbar configuration was called
        self.scrollbar_mock.config.assert_called()
        
        # Check that scrollbar command was set to widget's yview
        scrollbar_config_calls = self.scrollbar_mock.config.call_args_list
        command_set = any('command' in call[1] for call in scrollbar_config_calls)
        self.assertTrue(command_set, "Scrollbar command should be configured")
        
    @patch('code_editor.CodeView')
    def test_scrollbar_disconnection_on_widget_destruction(self, mock_codeview):
        """Test that scrollbar is properly disconnected when widget is destroyed."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Clear previous calls to track disconnection
        self.scrollbar_mock.config.reset_mock()
        
        # Destroy widget
        editor.destroy_widget_safely()
        
        # Verify scrollbar was disconnected (command set to empty or None)
        self.scrollbar_mock.config.assert_called()
        disconnect_calls = self.scrollbar_mock.config.call_args_list
        
        # Check if command was cleared
        command_cleared = any(
            'command' in call[1] and (call[1]['command'] == '' or call[1]['command'] is None)
            for call in disconnect_calls
        )
        self.assertTrue(command_cleared, "Scrollbar command should be cleared on widget destruction")
        
    @patch('code_editor.CodeView')
    def test_scrollbar_reconnection_on_widget_replacement(self, mock_codeview):
        """Test that scrollbar is reconnected when widget is replaced."""
        # Setup
        mock_widget1 = Mock()
        mock_widget2 = Mock()
        mock_codeview.side_effect = [mock_widget1, mock_widget2]
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Clear calls to track reconnection
        self.scrollbar_mock.config.reset_mock()
        
        # Replace widget
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        editor.replace_widget_with_lexer(lexer)
        
        # Verify scrollbar was reconfigured for new widget
        self.scrollbar_mock.config.assert_called()
        reconnection_calls = self.scrollbar_mock.config.call_args_list
        
        # Should have both disconnection and reconnection calls
        self.assertGreater(len(reconnection_calls), 0, "Scrollbar should be reconfigured after widget replacement")

class TestScrollbarStatePreservation(unittest.TestCase):
    """Test scrollbar state preservation during widget operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
        # Mock scrollbar methods
        self.scrollbar_mock.get.return_value = (0.2, 0.8)  # Mock current scroll position
        
    @patch('code_editor.CodeView')
    def test_scroll_position_preservation_during_replacement(self, mock_codeview):
        """Test that scroll position is preserved during widget replacement."""
        # Setup
        mock_widget1 = Mock()
        mock_widget2 = Mock()
        
        # Mock yview methods for position tracking - return proper scroll position
        mock_widget1.yview.return_value = (0.3, 0.7)  # Simulate widget at scroll position
        mock_widget1.yview_moveto = Mock()
        mock_widget2.yview.return_value = (0.0, 1.0)  # New widget starts at top
        mock_widget2.yview_moveto = Mock()
        
        # Mock other required methods
        mock_widget1.get.return_value = "test content"
        mock_widget1.index.return_value = "1.0"
        mock_widget1.tag_ranges.return_value = []
        mock_widget2.delete = Mock()
        mock_widget2.insert = Mock()
        mock_widget2.mark_set = Mock()
        mock_widget2.config = Mock()
        
        mock_codeview.side_effect = [mock_widget1, mock_widget2]
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Simulate scrollbar position
        self.scrollbar_mock.get.return_value = (0.3, 0.7)
        
        # Replace widget
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        editor.replace_widget_with_lexer(lexer)
        
        # Verify that the new widget's yview_moveto was called to restore position
        # Should be called with the scroll position from the old widget (0.3)
        mock_widget2.yview_moveto.assert_called_with(0.3)
        
    @patch('code_editor.CodeView')
    def test_scroll_position_preservation_with_content_update(self, mock_codeview):
        """Test scroll position preservation when updating content."""
        # Setup - create two mock widgets for initial and replacement
        mock_widget1 = Mock()
        mock_widget2 = Mock()
        
        # Setup first widget (initial)
        mock_widget1.yview.return_value = (0.4, 0.6)
        mock_widget1.get.return_value = "original content"
        mock_widget1.index.return_value = "1.0"
        mock_widget1.tag_ranges.return_value = []
        mock_widget1.config = Mock()
        
        # Setup second widget (replacement with syntax highlighting)
        mock_widget2.yview_moveto = Mock()
        mock_widget2.insert = Mock()
        mock_widget2.delete = Mock()
        mock_widget2.mark_set = Mock()
        mock_widget2.config = Mock()
        mock_widget2.yview.return_value = (0.0, 1.0)
        
        # Return different widgets for initial setup vs replacement
        mock_codeview.side_effect = [mock_widget1, mock_widget2]
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Set initial scroll position on scrollbar mock
        self.scrollbar_mock.get.return_value = (0.4, 0.6)
        
        # Update content with filename (triggers widget replacement with lexer)
        new_content = "def test():\n    pass\n" * 100  # Large content
        editor.update_file_content(new_content, "test.py")
        
        # Verify scroll position was preserved (should call yview_moveto with 0.4)
        mock_widget2.yview_moveto.assert_called_with(0.4)

class TestScrollbarContentSynchronization(unittest.TestCase):
    """Test scrollbar synchronization with content changes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_scrollbar_updates_with_content_changes(self, mock_codeview):
        """Test that scrollbar updates when content changes."""
        # Setup
        mock_widget = Mock()
        mock_widget.insert = Mock()
        mock_widget.delete = Mock()
        mock_widget.get = Mock(return_value="test content")
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Update content
        content = "print('hello')\n" * 50  # Content that would require scrolling
        editor.update_file_content(content, "test.py")
        
        # Verify widget content was updated
        mock_widget.delete.assert_called()
        mock_widget.insert.assert_called()
        
    @patch('code_editor.CodeView')
    def test_scrollbar_behavior_with_empty_content(self, mock_codeview):
        """Test scrollbar behavior with empty content."""
        # Setup
        mock_widget = Mock()
        mock_widget.insert = Mock()
        mock_widget.delete = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Set empty content
        editor.update_file_content("", "empty.txt")
        
        # Verify empty content was set
        mock_widget.delete.assert_called()
        mock_widget.insert.assert_called_with('1.0', "")
        
    @patch('code_editor.CodeView')
    def test_scrollbar_behavior_with_large_content(self, mock_codeview):
        """Test scrollbar behavior with large content that requires scrolling."""
        # Setup
        mock_widget = Mock()
        mock_widget.insert = Mock()
        mock_widget.delete = Mock()
        mock_widget.yview_moveto = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Create large content
        large_content = "# Line {}\nprint('This is line {}')\n".format(
            *[i for i in range(1000) for _ in range(2)]
        )
        
        # Set scroll position before content update
        self.scrollbar_mock.get.return_value = (0.0, 1.0)
        
        # Update with large content
        editor.update_file_content(large_content, "large.py")
        
        # Verify content was updated
        mock_widget.delete.assert_called()
        mock_widget.insert.assert_called()

class TestScrollbarErrorHandling(unittest.TestCase):
    """Test scrollbar error handling and edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_scrollbar_handling_with_none_scrollbar(self, mock_codeview):
        """Test behavior when no scrollbar is provided."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create editor without scrollbar
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=None
        )
        
        # Should not raise exception
        editor.setup_initial_widget()
        
        # Replace widget should also work without scrollbar
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        editor.replace_widget_with_lexer(lexer)
        
        # Should complete without errors
        self.assertTrue(True, "Operations should complete without scrollbar")
        
    @patch('code_editor.CodeView')
    def test_scrollbar_error_recovery(self, mock_codeview):
        """Test recovery from scrollbar operation errors."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Make scrollbar.config raise an exception
        self.scrollbar_mock.config.side_effect = Exception("Scrollbar error")
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Should handle scrollbar errors gracefully
        try:
            editor.setup_initial_widget()
            success = True
        except Exception:
            success = False
            
        # Widget creation should still succeed even if scrollbar fails
        self.assertTrue(success, "Widget creation should handle scrollbar errors gracefully")
        
    @patch('code_editor.CodeView')
    def test_scrollbar_get_method_error_handling(self, mock_codeview):
        """Test handling of scrollbar.get() errors during position preservation."""
        # Setup
        mock_widget = Mock()
        mock_widget.yview_moveto = Mock()
        mock_codeview.return_value = mock_widget
        
        # Make scrollbar.get raise an exception
        self.scrollbar_mock.get.side_effect = Exception("Get position error")
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Should handle get() errors gracefully during widget replacement
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        try:
            editor.replace_widget_with_lexer(lexer)
            success = True
        except Exception:
            success = False
            
        self.assertTrue(success, "Widget replacement should handle scrollbar.get() errors gracefully")

class TestScrollbarIntegration(unittest.TestCase):
    """Test scrollbar integration with other CodeEditor features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_scrollbar_with_caching_enabled(self, mock_codeview):
        """Test scrollbar behavior with widget caching enabled."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=True
        )
        
        editor.setup_initial_widget()
        
        # Test cached widget replacement
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        editor.replace_widget_with_cached_lexer(lexer)
        
        # Verify scrollbar operations still work with caching
        self.scrollbar_mock.config.assert_called()
        
    @patch('code_editor.CodeView')
    def test_scrollbar_with_multiple_rapid_replacements(self, mock_codeview):
        """Test scrollbar behavior with multiple rapid widget replacements."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Clear initial calls
        self.scrollbar_mock.config.reset_mock()
        
        # Perform multiple rapid replacements
        file_types = ["test.py", "test.js", "test.html", "test.css"]
        for file_type in file_types:
            lexer = self.syntax_manager.get_lexer_for_file(file_type)
            editor.replace_widget_with_lexer(lexer)
            
        # Verify scrollbar was configured for each replacement
        config_calls = len(self.scrollbar_mock.config.call_args_list)
        self.assertGreater(config_calls, 0, "Scrollbar should be configured during replacements")
        
    @patch('code_editor.CodeView')
    def test_scrollbar_state_consistency(self, mock_codeview):
        """Test that scrollbar state remains consistent across operations."""
        # Setup - create multiple widgets for different operations
        mock_widget1 = Mock()  # Initial widget
        mock_widget2 = Mock()  # Widget after content update  
        mock_widget3 = Mock()  # Widget after lexer replacement
        
        # Setup widgets with proper scroll positions
        mock_widget1.yview.return_value = (0.25, 0.75)
        mock_widget1.get.return_value = "initial content"
        mock_widget1.index.return_value = "1.0"
        mock_widget1.tag_ranges.return_value = []
        mock_widget1.config = Mock()
        
        mock_widget2.yview.return_value = (0.25, 0.75)
        mock_widget2.get.return_value = "print('test')"
        mock_widget2.index.return_value = "1.0"
        mock_widget2.tag_ranges.return_value = []
        mock_widget2.config = Mock()
        mock_widget2.delete = Mock()
        mock_widget2.insert = Mock()
        mock_widget2.mark_set = Mock()
        
        mock_widget3.yview_moveto = Mock()
        mock_widget3.delete = Mock()
        mock_widget3.insert = Mock()
        mock_widget3.mark_set = Mock()
        mock_widget3.config = Mock()
        
        # Return different widgets for different operations
        mock_codeview.side_effect = [mock_widget1, mock_widget2, mock_widget3]
        
        # Set up scrollbar to return consistent position
        self.scrollbar_mock.get.return_value = (0.25, 0.75)
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Perform operations that should preserve state
        editor.update_file_content("print('test')", "test.py")
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        editor.replace_widget_with_lexer(lexer)
        
        # Verify consistent behavior
        self.scrollbar_mock.config.assert_called()
        mock_widget3.yview_moveto.assert_called_with(0.25)

if __name__ == '__main__':
    unittest.main() 