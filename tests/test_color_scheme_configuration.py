"""
Unit tests for color scheme configuration system.

This module tests the configuration system that allows for dynamic color scheme
management, user customization, and easy extensibility of color schemes.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import json
import tempfile

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from color_schemes import get_nord_color_scheme, NORD0, NORD3, NORD6, NORD7, NORD8, NORD9, NORD11, NORD12, NORD13, NORD14, NORD15


class TestColorSchemeConfiguration(unittest.TestCase):
    """Test color scheme configuration system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.nord_scheme = get_nord_color_scheme()
        
    def test_color_scheme_config_class_exists(self):
        """Test that ColorSchemeConfig class can be imported and instantiated."""
        try:
            from color_scheme_config import ColorSchemeConfig
            config = ColorSchemeConfig()
            self.assertIsNotNone(config)
        except ImportError:
            self.fail("ColorSchemeConfig class should be importable from color_scheme_config module")
            
    def test_config_initialization_with_default_schemes(self):
        """Test ColorSchemeConfig initialization with default color schemes."""
        from color_scheme_config import ColorSchemeConfig
        
        config = ColorSchemeConfig()
        
        # Should have default schemes available
        available_schemes = config.get_available_schemes()
        self.assertIsInstance(available_schemes, list)
        self.assertGreater(len(available_schemes), 0)
        
        # Should include Nord scheme
        self.assertIn("nord", available_schemes)
        
    def test_get_color_scheme_by_name(self):
        """Test retrieving color schemes by name."""
        from color_scheme_config import ColorSchemeConfig
        
        config = ColorSchemeConfig()
        
        # Should be able to get Nord scheme
        nord_scheme = config.get_scheme("nord")
        self.assertIsNotNone(nord_scheme)
        self.assertIsInstance(nord_scheme, dict)
        
        # Should return None for unknown scheme
        unknown_scheme = config.get_scheme("nonexistent")
        self.assertIsNone(unknown_scheme)
        
    def test_register_custom_color_scheme(self):
        """Test registering a custom color scheme."""
        from color_scheme_config import ColorSchemeConfig
        
        config = ColorSchemeConfig()
        
        # Create a custom color scheme
        custom_scheme = {
            'keyword': {'declaration': '#FF0000'},
            'string': {'single': '#00FF00'},
            'comment': {'single': '#0000FF'}
        }
        
        # Register the custom scheme
        success = config.register_scheme("custom_red", custom_scheme)
        self.assertTrue(success)
        
        # Should be available now
        available_schemes = config.get_available_schemes()
        self.assertIn("custom_red", available_schemes)
        
        # Should be retrievable
        retrieved_scheme = config.get_scheme("custom_red")
        self.assertEqual(retrieved_scheme, custom_scheme)
        
    def test_validate_color_scheme_structure(self):
        """Test color scheme validation."""
        from color_scheme_config import ColorSchemeConfig
        
        config = ColorSchemeConfig()
        
        # Valid scheme should pass validation
        valid_scheme = {
            'keyword': {'declaration': '#FF0000'},
            'string': {'single': '#00FF00'},
            'comment': {'single': '#0000FF'}
        }
        self.assertTrue(config.validate_scheme(valid_scheme))
        
        # Invalid scheme should fail validation
        invalid_scheme = {
            'keyword': 'not_a_dict',  # Should be a dictionary
            'string': {'single': 'invalid_color'}  # Invalid color format
        }
        self.assertFalse(config.validate_scheme(invalid_scheme))
        
    def test_set_default_color_scheme(self):
        """Test setting and getting the default color scheme."""
        from color_scheme_config import ColorSchemeConfig
        
        config = ColorSchemeConfig()
        
        # Set default scheme
        config.set_default_scheme("nord")
        
        # Should return the set default
        default_scheme_name = config.get_default_scheme_name()
        self.assertEqual(default_scheme_name, "nord")
        
        # Should be able to get the default scheme
        default_scheme = config.get_default_scheme()
        self.assertIsNotNone(default_scheme)
        self.assertIsInstance(default_scheme, dict)
        
    def test_color_scheme_configuration_persistence(self):
        """Test saving and loading color scheme configuration."""
        from color_scheme_config import ColorSchemeConfig
        
        config = ColorSchemeConfig()
        
        # Register a custom scheme
        custom_scheme = {
            'keyword': {'declaration': '#FF0000'},
            'string': {'single': '#00FF00'}
        }
        config.register_scheme("test_scheme", custom_scheme)
        config.set_default_scheme("test_scheme")
        
        # Test save configuration
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            config_file = f.name
            
        try:
            # Save configuration
            success = config.save_configuration(config_file)
            self.assertTrue(success)
            
            # Create new config instance and load
            new_config = ColorSchemeConfig()
            load_success = new_config.load_configuration(config_file)
            self.assertTrue(load_success)
            
            # Should have the same schemes
            self.assertIn("test_scheme", new_config.get_available_schemes())
            self.assertEqual(new_config.get_default_scheme_name(), "test_scheme")
            
        finally:
            # Cleanup
            if os.path.exists(config_file):
                os.unlink(config_file)
                
    def test_create_color_scheme_from_template(self):
        """Test creating new color schemes from templates."""
        from color_scheme_config import ColorSchemeConfig
        
        config = ColorSchemeConfig()
        
        # Create scheme from Nord template with modifications
        modifications = {
            'keyword': {'declaration': '#FF5555'},  # Custom red for keywords
            'string': {'single': '#50FA7B'}         # Custom green for strings
        }
        
        new_scheme = config.create_scheme_from_template("nord", "custom_nord", modifications)
        self.assertIsNotNone(new_scheme)
        
        # Should have custom modifications
        self.assertEqual(new_scheme['keyword']['declaration'], '#FF5555')
        self.assertEqual(new_scheme['string']['single'], '#50FA7B')
        
        # Should preserve other Nord colors
        self.assertEqual(new_scheme['comment']['single'], NORD3)
        
    def test_color_scheme_inheritance(self):
        """Test color scheme inheritance functionality."""
        from color_scheme_config import ColorSchemeConfig
        
        config = ColorSchemeConfig()
        
        # Create base scheme
        base_scheme = {
            'keyword': {'declaration': '#FF0000'},
            'string': {'single': '#00FF00'},
            'comment': {'single': '#0000FF'}
        }
        config.register_scheme("base", base_scheme)
        
        # Create derived scheme with inheritance
        derived_overrides = {
            'keyword': {'declaration': '#FF5555'}  # Override only keywords
        }
        
        success = config.register_scheme_with_inheritance("derived", "base", derived_overrides)
        self.assertTrue(success)
        
        derived_scheme = config.get_scheme("derived")
        self.assertIsNotNone(derived_scheme)
        
        # Should have overridden keyword color
        self.assertEqual(derived_scheme['keyword']['declaration'], '#FF5555')
        
        # Should inherit other colors from base
        self.assertEqual(derived_scheme['string']['single'], '#00FF00')
        self.assertEqual(derived_scheme['comment']['single'], '#0000FF')
        
    def test_dynamic_color_scheme_switching(self):
        """Test dynamic switching between color schemes."""
        from color_scheme_config import ColorSchemeConfig
        
        config = ColorSchemeConfig()
        
        # Should be able to switch current scheme
        config.set_current_scheme("nord")
        self.assertEqual(config.get_current_scheme_name(), "nord")
        
        # Current scheme should be retrievable
        current_scheme = config.get_current_scheme()
        self.assertIsNotNone(current_scheme)
        
        # Should be able to switch to different scheme
        if "monokai" in config.get_available_schemes():
            config.set_current_scheme("monokai")
            self.assertEqual(config.get_current_scheme_name(), "monokai")


if __name__ == "__main__":
    unittest.main() 