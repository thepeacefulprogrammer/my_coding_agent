"""
Unit tests for Nord color scheme application to multiple programming languages.

This module tests that the Nord color scheme is properly applied to JavaScript,
HTML, CSS, and other common programming languages through syntax highlighting.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from color_schemes import get_nord_color_scheme, NORD0, NORD3, NORD6, NORD7, NORD8, NORD9, NORD11, NORD12, NORD13, NORD14, NORD15
from syntax_manager import SyntaxManager


class TestNordMultiLanguageSyntax(unittest.TestCase):
    """Test Nord color scheme application to multiple programming languages."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.syntax_manager = SyntaxManager()
        
    def test_javascript_lexer_detection(self):
        """Test that JavaScript lexer is correctly detected for JS files."""
        # Test .js extension
        js_lexer = self.syntax_manager.get_lexer_for_file("test.js")
        self.assertIsNotNone(js_lexer)
        self.assertEqual(js_lexer.name, "JavaScript")
        
        # Test .jsx extension
        jsx_lexer = self.syntax_manager.get_lexer_for_file("component.jsx")
        self.assertIsNotNone(jsx_lexer)
        self.assertEqual(jsx_lexer.name, "JSX")
        
        # Test .ts extension
        ts_lexer = self.syntax_manager.get_lexer_for_file("types.ts")
        self.assertIsNotNone(ts_lexer)
        self.assertEqual(ts_lexer.name, "TypeScript")
        
    def test_html_lexer_detection(self):
        """Test that HTML lexer is correctly detected for HTML files."""
        # Test .html extension
        html_lexer = self.syntax_manager.get_lexer_for_file("index.html")
        self.assertIsNotNone(html_lexer)
        self.assertEqual(html_lexer.name, "HTML")
        
        # Test .htm extension
        htm_lexer = self.syntax_manager.get_lexer_for_file("page.htm")
        self.assertIsNotNone(htm_lexer)
        self.assertEqual(htm_lexer.name, "HTML")
        
    def test_css_lexer_detection(self):
        """Test that CSS lexer is correctly detected for CSS files."""
        # Test .css extension
        css_lexer = self.syntax_manager.get_lexer_for_file("styles.css")
        self.assertIsNotNone(css_lexer)
        self.assertEqual(css_lexer.name, "CSS")
        
        # Test .scss extension
        scss_lexer = self.syntax_manager.get_lexer_for_file("styles.scss")
        self.assertIsNotNone(scss_lexer)
        self.assertEqual(scss_lexer.name, "SCSS")
        
    def test_other_common_language_lexer_detection(self):
        """Test lexer detection for other common programming languages."""
        # Test JSON
        json_lexer = self.syntax_manager.get_lexer_for_file("config.json")
        self.assertIsNotNone(json_lexer)
        self.assertEqual(json_lexer.name, "JSON")
        
        # Test Markdown
        md_lexer = self.syntax_manager.get_lexer_for_file("README.md")
        self.assertIsNotNone(md_lexer)
        self.assertEqual(md_lexer.name, "Markdown")
        
        # Test XML
        xml_lexer = self.syntax_manager.get_lexer_for_file("config.xml")
        self.assertIsNotNone(xml_lexer)
        self.assertEqual(xml_lexer.name, "XML")
        
        # Test YAML
        yaml_lexer = self.syntax_manager.get_lexer_for_file("config.yaml")
        self.assertIsNotNone(yaml_lexer)
        self.assertEqual(yaml_lexer.name, "YAML")
        
    def test_javascript_nord_scheme_compatibility(self):
        """Test that Nord color scheme is compatible with JavaScript syntax highlighting."""
        # Get JavaScript lexer
        js_lexer = self.syntax_manager.get_lexer_for_file("test.js")
        self.assertIsNotNone(js_lexer)
        self.assertEqual(js_lexer.name, "JavaScript")
        
        # Verify Nord scheme has all necessary color mappings for JavaScript
        nord_scheme = get_nord_color_scheme()
        
        # Essential JavaScript syntax elements should have color mappings
        self.assertIn('keyword', nord_scheme)
        self.assertIn('name', nord_scheme)
        self.assertIn('string', nord_scheme)
        self.assertIn('number', nord_scheme)
        self.assertIn('comment', nord_scheme)
        self.assertIn('operator', nord_scheme)
        
    def test_html_nord_scheme_compatibility(self):
        """Test that Nord color scheme is compatible with HTML syntax highlighting."""
        # Get HTML lexer
        html_lexer = self.syntax_manager.get_lexer_for_file("index.html")
        self.assertIsNotNone(html_lexer)
        self.assertEqual(html_lexer.name, "HTML")
        
        # Verify Nord scheme has all necessary color mappings for HTML
        nord_scheme = get_nord_color_scheme()
        
        # Essential HTML syntax elements should have color mappings
        self.assertIn('name', nord_scheme)  # For tags and attributes
        self.assertIn('string', nord_scheme)  # For attribute values
        self.assertIn('comment', nord_scheme)  # For HTML comments
        self.assertIn('keyword', nord_scheme)  # For DOCTYPE, etc.
        
    def test_css_nord_scheme_compatibility(self):
        """Test that Nord color scheme is compatible with CSS syntax highlighting."""
        # Get CSS lexer
        css_lexer = self.syntax_manager.get_lexer_for_file("styles.css")
        self.assertIsNotNone(css_lexer)
        self.assertEqual(css_lexer.name, "CSS")
        
        # Verify Nord scheme has all necessary color mappings for CSS
        nord_scheme = get_nord_color_scheme()
        
        # Essential CSS syntax elements should have color mappings
        self.assertIn('name', nord_scheme)  # For selectors and properties
        self.assertIn('string', nord_scheme)  # For values
        self.assertIn('number', nord_scheme)  # For measurements
        self.assertIn('comment', nord_scheme)  # For CSS comments
        
    def test_javascript_syntax_color_mapping(self):
        """Test that JavaScript syntax elements map to correct Nord colors."""
        nord_scheme = get_nord_color_scheme()
        
        # Test keyword colors (function, const, let, var, if, etc.)
        self.assertEqual(nord_scheme['keyword']['declaration'], NORD9)  # function, const, let
        self.assertEqual(nord_scheme['keyword']['reserved'], NORD9)     # if, else, for, while
        
        # Test name colors (functions, variables)
        self.assertEqual(nord_scheme['name']['function'], NORD8)        # Function names
        self.assertEqual(nord_scheme['name']['builtin'], NORD8)         # Built-in functions
        
        # Test string colors
        self.assertEqual(nord_scheme['string']['single'], NORD14)       # Single quotes
        self.assertEqual(nord_scheme['string']['double'], NORD14)       # Double quotes
        self.assertEqual(nord_scheme['string']['interpol'], NORD13)     # Template literals
        
        # Test number colors
        self.assertEqual(nord_scheme['number']['integer'], NORD15)      # Integers
        self.assertEqual(nord_scheme['number']['float'], NORD15)        # Floats
        
        # Test comment colors
        self.assertEqual(nord_scheme['comment']['single'], NORD3)       # // comments
        self.assertEqual(nord_scheme['comment']['multiline'], NORD3)    # /* */ comments
        
    def test_html_syntax_color_mapping(self):
        """Test that HTML syntax elements map to correct Nord colors."""
        nord_scheme = get_nord_color_scheme()
        
        # Test name colors for HTML elements
        self.assertEqual(nord_scheme['name']['tag'], NORD9)             # HTML tags
        self.assertEqual(nord_scheme['name']['attr'], NORD8)            # Attributes
        
        # Test string colors for attribute values
        self.assertEqual(nord_scheme['string']['double'], NORD14)       # Attribute values
        self.assertEqual(nord_scheme['string']['single'], NORD14)       # Single quote values
        
        # Test comment colors
        self.assertEqual(nord_scheme['comment']['multiline'], NORD3)    # <!-- --> comments
        
        # Test keyword type for doctype
        self.assertEqual(nord_scheme['keyword']['type'], NORD7)         # DOCTYPE
        
    def test_css_syntax_color_mapping(self):
        """Test that CSS syntax elements map to correct Nord colors."""
        nord_scheme = get_nord_color_scheme()
        
        # Test name colors for CSS selectors and properties
        self.assertEqual(nord_scheme['name']['tag'], NORD9)             # Element selectors
        self.assertEqual(nord_scheme['name']['class'], NORD7)           # Class selectors
        self.assertEqual(nord_scheme['name']['attr'], NORD8)            # Property names
        
        # Test string colors for CSS values
        self.assertEqual(nord_scheme['string']['single'], NORD14)       # Single quote values
        self.assertEqual(nord_scheme['string']['double'], NORD14)       # Double quote values
        
        # Test number colors for measurements
        self.assertEqual(nord_scheme['number']['integer'], NORD15)      # Numbers
        self.assertEqual(nord_scheme['number']['float'], NORD15)        # Decimal values
        
        # Test comment colors
        self.assertEqual(nord_scheme['comment']['multiline'], NORD3)    # /* */ comments
        
    def test_nord_scheme_universal_syntax_elements(self):
        """Test that Nord scheme handles universal syntax elements across languages."""
        nord_scheme = get_nord_color_scheme()
        
        # Test universal elements that should be consistent across languages
        self.assertEqual(nord_scheme['general']['keyword'], NORD9)      # General keywords
        self.assertEqual(nord_scheme['general']['string'], NORD14)      # General strings
        self.assertEqual(nord_scheme['general']['comment'], NORD3)      # General comments
        self.assertEqual(nord_scheme['general']['error'], NORD11)       # Error highlighting
        self.assertEqual(nord_scheme['general']['escape'], NORD13)      # Escape sequences
        self.assertEqual(nord_scheme['general']['punctuation'], NORD6)  # Punctuation
        
        # Test operator colors
        self.assertEqual(nord_scheme['operator']['symbol'], NORD9)      # Operators
        self.assertEqual(nord_scheme['operator']['word'], NORD9)        # Word operators
        
    def test_multi_language_file_lexer_compatibility(self):
        """Test that all supported languages have lexers that work with Nord scheme."""
        # Test different file types
        test_files = [
            ("test.js", "JavaScript"),
            ("index.html", "HTML"),
            ("styles.css", "CSS"),
            ("config.json", "JSON"),
            ("README.md", "Markdown"),
            ("script.ts", "TypeScript"),
            ("component.jsx", "JSX"),
            ("config.xml", "XML"),
            ("config.yaml", "YAML"),
        ]
        
        nord_scheme = get_nord_color_scheme()
        
        for filename, expected_lexer_name in test_files:
            with self.subTest(filename=filename):
                # Get lexer for file
                lexer = self.syntax_manager.get_lexer_for_file(filename)
                self.assertEqual(lexer.name, expected_lexer_name)
                
                # Verify that lexer exists and Nord scheme has required categories
                self.assertIsNotNone(lexer)
                
                # All languages should be able to use basic Nord color categories
                self.assertIn('general', nord_scheme)
                self.assertIn('keyword', nord_scheme)
                self.assertIn('string', nord_scheme)
                self.assertIn('comment', nord_scheme)


if __name__ == "__main__":
    unittest.main()
