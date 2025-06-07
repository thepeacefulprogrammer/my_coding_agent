"""
Color scheme definitions for syntax highlighting.

This module provides color scheme configurations for CodeView widgets,
including the popular Nord arctic color palette and other schemes.
"""

# Nord Color Palette Constants
# Based on the official Nord theme (https://www.nordtheme.com/)

# Polar Night - Dark colors for backgrounds and subtle elements
NORD0 = "#2e3440"   # Base background
NORD1 = "#3b4252"   # Elevated backgrounds
NORD2 = "#434c5e"   # Selection background
NORD3 = "#4c566a"   # Comments and subtle elements

# Snow Storm - Light colors for text
NORD4 = "#d8dee9"   # Base text
NORD5 = "#e5e9f0"   # Bright text
NORD6 = "#eceff4"   # Brightest text

# Frost - Blue colors for primary elements
NORD7 = "#8fbcbb"   # Calm blue for classes/types
NORD8 = "#88c0d0"   # Primary accent for functions
NORD9 = "#81a1c1"   # Secondary blue for keywords
NORD10 = "#5e81ac"  # Dark blue for pragmas

# Aurora - Colorful accents
NORD11 = "#bf616a"  # Red for errors/deletions
NORD12 = "#d08770"  # Orange for annotations
NORD13 = "#ebcb8b"  # Yellow for warnings/strings
NORD14 = "#a3be8c"  # Green for strings
NORD15 = "#b48ead"  # Purple for numbers


def get_nord_color_scheme():
    """
    Get the Nord color scheme configuration as a dictionary.
    
    Returns:
        dict: Color scheme configuration compatible with Chlorophyll CodeView
    """
    return {
        "editor": {
            "bg": NORD0,                    # Dark background
            "fg": NORD6,                    # Bright text
            "select_bg": NORD2,             # Selection background
            "select_fg": NORD6,             # Selection text
            "inactive_select_bg": NORD1,    # Inactive selection
            "caret": NORD4,                 # Cursor color
            "caret_width": 1,
            "border_width": 0,
            "focus_border_width": 0
        },
        
        "general": {
            "comment": NORD3,               # Comments - subtle gray
            "error": NORD11,                # Errors - red
            "escape": NORD13,               # Escape characters - yellow
            "keyword": NORD9,               # Keywords - blue
            "name": NORD8,                  # Names - bright blue
            "string": NORD14,               # Strings - green
            "punctuation": NORD6,           # Punctuation - bright text
        },
        
        "keyword": {
            "constant": NORD15,             # Constants - purple
            "declaration": NORD9,           # Declarations - blue
            "namespace": NORD9,             # Namespaces - blue
            "pseudo": NORD15,               # Pseudo keywords - purple
            "reserved": NORD9,              # Reserved words - blue
            "type": NORD7,                  # Types - calm blue
        },
        
        "name": {
            "attr": NORD8,                  # Attributes - bright blue
            "builtin": NORD8,               # Built-ins - bright blue
            "builtin_pseudo": NORD8,        # Pseudo built-ins - bright blue
            "class": NORD7,                 # Classes - calm blue
            "class_variable": NORD4,        # Class variables - base text
            "constant": NORD15,             # Constants - purple
            "decorator": NORD12,            # Decorators - orange
            "entity": NORD8,                # Entities - bright blue
            "exception": NORD11,            # Exceptions - red
            "function": NORD8,              # Functions - bright blue
            "global_variable": NORD4,       # Global variables - base text
            "instance_variable": NORD4,     # Instance variables - base text
            "label": NORD8,                 # Labels - bright blue
            "magic_function": NORD8,        # Magic functions - bright blue
            "magic_variable": NORD4,        # Magic variables - base text
            "namespace": NORD4,             # Namespace - base text
            "tag": NORD9,                   # Tags - blue
            "variable": NORD4,              # Variables - base text
        },
        
        "operator": {
            "symbol": NORD9,                # Operator symbols - blue
            "word": NORD9,                  # Word operators - blue
        },
        
        "string": {
            "affix": NORD14,                # String affixes - green
            "char": NORD14,                 # Characters - green
            "delimiter": NORD14,            # String delimiters - green
            "doc": NORD3,                   # Docstrings - subtle comment color
            "double": NORD14,               # Double quotes - green
            "escape": NORD13,               # Escape sequences - yellow
            "heredoc": NORD14,              # Heredoc - green
            "interpol": NORD13,             # String interpolation - yellow
            "regex": NORD13,                # Regex - yellow
            "single": NORD14,               # Single quotes - green
            "symbol": NORD14,               # String symbols - green
        },
        
        "number": {
            "binary": NORD15,               # Binary numbers - purple
            "float": NORD15,                # Floating point - purple
            "hex": NORD15,                  # Hexadecimal - purple
            "integer": NORD15,              # Integers - purple
            "long": NORD15,                 # Long integers - purple
            "octal": NORD15,                # Octal numbers - purple
        },
        
        "comment": {
            "hashbang": NORD3,              # Shebang lines - subtle
            "multiline": NORD3,             # Multiline comments - subtle
            "preproc": NORD10,              # Preprocessor - dark blue
            "preprocfile": NORD14,          # Preprocessor files - green
            "single": NORD3,                # Single line comments - subtle
            "special": NORD10,              # Special comments - dark blue
        }
    }


def get_available_color_schemes():
    """
    Get a dictionary of all available color schemes.
    
    Returns:
        dict: Dictionary mapping scheme names to their configurations
    """
    return {
        "nord": get_nord_color_scheme(),
        # Future color schemes can be added here
        # "solarized": get_solarized_color_scheme(),
        # "one_dark": get_one_dark_color_scheme(),
    }


def get_color_scheme(scheme_name):
    """
    Get a specific color scheme by name.
    
    Args:
        scheme_name (str or None): Name of the color scheme
        
    Returns:
        dict or None: Color scheme configuration or None if not found
    """
    if scheme_name is None:
        return None
        
    schemes = get_available_color_schemes()
    return schemes.get(scheme_name.lower())


def is_color_scheme_available(scheme_name):
    """
    Check if a color scheme is available.
    
    Args:
        scheme_name (str): Name of the color scheme
        
    Returns:
        bool: True if the scheme is available, False otherwise
    """
    return scheme_name.lower() in get_available_color_schemes() 