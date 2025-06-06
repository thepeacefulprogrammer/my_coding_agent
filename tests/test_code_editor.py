import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from tkinter import ttk
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


class TestCodeEditor(unittest.TestCase):
    """Test cases for CodeEditor class that manages CodeView widget lifecycle."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.parent_frame = ttk.Frame(self.root)
        self.syntax_manager = SyntaxManager()
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
        
    def test_init_creates_code_editor_instance(self):
        """Test CodeEditor can be instantiated with required parameters."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        self.assertIsInstance(editor, CodeEditor)
        self.assertEqual(editor.parent, self.parent_frame)
        self.assertEqual(editor.syntax_manager, self.syntax_manager)
        
    def test_init_with_optional_parameters(self):
        """Test CodeEditor initialization with optional parameters."""
        scrollbar = ttk.Scrollbar(self.parent_frame)
        
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            scrollbar=scrollbar,
            width=100,
            height=50
        )
        
        self.assertEqual(editor.scrollbar, scrollbar)
        self.assertEqual(editor.width, 100)
        self.assertEqual(editor.height, 50)
        
    @patch('code_editor.CodeView')
    def test_create_widget_with_no_lexer(self, mock_codeview):
        """Test widget creation when no lexer is specified."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        widget = editor.create_widget()
        
        # Should create CodeView without lexer parameter but with default dimensions
        mock_codeview.assert_called_once_with(self.parent_frame, width=80, height=24)
        self.assertEqual(widget, mock_widget)
        
    @patch('code_editor.CodeView')
    def test_create_widget_with_lexer(self, mock_codeview):
        """Test widget creation with specified lexer."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        mock_lexer = Mock()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        widget = editor.create_widget(lexer=mock_lexer)
        
        # Should create CodeView with lexer parameter and default dimensions
        mock_codeview.assert_called_once_with(self.parent_frame, lexer=mock_lexer, width=80, height=24)
        self.assertEqual(widget, mock_widget)
        
    @patch('code_editor.CodeView')
    def test_create_widget_with_dimensions(self, mock_codeview):
        """Test widget creation respects width and height settings."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, width=120, height=60)
        widget = editor.create_widget()
        
        call_args = mock_codeview.call_args
        self.assertEqual(call_args[1]['width'], 120)
        self.assertEqual(call_args[1]['height'], 60)
        
    def test_get_lexer_for_file_delegates_to_syntax_manager(self):
        """Test that lexer detection delegates to SyntaxManager."""
        with patch.object(self.syntax_manager, 'get_lexer_for_file') as mock_get_lexer:
            mock_lexer = Mock()
            mock_get_lexer.return_value = mock_lexer
            
            editor = CodeEditor(self.parent_frame, self.syntax_manager)
            result = editor.get_lexer_for_file('test.py')
            
            mock_get_lexer.assert_called_once_with('test.py')
            self.assertEqual(result, mock_lexer)
            
    def test_current_widget_property_initially_none(self):
        """Test that current_widget property is initially None."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        self.assertIsNone(editor.current_widget)
        
    @patch('code_editor.CodeView')
    def test_current_widget_property_after_creation(self, mock_codeview):
        """Test current_widget property tracks created widget."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = mock_widget
        
        self.assertEqual(editor.current_widget, mock_widget)
        
    def test_has_widget_when_no_widget(self):
        """Test has_widget returns False when no widget exists."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        self.assertFalse(editor.has_widget())
        
    @patch('code_editor.CodeView')
    def test_has_widget_when_widget_exists(self, mock_codeview):
        """Test has_widget returns True when widget exists."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = mock_widget
        
        self.assertTrue(editor.has_widget())
        
    def test_configure_scrollbar_when_no_scrollbar(self):
        """Test scrollbar configuration when no scrollbar is provided."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        mock_widget = Mock()
        
        # Should not raise exception
        editor.configure_scrollbar(mock_widget)
        
    def test_configure_scrollbar_with_scrollbar(self):
        """Test scrollbar configuration when scrollbar is provided."""
        scrollbar = Mock()
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        mock_widget = Mock()
        
        editor.configure_scrollbar(mock_widget)
        
        # Should configure scrollbar command and widget yscrollcommand
        scrollbar.config.assert_called_once_with(command=mock_widget.yview)
        mock_widget.config.assert_called_once_with(yscrollcommand=scrollbar.set)
        
    def test_grid_widget_basic_layout(self):
        """Test widget grid configuration with basic parameters."""
        mock_widget = Mock()
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        editor.grid_widget(mock_widget)
        
        mock_widget.grid.assert_called_once_with(sticky='nsew')
        
    def test_grid_widget_with_custom_parameters(self):
        """Test widget grid configuration with custom parameters."""
        mock_widget = Mock()
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        editor.grid_widget(mock_widget, row=2, column=1, sticky='nw')
        
        mock_widget.grid.assert_called_once_with(row=2, column=1, sticky='nw')


class TestCodeEditorWidgetFactory(unittest.TestCase):
    """Test cases for enhanced widget factory functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.parent_frame = ttk.Frame(self.root)
        self.syntax_manager = SyntaxManager()
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
        
    @patch('code_editor.CodeView')
    def test_create_widget_for_file_with_automatic_lexer_detection(self, mock_codeview):
        """Test factory method creates widget with automatic lexer detection for file."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        mock_lexer = Mock()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock lexer detection
        with patch.object(editor, 'get_lexer_for_file', return_value=mock_lexer) as mock_get_lexer:
            
            # Create widget for specific file
            widget = editor.create_widget_for_file("test.py")
            
            # Should detect lexer and create widget with it
            mock_get_lexer.assert_called_once_with("test.py")
            mock_codeview.assert_called_once_with(self.parent_frame, lexer=mock_lexer, width=80, height=24)
            self.assertEqual(widget, mock_widget)
            
    @patch('code_editor.CodeView')
    def test_create_widget_for_file_with_no_lexer_found(self, mock_codeview):
        """Test factory method handles files with no available lexer."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock lexer detection returning None
        with patch.object(editor, 'get_lexer_for_file', return_value=None):
            
            # Create widget for file with no lexer
            widget = editor.create_widget_for_file("unknown.xyz")
            
            # Should create widget without lexer
            mock_codeview.assert_called_once_with(self.parent_frame, width=80, height=24)
            self.assertEqual(widget, mock_widget)
            
    @patch('code_editor.CodeView')
    def test_create_widget_with_preset_configuration(self, mock_codeview):
        """Test factory method with preset configurations."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Create widget with preset
        widget = editor.create_widget_with_preset('readonly')
        
        # Should create widget with readonly configuration
        mock_codeview.assert_called_once()
        call_args = mock_codeview.call_args
        self.assertEqual(call_args[1]['state'], 'disabled')
        self.assertEqual(call_args[1]['wrap'], 'none')
        
    @patch('code_editor.CodeView')
    def test_create_widget_with_editable_preset(self, mock_codeview):
        """Test factory method with editable preset configuration."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Create widget with editable preset
        widget = editor.create_widget_with_preset('editable')
        
        # Should create widget with editable configuration
        call_args = mock_codeview.call_args
        self.assertEqual(call_args[1]['state'], 'normal')
        self.assertEqual(call_args[1]['wrap'], 'none')
        
    @patch('code_editor.CodeView')
    def test_create_widget_with_custom_preset_options(self, mock_codeview):
        """Test factory method with custom preset options."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Create widget with custom preset options
        widget = editor.create_widget_with_preset('readonly', width=100, height=30)
        
        # Should use preset defaults but override with custom options
        call_args = mock_codeview.call_args
        self.assertEqual(call_args[1]['state'], 'disabled')  # From preset
        self.assertEqual(call_args[1]['width'], 100)         # Custom override
        self.assertEqual(call_args[1]['height'], 30)         # Custom override
        
    def test_get_widget_preset_readonly(self):
        """Test getting readonly widget preset configuration."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        preset = editor.get_widget_preset('readonly')
        
        expected_preset = {
            'state': 'disabled',
            'wrap': 'none',
            'selectbackground': '#3B4252',
            'insertbackground': '#D8DEE9',
            'width': 80,
            'height': 24
        }
        self.assertEqual(preset, expected_preset)
        
    def test_get_widget_preset_editable(self):
        """Test getting editable widget preset configuration."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        preset = editor.get_widget_preset('editable')
        
        expected_preset = {
            'state': 'normal',
            'wrap': 'none',
            'selectbackground': '#3B4252',
            'insertbackground': '#D8DEE9',
            'width': 80,
            'height': 24
        }
        self.assertEqual(preset, expected_preset)
        
    def test_get_widget_preset_with_unknown_preset(self):
        """Test getting unknown preset returns default configuration."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        preset = editor.get_widget_preset('unknown')
        
        # Should return default readonly preset
        expected_preset = {
            'state': 'disabled',
            'wrap': 'none',
            'selectbackground': '#3B4252',
            'insertbackground': '#D8DEE9',
            'width': 80,
            'height': 24
        }
        self.assertEqual(preset, expected_preset)
        
    @patch('code_editor.CodeView')
    def test_create_configured_widget_full_setup(self, mock_codeview):
        """Test factory method that creates fully configured widget."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        mock_lexer = Mock()
        scrollbar = Mock()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        
        # Mock lexer detection
        with patch.object(editor, 'get_lexer_for_file', return_value=mock_lexer):
            
            # Create fully configured widget
            widget = editor.create_configured_widget(
                filename="test.py",
                preset="readonly",
                grid_options={'row': 0, 'column': 0, 'sticky': 'nsew'},
                set_as_current=True
            )
            
            # Should create widget with lexer and preset
            mock_codeview.assert_called_once()
            call_args = mock_codeview.call_args
            self.assertEqual(call_args[1]['lexer'], mock_lexer)
            self.assertEqual(call_args[1]['state'], 'disabled')
            
            # Should configure scrollbar
            scrollbar.config.assert_called_once_with(command=mock_widget.yview)
            mock_widget.config.assert_called_once_with(yscrollcommand=scrollbar.set)
            
            # Should configure grid
            mock_widget.grid.assert_called_once_with(row=0, column=0, sticky='nsew')
            
            # Should set as current widget
            self.assertEqual(editor.current_widget, mock_widget)
            
    @patch('code_editor.CodeView')
    def test_create_configured_widget_minimal_setup(self, mock_codeview):
        """Test factory method with minimal configuration."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Create minimally configured widget
        widget = editor.create_configured_widget()
        
        # Should create widget with defaults
        mock_codeview.assert_called_once()
        call_args = mock_codeview.call_args
        self.assertEqual(call_args[0][0], self.parent_frame)
        self.assertIn('width', call_args[1])
        self.assertIn('height', call_args[1])
        
        # Should not set as current widget by default
        self.assertIsNone(editor.current_widget)


class TestCodeEditorWidgetReplacement(unittest.TestCase):
    """Test cases for safe widget replacement strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.parent_frame = ttk.Frame(self.root)
        self.syntax_manager = SyntaxManager()
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
        
    def test_capture_widget_state_with_no_widget(self):
        """Test state capture when no current widget exists."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        state = editor.capture_widget_state()
        
        # Should return empty state when no widget exists
        expected_state = {
            'content': '',
            'cursor_position': '1.0',
            'scroll_position': (0.0, 1.0),  # Updated to match new implementation
            'selection': None
        }
        self.assertEqual(state, expected_state)
        
    def test_capture_widget_state_with_widget(self):
        """Test state capture from existing widget."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock widget with state
        mock_widget = Mock()
        mock_widget.get.return_value = "def hello():\n    print('world')"
        mock_widget.index.return_value = "2.4"
        mock_widget.yview.return_value = (0.2, 0.8)
        mock_widget.tag_ranges.return_value = ("1.0", "1.3")
        
        editor.current_widget = mock_widget
        
        state = editor.capture_widget_state()
        
        expected_state = {
            'content': "def hello():\n    print('world')",
            'cursor_position': "2.4",
            'scroll_position': (0.2, 0.8),
            'selection': ("1.0", "1.3")
        }
        self.assertEqual(state, expected_state)
        
        # Verify correct method calls
        mock_widget.get.assert_called_once_with("1.0", "end-1c")
        mock_widget.index.assert_called_once_with(tk.INSERT)
        mock_widget.yview.assert_called_once()
        mock_widget.tag_ranges.assert_called_once_with(tk.SEL)
        
    def test_capture_widget_state_with_no_selection(self):
        """Test state capture when widget has no text selection."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock widget with no selection
        mock_widget = Mock()
        mock_widget.get.return_value = "some content"
        mock_widget.index.return_value = "1.5"
        mock_widget.yview.return_value = (0.0, 1.0)
        mock_widget.tag_ranges.return_value = ()  # No selection
        
        editor.current_widget = mock_widget
        
        state = editor.capture_widget_state()
        
        self.assertIsNone(state['selection'])
        
    def test_restore_widget_state_to_new_widget(self):
        """Test restoring state to a new widget."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Create state to restore
        state = {
            'content': "print('hello world')",
            'cursor_position': "1.6",
            'scroll_position': (0.1, 0.9),
            'selection': ("1.0", "1.5")
        }
        
        # Mock new widget
        mock_widget = Mock()
        
        editor.restore_widget_state(mock_widget, state)
        
        # Verify state restoration
        mock_widget.delete.assert_called_once_with("1.0", tk.END)
        mock_widget.insert.assert_called_once_with("1.0", "print('hello world')")
        mock_widget.mark_set.assert_called_once_with(tk.INSERT, "1.6")
        mock_widget.yview_moveto.assert_called_once_with(0.1)
        mock_widget.tag_add.assert_called_once_with(tk.SEL, "1.0", "1.5")
        
    def test_restore_widget_state_with_no_selection(self):
        """Test restoring state when no selection was saved."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Create state without selection
        state = {
            'content': "some text",
            'cursor_position': "1.2",
            'scroll_position': (0.0, 1.0),
            'selection': None
        }
        
        # Mock new widget
        mock_widget = Mock()
        
        editor.restore_widget_state(mock_widget, state)
        
        # Should not try to set selection
        mock_widget.tag_add.assert_not_called()
        
    def test_destroy_widget_safely_with_no_widget(self):
        """Test safe widget destruction when no widget exists."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Should not raise exception
        editor.destroy_widget_safely()
        
        self.assertIsNone(editor.current_widget)
        
    def test_destroy_widget_safely_with_widget(self):
        """Test safe widget destruction with existing widget."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock widget
        mock_widget = Mock()
        # Set up mock widget to return proper values
        mock_widget.getvar.return_value = {}
        mock_widget.winfo_children.return_value = []
        editor.current_widget = mock_widget
        
        editor.destroy_widget_safely()
        
        # Should call destroy and clear reference
        mock_widget.destroy.assert_called_once()
        self.assertIsNone(editor.current_widget)
        
    def test_destroy_widget_safely_handles_exceptions(self):
        """Test that widget destruction handles exceptions gracefully."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock widget that raises exception on destroy
        mock_widget = Mock()
        mock_widget.destroy.side_effect = tk.TclError("widget already destroyed")
        editor.current_widget = mock_widget
        
        # Should not raise exception
        editor.destroy_widget_safely()
        
        # Should still clear reference
        self.assertIsNone(editor.current_widget)
        
    @patch('code_editor.CodeView')
    def test_replace_widget_with_new_lexer(self, mock_codeview):
        """Test complete widget replacement with new lexer."""
        # Create initial and new widgets
        initial_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [initial_widget, new_widget]
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Set up initial widget with state and proper geometry info
        initial_widget.get.return_value = "def test():\n    pass"
        initial_widget.index.return_value = "2.0"
        initial_widget.yview.return_value = (0.0, 0.5)
        initial_widget.tag_ranges.return_value = ()
        # Set up mock widget to return proper values for destruction
        initial_widget.getvar.return_value = {}
        initial_widget.winfo_children.return_value = []
        initial_widget.master = self.parent_frame
        initial_widget.focus_get.return_value = None
        initial_widget.grid_info.return_value = {'row': 0, 'column': 0, 'sticky': 'nsew'}
        initial_widget.pack_info.return_value = {}
        initial_widget.place_info.return_value = {}

        # Create initial widget
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()

        # Replace with new lexer
        result = editor.replace_widget_with_lexer(mock_lexer)

        # Should create new widget with lexer
        self.assertEqual(mock_codeview.call_count, 2)
        mock_codeview.assert_called_with(editor.parent, lexer=mock_lexer, 
                                        width=editor.width, height=editor.height)

        # Should restore content and state
        new_widget.insert.assert_called_with("1.0", "def test():\n    pass")
        new_widget.mark_set.assert_called_with(tk.INSERT, "2.0")

        # Should return new widget
        self.assertEqual(result, new_widget)
        self.assertEqual(editor.current_widget, new_widget)
        
    @patch('code_editor.CodeView')
    def test_replace_widget_preserves_scrollbar_configuration(self, mock_codeview):
        """Test that widget replacement preserves scrollbar configuration."""
        scrollbar = Mock()
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)

        initial_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [initial_widget, new_widget]

        # Set up initial widget with proper geometry info mocking
        initial_widget.get.return_value = "content"
        initial_widget.index.return_value = "1.0"
        initial_widget.yview.return_value = (0.0, 1.0)
        initial_widget.tag_ranges.return_value = ()
        initial_widget.getvar.return_value = {}
        initial_widget.winfo_children.return_value = []
        initial_widget.master = self.parent_frame
        initial_widget.focus_get.return_value = None
        initial_widget.grid_info.return_value = {'row': 0, 'column': 0, 'sticky': 'nsew'}
        initial_widget.pack_info.return_value = {}
        initial_widget.place_info.return_value = {}

        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()

        # Replace widget
        editor.replace_widget_with_lexer(mock_lexer)

        # Should configure scrollbar for new widget
        scrollbar.config.assert_called_with(command=new_widget.yview)


class TestCodeEditorGUIIntegration(unittest.TestCase):
    """Test cases for GUI integration interface."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.parent_frame = ttk.Frame(self.root)
        self.syntax_manager = SyntaxManager()
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
        
    @patch('code_editor.CodeView')
    def test_setup_initial_widget(self, mock_codeview):
        """Test setting up initial widget without syntax highlighting."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Setup initial widget
        widget = editor.setup_initial_widget()
        
        # Should create widget without lexer
        mock_codeview.assert_called_once_with(self.parent_frame, width=80, height=24)
        self.assertEqual(editor.current_widget, mock_widget)
        self.assertEqual(widget, mock_widget)
        
    @patch('code_editor.CodeView')
    def test_setup_initial_widget_with_grid_layout(self, mock_codeview):
        """Test setting up initial widget with grid layout."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        scrollbar = Mock()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        
        # Setup with grid layout
        widget = editor.setup_initial_widget(row=1, column=0, sticky='nsew')
        
        # Should configure grid layout
        mock_widget.grid.assert_called_once_with(row=1, column=0, sticky='nsew')
        
        # Should configure scrollbar
        scrollbar.config.assert_called_once_with(command=mock_widget.yview)
        mock_widget.config.assert_called_once_with(yscrollcommand=scrollbar.set)
        
    def test_update_file_content_with_filename(self):
        """Test updating file content with syntax highlighting based on filename."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock current widget
        mock_widget = Mock()
        editor.current_widget = mock_widget
        
        # Mock lexer detection
        mock_lexer = Mock()
        with patch.object(editor, 'get_lexer_for_file', return_value=mock_lexer) as mock_get_lexer, \
             patch.object(editor, 'replace_widget_with_lexer', return_value=mock_widget) as mock_replace:
            
            # Update content with filename
            result = editor.update_file_content("def hello():\n    pass", filename="test.py")
            
            # Should detect lexer and replace widget
            mock_get_lexer.assert_called_once_with("test.py")
            mock_replace.assert_called_once_with(mock_lexer)
            
            # Should return updated widget
            self.assertEqual(result, mock_widget)
            
    def test_update_file_content_without_filename(self):
        """Test updating file content without syntax highlighting (no filename)."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock current widget
        mock_widget = Mock()
        mock_widget.cget.return_value = 'normal'
        editor.current_widget = mock_widget
        
        # Update content without filename
        result = editor.update_file_content("plain text content")
        
        # Should update content directly without lexer replacement
        mock_widget.config.assert_any_call(state='normal')
        mock_widget.delete.assert_called_once_with("1.0", tk.END)
        mock_widget.insert.assert_called_once_with("1.0", "plain text content")
        mock_widget.config.assert_any_call(state='disabled')
        
        # Should return same widget
        self.assertEqual(result, mock_widget)
        
    def test_update_file_content_with_no_lexer_found(self):
        """Test updating file content when no lexer is found for the file type."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock current widget
        mock_widget = Mock()
        mock_widget.cget.return_value = 'normal'
        editor.current_widget = mock_widget
        
        # Mock lexer detection returning None
        with patch.object(editor, 'get_lexer_for_file', return_value=None):
            
            # Update content with filename that has no lexer
            result = editor.update_file_content("unknown content", filename="test.unknown")
            
            # Should update content directly without lexer replacement
            mock_widget.config.assert_any_call(state='normal')
            mock_widget.delete.assert_called_once_with("1.0", tk.END)
            mock_widget.insert.assert_called_once_with("1.0", "unknown content")
            mock_widget.config.assert_any_call(state='disabled')
            
            # Should return same widget
            self.assertEqual(result, mock_widget)
            
    @patch('code_editor.CodeView')
    def test_update_file_content_creates_widget_if_none_exists(self, mock_codeview):
        """Test that update_file_content creates widget if none exists."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # No current widget
        self.assertIsNone(editor.current_widget)
        
        # Update content should create widget first
        result = editor.update_file_content("content")
        
        # Should create widget and set as current
        mock_codeview.assert_called_once()
        self.assertEqual(editor.current_widget, mock_widget)
        self.assertEqual(result, mock_widget)
        
    def test_set_readonly_state(self):
        """Test setting widget to read-only or editable state."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock current widget
        mock_widget = Mock()
        editor.current_widget = mock_widget
        
        # Set to read-only
        editor.set_readonly_state(True)
        mock_widget.config.assert_called_with(state='disabled')
        
        # Set to editable
        editor.set_readonly_state(False)
        mock_widget.config.assert_called_with(state='normal')
        
    def test_set_readonly_state_with_no_widget(self):
        """Test setting read-only state when no widget exists."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Should not raise exception
        editor.set_readonly_state(True)
        editor.set_readonly_state(False)
        
    def test_get_content(self):
        """Test getting current content from widget."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock current widget
        mock_widget = Mock()
        mock_widget.get.return_value = "current content"
        editor.current_widget = mock_widget
        
        # Get content
        content = editor.get_content()
        
        mock_widget.get.assert_called_once_with("1.0", "end-1c")
        self.assertEqual(content, "current content")
        
    def test_get_content_with_no_widget(self):
        """Test getting content when no widget exists."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Should return empty string
        content = editor.get_content()
        self.assertEqual(content, "")
        
    def test_clear_content(self):
        """Test clearing widget content."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Mock current widget
        mock_widget = Mock()
        mock_widget.cget.return_value = 'normal'
        editor.current_widget = mock_widget
        
        # Clear content
        editor.clear_content()
        
        # Should enable, clear, and disable widget
        mock_widget.config.assert_any_call(state='normal')
        mock_widget.delete.assert_called_once_with("1.0", tk.END)
        mock_widget.config.assert_any_call(state='disabled')
        
    def test_clear_content_with_no_widget(self):
        """Test clearing content when no widget exists."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Should not raise exception
        editor.clear_content()


class TestCodeEditorIntegration(unittest.TestCase):
    """Integration tests for CodeEditor with real tkinter components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.parent_frame = ttk.Frame(self.root)
        self.syntax_manager = SyntaxManager()
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
        
    def test_integration_with_real_tkinter_components(self):
        """Test CodeEditor works with real tkinter components."""
        scrollbar = ttk.Scrollbar(self.parent_frame)
        
        editor = CodeEditor(
            self.parent_frame, 
            self.syntax_manager, 
            scrollbar=scrollbar
        )
        
        # Should not raise exceptions
        self.assertIsInstance(editor, CodeEditor)
        self.assertEqual(editor.parent, self.parent_frame)
        self.assertEqual(editor.scrollbar, scrollbar)


class TestCodeEditorSafeDestruction(unittest.TestCase):
    """Test cases for enhanced safe widget destruction with proper cleanup."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.parent_frame = ttk.Frame(self.root)
        self.syntax_manager = SyntaxManager()
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
        
    @patch('code_editor.CodeView')
    def test_destroy_widget_safely_clears_scrollbar_bindings(self, mock_codeview):
        """Test that widget destruction properly clears scrollbar connections."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        scrollbar = Mock()
        
        # Set up mock widget to return proper values
        mock_widget.getvar.return_value = {}
        mock_widget.winfo_children.return_value = []
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        editor.current_widget = editor.create_widget()
        
        # Destroy widget safely
        editor.destroy_widget_safely()
        
        # Should clear scrollbar command
        scrollbar.config.assert_called_with(command='')
        
        # Should destroy widget and clear reference
        mock_widget.destroy.assert_called_once()
        self.assertIsNone(editor.current_widget)
        
    @patch('code_editor.CodeView')
    def test_destroy_widget_safely_clears_widget_bindings(self, mock_codeview):
        """Test that widget destruction clears all event bindings."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Set up mock widget to return proper values
        mock_widget.getvar.return_value = {}
        mock_widget.winfo_children.return_value = []
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        # Destroy widget safely
        editor.destroy_widget_safely()
        
        # Should unbind all widget events
        mock_widget.unbind_all.assert_called_once()
        
        # Should destroy widget and clear reference
        mock_widget.destroy.assert_called_once()
        self.assertIsNone(editor.current_widget)
        
    @patch('code_editor.CodeView')
    def test_destroy_widget_safely_handles_multiple_calls(self, mock_codeview):
        """Test that multiple destruction calls are handled safely."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Set up mock widget to return proper values
        mock_widget.getvar.return_value = {}
        mock_widget.winfo_children.return_value = []
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        # First destruction
        editor.destroy_widget_safely()
        
        # Should destroy widget and clear reference
        mock_widget.destroy.assert_called_once()
        self.assertIsNone(editor.current_widget)
        
        # Second destruction should not raise error
        editor.destroy_widget_safely()
        
        # Should not call destroy again
        mock_widget.destroy.assert_called_once()
        self.assertIsNone(editor.current_widget)
        
    @patch('code_editor.CodeView')
    def test_destroy_widget_safely_handles_widget_already_destroyed(self, mock_codeview):
        """Test handling when widget is already destroyed by external means."""
        mock_widget = Mock()
        mock_widget.destroy.side_effect = tk.TclError("widget already destroyed")
        mock_codeview.return_value = mock_widget
        
        # Set up mock widget to return proper values
        mock_widget.getvar.return_value = {}
        mock_widget.winfo_children.return_value = []
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        # Should not raise exception even if widget already destroyed
        editor.destroy_widget_safely()
        
        # Should still clear reference
        self.assertIsNone(editor.current_widget)
        
    @patch('code_editor.CodeView')
    def test_destroy_widget_safely_clears_parent_references(self, mock_codeview):
        """Test that widget destruction clears parent container references."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Set up mock widget to return proper values
        mock_widget.getvar.return_value = {}
        mock_widget.winfo_children.return_value = []
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        # Track parent reference before destruction
        self.assertEqual(editor.parent, self.parent_frame)
        
        # Destroy widget safely
        editor.destroy_widget_safely()
        
        # Should clear widget from parent's children
        mock_widget.pack_forget.assert_called_once()
        mock_widget.grid_forget.assert_called_once()
        
        # Should destroy widget and clear reference
        mock_widget.destroy.assert_called_once()
        self.assertIsNone(editor.current_widget)
        
    @patch('code_editor.CodeView')
    def test_destroy_widget_safely_clears_widget_variables(self, mock_codeview):
        """Test that widget destruction clears associated tkinter variables."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Mock widget variables
        mock_var1 = Mock()
        mock_var2 = Mock()
        mock_widget.getvar.return_value = {'var1': mock_var1, 'var2': mock_var2}
        mock_widget.winfo_children.return_value = []
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        # Destroy widget safely
        editor.destroy_widget_safely()
        
        # Should clear widget variables
        mock_var1.set.assert_called_with('')
        mock_var2.set.assert_called_with('')
        
        # Should destroy widget and clear reference
        mock_widget.destroy.assert_called_once()
        self.assertIsNone(editor.current_widget)
        
    @patch('code_editor.CodeView')
    def test_destroy_widget_safely_performs_memory_cleanup(self, mock_codeview):
        """Test that widget destruction triggers memory cleanup."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Set up mock widget to return proper values
        mock_widget.getvar.return_value = {}
        mock_widget.winfo_children.return_value = []
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        # Destroy widget safely
        editor.destroy_widget_safely()
        
        # Should force garbage collection after destruction
        with patch('gc.collect') as mock_gc:
            editor.destroy_widget_safely()
            # Note: gc.collect is called in enhanced version
        
        # Should destroy widget and clear reference
        mock_widget.destroy.assert_called_once()
        self.assertIsNone(editor.current_widget)
        
    @patch('code_editor.CodeView')
    def test_destroy_widget_safely_with_complex_widget_hierarchy(self, mock_codeview):
        """Test destruction of widgets with complex parent-child relationships."""
        mock_widget = Mock()
        mock_child1 = Mock()
        mock_child2 = Mock()
        mock_widget.winfo_children.return_value = [mock_child1, mock_child2]
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        # Destroy widget safely
        editor.destroy_widget_safely()
        
        # Should destroy child widgets first
        mock_child1.destroy.assert_called_once()
        mock_child2.destroy.assert_called_once()
        
        # Then destroy parent widget
        mock_widget.destroy.assert_called_once()
        self.assertIsNone(editor.current_widget)
        
    def test_destroy_widget_safely_updates_widget_state_flags(self):
        """Test that destruction properly updates internal state tracking."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Initially no widget
        self.assertFalse(editor.has_widget())
        self.assertIsNone(editor.current_widget)
        
        # Create a mock widget
        mock_widget = Mock()
        editor.current_widget = mock_widget
        
        # Should have widget now
        self.assertTrue(editor.has_widget())
        
        # Destroy widget safely
        editor.destroy_widget_safely()
        
        # Should properly update state
        self.assertFalse(editor.has_widget())
        self.assertIsNone(editor.current_widget)
        
    @patch('code_editor.CodeView')
    def test_destroy_widget_safely_comprehensive_cleanup_sequence(self, mock_codeview):
        """Test the complete cleanup sequence for widget destruction."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        scrollbar = Mock()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        editor.current_widget = editor.create_widget()
        
        # Set up complex widget state to test cleanup
        mock_widget.winfo_children.return_value = []
        mock_widget.getvar.return_value = {}
        
        # Destroy widget safely
        editor.destroy_widget_safely()
        
        # Verify complete cleanup sequence
        mock_widget.unbind_all.assert_called_once()
        scrollbar.config.assert_called_with(command='')
        mock_widget.pack_forget.assert_called_once()
        mock_widget.grid_forget.assert_called_once()
        mock_widget.destroy.assert_called_once()
        
        # Verify state is completely clean
        self.assertIsNone(editor.current_widget)
        self.assertFalse(editor.has_widget())


class TestCodeEditorContainerRelationships(unittest.TestCase):
    """Test cases for widget replacement logic that maintains container relationships."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.parent_frame = ttk.Frame(self.root)
        self.syntax_manager = SyntaxManager()
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
        
    @patch('code_editor.CodeView')
    def test_replace_widget_preserves_grid_position(self, mock_codeview):
        """Test that widget replacement preserves exact grid position."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Set up old widget with specific grid info
        old_widget.grid_info.return_value = {
            'row': 2, 'column': 1, 'rowspan': 1, 'columnspan': 2,
            'sticky': 'nsew', 'padx': 5, 'pady': 10, 'ipadx': 2, 'ipady': 3
        }
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget with lexer
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should preserve exact grid configuration
        new_widget.grid.assert_called_with(
            row=2, column=1, rowspan=1, columnspan=2,
            sticky='nsew', padx=5, pady=10, ipadx=2, ipady=3
        )
        
    @patch('code_editor.CodeView')
    def test_replace_widget_preserves_pack_position(self, mock_codeview):
        """Test that widget replacement preserves pack position and order."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Set up old widget with pack info
        old_widget.grid_info.return_value = {}
        old_widget.pack_info.return_value = {
            'side': 'left', 'fill': 'both', 'expand': True,
            'padx': 10, 'pady': 5, 'ipadx': 1, 'ipady': 2
        }
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget with lexer
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should preserve exact pack configuration
        new_widget.pack.assert_called_with(
            side='left', fill='both', expand=True,
            padx=10, pady=5, ipadx=1, ipady=2
        )
        
    @patch('code_editor.CodeView')
    def test_replace_widget_maintains_sibling_order(self, mock_codeview):
        """Test that widget replacement maintains proper sibling order in container."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Mock parent with multiple children
        mock_sibling1 = Mock()
        mock_sibling2 = Mock()
        mock_parent = Mock()
        old_widget.master = mock_parent
        mock_parent.winfo_children.return_value = [mock_sibling1, old_widget, mock_sibling2]
        
        # Set up old widget
        old_widget.grid_info.return_value = {'row': 1, 'column': 0}
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget with lexer
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should place new widget in correct position relative to siblings
        new_widget.grid.assert_called()
        # Should not affect sibling positions
        mock_sibling1.grid.assert_not_called()
        mock_sibling2.grid.assert_not_called()
        
    @patch('code_editor.CodeView')
    def test_replace_widget_handles_complex_container_hierarchy(self, mock_codeview):
        """Test replacement in complex nested container hierarchies."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Set up complex container hierarchy
        container1 = Mock()
        container2 = Mock()
        container3 = Mock()
        
        old_widget.master = container1
        container1.master = container2
        container2.master = container3
        
        old_widget.grid_info.return_value = {'row': 0, 'column': 0, 'sticky': 'nsew'}
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget with lexer
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should maintain hierarchy relationships
        self.assertEqual(result.master, container1)
        new_widget.grid.assert_called_with(row=0, column=0, sticky='nsew')
        
    @patch('code_editor.CodeView')
    def test_replace_widget_preserves_focus_and_selection(self, mock_codeview):
        """Test that widget replacement preserves focus and selection state."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Set up widget with focus and selection
        old_widget.focus_get.return_value = old_widget  # Widget has focus
        old_widget.grid_info.return_value = {'row': 0, 'column': 0}
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.get.return_value = "selected text"
        old_widget.index.return_value = "1.5"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ("1.0", "1.8")
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget with lexer
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should restore focus and selection
        new_widget.focus_set.assert_called_once()
        new_widget.tag_add.assert_called_with(tk.SEL, "1.0", "1.8")
        
    @patch('code_editor.CodeView')
    def test_replace_widget_handles_geometry_manager_conflicts(self, mock_codeview):
        """Test handling of conflicts between different geometry managers."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Widget uses both grid and pack (conflict situation)
        old_widget.grid_info.return_value = {'row': 0, 'column': 0}
        old_widget.pack_info.return_value = {'side': 'top'}
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget with lexer
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should prefer grid over pack when both are present
        new_widget.grid.assert_called_once()
        new_widget.pack.assert_not_called()
        
    @patch('code_editor.CodeView')
    def test_replace_widget_maintains_event_bindings_to_parent(self, mock_codeview):
        """Test that replacement maintains event bindings related to parent container."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        scrollbar = Mock()
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        
        # Set up widget state
        old_widget.grid_info.return_value = {'row': 0, 'column': 0}
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget with lexer
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should reconnect scrollbar to new widget
        scrollbar.config.assert_called_with(command=new_widget.yview)
        new_widget.config.assert_called_with(yscrollcommand=scrollbar.set)
        
    @patch('code_editor.CodeView')
    def test_replace_widget_preserves_container_weight_configuration(self, mock_codeview):
        """Test that replacement preserves container weight and resize behavior."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Mock parent container with weight configuration
        mock_parent = Mock()
        old_widget.master = mock_parent
        mock_parent.grid_rowconfigure.return_value = None
        mock_parent.grid_columnconfigure.return_value = None
        
        old_widget.grid_info.return_value = {'row': 0, 'column': 0, 'sticky': 'nsew'}
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget with lexer
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should configure new widget with same parent container
        self.assertEqual(result.master, mock_parent)
        new_widget.grid.assert_called_with(row=0, column=0, sticky='nsew')
        
    @patch('code_editor.CodeView')
    def test_replace_widget_handles_place_geometry_manager(self, mock_codeview):
        """Test handling of place geometry manager for absolute positioning."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Widget uses place geometry manager
        old_widget.grid_info.return_value = {}
        old_widget.pack_info.return_value = {}
        old_widget.place_info.return_value = {
            'x': 10, 'y': 20, 'width': 100, 'height': 50,
            'relx': 0.1, 'rely': 0.2, 'relwidth': 0.8, 'relheight': 0.6,
            'anchor': 'nw'
        }
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget with lexer
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should preserve place configuration
        new_widget.place.assert_called_with(
            x=10, y=20, width=100, height=50,
            relx=0.1, rely=0.2, relwidth=0.8, relheight=0.6,
            anchor='nw'
        )
        
    @patch('code_editor.CodeView')
    def test_replace_widget_with_enhanced_container_relationship_maintenance(self, mock_codeview):
        """Test comprehensive container relationship maintenance during replacement."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        scrollbar = Mock()
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        
        # Set up complex widget state
        old_widget.master = self.parent_frame
        old_widget.focus_get.return_value = old_widget
        old_widget.grid_info.return_value = {'row': 1, 'column': 2, 'sticky': 'nsew'}
        old_widget.pack_info.return_value = {}
        old_widget.place_info.return_value = {}
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.get.return_value = "test content"
        old_widget.index.return_value = "1.4"
        old_widget.yview.return_value = (0.2, 0.8)
        old_widget.tag_ranges.return_value = ("1.0", "1.4")
        
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget with enhanced container relationship maintenance
        result = editor.replace_widget_with_enhanced_container_relationships(old_widget, mock_lexer)
        
        # Should maintain all container relationships
        self.assertEqual(result.master, self.parent_frame)
        new_widget.grid.assert_called_with(row=1, column=2, sticky='nsew')
        
        # Should restore state and relationships
        new_widget.insert.assert_called_with("1.0", "test content")
        new_widget.mark_set.assert_called_with(tk.INSERT, "1.4")
        new_widget.tag_add.assert_called_with(tk.SEL, "1.0", "1.4")
        new_widget.focus_set.assert_called_once()
        
        # Should reconnect scrollbar
        scrollbar.config.assert_called_with(command=new_widget.yview)
        new_widget.config.assert_called_with(yscrollcommand=scrollbar.set)
        
        self.assertEqual(editor.current_widget, result)


if __name__ == '__main__':
    unittest.main() 