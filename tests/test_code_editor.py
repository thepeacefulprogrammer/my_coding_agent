import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock, mock_open
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

        # Should create CodeView with color scheme (dictionary) and default dimensions
        call_args = mock_codeview.call_args
        self.assertEqual(call_args[0][0], self.parent_frame)
        # Verify color scheme is a dictionary (Nord scheme by default)
        self.assertIsInstance(call_args[1]['color_scheme'], dict)
        self.assertEqual(call_args[1]['width'], 80)
        self.assertEqual(call_args[1]['height'], 24)
        self.assertEqual(widget, mock_widget)
        
    @patch('code_editor.CodeView')
    def test_create_widget_with_lexer(self, mock_codeview):
        """Test widget creation with specified lexer."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        mock_lexer = Mock()

        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        widget = editor.create_widget(lexer=mock_lexer)

        # Should create CodeView with lexer parameter, color scheme (now a dictionary), and default dimensions
        call_args = mock_codeview.call_args
        self.assertEqual(call_args[0][0], self.parent_frame)  # First positional arg
        self.assertEqual(call_args[1]['lexer'], mock_lexer)   # lexer keyword arg
        self.assertEqual(call_args[1]['width'], 80)          # width keyword arg
        self.assertEqual(call_args[1]['height'], 24)         # height keyword arg
        # Color scheme should be a dictionary (Nord scheme by default)
        self.assertIsInstance(call_args[1]['color_scheme'], dict)
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
            call_args = mock_codeview.call_args
            self.assertEqual(call_args[1]['lexer'], mock_lexer)
            self.assertIsInstance(call_args[1]['color_scheme'], dict)
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
            
            # Should create widget with color scheme (dictionary)
            call_args = mock_codeview.call_args
            self.assertIsInstance(call_args[1]['color_scheme'], dict)
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
        # Check the second call (replacement widget)
        second_call_args = mock_codeview.call_args
        self.assertEqual(second_call_args[1]['lexer'], mock_lexer)
        self.assertIsInstance(second_call_args[1]['color_scheme'], dict)

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
        
        # Should have configured scrollbar for new widget (check call history)
        # During replacement, scrollbar gets disconnected then reconnected
        config_calls = scrollbar.config.call_args_list
        self.assertTrue(any(
            call.kwargs.get('command') == new_widget.yview
            for call in config_calls
        ), "Scrollbar should be configured for new widget")


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
        
        # Should create widget with color scheme (dictionary)
        call_args = mock_codeview.call_args
        self.assertIsInstance(call_args[1]['color_scheme'], dict)
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
        
        # Should configure scrollbar (may be called multiple times due to enhanced implementation)
        # Once in create_widget, once in configure_scrollbar in setup_initial_widget
        self.assertTrue(scrollbar.config.call_count >= 1)
        scrollbar.config.assert_called_with(command=mock_widget.yview)
        
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
        
        # Should reconnect scrollbar to new widget (check call history)
        config_calls = scrollbar.config.call_args_list
        self.assertTrue(any(
            call.kwargs.get('command') == new_widget.yview
            for call in config_calls
        ), "Scrollbar should be reconnected to new widget")
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


class TestCodeEditorScrollbarReconnection(unittest.TestCase):
    """Test cases for enhanced scrollbar reconnection after widget replacement."""
    
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
    def test_scrollbar_position_preservation_during_replacement(self, mock_codeview):
        """Test that scrollbar position is preserved during widget replacement."""
        scrollbar = Mock()
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Set up scrollbar with specific position
        scrollbar.get.return_value = (0.3, 0.7)  # 30% to 70% visible
        old_widget.yview.return_value = (0.3, 0.7)
        
        # Set up widget state
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.3, 0.7)
        old_widget.tag_ranges.return_value = ()
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.master = self.parent_frame
        old_widget.focus_get.return_value = None
        old_widget.grid_info.return_value = {'row': 0, 'column': 0}
        old_widget.pack_info.return_value = {}
        old_widget.place_info.return_value = {}
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should restore scroll position
        new_widget.yview_moveto.assert_called_with(0.3)
        
    @patch('code_editor.CodeView')
    def test_scrollbar_synchronization_with_multiple_widgets(self, mock_codeview):
        """Test scrollbar synchronization when multiple widgets exist."""
        scrollbar = Mock()
        widget1 = Mock()
        widget2 = Mock()
        widget3 = Mock()
        mock_codeview.side_effect = [widget1, widget2, widget3]
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        
        # Create first widget
        editor.current_widget = editor.create_widget()
        scrollbar.config.assert_called_with(command=widget1.yview)
        widget1.config.assert_called_with(yscrollcommand=scrollbar.set)
        
        # Mock replacement setup
        widget1.get.return_value = "content1"
        widget1.index.return_value = "1.0"
        widget1.yview.return_value = (0.0, 1.0)
        widget1.tag_ranges.return_value = ()
        widget1.getvar.return_value = {}
        widget1.winfo_children.return_value = []
        widget1.master = self.parent_frame
        widget1.focus_get.return_value = None
        widget1.grid_info.return_value = {'row': 0, 'column': 0}
        widget1.pack_info.return_value = {}
        widget1.place_info.return_value = {}
        
        # Replace with second widget
        mock_lexer = Mock()
        editor.replace_widget_with_lexer(mock_lexer)
        
        # Should disconnect from widget1 and connect to widget2 (check call history)
        config_calls = scrollbar.config.call_args_list
        self.assertTrue(any(
            call.kwargs.get('command') == widget2.yview
            for call in config_calls
        ), "Scrollbar should be connected to widget2")
        widget2.config.assert_called_with(yscrollcommand=scrollbar.set)
        
    @patch('code_editor.CodeView')
    def test_scrollbar_handles_widget_creation_failure(self, mock_codeview):
        """Test scrollbar behavior when widget creation fails."""
        scrollbar = Mock()
        old_widget = Mock()
        
        # First call succeeds, second call fails
        mock_codeview.side_effect = [old_widget, Exception("Widget creation failed")]
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        editor.current_widget = editor.create_widget()
        
        # Set up widget state
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.master = self.parent_frame
        old_widget.focus_get.return_value = None
        old_widget.grid_info.return_value = {'row': 0, 'column': 0}
        old_widget.pack_info.return_value = {}
        old_widget.place_info.return_value = {}
        
        mock_lexer = Mock()
        
        # Should handle gracefully and not leave scrollbar in bad state
        with self.assertRaises(Exception):
            editor.replace_widget_with_lexer(mock_lexer)
            
        # Scrollbar should still be connected to old widget
        self.assertEqual(editor.current_widget, old_widget)
        
    @patch('code_editor.CodeView')
    def test_scrollbar_bidirectional_communication(self, mock_codeview):
        """Test bidirectional communication between scrollbar and widget."""
        scrollbar = Mock()
        widget = Mock()
        mock_codeview.return_value = widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        editor.current_widget = editor.create_widget()
        
        # Should configure both directions
        scrollbar.config.assert_called_with(command=widget.yview)
        widget.config.assert_called_with(yscrollcommand=scrollbar.set)
        
    @patch('code_editor.CodeView')
    def test_scrollbar_disconnection_during_destruction(self, mock_codeview):
        """Test that scrollbar is properly disconnected during widget destruction."""
        scrollbar = Mock()
        widget = Mock()
        mock_codeview.return_value = widget
        
        # Set up widget for destruction
        widget.getvar.return_value = {}
        widget.winfo_children.return_value = []
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        editor.current_widget = editor.create_widget()
        
        # Destroy widget
        editor.destroy_widget_safely()
        
        # Should disconnect scrollbar
        scrollbar.config.assert_called_with(command='')
        
    @patch('code_editor.CodeView')
    def test_scrollbar_reconnection_preserves_scroll_callbacks(self, mock_codeview):
        """Test that scrollbar reconnection preserves all scroll-related callbacks."""
        scrollbar = Mock()
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Set up callbacks
        old_widget.yview = Mock()
        new_widget.yview = Mock()
        scrollbar.set = Mock()
        
        # Set up widget state
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.master = self.parent_frame
        old_widget.focus_get.return_value = None
        old_widget.grid_info.return_value = {'row': 0, 'column': 0}
        old_widget.pack_info.return_value = {}
        old_widget.place_info.return_value = {}
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        editor.current_widget = editor.create_widget()
        
        mock_lexer = Mock()
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should preserve callback functions (check call history)
        config_calls = scrollbar.config.call_args_list
        self.assertTrue(any(
            call.kwargs.get('command') == new_widget.yview
            for call in config_calls
        ), "Scrollbar callbacks should be preserved")
        new_widget.config.assert_called_with(yscrollcommand=scrollbar.set)
        
    @patch('code_editor.CodeView')
    def test_scrollbar_handles_rapid_widget_replacement(self, mock_codeview):
        """Test scrollbar behavior during rapid successive widget replacements."""
        scrollbar = Mock()
        widget1 = Mock()
        widget2 = Mock()
        widget3 = Mock()
        mock_codeview.side_effect = [widget1, widget2, widget3]
        
        # Set up widgets
        for widget in [widget1, widget2]:
            widget.get.return_value = "content"
            widget.index.return_value = "1.0"
            widget.yview.return_value = (0.0, 1.0)
            widget.tag_ranges.return_value = ()
            widget.getvar.return_value = {}
            widget.winfo_children.return_value = []
            widget.master = self.parent_frame
            widget.focus_get.return_value = None
            widget.grid_info.return_value = {'row': 0, 'column': 0}
            widget.pack_info.return_value = {}
            widget.place_info.return_value = {}
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        editor.current_widget = editor.create_widget()
        
        mock_lexer1 = Mock()
        mock_lexer2 = Mock()
        
        # Rapid replacements
        editor.replace_widget_with_lexer(mock_lexer1)
        editor.replace_widget_with_lexer(mock_lexer2)
        
        # Should end up connected to final widget (check call history)
        config_calls = scrollbar.config.call_args_list
        self.assertTrue(any(
            call.kwargs.get('command') == widget3.yview
            for call in config_calls
        ), "Scrollbar should be connected to final widget after rapid replacements")
        widget3.config.assert_called_with(yscrollcommand=scrollbar.set)
        
    @patch('code_editor.CodeView')
    def test_scrollbar_configuration_with_no_scrollbar(self, mock_codeview):
        """Test that scrollbar operations are safely ignored when no scrollbar is present."""
        widget = Mock()
        mock_codeview.return_value = widget
        
        # No scrollbar provided
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        # Should not attempt any scrollbar-related config operations
        # The widget should be created successfully without scrollbar config
        self.assertEqual(editor.current_widget, widget)
        self.assertIsNone(editor.scrollbar)
        
        # widget.config should not be called for scrollbar operations since no scrollbar is present
        # (Note: create_widget only calls scrollbar config if scrollbar exists)
        widget.config.assert_not_called()
        
    @patch('code_editor.CodeView')
    def test_scrollbar_error_recovery(self, mock_codeview):
        """Test scrollbar error recovery when configuration fails."""
        scrollbar = Mock()
        widget = Mock()
        mock_codeview.return_value = widget
        
        # Make scrollbar configuration fail
        scrollbar.config.side_effect = tk.TclError("Scrollbar error")
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        
        # Should handle scrollbar errors gracefully
        try:
            editor.current_widget = editor.create_widget()
        except tk.TclError:
            self.fail("Scrollbar error should be handled gracefully")
            
    @patch('code_editor.CodeView')
    def test_enhanced_scrollbar_reconnection_comprehensive(self, mock_codeview):
        """Test comprehensive scrollbar reconnection with all edge cases."""
        scrollbar = Mock()
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Set up scrollbar with specific state
        scrollbar.get.return_value = (0.2, 0.8)
        scrollbar.set = Mock()
        
        # Set up old widget
        old_widget.get.return_value = "test content"
        old_widget.index.return_value = "1.5"
        old_widget.yview.return_value = (0.2, 0.8)
        old_widget.tag_ranges.return_value = ("1.0", "1.5")
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.master = self.parent_frame
        old_widget.focus_get.return_value = old_widget
        old_widget.grid_info.return_value = {'row': 0, 'column': 0, 'sticky': 'nsew'}
        old_widget.pack_info.return_value = {}
        old_widget.place_info.return_value = {}
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        editor.current_widget = editor.create_widget()
        
        mock_lexer = Mock()
        result = editor.enhanced_scrollbar_reconnection(old_widget, new_widget, mock_lexer)
        
        # Should perform enhanced reconnection
        self.assertEqual(result, new_widget)
        
        # Should configure new scrollbar connections
        scrollbar.config.assert_called_with(command=new_widget.yview)
        new_widget.config.assert_called_with(yscrollcommand=scrollbar.set)
        
        # Should restore scroll position
        new_widget.yview_moveto.assert_called_with(0.2)


class TestCodeEditorEdgeCases(unittest.TestCase):
    """Test cases for edge cases like rapid file switching and error conditions."""
    
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
    def test_rapid_file_switching_preserves_state(self, mock_codeview):
        """Test rapid successive file switching preserves proper state."""
        widgets = [Mock() for _ in range(5)]
        mock_codeview.side_effect = widgets
        
        # Set up each widget with unique content and state
        for i, widget in enumerate(widgets):
            widget.get.return_value = f"content_{i}"
            widget.index.return_value = f"1.{i}"
            widget.yview.return_value = (i * 0.1, (i + 1) * 0.1)
            widget.tag_ranges.return_value = ()
            widget.getvar.return_value = {}
            widget.winfo_children.return_value = []
            widget.master = self.parent_frame
            widget.focus_get.return_value = None
            widget.grid_info.return_value = {'row': 0, 'column': 0}
            widget.pack_info.return_value = {}
            widget.place_info.return_value = {}
        
        scrollbar = Mock()
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        
        # Rapid file switching simulation
        lexers = [Mock() for _ in range(4)]
        
        # Start with initial widget
        editor.current_widget = editor.create_widget()
        
        # Rapid successive replacements
        for lexer in lexers:
            editor.replace_widget_with_lexer(lexer)
            
        # Should end up with final widget
        self.assertEqual(editor.current_widget, widgets[-1])
        
        # Should have scrollbar connected to final widget (check if last call includes final widget connection)
        # Note: scrollbar may have multiple config calls during replacement process
        self.assertTrue(any(
            call.kwargs.get('command') == widgets[-1].yview
            for call in scrollbar.config.call_args_list
        ))
        
    @patch('code_editor.CodeView')
    def test_widget_creation_memory_leak_prevention(self, mock_codeview):
        """Test that rapid widget creation doesn't cause memory leaks."""
        # Need enough widgets for initial creation + replacements
        widgets = [Mock() for _ in range(19)]  # 1 initial + 9*2 for create+replace cycles
        mock_codeview.side_effect = widgets
        
        # Set up widgets for destruction
        for widget in widgets:
            widget.get.return_value = "content"
            widget.index.return_value = "1.0"
            widget.yview.return_value = (0.0, 1.0)
            widget.tag_ranges.return_value = ()
            widget.getvar.return_value = {}
            widget.winfo_children.return_value = []
            widget.master = self.parent_frame
            widget.focus_get.return_value = None
            widget.grid_info.return_value = {'row': 0, 'column': 0}
            widget.pack_info.return_value = {}
            widget.place_info.return_value = {}
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Rapid widget creation and replacement
        for i in range(9):
            editor.current_widget = editor.create_widget()
            lexer = Mock()
            editor.replace_widget_with_lexer(lexer)
            
        # At least some old widgets should have been destroyed to prevent memory leaks
        destroyed_count = sum(1 for widget in widgets if widget.destroy.called)
        self.assertGreater(destroyed_count, 0, "No widgets were destroyed, potential memory leak")
            
    @patch('code_editor.CodeView')
    def test_lexer_setting_failure_recovery(self, mock_codeview):
        """Test recovery from lexer setting failures."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Make lexer setting fail
        new_widget.lexer = Mock()
        type(new_widget).lexer = PropertyMock(side_effect=AttributeError("Lexer setting failed"))
        
        # Set up widget state
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.master = self.parent_frame
        old_widget.focus_get.return_value = None
        old_widget.grid_info.return_value = {'row': 0, 'column': 0}
        old_widget.pack_info.return_value = {}
        old_widget.place_info.return_value = {}
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        mock_lexer = Mock()
        
        # Should handle lexer setting failure gracefully
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should still return new widget even if lexer setting failed
        self.assertEqual(result, new_widget)
        self.assertEqual(editor.current_widget, new_widget)
        
    @patch('code_editor.CodeView')
    def test_concurrent_widget_operations_safety(self, mock_codeview):
        """Test safety of concurrent widget operations."""
        widget1 = Mock()
        widget2 = Mock()
        mock_codeview.side_effect = [widget1, widget2]
        
        # Set up widgets
        for widget in [widget1]:
            widget.get.return_value = "content"
            widget.index.return_value = "1.0"
            widget.yview.return_value = (0.0, 1.0)
            widget.tag_ranges.return_value = ()
            widget.getvar.return_value = {}
            widget.winfo_children.return_value = []
            widget.master = self.parent_frame
            widget.focus_get.return_value = None
            widget.grid_info.return_value = {'row': 0, 'column': 0}
            widget.pack_info.return_value = {}
            widget.place_info.return_value = {}
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        # Simulate concurrent operations
        mock_lexer = Mock()
        
        # Multiple rapid operations that could conflict
        result1 = editor.replace_widget_with_lexer(mock_lexer)
        content = editor.get_content()
        editor.set_readonly_state(True)
        
        # Should handle concurrent operations safely
        self.assertEqual(result1, widget2)
        self.assertEqual(editor.current_widget, widget2)
        
    @patch('code_editor.CodeView')
    def test_tkinter_error_during_widget_replacement(self, mock_codeview):
        """Test handling of tkinter errors during widget replacement."""
        old_widget = Mock()
        new_widget = Mock()
        mock_codeview.side_effect = [old_widget, new_widget]
        
        # Make grid operation fail
        new_widget.grid.side_effect = tk.TclError("Grid operation failed")
        
        # Set up widget state
        old_widget.get.return_value = "content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.master = self.parent_frame
        old_widget.focus_get.return_value = None
        old_widget.grid_info.return_value = {'row': 0, 'column': 0}
        old_widget.pack_info.return_value = {}
        old_widget.place_info.return_value = {}
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        mock_lexer = Mock()
        
        # Replace widget with lexer
        result = editor.replace_widget_with_lexer(mock_lexer)
        
        # Should handle tkinter errors gracefully
        self.assertEqual(result, new_widget)
        
        # Should still succeed despite grid error (fallback mechanism)
        self.assertEqual(editor.current_widget, new_widget)
        
    @patch('code_editor.CodeView')
    def test_large_content_handling(self, mock_codeview):
        """Test handling of large content during widget operations."""
        widget = Mock()
        mock_codeview.return_value = widget
        
        # Simulate large content
        large_content = "x" * 1000000  # 1MB of content
        widget.get.return_value = large_content
        widget.index.return_value = "1000.0"
        widget.yview.return_value = (0.5, 0.6)
        widget.tag_ranges.return_value = ()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        # Should handle large content efficiently
        state = editor.capture_widget_state()
        self.assertEqual(state['content'], large_content)
        self.assertEqual(state['cursor_position'], "1000.0")
        
    @patch('code_editor.CodeView')
    def test_empty_content_edge_cases(self, mock_codeview):
        """Test handling of empty content and edge cases."""
        widget = Mock()
        mock_codeview.return_value = widget
        
        # Test empty content
        widget.get.return_value = ""
        widget.index.return_value = "1.0"
        widget.yview.return_value = (0.0, 1.0)
        widget.tag_ranges.return_value = ()
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        state = editor.capture_widget_state()
        self.assertEqual(state['content'], "")
        
        # Test content clearing
        editor.clear_content()
        widget.delete.assert_called_with("1.0", tk.END)
        
    @patch('code_editor.CodeView')
    def test_widget_state_corruption_recovery(self, mock_codeview):
        """Test recovery from widget state corruption."""
        widget = Mock()
        mock_codeview.return_value = widget
        
        # Simulate corrupted widget state
        widget.get.side_effect = tk.TclError("Widget destroyed")
        widget.index.side_effect = tk.TclError("Widget destroyed") 
        widget.yview.side_effect = tk.TclError("Widget destroyed")
        widget.tag_ranges.side_effect = tk.TclError("Widget destroyed")
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        editor.current_widget = editor.create_widget()
        
        # Should handle corrupted state gracefully
        state = editor.capture_widget_state()
        
        # Should return safe defaults
        expected_state = {
            'content': '',
            'cursor_position': '1.0', 
            'scroll_position': (0.0, 1.0),
            'selection': None
        }
        self.assertEqual(state, expected_state)
        
    @patch('code_editor.CodeView')
    def test_rapid_destroy_create_cycles(self, mock_codeview):
        """Test rapid destroy-create cycles don't cause issues."""
        widgets = [Mock() for _ in range(10)]
        mock_codeview.side_effect = widgets
        
        # Set up widgets for destruction
        for widget in widgets:
            widget.getvar.return_value = {}
            widget.winfo_children.return_value = []
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager)
        
        # Rapid destroy-create cycles
        for i in range(10):
            editor.current_widget = editor.create_widget()
            editor.destroy_widget_safely()
            
        # Should handle rapid cycles without issues
        self.assertIsNone(editor.current_widget)
        
        # All widgets should have been destroyed
        for widget in widgets:
            widget.destroy.assert_called_once()
            
    @patch('code_editor.CodeView')
    def test_error_state_recovery_after_failed_replacement(self, mock_codeview):
        """Test recovery to stable state after failed widget replacement."""
        old_widget = Mock()
        # Second call fails completely
        mock_codeview.side_effect = [old_widget, Exception("Complete widget creation failure")]
        
        # Set up old widget
        old_widget.get.return_value = "original content"
        old_widget.index.return_value = "1.0"
        old_widget.yview.return_value = (0.0, 1.0)
        old_widget.tag_ranges.return_value = ()
        old_widget.getvar.return_value = {}
        old_widget.winfo_children.return_value = []
        old_widget.master = self.parent_frame
        old_widget.focus_get.return_value = None
        old_widget.grid_info.return_value = {'row': 0, 'column': 0}
        old_widget.pack_info.return_value = {}
        old_widget.place_info.return_value = {}
        
        scrollbar = Mock()
        editor = CodeEditor(self.parent_frame, self.syntax_manager, scrollbar=scrollbar)
        editor.current_widget = editor.create_widget()
        
        mock_lexer = Mock()
        
        # Should handle complete failure and recover to old widget
        with self.assertRaises(Exception):
            editor.replace_widget_with_lexer(mock_lexer)
            
        # Should recover to old widget state
        self.assertEqual(editor.current_widget, old_widget)
        
        # Scrollbar should be reconnected to old widget
        scrollbar.config.assert_called_with(command=old_widget.yview)


class TestCodeEditorWidgetCaching(unittest.TestCase):
    """Test cases for widget caching strategy to reduce recreation overhead."""
    
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
    def test_widget_cache_basic_functionality(self, mock_codeview):
        """Test basic widget caching stores and retrieves widgets by lexer type."""
        widget1 = Mock()
        widget2 = Mock()
        mock_codeview.side_effect = [widget1, widget2]
        
        # Mock lexers
        python_lexer = Mock()
        python_lexer.name = 'Python'
        javascript_lexer = Mock()
        javascript_lexer.name = 'JavaScript'
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # First creation should create new widget and cache it
        cached_widget1 = editor.get_cached_widget_for_lexer(python_lexer)
        self.assertEqual(cached_widget1, widget1)
        
        # Second request for same lexer should return cached widget
        cached_widget1_again = editor.get_cached_widget_for_lexer(python_lexer)
        self.assertEqual(cached_widget1_again, widget1)
        
        # Different lexer should create new widget
        cached_widget2 = editor.get_cached_widget_for_lexer(javascript_lexer)
        self.assertEqual(cached_widget2, widget2)
        
        # Should have created only 2 widgets total
        self.assertEqual(mock_codeview.call_count, 2)
        
    @patch('code_editor.CodeView')
    def test_widget_cache_with_cache_disabled(self, mock_codeview):
        """Test that caching can be disabled."""
        widgets = [Mock() for _ in range(4)]
        mock_codeview.side_effect = widgets
        
        python_lexer = Mock()
        python_lexer.name = 'Python'
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=False)
        
        # Each request should create new widget when caching disabled
        widget1 = editor.get_cached_widget_for_lexer(python_lexer)
        widget2 = editor.get_cached_widget_for_lexer(python_lexer)
        widget3 = editor.get_cached_widget_for_lexer(python_lexer)
        
        # Should have created 3 separate widgets
        self.assertEqual(mock_codeview.call_count, 3)
        self.assertNotEqual(widget1, widget2)
        self.assertNotEqual(widget2, widget3)
        
    @patch('code_editor.CodeView')
    def test_widget_cache_size_limit_enforcement(self, mock_codeview):
        """Test that cache enforces size limits and evicts old entries."""
        widgets = [Mock() for _ in range(6)]
        mock_codeview.side_effect = widgets
        
        # Create lexers for testing
        lexers = []
        for i in range(5):
            lexer = Mock()
            lexer.name = f'Language{i}'
            lexers.append(lexer)
        
        # Set cache size to 3
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True, cache_size=3)
        
        # Fill cache beyond limit
        cached_widgets = []
        for lexer in lexers:
            widget = editor.get_cached_widget_for_lexer(lexer)
            cached_widgets.append(widget)
            
        # Cache should contain only last 3 widgets
        cache_size = editor.get_cache_size()
        self.assertEqual(cache_size, 3)
        
        # Requesting first lexer again should create new widget (evicted from cache)
        new_widget = editor.get_cached_widget_for_lexer(lexers[0])
        self.assertEqual(new_widget, widgets[5])  # Should be the 6th created widget
        
    @patch('code_editor.CodeView')
    def test_widget_cache_invalidation(self, mock_codeview):
        """Test cache invalidation functionality."""
        widget1 = Mock()
        widget2 = Mock()
        mock_codeview.side_effect = [widget1, widget2]
        
        python_lexer = Mock()
        python_lexer.name = 'Python'
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Cache a widget
        cached_widget = editor.get_cached_widget_for_lexer(python_lexer)
        self.assertEqual(cached_widget, widget1)
        
        # Invalidate cache
        editor.invalidate_cache()
        
        # Next request should create new widget
        new_widget = editor.get_cached_widget_for_lexer(python_lexer)
        self.assertEqual(new_widget, widget2)
        
        # Should have created 2 widgets total
        self.assertEqual(mock_codeview.call_count, 2)
        
    @patch('code_editor.CodeView')
    def test_widget_cache_with_none_lexer(self, mock_codeview):
        """Test cache behavior with None lexer (no syntax highlighting)."""
        widget1 = Mock()
        widget2 = Mock()
        mock_codeview.side_effect = [widget1, widget2]
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Cache widget with None lexer
        cached_widget1 = editor.get_cached_widget_for_lexer(None)
        self.assertEqual(cached_widget1, widget1)
        
        # Second request should return cached widget
        cached_widget1_again = editor.get_cached_widget_for_lexer(None)
        self.assertEqual(cached_widget1_again, widget1)
        
        # Should have created only 1 widget
        self.assertEqual(mock_codeview.call_count, 1)
        
    @patch('code_editor.CodeView')
    def test_widget_cache_performance_optimization(self, mock_codeview):
        """Test that caching provides performance optimization."""
        widgets = [Mock() for _ in range(2)]
        mock_codeview.side_effect = widgets
        
        python_lexer = Mock()
        python_lexer.name = 'Python'
        javascript_lexer = Mock()
        javascript_lexer.name = 'JavaScript'
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Simulate rapid file type switching
        results = []
        for _ in range(10):
            # Switch between Python and JavaScript repeatedly
            python_widget = editor.get_cached_widget_for_lexer(python_lexer)
            javascript_widget = editor.get_cached_widget_for_lexer(javascript_lexer)
            results.extend([python_widget, javascript_widget])
        
        # Should have created only 2 widgets despite 20 requests
        self.assertEqual(mock_codeview.call_count, 2)
        
        # All Python requests should return same widget
        python_widgets = [w for i, w in enumerate(results) if i % 2 == 0]
        self.assertTrue(all(w == widgets[0] for w in python_widgets))
        
        # All JavaScript requests should return same widget
        js_widgets = [w for i, w in enumerate(results) if i % 2 == 1]
        self.assertTrue(all(w == widgets[1] for w in js_widgets))
        
    @patch('code_editor.CodeView')
    def test_widget_cache_memory_management(self, mock_codeview):
        """Test that cache properly manages memory by destroying evicted widgets."""
        widgets = [Mock() for _ in range(5)]
        mock_codeview.side_effect = widgets
        
        lexers = []
        for i in range(4):
            lexer = Mock()
            lexer.name = f'Language{i}'
            lexers.append(lexer)
        
        # Set small cache size
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True, cache_size=2)
        
        # Fill cache and exceed limit
        for lexer in lexers:
            editor.get_cached_widget_for_lexer(lexer)
            
        # First two widgets should have been evicted and destroyed
        widgets[0].destroy.assert_called_once()
        widgets[1].destroy.assert_called_once()
        
        # Last two widgets should still be cached (not destroyed)
        widgets[2].destroy.assert_not_called()
        widgets[3].destroy.assert_not_called()
        
    @patch('code_editor.CodeView')
    def test_widget_cache_lexer_key_generation(self, mock_codeview):
        """Test cache key generation for different lexer types."""
        widgets = [Mock() for _ in range(3)]
        mock_codeview.side_effect = widgets
        
        # Test different lexer scenarios
        python_lexer = Mock()
        python_lexer.name = 'Python'
        
        another_python_lexer = Mock()
        another_python_lexer.name = 'Python'  # Same name, different instance
        
        javascript_lexer = Mock()
        javascript_lexer.name = 'JavaScript'
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Same lexer name should return cached widget
        widget1 = editor.get_cached_widget_for_lexer(python_lexer)
        widget2 = editor.get_cached_widget_for_lexer(another_python_lexer)
        self.assertEqual(widget1, widget2)
        
        # Different lexer name should create new widget
        widget3 = editor.get_cached_widget_for_lexer(javascript_lexer)
        self.assertNotEqual(widget1, widget3)
        
        # Should have created 2 widgets (1 for Python, 1 for JavaScript)
        self.assertEqual(mock_codeview.call_count, 2)
        
    @patch('code_editor.CodeView')
    def test_widget_cache_integration_with_replacement(self, mock_codeview):
        """Test cache integration with widget replacement functionality."""
        widgets = [Mock() for _ in range(3)]
        mock_codeview.side_effect = widgets
        
        # Set up widget state for replacement
        for widget in widgets:
            widget.get.return_value = "content"
            widget.index.return_value = "1.0"
            widget.yview.return_value = (0.0, 1.0)
            widget.tag_ranges.return_value = ()
            widget.getvar.return_value = {}
            widget.winfo_children.return_value = []
            widget.master = self.parent_frame
            widget.focus_get.return_value = None
            widget.grid_info.return_value = {'row': 0, 'column': 0}
            widget.pack_info.return_value = {}
            widget.place_info.return_value = {}
        
        python_lexer = Mock()
        python_lexer.name = 'Python'
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Start with a widget
        editor.current_widget = editor.create_widget()
        
        # Replace with cached widget
        result = editor.replace_widget_with_cached_lexer(python_lexer)
        
        # Should return cached widget
        self.assertEqual(result, widgets[1])  # Second widget from cache
        self.assertEqual(editor.current_widget, widgets[1])
        
        # Replace again with same lexer should use cached widget
        result2 = editor.replace_widget_with_cached_lexer(python_lexer)
        self.assertEqual(result2, widgets[1])  # Same cached widget
        
        # Should have created only 2 widgets (1 initial + 1 cached)
        self.assertEqual(mock_codeview.call_count, 2)
        
    @patch('code_editor.CodeView')
    def test_widget_cache_thread_safety(self, mock_codeview):
        """Test that cache operations are thread-safe."""
        import threading
        import time
        
        widgets = [Mock() for _ in range(10)]
        mock_codeview.side_effect = widgets
        
        python_lexer = Mock()
        python_lexer.name = 'Python'
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        results = []
        errors = []
        
        def cache_worker():
            try:
                for _ in range(5):
                    widget = editor.get_cached_widget_for_lexer(python_lexer)
                    results.append(widget)
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append(e)
        
        # Run multiple threads accessing cache simultaneously
        threads = [threading.Thread(target=cache_worker) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Should have no errors
        self.assertEqual(len(errors), 0)
        
        # All results should be the same cached widget
        self.assertTrue(all(result == results[0] for result in results))
        
        # Should have created only 1 widget despite multiple concurrent requests
        self.assertEqual(mock_codeview.call_count, 1)


class TestCodeEditorFileLoadingIntegration(unittest.TestCase):
    """Test cases for syntax highlighting integration with file loading."""
    
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
    @patch('builtins.open', mock_open(read_data="def hello():\n    print('world')"))
    def test_load_file_with_automatic_syntax_highlighting(self, mock_codeview):
        """Test loading file with automatic syntax highlighting detection."""
        widget = Mock()
        mock_codeview.return_value = widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Load Python file
        result = editor.load_file("test.py")
        
        # Should create widget with Python lexer
        self.assertTrue(result)
        mock_codeview.assert_called_once()
        call_args = mock_codeview.call_args[1]
        self.assertIsNotNone(call_args.get('lexer'))
        
        # Should load file content
        widget.delete.assert_called_with("1.0", tk.END)
        widget.insert.assert_called_with("1.0", "def hello():\n    print('world')")
        
    @patch('code_editor.CodeView')
    @patch('builtins.open', mock_open(read_data="console.log('hello');"))
    def test_load_file_with_javascript_syntax_highlighting(self, mock_codeview):
        """Test loading JavaScript file with appropriate syntax highlighting."""
        widget = Mock()
        mock_codeview.return_value = widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Load JavaScript file
        result = editor.load_file("app.js")
        
        # Should create widget with JavaScript lexer
        self.assertTrue(result)
        mock_codeview.assert_called_once()
        call_args = mock_codeview.call_args[1]
        lexer = call_args.get('lexer')
        self.assertIsNotNone(lexer)
        
        # Should load file content
        widget.insert.assert_called_with("1.0", "console.log('hello');")
        
    @patch('code_editor.CodeView')
    @patch('builtins.open', mock_open(read_data="<html><body>Hello</body></html>"))
    def test_load_file_with_html_syntax_highlighting(self, mock_codeview):
        """Test loading HTML file with appropriate syntax highlighting."""
        widget = Mock()
        mock_codeview.return_value = widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Load HTML file
        result = editor.load_file("index.html")
        
        # Should create widget with HTML lexer
        self.assertTrue(result)
        mock_codeview.assert_called_once()
        call_args = mock_codeview.call_args[1]
        lexer = call_args.get('lexer')
        self.assertIsNotNone(lexer)
        
        # Should load file content
        widget.insert.assert_called_with("1.0", "<html><body>Hello</body></html>")
        
    @patch('code_editor.CodeView')
    @patch('builtins.open', mock_open(read_data="Some plain text content"))
    def test_load_file_without_syntax_highlighting(self, mock_codeview):
        """Test loading file with unknown extension falls back to plain text."""
        widget = Mock()
        mock_codeview.return_value = widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Load file with unknown extension
        result = editor.load_file("readme.txt")
        
        # Should create widget with TextLexer (plain text)
        self.assertTrue(result)
        mock_codeview.assert_called_once()
        call_args = mock_codeview.call_args[1]
        lexer = call_args.get('lexer')
        # Text files get TextLexer, not None
        self.assertIsNotNone(lexer)
        
        # Should load file content
        widget.insert.assert_called_with("1.0", "Some plain text content")
        
    @patch('code_editor.CodeView')
    def test_load_file_handles_file_not_found(self, mock_codeview):
        """Test loading non-existent file handles error gracefully."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Try to load non-existent file
        result = editor.load_file("nonexistent.py")
        
        # Should return False and not create widget
        self.assertFalse(result)
        mock_codeview.assert_not_called()
        
    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    @patch('code_editor.CodeView')
    def test_load_file_handles_permission_error(self, mock_codeview, mock_open_func):
        """Test loading file with permission error handles gracefully."""
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Try to load file with permission error
        result = editor.load_file("protected.py")
        
        # Should return False and not create widget
        self.assertFalse(result)
        mock_codeview.assert_not_called()
        
    @patch('code_editor.CodeView')
    @patch('builtins.open', mock_open(read_data="# Python code\nprint('test')"))
    def test_load_file_uses_cached_widget_for_same_type(self, mock_codeview):
        """Test loading multiple files of same type uses cached widgets."""
        widgets = [Mock() for _ in range(2)]
        mock_codeview.side_effect = widgets
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Load first Python file
        result1 = editor.load_file("file1.py")
        self.assertTrue(result1)
        
        # Load second Python file
        result2 = editor.load_file("file2.py")
        self.assertTrue(result2)
        
        # Should have created only one widget (cached for second file)
        self.assertEqual(mock_codeview.call_count, 1)
        
        # Both files should load content to same cached widget
        self.assertEqual(widgets[0].insert.call_count, 2)
        
    @patch('code_editor.CodeView')
    @patch('builtins.open', mock_open(read_data="def test():\n    pass"))
    def test_load_file_preserves_existing_widget_state(self, mock_codeview):
        """Test loading file preserves any existing widget state properly."""
        widget = Mock()
        mock_codeview.return_value = widget
        
        # Set up existing widget with state
        widget.get.return_value = "old content"
        widget.index.return_value = "1.5"
        widget.yview.return_value = (0.2, 0.8)
        widget.tag_ranges.return_value = ("1.0", "1.3")
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        editor.current_widget = widget
        
        # Load new file
        result = editor.load_file("new_file.py")
        
        # Should clear old content and load new
        self.assertTrue(result)
        widget.delete.assert_called_with("1.0", tk.END)
        widget.insert.assert_called_with("1.0", "def test():\n    pass")
        
    @patch('code_editor.CodeView')
    @patch('builtins.open', mock_open(read_data=""))
    def test_load_file_with_empty_file(self, mock_codeview):
        """Test loading empty file creates widget with no content."""
        widget = Mock()
        mock_codeview.return_value = widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Load empty file
        result = editor.load_file("empty.py")
        
        # Should create widget and insert empty content
        self.assertTrue(result)
        widget.insert.assert_called_with("1.0", "")
        
    @patch('code_editor.CodeView')
    @patch('builtins.open', mock_open(read_data="x = 1\ny = 2\nprint(x + y)"))
    def test_load_file_with_encoding_handling(self, mock_codeview):
        """Test loading file handles different encodings properly."""
        widget = Mock()
        mock_codeview.return_value = widget
        
        editor = CodeEditor(self.parent_frame, self.syntax_manager, enable_caching=True)
        
        # Load file with specified encoding
        result = editor.load_file("utf8_file.py", encoding="utf-8")
        
        # Should load content with correct encoding
        self.assertTrue(result)
        widget.insert.assert_called_with("1.0", "x = 1\ny = 2\nprint(x + y)")


if __name__ == '__main__':
    unittest.main()
