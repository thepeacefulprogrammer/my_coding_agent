"""
Unit tests for color schemes module.

This module tests the color scheme definitions and functionality,
including the Nord color scheme implementation.
"""

import unittest
from src.color_schemes import (
    get_nord_color_scheme,
    get_available_color_schemes,
    get_color_scheme,
    is_color_scheme_available,
    NORD0, NORD1, NORD2, NORD3, NORD4, NORD5, NORD6,
    NORD7, NORD8, NORD9, NORD10, NORD11, NORD12, NORD13, NORD14, NORD15
)


class TestColorSchemes(unittest.TestCase):
    """Test color scheme definitions and functionality."""
    
    def test_nord_color_constants(self):
        """Test that Nord color constants are properly defined."""
        # Test Polar Night colors (dark)
        self.assertEqual(NORD0, "#2e3440")
        self.assertEqual(NORD1, "#3b4252")
        self.assertEqual(NORD2, "#434c5e")
        self.assertEqual(NORD3, "#4c566a")
        
        # Test Snow Storm colors (light)
        self.assertEqual(NORD4, "#d8dee9")
        self.assertEqual(NORD5, "#e5e9f0")
        self.assertEqual(NORD6, "#eceff4")
        
        # Test Frost colors (blue)
        self.assertEqual(NORD7, "#8fbcbb")
        self.assertEqual(NORD8, "#88c0d0")
        self.assertEqual(NORD9, "#81a1c1")
        self.assertEqual(NORD10, "#5e81ac")
        
        # Test Aurora colors (colorful)
        self.assertEqual(NORD11, "#bf616a")
        self.assertEqual(NORD12, "#d08770")
        self.assertEqual(NORD13, "#ebcb8b")
        self.assertEqual(NORD14, "#a3be8c")
        self.assertEqual(NORD15, "#b48ead")
        
    def test_get_nord_color_scheme(self):
        """Test that Nord color scheme is properly structured."""
        scheme = get_nord_color_scheme()
        
        # Test that it's a dictionary
        self.assertIsInstance(scheme, dict)
        
        # Test required sections exist
        required_sections = ['editor', 'general', 'keyword', 'name', 'operator', 'string', 'number', 'comment']
        for section in required_sections:
            self.assertIn(section, scheme)
            self.assertIsInstance(scheme[section], dict)
            
    def test_get_color_scheme(self):
        """Test getting specific color scheme by name."""
        # Test getting Nord scheme
        nord_scheme = get_color_scheme('nord')
        self.assertIsNotNone(nord_scheme)
        self.assertEqual(nord_scheme, get_nord_color_scheme())
        
        # Test case insensitive
        nord_scheme_upper = get_color_scheme('NORD')
        self.assertEqual(nord_scheme_upper, get_nord_color_scheme())
        
        # Test non-existent scheme
        nonexistent = get_color_scheme('nonexistent')
        self.assertIsNone(nonexistent)


if __name__ == "__main__":
    unittest.main()
