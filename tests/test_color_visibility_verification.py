"""
Unit tests for color visibility verification against dark background themes.

This module tests that the Nord color scheme provides adequate contrast and
visibility against various dark background themes for syntax highlighting.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from color_schemes import get_nord_color_scheme, NORD0, NORD3, NORD6, NORD7, NORD8, NORD9, NORD11, NORD12, NORD13, NORD14, NORD15
from color_visibility_report import ColorVisibilityReporter


class TestColorVisibilityVerification(unittest.TestCase):
    """Test color visibility verification against dark backgrounds."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reporter = ColorVisibilityReporter()
        self.nord_scheme = get_nord_color_scheme()
        
    def test_color_visibility_reporter_initialization(self):
        """Test that ColorVisibilityReporter initializes correctly."""
        self.assertIsNotNone(self.reporter)
        self.assertIsNotNone(self.reporter.config)
        
        # Test that standard dark backgrounds are defined
        self.assertIn('nord_polar_night', self.reporter.test_backgrounds)
        self.assertIn('vscode_dark', self.reporter.test_backgrounds)
        self.assertIn('sublime_monokai', self.reporter.test_backgrounds)
        self.assertIn('github_dark', self.reporter.test_backgrounds)
        self.assertIn('pure_black', self.reporter.test_backgrounds)
        
        # Test that WCAG standards are defined
        self.assertIn('AA_normal', self.reporter.wcag_standards)
        self.assertIn('AA_large', self.reporter.wcag_standards)
        self.assertIn('AAA_normal', self.reporter.wcag_standards)
        self.assertIn('AAA_large', self.reporter.wcag_standards)
        
    def test_nord_color_scheme_contrast_ratios(self):
        """Test that Nord color scheme meets minimum contrast ratios."""
        # Test against Nord's primary background (Polar Night)
        primary_bg = NORD0  # #2e3440
        
        # Test essential syntax elements have adequate contrast
        test_cases = [
            ('keywords', NORD9, 'AA_large'),      # Blue keywords
            ('strings', NORD14, 'AA_large'),      # Green strings  
            ('functions', NORD8, 'AA_large'),     # Cyan functions
            ('classes', NORD7, 'AA_large'),       # Purple classes
            ('numbers', NORD15, 'AA_large'),      # Purple numbers
            ('operators', NORD9, 'AA_large'),     # Blue operators
        ]
        
        for element_name, color, standard in test_cases:
            with self.subTest(element=element_name):
                contrast = self.reporter._calculate_contrast_ratio(color, primary_bg)
                required_ratio = self.reporter.wcag_standards[standard]
                self.assertGreaterEqual(
                    contrast, required_ratio,
                    f"{element_name} ({color}) contrast {contrast:.2f} should be >= {required_ratio}"
                )
                
    def test_nord_comments_visibility_awareness(self):
        """Test that we're aware of comment visibility limitations."""
        # Comments (NORD3) are intentionally subtle but should still be readable
        primary_bg = NORD0
        comment_color = NORD3
        
        contrast = self.reporter._calculate_contrast_ratio(comment_color, primary_bg)
        
        # Comments may not meet WCAG AA but should be > 1.5 for basic readability
        self.assertGreater(contrast, 1.5, 
                          "Comments should have basic readability contrast")
        
        # Document that this is intentional design choice
        self.assertLess(contrast, self.reporter.wcag_standards['AA_large'],
                       "Comments are intentionally subtle (design choice)")
                       
    def test_color_visibility_against_multiple_dark_backgrounds(self):
        """Test color visibility against various dark background themes."""
        essential_colors = {
            'keyword': NORD9,     # Blue - keywords, operators
            'string': NORD14,     # Green - strings
            'function': NORD8,    # Cyan - functions  
            'class': NORD7,       # Purple - classes
            'number': NORD15,     # Purple - numbers
        }
        
        dark_backgrounds = {
            'vscode_dark': '#1e1e1e',
            'sublime_monokai': '#272822', 
            'github_dark': '#0d1117',
        }
        
        for bg_name, bg_color in dark_backgrounds.items():
            for element_name, element_color in essential_colors.items():
                with self.subTest(background=bg_name, element=element_name):
                    contrast = self.reporter._calculate_contrast_ratio(element_color, bg_color)
                    # Should meet WCAG AA Large text (3.0) at minimum
                    self.assertGreaterEqual(
                        contrast, 3.0,
                        f"{element_name} on {bg_name}: {contrast:.2f} should be >= 3.0"
                    )
                    
    def test_generate_comprehensive_visibility_report(self):
        """Test that comprehensive visibility report can be generated."""
        report = self.reporter.generate_comprehensive_report("nord")
        
        # Test report structure
        required_sections = [
            'scheme_name', 'timestamp', 'summary', 'contrast_analysis',
            'accessibility_compliance', 'recommendations', 'detailed_results'
        ]
        
        for section in required_sections:
            self.assertIn(section, report)
            
        # Test summary contains expected metrics
        summary = report['summary']
        self.assertIn('overall_rating', summary)
        self.assertIn('avg_contrast_ratio', summary)
        self.assertIn('wcag_aa_compliance', summary)
        self.assertIn('wcag_aaa_compliance', summary)
        
        # Test contrast analysis structure
        contrast_analysis = report['contrast_analysis']
        self.assertIn('by_element', contrast_analysis)
        self.assertIn('by_background', contrast_analysis)
        self.assertIn('overall_stats', contrast_analysis)
        
    def test_wcag_accessibility_compliance_check(self):
        """Test WCAG accessibility compliance checking."""
        accessibility_results = self.reporter._check_accessibility_compliance(self.nord_scheme)
        
        # Test structure
        self.assertIn('wcag_aa_compliance', accessibility_results)
        self.assertIn('wcag_aaa_compliance', accessibility_results)
        self.assertIn('summary', accessibility_results)
        
        # Test that essential elements are checked
        aa_compliance = accessibility_results['wcag_aa_compliance']
        essential_elements = ['keyword', 'string', 'function', 'class', 'number']
        
        for element in essential_elements:
            if element in aa_compliance:
                result = aa_compliance[element]
                self.assertIn('contrast_ratio', result)
                self.assertIn('required', result)
                self.assertIn('passes', result)
                self.assertIsInstance(result['passes'], bool)
                
    def test_contrast_calculation_accuracy(self):
        """Test that contrast ratio calculations are accurate."""
        # Test with known values
        test_cases = [
            ('#ffffff', '#000000', 21.0),   # White on black (maximum contrast)
            ('#000000', '#ffffff', 21.0),   # Black on white (same ratio)
            ('#ffffff', '#ffffff', 1.0),    # White on white (no contrast)
            ('#000000', '#000000', 1.0),    # Black on black (no contrast)
        ]
        
        for color1, color2, expected_ratio in test_cases:
            with self.subTest(color1=color1, color2=color2):
                calculated_ratio = self.reporter._calculate_contrast_ratio(color1, color2)
                self.assertAlmostEqual(
                    calculated_ratio, expected_ratio,
                    places=1,
                    msg=f"Contrast between {color1} and {color2} should be {expected_ratio}"
                )
                
    def test_extract_syntax_colors_functionality(self):
        """Test that syntax colors are properly extracted from color scheme."""
        syntax_colors = self.reporter._extract_syntax_colors(self.nord_scheme)
        
        # Test that essential syntax elements are extracted
        expected_elements = ['keyword', 'string', 'function', 'class', 'comment', 'number']
        
        for element in expected_elements:
            self.assertIn(element, syntax_colors)
            color_value = syntax_colors[element]
            self.assertIsInstance(color_value, str)
            self.assertTrue(color_value.startswith('#'))
            self.assertEqual(len(color_value), 7)  # Should be hex color
            
    def test_nord_scheme_overall_accessibility_rating(self):
        """Test that Nord scheme gets an acceptable overall accessibility rating."""
        report = self.reporter.generate_comprehensive_report("nord")
        summary = report['summary']
        
        # Overall rating should be Good or Excellent
        rating = summary.get('overall_rating', '')
        acceptable_ratings = ['Good', 'Excellent', 'Very Good']
        self.assertIn(rating, acceptable_ratings,
                     f"Nord scheme overall rating '{rating}' should be acceptable")
        
        # Average contrast should be reasonable (>= 4.0 for code)
        avg_contrast = summary.get('avg_contrast_ratio', 0)
        self.assertGreaterEqual(avg_contrast, 4.0,
                               f"Average contrast {avg_contrast} should be >= 4.0")
        
        # WCAG AA compliance should be high (>= 75%)
        aa_compliance = summary.get('wcag_aa_compliance', '0%')
        if isinstance(aa_compliance, str) and aa_compliance.endswith('%'):
            aa_percentage = float(aa_compliance.replace('%', ''))
            self.assertGreaterEqual(aa_percentage, 75.0,
                                   f"WCAG AA compliance {aa_percentage}% should be >= 75%")
                                   
    def test_dark_theme_suitability(self):
        """Test that Nord scheme is suitable for dark themes."""
        report = self.reporter.generate_comprehensive_report("nord")
        summary = report['summary']
        
        # Should be recommended for dark themes
        recommended = summary.get('recommended_for_dark_themes', False)
        self.assertTrue(recommended, "Nord scheme should be recommended for dark themes")
        
        # Test against multiple dark backgrounds
        contrast_analysis = report['contrast_analysis']['by_background']
        
        dark_backgrounds = ['nord_polar_night', 'vscode_dark', 'sublime_monokai', 'github_dark']
        for bg_name in dark_backgrounds:
            if bg_name in contrast_analysis:
                bg_results = contrast_analysis[bg_name]
                # Most elements should have good contrast (>= 3.0)
                good_contrast_count = sum(1 for ratio in bg_results.values() if ratio >= 3.0)
                total_elements = len(bg_results)
                
                if total_elements > 0:
                    good_contrast_percentage = (good_contrast_count / total_elements) * 100
                    self.assertGreaterEqual(
                        good_contrast_percentage, 70.0,
                        f"At least 70% of elements should have good contrast on {bg_name}"
                    )


if __name__ == "__main__":
    unittest.main() 