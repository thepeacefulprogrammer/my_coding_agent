#!/usr/bin/env python3

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


class TestLineNumbersConfiguration(unittest.TestCase):
    """Test suite for line numbers configuration functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.parent_frame = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar = Mock()
        
    def tearDown(self):
        """Clean up test environment."""
        pass
    
    def test_init_with_line_numbers_enabled_by_default(self):
        """Test CodeEditor initializes with line numbers enabled by default."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        self.assertTrue(editor.show_line_numbers)
        self.assertEqual(editor.line_numbers_border, 1)
    
    def test_init_with_line_numbers_disabled(self):
        """Test CodeEditor can be initialized with line numbers disabled."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            show_line_numbers=False
        )
        
        self.assertFalse(editor.show_line_numbers)
        self.assertEqual(editor.line_numbers_border, 1)  # Border setting still available
    
    def test_init_with_custom_line_numbers_border(self):
        """Test CodeEditor can be initialized with custom line numbers border width."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            line_numbers_border=3
        )
        
        self.assertTrue(editor.show_line_numbers)
        self.assertEqual(editor.line_numbers_border, 3)
    
    def test_line_numbers_configuration_properties(self):
        """Test that line numbers configuration properties are set correctly."""
        # Test with line numbers enabled
        editor_enabled = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            show_line_numbers=True,
            line_numbers_border=2
        )
        
        self.assertTrue(editor_enabled.show_line_numbers)
        self.assertEqual(editor_enabled.line_numbers_border, 2)
        
        # Test with line numbers disabled
        editor_disabled = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            show_line_numbers=False,
            line_numbers_border=3
        )
        
        self.assertFalse(editor_disabled.show_line_numbers)
        self.assertEqual(editor_disabled.line_numbers_border, 3)  # Border setting preserved
    
    def test_line_numbers_config_defaults(self):
        """Test default line numbers configuration."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Should have line numbers enabled by default with border width 1
        self.assertTrue(editor.show_line_numbers)
        self.assertEqual(editor.line_numbers_border, 1)
    
    def test_set_line_numbers_enabled_true(self):
        """Test enabling line numbers dynamically."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            show_line_numbers=False
        )
        
        # Test without current widget (should still update setting)
        result = editor.set_line_numbers_enabled(True)
        
        self.assertTrue(result)
        self.assertTrue(editor.show_line_numbers)
    
    def test_set_line_numbers_enabled_false(self):
        """Test disabling line numbers dynamically."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            show_line_numbers=True
        )
        
        # Test without current widget (should still update setting)
        result = editor.set_line_numbers_enabled(False)
        
        self.assertTrue(result)
        self.assertFalse(editor.show_line_numbers)
    
    def test_set_line_numbers_border_width(self):
        """Test changing line numbers border width dynamically."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Test without current widget (should still update setting)
        result = editor.set_line_numbers_border(3)
        
        self.assertTrue(result)
        self.assertEqual(editor.line_numbers_border, 3)
    
    def test_set_line_numbers_border_when_disabled(self):
        """Test changing border width when line numbers are disabled."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            show_line_numbers=False
        )
        
        # Test without current widget (should still update setting)
        result = editor.set_line_numbers_border(5)
        
        self.assertTrue(result)
        self.assertEqual(editor.line_numbers_border, 5)
    
    def test_get_line_numbers_config(self):
        """Test getting current line numbers configuration."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            show_line_numbers=True,
            line_numbers_border=2
        )
        
        config = editor.get_line_numbers_config()
        
        expected_config = {
            'enabled': True,
            'border_width': 2
        }
        self.assertEqual(config, expected_config)
    
    def test_error_handling_in_set_line_numbers_enabled(self):
        """Test error handling when setting line numbers enabled fails."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            show_line_numbers=True
        )
        
        # Mock create_widget to raise an exception
        with patch.object(editor, 'create_widget', side_effect=Exception("widget creation failed")):
            # Set up current widget
            mock_widget = Mock()
            editor.current_widget = mock_widget
            
            result = editor.set_line_numbers_enabled(False)
            
            # Should return False and restore original setting
            self.assertFalse(result)
            self.assertTrue(editor.show_line_numbers)  # Should be restored to original value
    
    def test_error_handling_in_set_line_numbers_border(self):
        """Test error handling when setting line numbers border fails."""
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Mock create_widget to raise an exception
        with patch.object(editor, 'create_widget', side_effect=Exception("widget creation failed")):
            # Set up current widget
            mock_widget = Mock()
            editor.current_widget = mock_widget
            
            result = editor.set_line_numbers_border(5)
            
            # Should return False and restore original setting
            self.assertFalse(result)
            self.assertEqual(editor.line_numbers_border, 1)  # Should be restored to original value


if __name__ == '__main__':
    unittest.main() 