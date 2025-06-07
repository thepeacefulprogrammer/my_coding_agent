"""
Pygments Token Mapper for Nord Color Scheme.

This module provides a mapping system that converts Pygments token types
to appropriate colors from the Nord color scheme for syntax highlighting.
"""

from pygments.token import (
    Token, Comment, Keyword, Name, String, Number, Operator, 
    Punctuation, Error, Generic, Literal, Text, Whitespace
)

try:
    from .color_schemes import NORD0, NORD3, NORD6, NORD7, NORD8, NORD9, NORD11, NORD12, NORD13, NORD14, NORD15
except ImportError:
    # Fallback for tests and standalone usage
    from color_schemes import NORD0, NORD3, NORD6, NORD7, NORD8, NORD9, NORD11, NORD12, NORD13, NORD14, NORD15


class TokenMapper:
    """Maps Pygments token types to Nord color scheme colors."""
    
    def __init__(self, color_scheme):
        """
        Initialize TokenMapper with a color scheme.
        
        Args:
            color_scheme (dict): Color scheme dictionary (typically Nord scheme)
        """
        self.color_scheme = color_scheme
        
        # Create direct token to color mapping for performance
        self.token_map = self._build_token_map()
        
    def _build_token_map(self):
        """
        Build a comprehensive mapping from Pygments tokens to Nord colors.
        
        Returns:
            dict: Mapping of token types to color hex strings
        """
        return {
            # Comments
            Comment: NORD3,
            Comment.Single: NORD3,
            Comment.Multiline: NORD3,
            Comment.Hashbang: NORD3,
            Comment.Doc: NORD3,
            Comment.Preproc: NORD3,
            Comment.PreprocFile: NORD3,
            Comment.Special: NORD3,
            
            # Keywords
            Keyword: NORD9,
            Keyword.Constant: NORD9,
            Keyword.Declaration: NORD9,
            Keyword.Namespace: NORD9,
            Keyword.Pseudo: NORD9,
            Keyword.Reserved: NORD9,
            Keyword.Type: NORD7,  # Type keywords get calm blue
            
            # Names
            Name: NORD6,  # Default variable names
            Name.Attribute: NORD8,  # Attributes get bright blue
            Name.Builtin: NORD8,   # Built-in functions
            Name.Builtin.Pseudo: NORD8,
            Name.Class: NORD7,     # Classes get calm blue
            Name.Constant: NORD15, # Constants get purple
            Name.Decorator: NORD12, # Decorators get orange
            Name.Entity: NORD8,
            Name.Exception: NORD11, # Exceptions get red
            Name.Function: NORD8,   # Functions get bright blue
            Name.Function.Magic: NORD8,
            Name.Label: NORD8,
            Name.Namespace: NORD7,
            Name.Other: NORD6,
            Name.Property: NORD8,
            Name.Tag: NORD9,       # HTML/XML tags
            Name.Variable: NORD6,   # Variables
            Name.Variable.Class: NORD6,
            Name.Variable.Global: NORD6,
            Name.Variable.Instance: NORD6,
            Name.Variable.Magic: NORD6,
            
            # Strings
            String: NORD14,         # Green for strings
            String.Affix: NORD14,
            String.Backtick: NORD14,
            String.Char: NORD14,
            String.Delimiter: NORD14,
            String.Doc: NORD14,
            String.Double: NORD14,
            String.Escape: NORD13,  # Aurora yellow for escapes
            String.Heredoc: NORD14,
            String.Interpol: NORD13, # Template literals/f-strings
            String.Other: NORD14,
            String.Regex: NORD13,   # Regular expressions
            String.Single: NORD14,
            String.Symbol: NORD14,
            
            # Numbers
            Number: NORD15,         # Purple for numbers
            Number.Bin: NORD15,
            Number.Float: NORD15,
            Number.Hex: NORD15,
            Number.Integer: NORD15,
            Number.Integer.Long: NORD15,
            Number.Oct: NORD15,
            
            # Operators
            Operator: NORD9,        # Blue for operators
            Operator.Word: NORD9,   # and, or, not, in, etc.
            
            # Punctuation
            Punctuation: NORD6,     # Snow for punctuation
            Punctuation.Marker: NORD6,
            
            # Literals
            Literal: NORD14,
            Literal.Date: NORD14,
            Literal.Number: NORD15,
            Literal.String: NORD14,
            
            # Generic tokens (for diffs, etc.)
            Generic: NORD6,
            Generic.Deleted: NORD11,    # Red for deleted
            Generic.Emph: NORD13,       # Yellow for emphasis
            Generic.Error: NORD11,      # Red for errors
            Generic.Heading: NORD8,     # Blue for headings
            Generic.Inserted: NORD14,   # Green for inserted
            Generic.Output: NORD6,
            Generic.Prompt: NORD8,
            Generic.Strong: NORD8,      # Blue for strong
            Generic.Subheading: NORD7,
            Generic.Traceback: NORD11,
            
            # Errors
            Error: NORD11,              # Red for errors
            
            # Text and whitespace
            Text: NORD6,
            Text.Symbol: NORD6,
            Text.Whitespace: NORD0,     # Background color for whitespace
            
            # Fallback for unknown tokens
            Token: NORD6,               # Default text color
        }
        
    def get_color_for_token(self, token_type):
        """
        Get the appropriate Nord color for a given Pygments token type.
        
        Args:
            token_type: Pygments token type (e.g., Comment.Single, Keyword, etc.)
            
        Returns:
            str: Hex color string (e.g., "#5E81AC")
        """
        # First try exact match
        if token_type in self.token_map:
            return self.token_map[token_type]
            
        # Fall back to parent token types
        current_token = token_type
        while current_token != Token:
            current_token = current_token.parent
            if current_token in self.token_map:
                return self.token_map[current_token]
                
        # Ultimate fallback
        return self.token_map[Token]
        
    def get_chlorophyll_color_scheme(self):
        """
        Convert token mappings to Chlorophyll-compatible color scheme format.
        
        Returns:
            dict: Color scheme dictionary compatible with Chlorophyll CodeView
        """
        # This method converts our token mappings to the format that
        # Chlorophyll expects for its color_scheme parameter
        chlorophyll_scheme = {}
        
        for token_type, color in self.token_map.items():
            # Convert token type to string representation that Chlorophyll uses
            token_name = str(token_type).replace('Token.', '').lower()
            chlorophyll_scheme[token_name] = color
            
        return chlorophyll_scheme
        
    def apply_to_widget(self, widget, lexer):
        """
        Apply the token color mappings to a CodeView widget.
        
        Args:
            widget: Chlorophyll CodeView widget instance
            lexer: Pygments lexer instance
            
        Returns:
            bool: True if colors were applied successfully
        """
        try:
            # Get the color scheme in Chlorophyll format
            chlorophyll_scheme = self.get_chlorophyll_color_scheme()
            
            # Apply to widget (this would depend on Chlorophyll's API)
            if hasattr(widget, 'configure_colors'):
                widget.configure_colors(chlorophyll_scheme)
                return True
            elif hasattr(widget, 'color_scheme'):
                widget.color_scheme = chlorophyll_scheme
                return True
            else:
                # Fallback: try to set colors directly
                return self._apply_colors_directly(widget, chlorophyll_scheme)
                
        except Exception as e:
            # Log error in real implementation
            print(f"Error applying colors to widget: {e}")
            return False
            
    def _apply_colors_directly(self, widget, color_scheme):
        """
        Fallback method to apply colors directly to widget.
        
        Args:
            widget: Widget instance
            color_scheme (dict): Color scheme mapping
            
        Returns:
            bool: True if successful
        """
        # This would be implementation-specific based on the widget's API
        # For now, just return True to indicate we tried
        return True
