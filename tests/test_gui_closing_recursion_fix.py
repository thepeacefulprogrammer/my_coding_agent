"""
Unit tests for GUI closing recursion fix.

This module tests that the GUI can be closed safely without recursion errors,
even when widgets are being created and destroyed during the closing process.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui import GUI
from code_editor import CodeEditor
from syntax_manager import SyntaxManager


class TestGUIClosingRecursionFix(unittest.TestCase):
    """Test cases for GUI closing recursion fix."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a root window for testing
        self.root = tk.Tk()
        
        # Make the window not visible during testing
        self.root.withdraw()
        
    def tearDown(self):
        """Clean up test fixtures."""
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except:
            pass
            
    def test_closing_flag_initialization(self):
        """Test that the closing flag is properly initialized."""
        gui = GUI(self.root)
        
        # Closing flag should be False initially
        self.assertFalse(gui._closing)
        
        # CodeEditor should also have closing flag
        self.assertFalse(gui.code_editor._closing)
        
    def test_closing_flag_prevents_operations(self):
        """Test that setting closing flag prevents widget operations."""
        gui = GUI(self.root)
        
        # Set closing flag
        gui._closing = True
        
        # Operations should return early or do nothing
        result = gui.update_file_content("test content", "test.py")
        self.assertIsNone(result)
        
    def test_code_editor_closing_flag_prevents_operations(self):
        """Test that CodeEditor closing flag prevents operations."""
        gui = GUI(self.root)
        code_editor = gui.code_editor
        
        # Set closing flag
        code_editor._closing = True
        
        # Operations should return None or current widget
        result = code_editor.update_file_content("test content", "test.py")
        self.assertIsNone(result)
        
    def test_widget_replacement_during_closing(self):
        """Test that widget replacement is prevented during closing."""
        gui = GUI(self.root)
        code_editor = gui.code_editor
        
        # Create initial widget
        initial_widget = code_editor.create_widget()
        code_editor.current_widget = initial_widget
        
        # Set closing flag
        code_editor._closing = True
        
        # Widget replacement should return current widget
        lexer = Mock()
        result = code_editor.replace_widget_with_lexer(lexer)
        self.assertEqual(result, initial_widget)
        
    @patch('sys.exit')
    def test_on_closing_sets_flags(self, mock_exit):
        """Test that on_closing properly sets closing flags."""
        gui = GUI(self.root)
        
        # Mock the root methods to prevent actual destruction
        gui.root.after_idle = Mock()
        gui.root.unbind = Mock()
        
        # Call on_closing
        gui.on_closing()
        
        # Closing flags should be set
        self.assertTrue(gui._closing)
        self.assertTrue(gui.code_editor._closing)
        
        # Current widget should be cleared
        self.assertIsNone(gui.code_editor.current_widget)
        
        # after_idle should be called for delayed cleanup
        gui.root.after_idle.assert_called_once()
        
    def test_final_cleanup_handles_exceptions(self):
        """Test that final cleanup handles exceptions gracefully."""
        gui = GUI(self.root)
        
        # Mock methods to raise exceptions
        gui.root.winfo_children = Mock(side_effect=Exception("Test exception"))
        gui.root.quit = Mock(side_effect=Exception("Quit exception"))
        gui.root.after = Mock()
        
        # final_cleanup should not raise exceptions
        try:
            gui._final_cleanup()
        except SystemExit:
            # SystemExit is expected as fallback
            pass
        except Exception as e:
            self.fail(f"_final_cleanup raised unexpected exception: {e}")
            
    @patch('sys.exit')
    def test_destroy_window_handles_exceptions(self, mock_exit):
        """Test that window destruction handles exceptions gracefully."""
        gui = GUI(self.root)
        
        # Mock destroy to raise exception
        gui.root.destroy = Mock(side_effect=Exception("Destroy exception"))
        
        # Should handle exception and call sys.exit
        gui._destroy_window()
        
        mock_exit.assert_called_once_with(0)
        
    def test_recursion_prevention_in_update_chain(self):
        """Test that recursion is prevented in the update chain."""
        gui = GUI(self.root)
        
        # Mock to simulate update calls during closing
        original_update = gui.update_file_content
        call_count = 0
        
        def mock_update(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # Simulate recursion by calling update again
            if call_count < 5 and not gui._closing:
                return original_update(*args, **kwargs)
            else:
                # Set closing flag to simulate closing during recursion
                gui._closing = True
                return original_update(*args, **kwargs)
        
        gui.update_file_content = mock_update
        
        # This should not cause infinite recursion
        try:
            result = gui.update_file_content("test", "test.py")
            # Should return None when closing flag is set
            self.assertIsNone(result)
        except RecursionError:
            self.fail("Recursion was not prevented")
            
    def test_cache_clearing_during_close(self):
        """Test that widget cache is properly cleared during close."""
        gui = GUI(self.root)
        code_editor = gui.code_editor
        
        # Add some items to cache
        if hasattr(code_editor, '_widget_cache'):
            code_editor._widget_cache['test_key'] = Mock()
            self.assertEqual(len(code_editor._widget_cache), 1)
        
        # Mock to prevent actual destruction
        gui.root.after_idle = Mock()
        gui.root.unbind = Mock()
        
        # Call on_closing
        gui.on_closing()
        
        # Cache should be cleared
        if hasattr(code_editor, '_widget_cache'):
            self.assertEqual(len(code_editor._widget_cache), 0)


if __name__ == '__main__':
    # Run tests with minimal output to avoid GUI windows
    unittest.main(verbosity=2, exit=False) 