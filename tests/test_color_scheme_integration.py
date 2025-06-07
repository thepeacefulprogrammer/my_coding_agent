"""
Integration tests for color scheme configuration with CodeEditor.

This module tests the integration between ColorSchemeConfig and CodeEditor,
ensuring dynamic color scheme switching works correctly in practice.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import tempfile

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from color_scheme_config import ColorSchemeConfig
from code_editor import CodeEditor
from color_schemes import get_nord_color_scheme


class TestColorSchemeIntegration(unittest.TestCase):
    """Test integration between ColorSchemeConfig and CodeEditor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ColorSchemeConfig()
        
        # Mock tkinter components to avoid GUI creation
        self.mock_parent = Mock()
        self.mock_parent._last_child_ids = {}
        self.mock_parent.tk = Mock()
        self.mock_scrollbar = Mock()
        self.mock_syntax_manager = Mock()
        
        # Configure syntax manager mock
        self.mock_syntax_manager.get_lexer_for_file.return_value = Mock()
        
    def test_code_editor_with_config_integration(self):
        """Test CodeEditor can use ColorSchemeConfig for dynamic scheme switching."""
        with patch('tkinter.Tk'), patch('chlorophyll.CodeView'):
            editor = CodeEditor(
                parent=self.mock_parent,
                syntax_manager=self.mock_syntax_manager,
                scrollbar=self.mock_scrollbar,
                color_scheme_config=self.config
            )
            
            # Should have config attached
            self.assertIsNotNone(editor.color_scheme_config)
            self.assertEqual(editor.color_scheme_config, self.config)
            
    def test_dynamic_color_scheme_switching(self):
        """Test switching color schemes dynamically in CodeEditor."""
        with patch('tkinter.Tk'), patch('chlorophyll.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            editor = CodeEditor(
                parent=self.mock_parent,
                syntax_manager=self.mock_syntax_manager,
                scrollbar=self.mock_scrollbar,
                color_scheme_config=self.config
            )
            
            # Switch to monokai scheme
            success = editor.switch_color_scheme("monokai")
            self.assertTrue(success)
            
            # Should update current scheme in config
            self.assertEqual(self.config.get_current_scheme_name(), "monokai")
            
    def test_color_scheme_application_on_widget_creation(self):
        """Test that color scheme is applied when creating widgets."""
        with patch('tkinter.Tk'), patch('code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            # Set current scheme to monokai
            self.config.set_current_scheme("monokai")
            
            editor = CodeEditor(
                parent=self.mock_parent,
                syntax_manager=self.mock_syntax_manager,
                scrollbar=self.mock_scrollbar,
                color_scheme_config=self.config
            )
            
            # Create widget with Python lexer
            widget = editor.create_widget(lexer="python")
            
            # Should have applied monokai colors
            self.assertIsNotNone(widget)
            
    def test_fallback_to_default_scheme_on_invalid_scheme(self):
        """Test fallback behavior when invalid scheme is requested."""
        with patch('tkinter.Tk'), patch('chlorophyll.CodeView'):
            editor = CodeEditor(
                parent=self.mock_parent,
                syntax_manager=self.mock_syntax_manager,
                scrollbar=self.mock_scrollbar,
                color_scheme_config=self.config
            )
            
            # Try to switch to non-existent scheme
            success = editor.switch_color_scheme("nonexistent")
            self.assertFalse(success)
            
            # Should remain on current scheme
            current_scheme = self.config.get_current_scheme_name()
            self.assertIn(current_scheme, self.config.get_available_schemes())
            
    def test_config_persistence_with_editor_state(self):
        """Test that configuration changes persist when saving/loading."""
        with patch('tkinter.Tk'), patch('chlorophyll.CodeView'):
            editor = CodeEditor(
                parent=self.mock_parent,
                syntax_manager=self.mock_syntax_manager,
                scrollbar=self.mock_scrollbar,
                color_scheme_config=self.config
            )
            
            # Switch to monokai
            editor.switch_color_scheme("monokai")
            
            # Save configuration
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                config_file = f.name
                
            try:
                success = self.config.save_configuration(config_file)
                self.assertTrue(success)
                
                # Create new config and editor
                new_config = ColorSchemeConfig()
                load_success = new_config.load_configuration(config_file)
                self.assertTrue(load_success)
                
                # Should have monokai as current scheme
                self.assertEqual(new_config.get_current_scheme_name(), "monokai")
                
            finally:
                # Cleanup
                if os.path.exists(config_file):
                    os.unlink(config_file)
                    
    def test_custom_scheme_registration_and_usage(self):
        """Test registering custom schemes and using them in CodeEditor."""
        with patch('tkinter.Tk'), patch('chlorophyll.CodeView'):
            editor = CodeEditor(
                parent=self.mock_parent,
                syntax_manager=self.mock_syntax_manager,
                scrollbar=self.mock_scrollbar,
                color_scheme_config=self.config
            )
            
            # Register custom scheme
            custom_scheme = {
                'keyword': {'declaration': '#FF0000'},
                'string': {'single': '#00FF00'},
                'comment': {'single': '#0000FF'}
            }
            
            success = self.config.register_scheme("custom", custom_scheme)
            self.assertTrue(success)
            
            # Switch to custom scheme
            switch_success = editor.switch_color_scheme("custom")
            self.assertTrue(switch_success)
            
            # Should be using custom scheme
            self.assertEqual(self.config.get_current_scheme_name(), "custom")
            current_scheme = self.config.get_current_scheme()
            self.assertEqual(current_scheme['keyword']['declaration'], '#FF0000')
            
    def test_scheme_inheritance_integration(self):
        """Test scheme inheritance functionality with CodeEditor."""
        with patch('tkinter.Tk'), patch('chlorophyll.CodeView'):
            editor = CodeEditor(
                parent=self.mock_parent,
                syntax_manager=self.mock_syntax_manager,
                scrollbar=self.mock_scrollbar,
                color_scheme_config=self.config
            )
            
            # Create derived scheme from Nord
            overrides = {
                'keyword': {'declaration': '#FF5555'},  # Custom red for keywords
                'string': {'single': '#50FA7B'}         # Custom green for strings
            }
            
            success = self.config.register_scheme_with_inheritance(
                "custom_nord", "nord", overrides
            )
            self.assertTrue(success)
            
            # Switch to derived scheme
            switch_success = editor.switch_color_scheme("custom_nord")
            self.assertTrue(switch_success)
            
            # Should have custom overrides
            current_scheme = self.config.get_current_scheme()
            self.assertEqual(current_scheme['keyword']['declaration'], '#FF5555')
            self.assertEqual(current_scheme['string']['single'], '#50FA7B')
            
            # Should preserve other Nord colors
            nord_scheme = get_nord_color_scheme()
            self.assertEqual(current_scheme['comment']['single'], nord_scheme['comment']['single'])


if __name__ == "__main__":
    unittest.main() 