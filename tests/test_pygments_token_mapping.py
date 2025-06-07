"""
Unit tests for Pygments token mapping system.

This module tests the mapping of Pygments token types to Nord color scheme colors,
ensuring that syntax highlighting works correctly with the underlying Pygments tokenization.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from color_schemes import get_nord_color_scheme, NORD0, NORD3, NORD6, NORD7, NORD8, NORD9, NORD11, NORD12, NORD13, NORD14, NORD15

# Import Pygments token types for testing
from pygments.token import (
    Token, Comment, Keyword, Name, String, Number, Operator, 
    Punctuation, Error, Generic, Literal, Text, Whitespace
)


class TestPygmentsTokenMapping(unittest.TestCase):
    """Test Pygments token type mapping to Nord colors."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.nord_scheme = get_nord_color_scheme()
        
    def test_token_mapper_class_exists(self):
        """Test that TokenMapper class can be imported and instantiated."""
        try:
            from token_mapper import TokenMapper
            mapper = TokenMapper(self.nord_scheme)
            self.assertIsNotNone(mapper)
        except ImportError:
            self.fail("TokenMapper class should be importable from token_mapper module")
            
    def test_comment_token_mapping(self):
        """Test that comment tokens map to correct Nord colors."""
        from token_mapper import TokenMapper
        
        mapper = TokenMapper(self.nord_scheme)
        
        # Test single line comments
        comment_color = mapper.get_color_for_token(Comment.Single)
        self.assertEqual(comment_color, NORD3)
        
        # Test multiline comments
        multiline_color = mapper.get_color_for_token(Comment.Multiline)
        self.assertEqual(multiline_color, NORD3)
        
    def test_keyword_token_mapping(self):
        """Test that keyword tokens map to correct Nord colors."""
        from token_mapper import TokenMapper
        
        mapper = TokenMapper(self.nord_scheme)
        
        # Test general keywords
        keyword_color = mapper.get_color_for_token(Keyword)
        self.assertEqual(keyword_color, NORD9)
        
        # Test declarations (function, class, def)
        declaration_color = mapper.get_color_for_token(Keyword.Declaration)
        self.assertEqual(declaration_color, NORD9)
        
    def test_string_token_mapping(self):
        """Test that string tokens map to correct Nord colors."""
        from token_mapper import TokenMapper
        
        mapper = TokenMapper(self.nord_scheme)
        
        # Test general strings
        string_color = mapper.get_color_for_token(String)
        self.assertEqual(string_color, NORD14)
        
        # Test double quoted strings
        double_string_color = mapper.get_color_for_token(String.Double)
        self.assertEqual(double_string_color, NORD14)
        
    def test_number_token_mapping(self):
        """Test that number tokens map to correct Nord colors."""
        from token_mapper import TokenMapper
        
        mapper = TokenMapper(self.nord_scheme)
        
        # Test general numbers
        number_color = mapper.get_color_for_token(Number)
        self.assertEqual(number_color, NORD15)
        
        # Test integers
        integer_color = mapper.get_color_for_token(Number.Integer)
        self.assertEqual(integer_color, NORD15)
        
        # Test floats
        float_color = mapper.get_color_for_token(Number.Float)
        self.assertEqual(float_color, NORD15)
        
    def test_name_token_mapping(self):
        """Test that name tokens map to correct Nord colors."""
        from token_mapper import TokenMapper
        
        mapper = TokenMapper(self.nord_scheme)
        
        # Test function names
        function_color = mapper.get_color_for_token(Name.Function)
        self.assertEqual(function_color, NORD8)
        
        # Test class names
        class_color = mapper.get_color_for_token(Name.Class)
        self.assertEqual(class_color, NORD7)
        
        # Test variable names (default)
        variable_color = mapper.get_color_for_token(Name)
        self.assertEqual(variable_color, NORD6)
        
    def test_operator_token_mapping(self):
        """Test that operator tokens map to correct Nord colors."""
        from token_mapper import TokenMapper
        
        mapper = TokenMapper(self.nord_scheme)
        
        # Test general operators
        operator_color = mapper.get_color_for_token(Operator)
        self.assertEqual(operator_color, NORD9)
        
        # Test word operators (and, or, not, in)
        word_op_color = mapper.get_color_for_token(Operator.Word)
        self.assertEqual(word_op_color, NORD9)
        
    def test_error_token_mapping(self):
        """Test that error tokens map to correct Nord colors."""
        from token_mapper import TokenMapper
        
        mapper = TokenMapper(self.nord_scheme)
        
        # Test error tokens
        error_color = mapper.get_color_for_token(Error)
        self.assertEqual(error_color, NORD11)
        
    def test_token_inheritance_fallback(self):
        """Test that token inheritance works for fallback colors."""
        from token_mapper import TokenMapper
        
        mapper = TokenMapper(self.nord_scheme)
        
        # Test that specific string types fall back to general string color
        # if no specific mapping exists
        doc_string_color = mapper.get_color_for_token(String.Doc)
        self.assertEqual(doc_string_color, NORD14)  # Should fall back to general string
        
        # Test that specific number types fall back to general number color
        hex_color = mapper.get_color_for_token(Number.Hex)
        self.assertEqual(hex_color, NORD15)  # Should fall back to general number
        
    def test_unknown_token_fallback(self):
        """Test that unknown tokens have a reasonable fallback color."""
        from token_mapper import TokenMapper
        
        mapper = TokenMapper(self.nord_scheme)
        
        # Test completely unknown token type
        unknown_color = mapper.get_color_for_token(Token)
        self.assertIsNotNone(unknown_color)
        # Should fall back to a neutral color
        self.assertEqual(unknown_color, NORD6)


if __name__ == "__main__":
    unittest.main()
