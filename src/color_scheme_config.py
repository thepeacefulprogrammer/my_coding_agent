"""
Color scheme configuration system for syntax highlighting.

This module provides a comprehensive configuration system for managing color schemes,
allowing for dynamic scheme switching, user customization, persistence, and easy
extensibility of color schemes.
"""

import json
import os
import copy
from typing import Dict, List, Optional, Any, Union
import re

from color_schemes import get_nord_color_scheme


class ColorSchemeConfig:
    """
    Configuration manager for color schemes.
    
    Provides functionality for:
    - Managing multiple color schemes
    - Dynamic scheme switching
    - Custom scheme registration
    - Scheme validation and inheritance
    - Configuration persistence
    - Template-based scheme creation
    """
    
    def __init__(self):
        """Initialize the color scheme configuration."""
        self._schemes = {}
        self._default_scheme_name = "nord"
        self._current_scheme_name = "nord"
        
        # Register built-in schemes
        self._register_builtin_schemes()
        
    def _register_builtin_schemes(self):
        """Register built-in color schemes."""
        # Register Nord scheme
        nord_scheme = get_nord_color_scheme()
        self._schemes["nord"] = nord_scheme
        
        # Register a basic monokai-style scheme for variety
        monokai_scheme = {
            'keyword': {
                'declaration': '#F92672',  # Magenta
                'namespace': '#F92672',
                'pseudo': '#F92672'
            },
            'name': {
                'attribute': '#A6E22E',    # Green
                'builtin': '#66D9EF',      # Cyan
                'builtin.pseudo': '#66D9EF',
                'class': '#A6E22E',        # Green
                'constant': '#AE81FF',     # Purple
                'decorator': '#A6E22E',    # Green
                'entity': '#A6E22E',       # Green
                'exception': '#F92672',    # Magenta
                'function': '#A6E22E',     # Green
                'function.magic': '#66D9EF', # Cyan
                'label': '#A6E22E',        # Green
                'namespace': '#F92672',    # Magenta
                'other': '#A6E22E',        # Green
                'tag': '#F92672',          # Magenta
                'variable': '#FD971F',     # Orange
                'variable.class': '#FD971F',
                'variable.function': '#FD971F',
                'variable.global': '#FD971F',
                'variable.instance': '#FD971F',
                'variable.magic': '#FD971F'
            },
            'literal': {
                'date': '#E6DB74',         # Yellow
                'number': {
                    'bin': '#AE81FF',      # Purple
                    'float': '#AE81FF',    # Purple
                    'hex': '#AE81FF',      # Purple
                    'integer': '#AE81FF',  # Purple
                    'integer.long': '#AE81FF', # Purple
                    'oct': '#AE81FF'       # Purple
                }
            },
            'string': {
                'affix': '#E6DB74',        # Yellow
                'char': '#E6DB74',         # Yellow
                'delimiter': '#E6DB74',    # Yellow
                'doc': '#E6DB74',          # Yellow
                'double': '#E6DB74',       # Yellow
                'escape': '#AE81FF',       # Purple
                'heredoc': '#E6DB74',      # Yellow
                'interpol': '#E6DB74',     # Yellow
                'other': '#E6DB74',        # Yellow
                'regex': '#E6DB74',        # Yellow
                'single': '#E6DB74',       # Yellow
                'symbol': '#E6DB74'        # Yellow
            },
            'comment': {
                'hashbang': '#75715E',     # Gray
                'multiline': '#75715E',    # Gray
                'preproc': '#A6E22E',      # Green
                'preprocfile': '#E6DB74',  # Yellow
                'single': '#75715E',       # Gray
                'special': '#75715E'       # Gray
            },
            'error': '#F92672',            # Magenta
            'other': '#F8F8F2',            # White
            'punctuation': '#F8F8F2',      # White
            'operator': {
                'symbol': '#F92672',       # Magenta
                'word': '#F92672'          # Magenta
            },
            'generic': {
                'deleted': '#F92672',      # Magenta
                'emph': '#F8F8F2',         # White
                'error': '#F92672',        # Magenta
                'heading': '#A6E22E',      # Green
                'inserted': '#A6E22E',     # Green
                'output': '#66D9EF',       # Cyan
                'prompt': '#E6DB74',       # Yellow
                'strong': '#F8F8F2',       # White
                'subheading': '#A6E22E',   # Green
                'traceback': '#F92672'     # Magenta
            },
            'text': '#F8F8F2'              # White
        }
        self._schemes["monokai"] = monokai_scheme
        
    def get_available_schemes(self) -> List[str]:
        """
        Get list of available color scheme names.
        
        Returns:
            List of color scheme names.
        """
        return list(self._schemes.keys())
        
    def get_scheme(self, scheme_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a color scheme by name.
        
        Args:
            scheme_name: Name of the color scheme.
            
        Returns:
            Color scheme dictionary or None if not found.
        """
        return self._schemes.get(scheme_name)
        
    def register_scheme(self, scheme_name: str, scheme: Dict[str, Any]) -> bool:
        """
        Register a new color scheme.
        
        Args:
            scheme_name: Name for the color scheme.
            scheme: Color scheme dictionary.
            
        Returns:
            True if registration successful, False otherwise.
        """
        if not self.validate_scheme(scheme):
            return False
            
        self._schemes[scheme_name] = copy.deepcopy(scheme)
        return True
        
    def validate_scheme(self, scheme: Dict[str, Any]) -> bool:
        """
        Validate a color scheme structure.
        
        Args:
            scheme: Color scheme dictionary to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        if not isinstance(scheme, dict):
            return False
            
        # Check for required structure
        for key, value in scheme.items():
            if isinstance(value, dict):
                # Nested structure - validate colors within
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        if not self._is_valid_color(sub_value):
                            return False
                    elif isinstance(sub_value, dict):
                        # Further nested - validate recursively
                        for nested_key, nested_value in sub_value.items():
                            if isinstance(nested_value, str):
                                if not self._is_valid_color(nested_value):
                                    return False
            elif isinstance(value, str):
                # Direct color value
                if not self._is_valid_color(value):
                    return False
            else:
                # Invalid structure
                return False
                
        return True
        
    def _is_valid_color(self, color: str) -> bool:
        """
        Validate if a string is a valid color value.
        
        Args:
            color: Color string to validate.
            
        Returns:
            True if valid color, False otherwise.
        """
        if not isinstance(color, str):
            return False
            
        # Check for hex color format (#RRGGBB or #RGB)
        hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        if re.match(hex_pattern, color):
            return True
            
        # Check for common color names (basic validation)
        color_names = {
            'red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink',
            'brown', 'black', 'white', 'gray', 'grey', 'cyan', 'magenta'
        }
        if color.lower() in color_names:
            return True
            
        return False
        
    def set_default_scheme(self, scheme_name: str) -> bool:
        """
        Set the default color scheme.
        
        Args:
            scheme_name: Name of the scheme to set as default.
            
        Returns:
            True if successful, False if scheme doesn't exist.
        """
        if scheme_name in self._schemes:
            self._default_scheme_name = scheme_name
            return True
        return False
        
    def get_default_scheme_name(self) -> str:
        """
        Get the name of the default color scheme.
        
        Returns:
            Default scheme name.
        """
        return self._default_scheme_name
        
    def get_default_scheme(self) -> Optional[Dict[str, Any]]:
        """
        Get the default color scheme.
        
        Returns:
            Default color scheme dictionary.
        """
        return self.get_scheme(self._default_scheme_name)
        
    def save_configuration(self, config_file: str) -> bool:
        """
        Save color scheme configuration to file.
        
        Args:
            config_file: Path to configuration file.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            config_data = {
                'schemes': self._schemes,
                'default_scheme': self._default_scheme_name,
                'current_scheme': self._current_scheme_name
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception:
            return False
            
    def load_configuration(self, config_file: str) -> bool:
        """
        Load color scheme configuration from file.
        
        Args:
            config_file: Path to configuration file.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            if not os.path.exists(config_file):
                return False
                
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Validate loaded data
            if not isinstance(config_data, dict):
                return False
                
            # Load schemes
            if 'schemes' in config_data and isinstance(config_data['schemes'], dict):
                for name, scheme in config_data['schemes'].items():
                    if self.validate_scheme(scheme):
                        self._schemes[name] = scheme
                        
            # Load default scheme
            if 'default_scheme' in config_data:
                default_name = config_data['default_scheme']
                if default_name in self._schemes:
                    self._default_scheme_name = default_name
                    
            # Load current scheme
            if 'current_scheme' in config_data:
                current_name = config_data['current_scheme']
                if current_name in self._schemes:
                    self._current_scheme_name = current_name
                    
            return True
        except Exception:
            return False
            
    def create_scheme_from_template(self, template_name: str, new_name: str, 
                                  modifications: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new color scheme from an existing template with modifications.
        
        Args:
            template_name: Name of template scheme.
            new_name: Name for the new scheme.
            modifications: Dictionary of modifications to apply.
            
        Returns:
            New color scheme dictionary or None if failed.
        """
        template_scheme = self.get_scheme(template_name)
        if not template_scheme:
            return None
            
        # Deep copy the template
        new_scheme = copy.deepcopy(template_scheme)
        
        # Apply modifications recursively
        self._apply_modifications(new_scheme, modifications)
        
        # Validate the resulting scheme
        if not self.validate_scheme(new_scheme):
            return None
            
        # Register the new scheme
        if self.register_scheme(new_name, new_scheme):
            return new_scheme
            
        return None
        
    def _apply_modifications(self, target: Dict[str, Any], modifications: Dict[str, Any]):
        """
        Apply modifications to a target dictionary recursively.
        
        Args:
            target: Target dictionary to modify.
            modifications: Modifications to apply.
        """
        for key, value in modifications.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursive modification for nested dictionaries
                self._apply_modifications(target[key], value)
            else:
                # Direct replacement
                target[key] = value
                
    def register_scheme_with_inheritance(self, scheme_name: str, parent_name: str, 
                                       overrides: Dict[str, Any]) -> bool:
        """
        Register a new scheme that inherits from a parent scheme with overrides.
        
        Args:
            scheme_name: Name for the new scheme.
            parent_name: Name of parent scheme to inherit from.
            overrides: Dictionary of properties to override.
            
        Returns:
            True if successful, False otherwise.
        """
        parent_scheme = self.get_scheme(parent_name)
        if not parent_scheme:
            return False
            
        # Create inherited scheme
        inherited_scheme = copy.deepcopy(parent_scheme)
        self._apply_modifications(inherited_scheme, overrides)
        
        # Register the inherited scheme
        return self.register_scheme(scheme_name, inherited_scheme)
        
    def set_current_scheme(self, scheme_name: str) -> bool:
        """
        Set the current active color scheme.
        
        Args:
            scheme_name: Name of scheme to set as current.
            
        Returns:
            True if successful, False if scheme doesn't exist.
        """
        if scheme_name in self._schemes:
            self._current_scheme_name = scheme_name
            return True
        return False
        
    def get_current_scheme_name(self) -> str:
        """
        Get the name of the current active color scheme.
        
        Returns:
            Current scheme name.
        """
        return self._current_scheme_name
        
    def get_current_scheme(self) -> Optional[Dict[str, Any]]:
        """
        Get the current active color scheme.
        
        Returns:
            Current color scheme dictionary.
        """
        return self.get_scheme(self._current_scheme_name) 