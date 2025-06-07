#!/usr/bin/env python3
"""
Unit tests for visual verification test application.

Tests the functionality of the manual test application without requiring GUI interaction.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tkinter as tk

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'examples'))

# Import the test application
try:
    from test_live_syntax_highlighting import SyntaxHighlightingTestApp
except ImportError:
    # Skip tests if GUI dependencies are not available
    class SyntaxHighlightingTestApp:
        pass

class TestSyntaxHighlightingTestApp(unittest.TestCase):
    """Test cases for the syntax highlighting test application."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock tkinter root to avoid GUI creation during tests
        self.root_mock = Mock(spec=tk.Tk)
        self.root_mock.title = Mock()
        self.root_mock.geometry = Mock()
        self.root_mock.configure = Mock()
        self.root_mock.after = Mock()
        
    @patch('test_live_syntax_highlighting.ttk')
    @patch('test_live_syntax_highlighting.tk')
    @patch('test_live_syntax_highlighting.CodeEditor')
    @patch('test_live_syntax_highlighting.SyntaxManager')
    @patch('test_live_syntax_highlighting.ColorSchemeConfig')
    def test_app_can_be_imported_and_initialized(self, mock_color_config, mock_syntax_manager, 
                                               mock_code_editor, mock_tk, mock_ttk):
        """Test that the application can be imported and initialized."""
        try:
            from test_live_syntax_highlighting import SyntaxHighlightingTestApp
            
            # Setup basic mocks
            root_mock = Mock()
            mock_tk.StringVar.return_value = Mock()
            mock_ttk.Frame.return_value = Mock()
            mock_ttk.LabelFrame.return_value = Mock()
            
            # Create app instance
            app = SyntaxHighlightingTestApp(root_mock)
            
            # Verify basic initialization
            self.assertIsNotNone(app.sample_code)
            self.assertIn('Python', app.sample_code)
            self.assertIn('JavaScript', app.sample_code)
            
        except ImportError as e:
            self.skipTest(f"Cannot import test app, skipping: {e}")

    @patch('test_live_syntax_highlighting.ttk')
    @patch('test_live_syntax_highlighting.tk')
    @patch('test_live_syntax_highlighting.CodeEditor')
    @patch('test_live_syntax_highlighting.SyntaxManager')
    @patch('test_live_syntax_highlighting.ColorSchemeConfig')
    def test_app_initialization(self, mock_color_config, mock_syntax_manager, 
                               mock_code_editor, mock_tk, mock_ttk):
        """Test that the application initializes correctly."""
        # Setup mocks
        mock_syntax_manager.return_value = Mock()
        mock_color_config.return_value = Mock()
        mock_code_editor.return_value = Mock()
        
        # Mock tkinter components
        mock_tk.StringVar.return_value = Mock()
        mock_ttk.Frame.return_value = Mock()
        mock_ttk.LabelFrame.return_value = Mock()
        mock_ttk.Label.return_value = Mock()
        mock_ttk.Combobox.return_value = Mock()
        mock_ttk.Button.return_value = Mock()
        mock_ttk.Scrollbar.return_value = Mock()
        
        # Create app instance
        app = SyntaxHighlightingTestApp(self.root_mock)
        
        # Verify initialization
        self.assertIsNotNone(app.root)
        self.assertIsNotNone(app.sample_code)
        mock_syntax_manager.assert_called_once()
        mock_color_config.assert_called_once()
        
    def test_sample_code_content(self):
        """Test that sample code is available for all supported languages."""
        with patch('test_live_syntax_highlighting.ttk'), \
             patch('test_live_syntax_highlighting.tk'), \
             patch('test_live_syntax_highlighting.CodeEditor'), \
             patch('test_live_syntax_highlighting.SyntaxManager'), \
             patch('test_live_syntax_highlighting.ColorSchemeConfig'):
            
            app = SyntaxHighlightingTestApp(self.root_mock)
            
            # Expected languages
            expected_languages = ['Python', 'JavaScript', 'HTML', 'CSS', 'JSON', 'Markdown']
            
            # Verify all languages have sample code
            for language in expected_languages:
                self.assertIn(language, app.sample_code)
                self.assertIsInstance(app.sample_code[language], str)
                self.assertGreater(len(app.sample_code[language]), 0)
                
    def test_python_sample_code_features(self):
        """Test that Python sample code includes various language features."""
        with patch('test_live_syntax_highlighting.ttk'), \
             patch('test_live_syntax_highlighting.tk'), \
             patch('test_live_syntax_highlighting.CodeEditor'), \
             patch('test_live_syntax_highlighting.SyntaxManager'), \
             patch('test_live_syntax_highlighting.ColorSchemeConfig'):
            
            app = SyntaxHighlightingTestApp(self.root_mock)
            python_code = app.sample_code['Python']
            
            # Check for Python-specific features
            self.assertIn('class ', python_code)
            self.assertIn('def ', python_code)
            self.assertIn('import ', python_code)
            self.assertIn('@property', python_code)
            self.assertIn('@staticmethod', python_code)
            self.assertIn('"""', python_code)  # Docstrings
            self.assertIn('if __name__', python_code)
            self.assertIn('try:', python_code)
            self.assertIn('except', python_code)
            
    def test_javascript_sample_code_features(self):
        """Test that JavaScript sample code includes various language features."""
        with patch('test_live_syntax_highlighting.ttk'), \
             patch('test_live_syntax_highlighting.tk'), \
             patch('test_live_syntax_highlighting.CodeEditor'), \
             patch('test_live_syntax_highlighting.SyntaxManager'), \
             patch('test_live_syntax_highlighting.ColorSchemeConfig'):
            
            app = SyntaxHighlightingTestApp(self.root_mock)
            js_code = app.sample_code['JavaScript']
            
            # Check for JavaScript-specific features
            self.assertIn('class ', js_code)
            self.assertIn('constructor', js_code)
            self.assertIn('async ', js_code)
            self.assertIn('await ', js_code)
            self.assertIn('=>', js_code)  # Arrow functions
            self.assertIn('const ', js_code)
            # Check for variable declarations (const is used more than let in this sample)
            has_declarations = 'const ' in js_code or 'let ' in js_code or 'var ' in js_code
            self.assertTrue(has_declarations, "JavaScript should contain variable declarations")
            self.assertIn('export', js_code)
            self.assertIn('import', js_code)
            
    def test_html_sample_code_features(self):
        """Test that HTML sample code includes various markup features."""
        with patch('test_live_syntax_highlighting.ttk'), \
             patch('test_live_syntax_highlighting.tk'), \
             patch('test_live_syntax_highlighting.CodeEditor'), \
             patch('test_live_syntax_highlighting.SyntaxManager'), \
             patch('test_live_syntax_highlighting.ColorSchemeConfig'):
            
            app = SyntaxHighlightingTestApp(self.root_mock)
            html_code = app.sample_code['HTML']
            
            # Check for HTML-specific features
            self.assertIn('<!DOCTYPE html>', html_code)
            self.assertIn('<html', html_code)
            self.assertIn('<head>', html_code)
            self.assertIn('<body>', html_code)
            self.assertIn('<script>', html_code)
            self.assertIn('<style>', html_code)
            self.assertIn('class="', html_code)
            self.assertIn('id="', html_code)
            
    def test_css_sample_code_features(self):
        """Test that CSS sample code includes various styling features."""
        with patch('test_live_syntax_highlighting.ttk'), \
             patch('test_live_syntax_highlighting.tk'), \
             patch('test_live_syntax_highlighting.CodeEditor'), \
             patch('test_live_syntax_highlighting.SyntaxManager'), \
             patch('test_live_syntax_highlighting.ColorSchemeConfig'):
            
            app = SyntaxHighlightingTestApp(self.root_mock)
            css_code = app.sample_code['CSS']
            
            # Check for CSS-specific features
            self.assertIn(':root', css_code)
            self.assertIn('--nord-', css_code)  # CSS variables
            self.assertIn('background-color:', css_code)
            self.assertIn('@media', css_code)
            # Check for CSS pseudo-selectors or general selector syntax
            has_pseudo = '::before' in css_code or '::after' in css_code or ':hover' in css_code
            self.assertTrue(has_pseudo, "CSS should contain pseudo-selectors")
            self.assertIn('rgba(', css_code)
            self.assertIn('linear-gradient', css_code)
            
    def test_json_sample_code_features(self):
        """Test that JSON sample code includes proper JSON structure."""
        with patch('test_live_syntax_highlighting.ttk'), \
             patch('test_live_syntax_highlighting.tk'), \
             patch('test_live_syntax_highlighting.CodeEditor'), \
             patch('test_live_syntax_highlighting.SyntaxManager'), \
             patch('test_live_syntax_highlighting.ColorSchemeConfig'):
            
            app = SyntaxHighlightingTestApp(self.root_mock)
            json_code = app.sample_code['JSON']
            
            # Check for JSON structure
            self.assertTrue(json_code.strip().startswith('{'))
            self.assertTrue(json_code.strip().endswith('}'))
            self.assertIn('"name":', json_code)
            self.assertIn('"version":', json_code)
            self.assertIn('"dependencies":', json_code)
            self.assertIn('"scripts":', json_code)
            
    def test_markdown_sample_code_features(self):
        """Test that Markdown sample code includes various markdown features."""
        with patch('test_live_syntax_highlighting.ttk'), \
             patch('test_live_syntax_highlighting.tk'), \
             patch('test_live_syntax_highlighting.CodeEditor'), \
             patch('test_live_syntax_highlighting.SyntaxManager'), \
             patch('test_live_syntax_highlighting.ColorSchemeConfig'):
            
            app = SyntaxHighlightingTestApp(self.root_mock)
            md_code = app.sample_code['Markdown']
            
            # Check for Markdown features
            self.assertIn('# ', md_code)  # Headers
            self.assertIn('## ', md_code)
            self.assertIn('**', md_code)  # Bold
            self.assertIn('*', md_code)   # Italic
            self.assertIn('```', md_code) # Code blocks
            self.assertIn('- [ ]', md_code) # Task lists
            self.assertIn('| ', md_code) # Tables
            self.assertIn('[', md_code) # Links
            
    @patch('test_live_syntax_highlighting.CodeEditor')
    def test_get_file_extension(self, mock_code_editor):
        """Test file extension mapping for different languages."""
        with patch('test_live_syntax_highlighting.ttk'), \
             patch('test_live_syntax_highlighting.tk'), \
             patch('test_live_syntax_highlighting.SyntaxManager'), \
             patch('test_live_syntax_highlighting.ColorSchemeConfig'):
            
            app = SyntaxHighlightingTestApp(self.root_mock)
            
            # Test extension mappings
            self.assertEqual(app.get_file_extension('Python'), 'py')
            self.assertEqual(app.get_file_extension('JavaScript'), 'js')
            self.assertEqual(app.get_file_extension('HTML'), 'html')
            self.assertEqual(app.get_file_extension('CSS'), 'css')
            self.assertEqual(app.get_file_extension('JSON'), 'json')
            self.assertEqual(app.get_file_extension('Markdown'), 'md')
            self.assertEqual(app.get_file_extension('Unknown'), 'txt')
            
    @patch('test_live_syntax_highlighting.CodeEditor')
    def test_get_language_from_extension(self, mock_code_editor):
        """Test language detection from file extensions."""
        with patch('test_live_syntax_highlighting.ttk'), \
             patch('test_live_syntax_highlighting.tk'), \
             patch('test_live_syntax_highlighting.SyntaxManager'), \
             patch('test_live_syntax_highlighting.ColorSchemeConfig'):
            
            app = SyntaxHighlightingTestApp(self.root_mock)
            
            # Test language mappings
            self.assertEqual(app.get_language_from_extension('.py'), 'Python')
            self.assertEqual(app.get_language_from_extension('.js'), 'JavaScript')
            self.assertEqual(app.get_language_from_extension('.html'), 'HTML')
            self.assertEqual(app.get_language_from_extension('.htm'), 'HTML')
            self.assertEqual(app.get_language_from_extension('.css'), 'CSS')
            self.assertEqual(app.get_language_from_extension('.json'), 'JSON')
            self.assertEqual(app.get_language_from_extension('.md'), 'Markdown')
            self.assertEqual(app.get_language_from_extension('.markdown'), 'Markdown')
            self.assertIsNone(app.get_language_from_extension('.unknown'))
            
    @patch('test_live_syntax_highlighting.CodeEditor')
    def test_load_sample_functionality(self, mock_code_editor):
        """Test that load_sample method works correctly."""
        with patch('test_live_syntax_highlighting.ttk'), \
             patch('test_live_syntax_highlighting.tk') as mock_tk, \
             patch('test_live_syntax_highlighting.SyntaxManager'), \
             patch('test_live_syntax_highlighting.ColorSchemeConfig'):
            
            # Setup mocks
            language_var_mock = Mock()
            language_var_mock.get.return_value = 'Python'
            mock_tk.StringVar.return_value = language_var_mock
            
            code_editor_instance = Mock()
            mock_code_editor.return_value = code_editor_instance
            
            app = SyntaxHighlightingTestApp(self.root_mock)
            app.language_var = language_var_mock
            app.code_editor = code_editor_instance
            
            # Test load_sample
            app.load_sample()
            
            # Verify code editor was called (using update_file_content method)
            self.assertGreaterEqual(code_editor_instance.update_file_content.call_count, 1)
            # Check the most recent call
            call_args = code_editor_instance.update_file_content.call_args[0]
            self.assertIsInstance(call_args[0], str)  # Content
            self.assertEqual(call_args[1], 'sample.py')  # Filename

class TestVisualVerificationIntegration(unittest.TestCase):
    """Integration tests for visual verification components."""
    
    def test_import_dependencies(self):
        """Test that all required dependencies can be imported."""
        try:
            from test_live_syntax_highlighting import SyntaxHighlightingTestApp
            # Try to import the dependencies the app uses
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            
            from code_editor import CodeEditor
            from syntax_manager import SyntaxManager
            from color_scheme_config import ColorSchemeConfig
            
            self.assertTrue(True, "All dependencies imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import dependencies: {e}")
            
    def test_sample_code_syntax_validity(self):
        """Test that sample code has valid syntax for basic parsing."""
        with patch('test_live_syntax_highlighting.ttk'), \
             patch('test_live_syntax_highlighting.tk'), \
             patch('test_live_syntax_highlighting.CodeEditor'), \
             patch('test_live_syntax_highlighting.SyntaxManager'), \
             patch('test_live_syntax_highlighting.ColorSchemeConfig'):
            
            app = SyntaxHighlightingTestApp(Mock())
            
            # Test Python syntax validity
            python_code = app.sample_code['Python']
            try:
                compile(python_code, '<string>', 'exec')
            except SyntaxError as e:
                self.fail(f"Python sample code has syntax errors: {e}")
                
            # Test JSON validity
            import json
            json_code = app.sample_code['JSON']
            try:
                json.loads(json_code)
            except json.JSONDecodeError as e:
                self.fail(f"JSON sample code is invalid: {e}")

if __name__ == '__main__':
    unittest.main() 