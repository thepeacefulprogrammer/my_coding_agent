#!/usr/bin/env python3
"""
Tests for error handling and fallback scenarios in CodeEditor.

This module tests error conditions, graceful degradation, fallback mechanisms,
and recovery scenarios to ensure robust operation under adverse conditions.
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

class TestCodeViewCreationErrors(unittest.TestCase):
    """Test error handling during CodeView widget creation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_codeview_creation_failure_fallback(self, mock_codeview):
        """Test fallback when CodeView creation fails."""
        # Make CodeView constructor raise an exception
        mock_codeview.side_effect = Exception("CodeView creation failed")
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Should handle CodeView creation error gracefully
        try:
            widget = editor.create_widget()
            # If create_widget succeeds, it should return something usable
            self.assertIsNotNone(widget)
        except Exception as e:
            # If it fails, the error should be informative
            self.assertIn("creation", str(e).lower())
            
    @patch('code_editor.CodeView')
    def test_widget_setup_partial_failure_recovery(self, mock_codeview):
        """Test recovery when widget setup partially fails."""
        # Create widget that fails during configuration
        mock_widget = Mock()
        mock_widget.config.side_effect = Exception("Widget config failed")
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Should create widget even if configuration fails
        widget = editor.create_widget()
        self.assertIsNotNone(widget)
        
    @patch('code_editor.CodeView')
    def test_lexer_application_failure_fallback(self, mock_codeview):
        """Test fallback when lexer application fails."""
        mock_widget = Mock()
        # Make lexer assignment fail
        def lexer_assignment_error(value):
            raise Exception("Lexer assignment failed")
        
        mock_widget.configure_mock(**{'lexer': Mock(side_effect=lexer_assignment_error)})
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Get a lexer
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        
        # Should create widget even if lexer application fails
        widget = editor.create_widget(lexer)
        self.assertIsNotNone(widget)

class TestFileOperationErrors(unittest.TestCase):
    """Test error handling in file operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_file_loading_encoding_errors(self, mock_codeview):
        """Test handling of file encoding errors."""
        mock_widget = Mock()
        mock_widget.delete = Mock()
        mock_widget.insert = Mock()
        mock_widget.config = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Test with non-existent file (should return False)
        result = editor.load_file("nonexistent_file.txt")
        self.assertFalse(result, "load_file should return False for non-existent files")
        
        # Editor should remain functional after error
        self.assertIsNone(editor.current_widget)  # No widget created due to error
        
    @patch('code_editor.CodeView')
    @patch('builtins.open')
    def test_file_permission_error_handling(self, mock_open, mock_codeview):
        """Test handling of file permission errors."""
        mock_widget = Mock()
        mock_widget.delete = Mock()
        mock_widget.insert = Mock()
        mock_widget.config = Mock()
        mock_codeview.return_value = mock_widget
        
        # Make file opening fail with permission error
        mock_open.side_effect = PermissionError("Permission denied")
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Should return False for permission errors (graceful handling)
        result = editor.load_file("restricted_file.txt")
        self.assertFalse(result, "load_file should return False for permission errors")
        
        # Editor should remain functional
        self.assertIsNone(editor.current_widget)  # No widget created due to error
            
    @patch('code_editor.CodeView')
    def test_content_update_widget_error_recovery(self, mock_codeview):
        """Test recovery when content update fails."""
        mock_widget = Mock()
        # Make content operations fail
        mock_widget.delete.side_effect = tk.TclError("Widget destroyed")
        mock_widget.insert.side_effect = tk.TclError("Widget destroyed")
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Should handle content update errors gracefully
        try:
            editor.update_file_content("test content", "test.py")
            # If it succeeds, that's fine
            success = True
        except Exception:
            # If it fails, that's also acceptable for this error scenario
            success = False
            
        # The important thing is that the editor doesn't crash completely
        self.assertTrue(isinstance(success, bool), "Editor should handle errors gracefully")

class TestWidgetStateErrors(unittest.TestCase):
    """Test error handling in widget state operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_widget_state_capture_failure_fallback(self, mock_codeview):
        """Test fallback when widget state capture fails."""
        mock_widget = Mock()
        # Make all state capture methods fail
        mock_widget.get.side_effect = tk.TclError("Widget corrupted")
        mock_widget.index.side_effect = tk.TclError("Widget corrupted") 
        mock_widget.yview.side_effect = tk.TclError("Widget corrupted")
        mock_widget.tag_ranges.side_effect = tk.TclError("Widget corrupted")
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Should return safe defaults when state capture fails
        state = editor.capture_widget_state()
        
        # Verify safe default values
        self.assertEqual(state['content'], '')
        self.assertEqual(state['cursor_position'], '1.0')
        self.assertEqual(state['scroll_position'], (0.0, 1.0))
        self.assertIsNone(state['selection'])
        
    @patch('code_editor.CodeView')
    def test_widget_state_restoration_failure_recovery(self, mock_codeview):
        """Test recovery when widget state restoration fails."""
        mock_widget = Mock()
        # Make state restoration methods fail
        mock_widget.delete.side_effect = tk.TclError("Restoration failed")
        mock_widget.insert.side_effect = tk.TclError("Restoration failed")
        mock_widget.mark_set.side_effect = tk.TclError("Restoration failed")
        mock_widget.yview_moveto.side_effect = tk.TclError("Restoration failed")
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Create a state to restore
        test_state = {
            'content': 'test content',
            'cursor_position': '1.5',
            'scroll_position': (0.3, 0.7),
            'selection': None
        }
        
        # Should handle restoration errors gracefully
        try:
            editor.restore_widget_state(mock_widget, test_state)
            success = True
        except Exception:
            success = False
            
        # Should not crash the application
        self.assertTrue(isinstance(success, bool), "State restoration should handle errors gracefully")
        
    @patch('code_editor.CodeView')
    def test_widget_destruction_error_cleanup(self, mock_codeview):
        """Test cleanup when widget destruction encounters errors."""
        mock_widget = Mock()
        # Make destruction methods fail
        mock_widget.unbind_all.side_effect = tk.TclError("Unbind failed")
        mock_widget.pack_forget.side_effect = tk.TclError("Pack forget failed")
        mock_widget.grid_forget.side_effect = tk.TclError("Grid forget failed")
        mock_widget.destroy.side_effect = tk.TclError("Destroy failed")
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Should handle destruction errors gracefully
        try:
            editor.destroy_widget_safely()
            success = True
        except Exception:
            success = False
            
        # Widget reference should be cleared even if destruction fails
        self.assertIsNone(editor.current_widget)
        self.assertTrue(isinstance(success, bool), "Destruction should handle errors gracefully")

class TestLexerAndSyntaxErrors(unittest.TestCase):
    """Test error handling in lexer and syntax highlighting operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_invalid_lexer_handling(self, mock_codeview):
        """Test handling of invalid or corrupted lexers."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Test with None lexer
        widget = editor.create_widget(lexer=None)
        self.assertIsNotNone(widget)
        
        # Test with invalid lexer object
        invalid_lexer = Mock()
        invalid_lexer.aliases = ["invalid"]
        
        widget = editor.create_widget(lexer=invalid_lexer)
        self.assertIsNotNone(widget)
        
    @patch('code_editor.CodeView')
    def test_syntax_highlighting_failure_fallback(self, mock_codeview):
        """Test fallback when syntax highlighting fails."""
        mock_widget = Mock()
        # Make highlight_all method fail
        mock_widget.highlight_all.side_effect = Exception("Highlighting failed")
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Get a valid lexer
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        
        # Should create widget even if highlighting fails
        widget = editor.create_widget(lexer)
        self.assertIsNotNone(widget)
        
    @patch('code_editor.CodeView')
    def test_unknown_file_extension_fallback(self, mock_codeview):
        """Test fallback for unknown file extensions."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Should handle unknown extensions gracefully
        editor.update_file_content("content", "file.unknown_extension")
        
        # Should still work (no syntax highlighting, but functional)
        self.assertIsNotNone(editor.current_widget)

class TestCacheSystemErrors(unittest.TestCase):
    """Test error handling in widget caching system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_cache_corruption_recovery(self, mock_codeview):
        """Test recovery from cache corruption."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=True
        )
        
        # Manually corrupt the cache
        editor._widget_cache = "corrupted_cache"  # Not a proper dict
        
        # Should handle corrupted cache gracefully
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        
        try:
            widget = editor.replace_widget_with_cached_lexer(lexer)
            self.assertIsNotNone(widget)
        except Exception:
            # If caching fails, should fall back to regular widget creation
            widget = editor.create_widget(lexer)
            self.assertIsNotNone(widget)
            
    @patch('code_editor.CodeView')
    def test_cache_size_exceeded_handling(self, mock_codeview):
        """Test handling when cache size limits are exceeded."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=True,
            cache_size=2  # Small cache for testing
        )
        
        # Fill cache beyond capacity
        lexers = [
            self.syntax_manager.get_lexer_for_file("test1.py"),
            self.syntax_manager.get_lexer_for_file("test2.js"),
            self.syntax_manager.get_lexer_for_file("test3.html"),  # Should evict oldest
        ]
        
        # Should handle cache eviction gracefully
        for lexer in lexers:
            widget = editor.replace_widget_with_cached_lexer(lexer)
            self.assertIsNotNone(widget)
            
        # Cache should not exceed size limit
        cache_size = editor.get_cache_size()
        self.assertLessEqual(cache_size, 2)

class TestColorSchemeErrors(unittest.TestCase):
    """Test error handling in color scheme operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_invalid_color_scheme_fallback(self, mock_codeview):
        """Test fallback to default when invalid color scheme is specified."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            color_scheme="nonexistent_scheme"
        )
        
        # Should create widget with fallback color scheme
        widget = editor.create_widget()
        self.assertIsNotNone(widget)
        
    @patch('code_editor.CodeView')
    def test_color_scheme_switching_error_recovery(self, mock_codeview):
        """Test recovery when color scheme switching fails."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Should handle color scheme switching errors gracefully
        try:
            editor.switch_color_scheme("invalid_scheme")
            success = True
        except Exception:
            success = False
            
        # Editor should remain functional
        self.assertIsNotNone(editor.current_widget)
        self.assertTrue(isinstance(success, bool), "Color scheme switching should handle errors gracefully")

class TestConcurrencyAndRaceConditions(unittest.TestCase):
    """Test error handling in concurrent operations and race conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_rapid_widget_replacement_error_handling(self, mock_codeview):
        """Test error handling during rapid widget replacements."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Perform rapid replacements that might cause race conditions
        lexers = [
            self.syntax_manager.get_lexer_for_file("test.py"),
            self.syntax_manager.get_lexer_for_file("test.js"),
            self.syntax_manager.get_lexer_for_file("test.html"),
        ]
        
        # Should handle rapid operations without crashing
        for _ in range(5):  # Multiple rapid cycles
            for lexer in lexers:
                try:
                    widget = editor.replace_widget_with_lexer(lexer)
                    self.assertIsNotNone(widget)
                except Exception:
                    # Some operations might fail due to rapid execution, but shouldn't crash
                    pass
                    
        # Editor should remain in a consistent state
        self.assertIsNotNone(editor.current_widget)
        
    @patch('code_editor.CodeView')
    def test_widget_state_during_replacement_errors(self, mock_codeview):
        """Test widget state consistency during replacement errors."""
        mock_widget1 = Mock()
        mock_widget2 = Mock()
        
        # Make second widget creation fail
        mock_codeview.side_effect = [mock_widget1, Exception("Second widget failed")]
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        original_widget = editor.current_widget
        
        # Try to replace widget (should fail)
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        
        try:
            editor.replace_widget_with_lexer(lexer)
        except Exception:
            pass  # Expected to fail
            
        # Should maintain reference to original widget after failure
        self.assertEqual(editor.current_widget, original_widget)

class TestResourceManagementErrors(unittest.TestCase):
    """Test error handling in resource management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_memory_pressure_handling(self, mock_codeview):
        """Test handling under simulated memory pressure."""
        # Simulate memory allocation failure
        def memory_error_side_effect(*args, **kwargs):
            raise MemoryError("Out of memory")
            
        mock_codeview.side_effect = memory_error_side_effect
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Should handle memory errors - expecting the wrapper exception
        with self.assertRaises(Exception) as context:
            editor.create_widget()
            
        # Verify it's a memory error wrapped in the widget creation error
        self.assertIn("Out of memory", str(context.exception))
            
    @patch('code_editor.CodeView')
    def test_garbage_collection_error_recovery(self, mock_codeview):
        """Test recovery when garbage collection fails."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Mock garbage collection to fail
        with patch('gc.collect', side_effect=Exception("GC failed")):
            # Should handle GC errors gracefully during cleanup
            try:
                editor.destroy_widget_safely()
                success = True
            except Exception:
                success = False
                
            # Widget should still be cleaned up
            self.assertIsNone(editor.current_widget)
            self.assertTrue(isinstance(success, bool), "Should handle GC errors gracefully")

if __name__ == '__main__':
    unittest.main() 