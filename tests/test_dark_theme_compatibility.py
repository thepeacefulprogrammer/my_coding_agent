"""
Tests for dark theme compatibility and edge cases.

This module tests color schemes against various dark theme scenarios,
including popular editor themes and accessibility edge cases.
"""

import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from color_schemes import get_nord_color_scheme, NORD0, NORD1, NORD2, NORD3
from color_scheme_config import ColorSchemeConfig


class TestDarkThemeCompatibility(unittest.TestCase):
    """Test compatibility with various dark themes and scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ColorSchemeConfig()
        self.nord_scheme = get_nord_color_scheme()
        
        # Popular dark theme backgrounds from various editors
        self.editor_dark_themes = {
            'vscode_dark': '#1e1e1e',
            'sublime_monokai': '#272822',
            'atom_one_dark': '#282c34',
            'intellij_darcula': '#2b2b2b',
            'github_dark': '#0d1117',
            'terminal_black': '#000000',
            'slack_dark': '#1a1d21',
            'discord_dark': '#36393f',
            'nord_polar': NORD0,  # #2e3440
        }
        
    def test_syntax_highlighting_against_popular_dark_themes(self):
        """Test syntax highlighting visibility against popular dark editor themes."""
        
        # Key syntax elements that must be visible
        syntax_elements = {
            'keyword': self.nord_scheme['keyword']['declaration'],
            'string': self.nord_scheme['string']['single'],
            'function': self.nord_scheme['name']['function'],
            'comment': self.nord_scheme['comment']['single'],
            'number': self.nord_scheme['number']['integer'],
            'operator': self.nord_scheme['operator']['symbol'],
        }
        
        for theme_name, bg_color in self.editor_dark_themes.items():
            for element_name, element_color in syntax_elements.items():
                with self.subTest(theme=theme_name, element=element_name):
                    contrast = self._calculate_contrast_ratio(element_color, bg_color)
                    
                    # Minimum readability thresholds
                    min_contrast = 1.5 if element_name == 'comment' else 2.5
                    
                    self.assertGreater(
                        contrast, min_contrast,
                        f"{element_name} ({element_color}) not visible enough "
                        f"against {theme_name} ({bg_color}): {contrast:.2f}:1"
                    )
                    
    def test_low_vision_accessibility(self):
        """Test color schemes meet requirements for users with low vision."""
        
        # Test against very dark backgrounds that might be used with high contrast needs
        high_contrast_backgrounds = ['#000000', '#0a0a0a', '#111111']
        
        critical_elements = {
            'keyword': self.nord_scheme['keyword']['declaration'],
            'string': self.nord_scheme['string']['single'],
            'function': self.nord_scheme['name']['function'],
            'error': self.nord_scheme.get('general', {}).get('error', NORD3),
        }
        
        for bg in high_contrast_backgrounds:
            for element_name, element_color in critical_elements.items():
                with self.subTest(background=bg, element=element_name):
                    contrast = self._calculate_contrast_ratio(element_color, bg)
                    
                    # Higher contrast requirement for accessibility
                    min_contrast = 4.0 if element_name == 'error' else 3.0
                    
                    self.assertGreater(
                        contrast, min_contrast,
                        f"{element_name} fails accessibility test against {bg}: "
                        f"{contrast:.2f}:1 (required: {min_contrast}:1)"
                    )
                    
    def test_color_blindness_compatibility(self):
        """Test that color schemes work well for users with color blindness."""
        
        # Test that different syntax elements are distinguishable by brightness/saturation
        # even if color perception is limited
        
        syntax_colors = {
            'keyword': self.nord_scheme['keyword']['declaration'],
            'string': self.nord_scheme['string']['single'],
            'function': self.nord_scheme['name']['function'],
            'number': self.nord_scheme['number']['integer'],
            'comment': self.nord_scheme['comment']['single'],
        }
        
        # Calculate luminance for each color
        luminances = {}
        for element, color in syntax_colors.items():
            luminances[element] = self._get_relative_luminance(color)
            
        # Verify that important elements have distinct luminance values
        important_pairs = [
            ('keyword', 'string'),
            ('function', 'keyword'),
            ('string', 'number'),
        ]
        
        for elem1, elem2 in important_pairs:
            lum1 = luminances[elem1]
            lum2 = luminances[elem2]
            
            # Elements should have noticeably different brightness
            luminance_diff = abs(lum1 - lum2)
            self.assertGreater(
                luminance_diff, 0.05,  # 5% minimum difference
                f"{elem1} and {elem2} are too similar in brightness: "
                f"{lum1:.3f} vs {lum2:.3f} (diff: {luminance_diff:.3f})"
            )
            
    def test_terminal_compatibility(self):
        """Test compatibility with terminal environments."""
        
        # Terminal colors can vary widely, test against common terminal backgrounds
        terminal_backgrounds = {
            'xterm_black': '#000000',
            'gnome_terminal': '#2e3436',
            'iterm_default': '#1d1f21',
            'windows_terminal': '#0c0c0c',
            'putty_black': '#000000',
        }
        
        # Terminal syntax highlighting typically uses basic colors
        terminal_elements = {
            'keyword': self.nord_scheme['keyword']['declaration'],
            'string': self.nord_scheme['string']['single'],
            'error': self.nord_scheme.get('general', {}).get('error', NORD3),
        }
        
        for terminal, bg_color in terminal_backgrounds.items():
            for element, color in terminal_elements.items():
                with self.subTest(terminal=terminal, element=element):
                    contrast = self._calculate_contrast_ratio(color, bg_color)
                    
                    # Terminal environments need higher contrast due to varying quality
                    min_contrast = 3.0
                    
                    self.assertGreater(
                        contrast, min_contrast,
                        f"{element} not visible in {terminal}: {contrast:.2f}:1"
                    )
                    
    def test_ambient_lighting_conditions(self):
        """Test visibility under different ambient lighting conditions."""
        
        # Simulate different viewing conditions by testing against
        # backgrounds that represent various screen brightness levels
        viewing_conditions = {
            'bright_room': '#404040',      # Screen appears lighter in bright rooms
            'normal_room': NORD0,          # Normal viewing
            'dark_room': '#1a1a1a',        # Very dark room
            'outdoor': '#606060',          # Bright outdoor viewing
        }
        
        key_elements = {
            'keyword': self.nord_scheme['keyword']['declaration'],
            'string': self.nord_scheme['string']['single'],
            'function': self.nord_scheme['name']['function'],
        }
        
        for condition, bg_color in viewing_conditions.items():
            for element, color in key_elements.items():
                with self.subTest(condition=condition, element=element):
                    contrast = self._calculate_contrast_ratio(color, bg_color)
                    
                    # Adjust requirements based on viewing condition
                    if condition == 'outdoor':
                        min_contrast = 2.0  # Outdoor is challenging, just ensure basic visibility
                    elif condition == 'bright_room':
                        min_contrast = 3.0
                    else:
                        min_contrast = 2.5
                        
                    self.assertGreater(
                        contrast, min_contrast,
                        f"{element} not visible in {condition} lighting: {contrast:.2f}:1"
                    )
                    
    def test_screen_technology_compatibility(self):
        """Test compatibility with different screen technologies."""
        
        # Different screen types can affect color perception
        # Test against backgrounds that simulate various screen characteristics
        
        screen_types = {
            'oled_pure_black': '#000000',    # OLED screens with pure black
            'lcd_dark': '#0f0f0f',           # LCD "black" is actually dark gray
            'e_ink': '#e0e0e0',              # E-ink displays (inverted for dark mode)
            'low_quality_lcd': '#333333',     # Older/cheaper LCDs
        }
        
        visibility_elements = {
            'keyword': self.nord_scheme['keyword']['declaration'],
            'string': self.nord_scheme['string']['single'],
            'error': self.nord_scheme.get('general', {}).get('error', NORD3),
        }
        
        for screen_type, bg_color in screen_types.items():
            for element, color in visibility_elements.items():
                with self.subTest(screen=screen_type, element=element):
                    # Skip e-ink test for now (would need different color scheme)
                    if screen_type == 'e_ink':
                        continue
                        
                    contrast = self._calculate_contrast_ratio(color, bg_color)
                    
                    # OLED can handle lower contrast due to perfect blacks
                    min_contrast = 2.0 if screen_type == 'oled_pure_black' else 2.5
                    
                    self.assertGreater(
                        contrast, min_contrast,
                        f"{element} not suitable for {screen_type}: {contrast:.2f}:1"
                    )
                    
    def test_monokai_dark_theme_compatibility(self):
        """Test that Monokai scheme works well with dark themes."""
        
        monokai_scheme = self.config.get_scheme("monokai")
        self.assertIsNotNone(monokai_scheme)
        
        # Test Monokai against dark backgrounds
        dark_backgrounds = [NORD0, '#1e1e1e', '#272822', '#000000']
        
        monokai_elements = {
            'keyword': monokai_scheme['keyword']['declaration'],
            'string': monokai_scheme['string']['single'],
            'function': monokai_scheme['name']['function'],
            'comment': monokai_scheme['comment']['single'],
        }
        
        for bg_color in dark_backgrounds:
            for element_name, element_color in monokai_elements.items():
                with self.subTest(background=bg_color, element=element_name):
                    contrast = self._calculate_contrast_ratio(element_color, bg_color)
                    
                    min_contrast = 1.8 if element_name == 'comment' else 2.5
                    
                    self.assertGreater(
                        contrast, min_contrast,
                        f"Monokai {element_name} poor contrast against {bg_color}: "
                        f"{contrast:.2f}:1"
                    )
                    
    def test_performance_with_color_calculations(self):
        """Test that color calculations don't impact performance significantly."""
        
        import time
        
        # Time multiple contrast calculations
        test_colors = [
            self.nord_scheme['keyword']['declaration'],
            self.nord_scheme['string']['single'],
            self.nord_scheme['name']['function'],
            self.nord_scheme['number']['integer'],
        ]
        
        backgrounds = list(self.editor_dark_themes.values())
        
        start_time = time.time()
        
        # Perform many contrast calculations
        for _ in range(100):
            for color in test_colors:
                for bg in backgrounds:
                    self._calculate_contrast_ratio(color, bg)
                    
        end_time = time.time()
        
        # Should complete quickly (within reasonable time)
        calculation_time = end_time - start_time
        self.assertLess(
            calculation_time, 1.0,  # Should take less than 1 second
            f"Color calculations too slow: {calculation_time:.3f} seconds"
        )
        
    # Helper methods
    
    def _calculate_contrast_ratio(self, color1, color2):
        """Calculate contrast ratio between two colors."""
        l1 = self._get_relative_luminance(color1)
        l2 = self._get_relative_luminance(color2)
        
        # Ensure l1 is the lighter color
        if l1 < l2:
            l1, l2 = l2, l1
            
        return (l1 + 0.05) / (l2 + 0.05)
        
    def _get_relative_luminance(self, hex_color):
        """Calculate relative luminance of a color according to WCAG standards."""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert hex to RGB
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        # Apply gamma correction
        def gamma_correct(c):
            if c <= 0.03928:
                return c / 12.92
            else:
                return pow((c + 0.055) / 1.055, 2.4)
                
        r = gamma_correct(r)
        g = gamma_correct(g)
        b = gamma_correct(b)
        
        # Calculate relative luminance
        return 0.2126 * r + 0.7152 * g + 0.0722 * b


if __name__ == "__main__":
    unittest.main() 