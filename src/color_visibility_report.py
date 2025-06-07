"""
Color visibility report generator.

This module provides tools to generate comprehensive visibility and accessibility
reports for color schemes, including contrast analysis and recommendations.
"""

import colorsys
import json
from typing import Dict, List, Tuple, Any

from color_schemes import get_nord_color_scheme, NORD0
from color_scheme_config import ColorSchemeConfig


class ColorVisibilityReporter:
    """Generate comprehensive visibility reports for color schemes."""
    
    def __init__(self):
        """Initialize the visibility reporter."""
        self.config = ColorSchemeConfig()
        
        # Standard dark backgrounds for testing
        self.test_backgrounds = {
            'nord_polar_night': NORD0,        # #2e3440
            'vscode_dark': '#1e1e1e',
            'sublime_monokai': '#272822',
            'github_dark': '#0d1117',
            'pure_black': '#000000',
        }
        
        # WCAG contrast standards
        self.wcag_standards = {
            'AA_normal': 4.5,      # WCAG AA for normal text
            'AA_large': 3.0,       # WCAG AA for large text (code)
            'AAA_normal': 7.0,     # WCAG AAA for normal text
            'AAA_large': 4.5,      # WCAG AAA for large text
        }
        
    def generate_comprehensive_report(self, scheme_name: str = "nord") -> Dict[str, Any]:
        """
        Generate a comprehensive visibility report for a color scheme.
        
        Args:
            scheme_name: Name of the color scheme to analyze
            
        Returns:
            Dictionary containing the complete visibility report
        """
        scheme = self.config.get_scheme(scheme_name)
        if not scheme:
            raise ValueError(f"Color scheme '{scheme_name}' not found")
            
        report = {
            'scheme_name': scheme_name,
            'timestamp': self._get_timestamp(),
            'summary': {},
            'contrast_analysis': {},
            'accessibility_compliance': {},
            'recommendations': [],
            'detailed_results': {}
        }
        
        # Analyze contrast against all test backgrounds
        contrast_results = self._analyze_contrast_ratios(scheme)
        report['contrast_analysis'] = contrast_results
        
        # Check accessibility compliance
        accessibility_results = self._check_accessibility_compliance(scheme)
        report['accessibility_compliance'] = accessibility_results
        
        # Generate summary
        report['summary'] = self._generate_summary(contrast_results, accessibility_results)
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(
            contrast_results, accessibility_results, scheme
        )
        
        # Store detailed color information
        report['detailed_results'] = self._extract_detailed_color_info(scheme)
        
        return report
        
    def generate_comparison_report(self, scheme_names: List[str] = None) -> Dict[str, Any]:
        """
        Generate a comparison report between multiple color schemes.
        
        Args:
            scheme_names: List of scheme names to compare (default: all available)
            
        Returns:
            Dictionary containing comparison results
        """
        if scheme_names is None:
            scheme_names = self.config.get_available_schemes()
            
        comparison = {
            'timestamp': self._get_timestamp(),
            'schemes_compared': scheme_names,
            'comparison_matrix': {},
            'best_performers': {},
            'recommendations': []
        }
        
        # Analyze each scheme
        scheme_results = {}
        for scheme_name in scheme_names:
            try:
                scheme_results[scheme_name] = self.generate_comprehensive_report(scheme_name)
            except ValueError:
                continue  # Skip unavailable schemes
                
        # Create comparison matrix
        comparison['comparison_matrix'] = self._create_comparison_matrix(scheme_results)
        
        # Identify best performers
        comparison['best_performers'] = self._identify_best_performers(scheme_results)
        
        # Generate comparative recommendations
        comparison['recommendations'] = self._generate_comparative_recommendations(scheme_results)
        
        return comparison
        
    def _analyze_contrast_ratios(self, scheme: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze contrast ratios for all syntax elements against test backgrounds."""
        
        # Extract syntax colors
        syntax_colors = self._extract_syntax_colors(scheme)
        
        results = {
            'by_element': {},
            'by_background': {},
            'overall_stats': {}
        }
        
        # Analyze each syntax element
        for element_name, element_color in syntax_colors.items():
            element_results = {}
            
            for bg_name, bg_color in self.test_backgrounds.items():
                contrast_ratio = self._calculate_contrast_ratio(element_color, bg_color)
                element_results[bg_name] = {
                    'contrast_ratio': round(contrast_ratio, 2),
                    'wcag_aa_pass': contrast_ratio >= self.wcag_standards['AA_large'],
                    'wcag_aaa_pass': contrast_ratio >= self.wcag_standards['AAA_large'],
                }
                
            results['by_element'][element_name] = element_results
            
        # Analyze by background
        for bg_name, bg_color in self.test_backgrounds.items():
            bg_results = {}
            
            for element_name, element_color in syntax_colors.items():
                contrast_ratio = self._calculate_contrast_ratio(element_color, bg_color)
                bg_results[element_name] = round(contrast_ratio, 2)
                
            results['by_background'][bg_name] = bg_results
            
        # Calculate overall statistics
        results['overall_stats'] = self._calculate_contrast_statistics(results['by_element'])
        
        return results
        
    def _check_accessibility_compliance(self, scheme: Dict[str, Any]) -> Dict[str, Any]:
        """Check WCAG accessibility compliance for the color scheme."""
        
        syntax_colors = self._extract_syntax_colors(scheme)
        
        compliance = {
            'wcag_aa_compliance': {},
            'wcag_aaa_compliance': {},
            'summary': {}
        }
        
        # Check against primary background (Nord Polar Night)
        primary_bg = NORD0
        
        aa_passes = 0
        aaa_passes = 0
        total_elements = len(syntax_colors)
        
        for element_name, element_color in syntax_colors.items():
            contrast_ratio = self._calculate_contrast_ratio(element_color, primary_bg)
            
            aa_pass = contrast_ratio >= self.wcag_standards['AA_large']
            aaa_pass = contrast_ratio >= self.wcag_standards['AAA_large']
            
            compliance['wcag_aa_compliance'][element_name] = {
                'contrast_ratio': round(contrast_ratio, 2),
                'required': self.wcag_standards['AA_large'],
                'passes': aa_pass
            }
            
            compliance['wcag_aaa_compliance'][element_name] = {
                'contrast_ratio': round(contrast_ratio, 2),
                'required': self.wcag_standards['AAA_large'],
                'passes': aaa_pass
            }
            
            if aa_pass:
                aa_passes += 1
            if aaa_pass:
                aaa_passes += 1
                
        # Calculate summary percentages
        compliance['summary'] = {
            'aa_compliance_percentage': round((aa_passes / total_elements) * 100, 1),
            'aaa_compliance_percentage': round((aaa_passes / total_elements) * 100, 1),
            'total_elements_tested': total_elements,
            'aa_passing_elements': aa_passes,
            'aaa_passing_elements': aaa_passes
        }
        
        return compliance
        
    def _extract_syntax_colors(self, scheme: Dict[str, Any]) -> Dict[str, str]:
        """Extract syntax highlighting colors from a color scheme."""
        
        syntax_colors = {}
        
        # Common syntax elements
        color_paths = {
            'keyword': ['keyword', 'declaration'],
            'string': ['string', 'single'],
            'function': ['name', 'function'],
            'class': ['name', 'class'],
            'comment': ['comment', 'single'],
            'number': ['number', 'integer'],
            'operator': ['operator', 'symbol'],
            'error': ['general', 'error'],  # May not exist in all schemes
        }
        
        for element_name, path in color_paths.items():
            try:
                color_value = scheme
                for key in path:
                    color_value = color_value[key]
                syntax_colors[element_name] = color_value
            except (KeyError, TypeError):
                # Element doesn't exist in this scheme
                continue
                
        return syntax_colors
        
    def _calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate contrast ratio between two colors."""
        l1 = self._get_relative_luminance(color1)
        l2 = self._get_relative_luminance(color2)
        
        # Ensure l1 is the lighter color
        if l1 < l2:
            l1, l2 = l2, l1
            
        return (l1 + 0.05) / (l2 + 0.05)
        
    def _get_relative_luminance(self, hex_color: str) -> float:
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
        
    def _generate_summary(self, contrast_results: Dict, accessibility_results: Dict) -> Dict[str, Any]:
        """Generate a summary of the visibility analysis."""
        
        stats = contrast_results['overall_stats']
        compliance = accessibility_results['summary']
        
        # Determine overall rating
        aa_percentage = compliance['aa_compliance_percentage']
        if aa_percentage >= 90:
            overall_rating = "Excellent"
        elif aa_percentage >= 75:
            overall_rating = "Good"
        elif aa_percentage >= 60:
            overall_rating = "Fair"
        else:
            overall_rating = "Poor"
            
        return {
            'overall_rating': overall_rating,
            'avg_contrast_ratio': stats['average_contrast'],
            'min_contrast_ratio': stats['minimum_contrast'],
            'max_contrast_ratio': stats['maximum_contrast'],
            'wcag_aa_compliance': f"{compliance['aa_compliance_percentage']}%",
            'wcag_aaa_compliance': f"{compliance['aaa_compliance_percentage']}%",
            'recommended_for_dark_themes': aa_percentage >= 75
        }
        
    def _generate_recommendations(self, contrast_results: Dict, accessibility_results: Dict, 
                                scheme: Dict) -> List[str]:
        """Generate recommendations for improving color scheme visibility."""
        
        recommendations = []
        
        # Check overall compliance
        aa_percentage = accessibility_results['summary']['aa_compliance_percentage']
        
        if aa_percentage < 75:
            recommendations.append(
                "Consider increasing contrast for better accessibility compliance."
            )
            
        # Check specific elements
        for element, compliance in accessibility_results['wcag_aa_compliance'].items():
            if not compliance['passes']:
                recommendations.append(
                    f"Improve contrast for {element} elements "
                    f"(current: {compliance['contrast_ratio']}:1, "
                    f"required: {compliance['required']}:1)"
                )
                
        # Check consistency across backgrounds
        stats = contrast_results['overall_stats']
        if stats['minimum_contrast'] < 2.0:
            recommendations.append(
                "Some colors may be difficult to read on very dark backgrounds."
            )
            
        if not recommendations:
            recommendations.append("Color scheme has excellent visibility characteristics!")
            
        return recommendations
        
    def _calculate_contrast_statistics(self, element_results: Dict) -> Dict[str, float]:
        """Calculate statistical summary of contrast ratios."""
        
        all_ratios = []
        
        for element_data in element_results.values():
            for bg_data in element_data.values():
                all_ratios.append(bg_data['contrast_ratio'])
                
        return {
            'average_contrast': round(sum(all_ratios) / len(all_ratios), 2),
            'minimum_contrast': round(min(all_ratios), 2),
            'maximum_contrast': round(max(all_ratios), 2),
            'total_measurements': len(all_ratios)
        }
        
    def _extract_detailed_color_info(self, scheme: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed color information for documentation."""
        
        syntax_colors = self._extract_syntax_colors(scheme)
        
        detailed_info = {}
        
        for element_name, color_hex in syntax_colors.items():
            # Convert to other color spaces
            h, s, v = self._hex_to_hsv(color_hex)
            luminance = self._get_relative_luminance(color_hex)
            
            detailed_info[element_name] = {
                'hex': color_hex,
                'hue': round(h * 360, 1),
                'saturation': round(s * 100, 1),
                'value': round(v * 100, 1),
                'luminance': round(luminance, 3)
            }
            
        return detailed_info
        
    def _hex_to_hsv(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to HSV values."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        return colorsys.rgb_to_hsv(r, g, b)
        
    def _get_timestamp(self) -> str:
        """Get current timestamp for reports."""
        from datetime import datetime
        return datetime.now().isoformat()
        
    def _create_comparison_matrix(self, scheme_results: Dict) -> Dict[str, Any]:
        """Create a comparison matrix between schemes."""
        # Implementation for comparison would go here
        return {"placeholder": "Comparison matrix implementation"}
        
    def _identify_best_performers(self, scheme_results: Dict) -> Dict[str, str]:
        """Identify best performing schemes in different categories."""
        # Implementation for best performer identification would go here
        return {"placeholder": "Best performer identification"}
        
    def _generate_comparative_recommendations(self, scheme_results: Dict) -> List[str]:
        """Generate recommendations based on scheme comparison."""
        # Implementation for comparative recommendations would go here
        return ["Comparative recommendations implementation"]
        
    def save_report_to_file(self, report: Dict[str, Any], filename: str):
        """Save a visibility report to a JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
    def print_summary_report(self, scheme_name: str = "nord"):
        """Print a human-readable summary report to console."""
        
        report = self.generate_comprehensive_report(scheme_name)
        summary = report['summary']
        
        print(f"\n=== Color Visibility Report: {scheme_name.title()} ===")
        print(f"Overall Rating: {summary['overall_rating']}")
        print(f"Average Contrast: {summary['avg_contrast_ratio']}:1")
        print(f"WCAG AA Compliance: {summary['wcag_aa_compliance']}")
        print(f"WCAG AAA Compliance: {summary['wcag_aaa_compliance']}")
        print(f"Recommended for Dark Themes: {'Yes' if summary['recommended_for_dark_themes'] else 'No'}")
        
        print("\nRecommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
            
        print(f"\nDetailed report saved with {report['contrast_analysis']['overall_stats']['total_measurements']} contrast measurements.")


def main():
    """Generate and display a sample visibility report."""
    reporter = ColorVisibilityReporter()
    
    # Generate report for Nord scheme
    reporter.print_summary_report("nord")
    
    # Generate and save detailed report
    detailed_report = reporter.generate_comprehensive_report("nord")
    reporter.save_report_to_file(detailed_report, "nord_visibility_report.json")
    print("\nDetailed report saved to 'nord_visibility_report.json'")


if __name__ == "__main__":
    main() 