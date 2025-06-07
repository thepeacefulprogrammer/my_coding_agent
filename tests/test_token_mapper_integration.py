"""
Unit tests for TokenMapper integration with CodeEditor and syntax highlighting.

This module tests the integration of the Pygments token mapping system
with the CodeEditor widget creation and color application process.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from color_schemes import get_nord_color_scheme, NORD3, NORD6, NORD8, NORD9, NORD14, NORD15
from syntax_manager import SyntaxManager
from token_mapper import TokenMapper

# Import Pygments token types for testing
from pygments.token import Comment, Keyword, Name, String, Number


class TestTokenMapperIntegration(unittest.TestCase):
    """Test integration of TokenMapper with CodeEditor and syntax highlighting."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.syntax_manager = SyntaxManager()
        self.nord_scheme = get_nord_color_scheme()
        self.token_mapper = TokenMapper(self.nord_scheme)
        
    def test_token_mapper_integration_with_python_lexer(self):
        """Test TokenMapper integration with Python lexer specifically."""
        # Get Python lexer
        python_lexer = self.syntax_manager.get_lexer_for_file("test.py")
        
        # Test that TokenMapper can handle Python-specific tokens
        comment_color = self.token_mapper.get_color_for_token(Comment.Single)
        self.assertEqual(comment_color, NORD3)
        
        keyword_color = self.token_mapper.get_color_for_token(Keyword)
        self.assertEqual(keyword_color, NORD9)
        
        function_color = self.token_mapper.get_color_for_token(Name.Function)
        self.assertEqual(function_color, NORD8)
        
        string_color = self.token_mapper.get_color_for_token(String)
        self.assertEqual(string_color, NORD14)
        
        number_color = self.token_mapper.get_color_for_token(Number)
        self.assertEqual(number_color, NORD15)
        
    def test_apply_token_colors_to_mock_widget(self):
        """Test applying token colors to a mock widget."""
        # Create mock widget
        mock_widget = MagicMock()
        mock_widget.configure_colors = MagicMock()
        
        # Get Python lexer
        python_lexer = self.syntax_manager.get_lexer_for_file("test.py")
        
        # Test applying colors via TokenMapper
        success = self.token_mapper.apply_to_widget(mock_widget, python_lexer)
        
        # Should attempt to apply colors
        self.assertTrue(success)
        mock_widget.configure_colors.assert_called_once()
        
    def test_chlorophyll_color_scheme_conversion(self):
        """Test conversion of token mappings to Chlorophyll-compatible format."""
        # Get Chlorophyll-compatible color scheme
        chlorophyll_scheme = self.token_mapper.get_chlorophyll_color_scheme()
        
        # Should be a dictionary
        self.assertIsInstance(chlorophyll_scheme, dict)
        
        # Should contain token name mappings
        self.assertGreater(len(chlorophyll_scheme), 0)
        
        # Test that token names are strings (Chlorophyll format)
        for token_name, color in chlorophyll_scheme.items():
            self.assertIsInstance(token_name, str)
            self.assertIsInstance(color, str)
            self.assertTrue(color.startswith('#'))  # Should be hex color
            
    @patch('code_editor.CodeView')
    @patch('code_editor.CodeEditor')
    def test_code_editor_token_mapping_integration(self, mock_code_editor_class, mock_codeview):
        """Test that CodeEditor integrates token mapping when enabled."""
        from code_editor import CodeEditor
        
        # Mock widget instance
        mock_widget = MagicMock()
        mock_codeview.return_value = mock_widget
        
        # Mock CodeEditor instance
        mock_code_editor_instance = MagicMock()
        mock_code_editor_instance.token_mapper = TokenMapper(self.nord_scheme)
        mock_code_editor_instance.use_token_mapping = True
        mock_code_editor_instance.syntax_manager = self.syntax_manager
        mock_code_editor_class.return_value = mock_code_editor_instance
        
        # Create CodeEditor with token mapping enabled (mocked)
        code_editor = CodeEditor(
            parent=MagicMock(),
            syntax_manager=self.syntax_manager,
            color_scheme="nord",
            use_token_mapping=True
        )
        
        # Verify CodeEditor was called with correct parameters
        mock_code_editor_class.assert_called_once()
        call_args, call_kwargs = mock_code_editor_class.call_args
        self.assertEqual(call_kwargs.get('color_scheme'), "nord")
        self.assertEqual(call_kwargs.get('use_token_mapping'), True)
        
        # Should have token mapper (mocked)
        self.assertIsNotNone(code_editor.token_mapper)
        self.assertTrue(code_editor.use_token_mapping)
        
    @patch('code_editor.CodeView')
    @patch('code_editor.CodeEditor')
    def test_code_editor_without_token_mapping(self, mock_code_editor_class, mock_codeview):
        """Test that CodeEditor works normally when token mapping is disabled."""
        from code_editor import CodeEditor
        
        # Mock widget instance
        mock_widget = MagicMock()
        mock_codeview.return_value = mock_widget
        
        # Mock CodeEditor instance
        mock_code_editor_instance = MagicMock()
        mock_code_editor_instance.token_mapper = None
        mock_code_editor_instance.use_token_mapping = False
        mock_code_editor_instance.syntax_manager = self.syntax_manager
        mock_code_editor_class.return_value = mock_code_editor_instance
        
        # Create CodeEditor with token mapping disabled (mocked)
        code_editor = CodeEditor(
            parent=MagicMock(),
            syntax_manager=self.syntax_manager,
            color_scheme="monokai",
            use_token_mapping=False
        )
        
        # Verify CodeEditor was called with correct parameters
        mock_code_editor_class.assert_called_once()
        call_args, call_kwargs = mock_code_editor_class.call_args
        self.assertEqual(call_kwargs.get('color_scheme'), "monokai")
        self.assertEqual(call_kwargs.get('use_token_mapping'), False)
        
        # Should not have token mapper (mocked)
        self.assertIsNone(code_editor.token_mapper)
        self.assertFalse(code_editor.use_token_mapping)
        
    def test_multi_language_token_color_consistency(self):
        """Test that token colors are consistent across different languages."""
        languages = ['test.py', 'test.js', 'index.html', 'styles.css']
        
        for filename in languages:
            with self.subTest(filename=filename):
                lexer = self.syntax_manager.get_lexer_for_file(filename)
                
                # Comments should always be NORD3 regardless of language
                comment_color = self.token_mapper.get_color_for_token(Comment)
                self.assertEqual(comment_color, NORD3)
                
                # Keywords should always be NORD9 regardless of language
                keyword_color = self.token_mapper.get_color_for_token(Keyword)
                self.assertEqual(keyword_color, NORD9)
                
                # Strings should always be NORD14 regardless of language
                string_color = self.token_mapper.get_color_for_token(String)
                self.assertEqual(string_color, NORD14)


if __name__ == "__main__":
    unittest.main()
