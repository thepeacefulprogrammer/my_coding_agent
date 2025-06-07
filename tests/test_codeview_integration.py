import unittest
import tkinter as tk
from unittest.mock import patch, MagicMock, Mock
import tempfile
import os


class TestCodeViewIntegration(unittest.TestCase):
    """Test CodeView integration in the GUI"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        
    def tearDown(self):
        """Clean up after tests"""
        if self.root:
            self.root.destroy()
    
    def test_gui_has_codeview_widget_instead_of_text(self):
        """Test that GUI uses CodeView instead of Text widget for file content"""
        from src.gui import GUI
        gui = GUI(self.root)
        
        # Should have file_content_codeview instead of file_content_text
        self.assertTrue(hasattr(gui, 'file_content_codeview'), 
                       "GUI should have file_content_codeview attribute")
        
        # Should NOT have the old text widget
        self.assertFalse(hasattr(gui, 'file_content_text'),
                        "GUI should not have file_content_text attribute anymore")
    
    def test_codeview_widget_is_chlorophyll_codeview(self):
        """Test that the CodeView widget is actually from chlorophyll"""
        from src.gui import GUI
        from chlorophyll import CodeView
        
        gui = GUI(self.root)
        
        # Should be an instance of CodeView
        self.assertIsInstance(gui.file_content_codeview, CodeView,
                             "file_content_codeview should be a CodeView instance")
    
    def test_codeview_has_syntax_manager_integration(self):
        """Test that GUI integrates SyntaxManager with CodeView"""
        from src.gui import GUI
        from src.syntax_manager import SyntaxManager
        
        gui = GUI(self.root)
        
        # Should have a syntax_manager attribute
        self.assertTrue(hasattr(gui, 'syntax_manager'),
                       "GUI should have syntax_manager attribute")
        self.assertIsInstance(gui.syntax_manager, SyntaxManager,
                             "syntax_manager should be a SyntaxManager instance")
    
    def test_codeview_is_configured_with_scrollbar(self):
        """Test that CodeView is properly configured with scrollbar"""
        from src.gui import GUI
        
        gui = GUI(self.root)
        
        # Should still have file_content_scrollbar
        self.assertTrue(hasattr(gui, 'file_content_scrollbar'),
                       "GUI should still have file_content_scrollbar")
        
        # CodeView should be configured with scrollbar
        codeview = gui.file_content_codeview
        scrollbar = gui.file_content_scrollbar
        
        # Check if scrollbar is connected to codeview
        # CodeView should have yscrollcommand configured
        self.assertIsNotNone(codeview.cget('yscrollcommand'),
                           "CodeView should have yscrollcommand configured")
    
    def test_codeview_is_readonly_initially(self):
        """Test that CodeView is configured as read-only initially"""
        from src.gui import GUI
        
        gui = GUI(self.root)
        codeview = gui.file_content_codeview
        
        # CodeView should be in disabled state (read-only)
        self.assertEqual(codeview.cget('state'), 'disabled',
                        "CodeView should be read-only (disabled) initially")
    
    def test_update_file_content_uses_codeview_with_syntax_highlighting(self):
        """Test that update_file_content applies syntax highlighting via SyntaxManager"""
        from src.gui import GUI
        
        gui = GUI(self.root)
        
        # Mock the syntax manager through the CodeEditor to control lexer selection
        mock_lexer = Mock()
        gui.code_editor.syntax_manager.get_lexer_for_file = Mock(return_value=mock_lexer)
        
        # Test Python content with syntax highlighting
        python_content = "def hello():\n    print('Hello, World!')"
        
        # Should be able to call update_file_content with filename
        gui.update_file_content(python_content, filename="test.py")
        
        # Should have called syntax_manager to get lexer
        gui.code_editor.syntax_manager.get_lexer_for_file.assert_called_with("test.py")
    
    def test_update_file_content_fallback_without_filename(self):
        """Test that update_file_content works without filename (plain text)"""
        from src.gui import GUI
        
        gui = GUI(self.root)
        
        # Should be able to call update_file_content without filename
        content = "Plain text content"
        gui.update_file_content(content)
        
        # Should not raise any errors
        self.assertTrue(True, "update_file_content should work without filename")
    
    def test_on_tree_item_select_passes_filename_to_update_file_content(self):
        """Test that file selection passes filename for syntax highlighting"""
        from src.gui import GUI
        
        gui = GUI(self.root)
        
        # Mock the file explorer
        gui.file_explorer = Mock()
        gui.file_explorer.read_file.return_value = "print('test')"
        
        # Mock update_file_content to verify it's called with filename
        gui.update_file_content = Mock()
        
        # Create a mock tree selection event
        mock_event = Mock()
        mock_treeview = Mock()
        mock_event.widget = mock_treeview
        
        # Mock tree selection data
        mock_treeview.selection.return_value = ['item1']
        mock_treeview.item.return_value = {
            'values': ['/path/to/test.py', 'file']
        }
        
        # Call the selection handler
        gui.on_tree_item_select(mock_event)
        
        # Should call update_file_content with content and filename
        gui.update_file_content.assert_called_once()
        args = gui.update_file_content.call_args
        
        # Should pass filename as keyword argument
        self.assertIn('filename', args.kwargs,
                     "update_file_content should be called with filename")
        self.assertEqual(args.kwargs['filename'], '/path/to/test.py',
                        "filename should be the full file path")
    
    def test_codeview_has_expected_configuration_options(self):
        """Test that CodeView is configured with appropriate options for code viewing"""
        from src.gui import GUI
        
        gui = GUI(self.root)
        codeview = gui.file_content_codeview
        
        # Should have appropriate configuration for code viewing
        expected_configs = {
            'wrap': 'none',  # No text wrapping for code
            'state': 'disabled',  # Read-only initially
        }
        
        for config_key, expected_value in expected_configs.items():
            actual_value = codeview.cget(config_key)
            self.assertEqual(actual_value, expected_value,
                           f"CodeView {config_key} should be {expected_value}, got {actual_value}")
    
    def test_gui_imports_chlorophyll_and_syntax_manager(self):
        """Test that GUI properly imports chlorophyll and SyntaxManager"""
        # This test verifies imports work correctly
        from src.gui import GUI
        
        # If we get here without ImportError, the imports are working
        self.assertTrue(True, "GUI should import chlorophyll and SyntaxManager successfully")


if __name__ == '__main__':
    unittest.main() 