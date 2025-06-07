#!/usr/bin/env python3
"""
Test suite for GUI line numbers integration.

This tests the specific integration between GUI and CodeEditor
to ensure line numbers show when files are loaded through the GUI.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tkinter as tk

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.gui import GUI
from src.code_editor import CodeEditor
from src.syntax_manager import SyntaxManager
from src.file_explorer import FileExplorer


class TestGUILineNumbersIntegration(unittest.TestCase):
    """Test suite for GUI line numbers integration functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = Mock()
        self.root.title = Mock()
        self.root.geometry = Mock()
        self.root.protocol = Mock()
        
    def tearDown(self):
        """Clean up test environment."""
        pass
        
    @patch('src.gui.tk.Menu')
    @patch('src.gui.tk.Button')
    @patch('src.gui.tk.PanedWindow')
    @patch('src.gui.ttk.Treeview')
    @patch('src.gui.tk.Frame')
    @patch('src.gui.tk.Scrollbar')
    @patch('src.gui.CodeEditor')
    @patch('src.gui.SyntaxManager')
    @patch('src.gui.FileExplorer')
    def test_gui_initializes_code_editor_with_line_numbers(
        self, mock_file_explorer, mock_syntax_manager, mock_code_editor,
        mock_scrollbar, mock_frame, mock_treeview, mock_paned_window, mock_button, mock_menu
    ):
        """Test that GUI initializes CodeEditor with line numbers enabled."""
        # Mock the CodeEditor instance
        mock_editor_instance = Mock()
        mock_code_editor.return_value = mock_editor_instance
        
        # Mock the widget creation
        mock_widget = Mock()
        mock_editor_instance.create_widget.return_value = mock_widget
        mock_editor_instance.current_widget = mock_widget
        
        # Create real tkinter root for testing
        root = tk.Tk()
        root.withdraw()
        
        try:
            # Create GUI instance
            gui = GUI(root)
            
            # Verify CodeEditor was initialized with line numbers enabled
            mock_code_editor.assert_called_once()
            call_args = mock_code_editor.call_args
            
            # Check that show_line_numbers=True and line_numbers_border=1 were passed
            self.assertEqual(call_args[1]['show_line_numbers'], True)
            self.assertEqual(call_args[1]['line_numbers_border'], 1)
        finally:
            # Clean up
            try:
                root.destroy()
            except Exception:
                pass
        
    @patch('src.code_editor.CodeView')
    def test_gui_update_file_content_preserves_line_numbers(self, mock_codeview):
        """Test that GUI's update_file_content preserves line numbers when recreating widgets."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create GUI components manually for testing
        syntax_manager = SyntaxManager()
        file_explorer = FileExplorer()
        
        # Create CodeEditor with line numbers enabled
        parent_frame = Mock()
        scrollbar = Mock()
        code_editor = CodeEditor(
            parent_frame, 
            syntax_manager, 
            scrollbar=scrollbar,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Create GUI instance and set up its components
        gui = GUI.__new__(GUI)  # Create without calling __init__
        gui._closing = False  # Initialize closing flag for test
        gui.code_editor = code_editor
        gui.syntax_manager = syntax_manager
        gui.file_explorer = file_explorer
        
        # Mock file content for testing
        test_content = "def hello():\n    print('Hello, World!')\n    return 42"
        
        # Call update_file_content with a Python file
        gui.update_file_content(test_content, filename="test.py")
        
        # Verify that CodeView was called with line numbers enabled
        self.assertGreater(mock_codeview.call_count, 0)
        
        # Check the most recent call to ensure line numbers are enabled
        last_call_args = mock_codeview.call_args
        self.assertIn('linenums_border', last_call_args[1])
        self.assertEqual(last_call_args[1]['linenums_border'], 1)
        
    @patch('src.code_editor.CodeView')
    def test_gui_multiple_file_loads_maintain_line_numbers(self, mock_codeview):
        """Test that loading multiple files maintains line numbers consistently."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create GUI components manually for testing
        syntax_manager = SyntaxManager()
        file_explorer = FileExplorer()
        
        # Create CodeEditor with line numbers enabled
        parent_frame = Mock()
        scrollbar = Mock()
        code_editor = CodeEditor(
            parent_frame, 
            syntax_manager, 
            scrollbar=scrollbar,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Create GUI instance and set up its components
        gui = GUI.__new__(GUI)  # Create without calling __init__
        gui._closing = False  # Initialize closing flag for test
        gui.code_editor = code_editor
        gui.syntax_manager = syntax_manager
        gui.file_explorer = file_explorer
        
        # Test loading different file types
        test_files = [
            ("print('Python')", "test.py"),
            ("console.log('JavaScript');", "test.js"),
            ("<html><body>HTML</body></html>", "test.html"),
            ("body { color: red; }", "test.css")
        ]
        
        for content, filename in test_files:
            with self.subTest(filename=filename):
                # Load file content
                gui.update_file_content(content, filename=filename)
                
                # Verify line numbers are enabled in widget creation
                self.assertGreater(mock_codeview.call_count, 0)
                last_call_args = mock_codeview.call_args
                self.assertIn('linenums_border', last_call_args[1])
                self.assertEqual(last_call_args[1]['linenums_border'], 1)
                
    @patch('src.code_editor.CodeView')
    def test_gui_handles_widget_recreation_properly(self, mock_codeview):
        """Test that GUI properly handles widget recreation while preserving line numbers."""
        mock_widget_1 = Mock()
        mock_widget_2 = Mock()
        mock_codeview.side_effect = [mock_widget_1, mock_widget_2]
        
        # Create GUI components manually for testing
        syntax_manager = SyntaxManager()
        file_explorer = FileExplorer()
        
        # Create CodeEditor with line numbers enabled
        parent_frame = Mock()
        scrollbar = Mock()
        code_editor = CodeEditor(
            parent_frame, 
            syntax_manager, 
            scrollbar=scrollbar,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Start with no widget to ensure creation happens
        code_editor.current_widget = None
        
        # Create GUI instance and set up its components
        gui = GUI.__new__(GUI)  # Create without calling __init__
        gui._closing = False  # Initialize closing flag for test
        gui.code_editor = code_editor
        gui.syntax_manager = syntax_manager
        gui.file_explorer = file_explorer
        gui.file_content_codeview = None
        
        # Load content that should trigger widget creation
        content = "def test():\n    pass"
        gui.update_file_content(content, filename="test.py")
        
        # Verify that widget(s) were created with line numbers
        self.assertEqual(mock_codeview.call_count, 2)  # Initial creation + lexer replacement
        
        # Check that all widget creations had line numbers enabled
        for call in mock_codeview.call_args_list:
            self.assertIn('linenums_border', call[1])
            self.assertEqual(call[1]['linenums_border'], 1)
            
    @patch('src.code_editor.CodeView')
    def test_gui_fallback_content_update_preserves_line_numbers(self, mock_codeview):
        """Test that GUI's fallback content update mechanism preserves line numbers."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create GUI components manually for testing
        syntax_manager = SyntaxManager()
        file_explorer = FileExplorer()
        
        # Create CodeEditor with line numbers enabled
        parent_frame = Mock()
        scrollbar = Mock()
        code_editor = CodeEditor(
            parent_frame, 
            syntax_manager, 
            scrollbar=scrollbar,
            show_line_numbers=True,
            line_numbers_border=1
        )
        
        # Set initial widget
        code_editor.current_widget = mock_widget
        
        # Create GUI instance and set up its components
        gui = GUI.__new__(GUI)  # Create without calling __init__
        gui._closing = False  # Initialize closing flag for test
        gui.code_editor = code_editor
        gui.syntax_manager = syntax_manager
        gui.file_explorer = file_explorer
        gui.file_content_codeview = mock_widget
        
        # Mock an error in the main update path to trigger fallback
        with patch.object(gui.syntax_manager, 'get_lexer_for_file', side_effect=Exception("Lexer error")):
            # This should trigger the fallback content update
            content = "fallback content"
            gui.update_file_content(content, filename="test.py")
            
            # Verify that the widget still has the content updated
            # (The fallback doesn't recreate widgets, just updates content)
            mock_widget.config.assert_called()
            mock_widget.delete.assert_called()
            mock_widget.insert.assert_called()
            
    def test_line_numbers_configuration_accessible_from_gui(self):
        """Test that line numbers configuration is accessible through the GUI's CodeEditor."""
        # Create GUI components manually for testing
        syntax_manager = SyntaxManager()
        file_explorer = FileExplorer()
        
        # Create CodeEditor with line numbers enabled
        parent_frame = Mock()
        scrollbar = Mock()
        code_editor = CodeEditor(
            parent_frame, 
            syntax_manager, 
            scrollbar=scrollbar,
            show_line_numbers=True,
            line_numbers_border=2
        )
        
        # Create GUI instance and set up its components
        gui = GUI.__new__(GUI)  # Create without calling __init__
        gui._closing = False  # Initialize closing flag for test
        gui.code_editor = code_editor
        
        # Test that we can access line numbers configuration
        config = gui.code_editor.get_line_numbers_config()
        self.assertEqual(config['enabled'], True)
        self.assertEqual(config['border_width'], 2)
        
        # Test that we can modify line numbers configuration
        result = gui.code_editor.set_line_numbers_enabled(False)
        self.assertTrue(result)
        
        config = gui.code_editor.get_line_numbers_config()
        self.assertEqual(config['enabled'], False)
        self.assertEqual(config['border_width'], 2)


if __name__ == '__main__':
    unittest.main() 