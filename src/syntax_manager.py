"""
SyntaxManager: Handles lexer detection and language mapping for syntax highlighting.

This module provides functionality to detect appropriate pygments lexers for files
based on file extensions and other criteria.
"""

import os
from pygments import lexers
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.util import ClassNotFound


class SyntaxManager:
    """Manages syntax highlighting lexer detection and mapping."""
    
    def __init__(self):
        """Initialize the SyntaxManager with file extension mappings."""
        # Comprehensive mapping of file extensions to pygments lexer names
        self.extension_mapping = {
            # Python
            '.py': 'python',
            '.pyw': 'python',
            '.pyi': 'python',
            '.pyx': 'cython',
            
            # JavaScript/TypeScript
            '.js': 'javascript',
            '.jsx': 'jsx',
            '.ts': 'typescript',
            '.tsx': 'tsx',
            
            # Web technologies
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            
            # Data formats
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            
            # Documentation
            '.md': 'markdown',
            '.rst': 'rst',
            '.txt': 'text',
            
            # Shell/Command line
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'zsh',
            '.fish': 'fish',
            '.bat': 'batch',
            '.cmd': 'batch',
            '.ps1': 'powershell',
            
            # Programming languages
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.hpp': 'cpp',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.m': 'matlab',
            
            # Database
            '.sql': 'sql',
            
            # Configuration
            '.conf': 'ini',
            '.cfg': 'ini',
            '.properties': 'properties',
            
            # Docker/Infrastructure
            '.dockerfile': 'dockerfile',
            '.dockerignore': 'text',
            
            # Other common files
            '.log': 'text',
            '.csv': 'text',
        }
        
        # Cache for lexer instances to avoid repeated creation
        self._lexer_cache = {}
    
    def get_lexer_by_extension(self, extension):
        """
        Get a pygments lexer for the given file extension.
        
        Args:
            extension (str): File extension including the dot (e.g., '.py')
            
        Returns:
            pygments lexer instance or None for unknown extensions
        """
        if not extension:
            return self._get_text_lexer()
        
        # Normalize extension to lowercase
        extension = extension.lower()
        
        # Check if we have a mapping for this extension
        lexer_name = self.extension_mapping.get(extension)
        
        if lexer_name:
            # Check cache first
            if lexer_name in self._lexer_cache:
                return self._lexer_cache[lexer_name]
            
            try:
                lexer = get_lexer_by_name(lexer_name)
                self._lexer_cache[lexer_name] = lexer
                return lexer
            except ClassNotFound:
                # If pygments doesn't have this lexer, fallback to text
                return self._get_text_lexer()
        
        # Unknown extension - return text lexer as fallback
        return self._get_text_lexer()
    
    def get_lexer_for_file(self, filename):
        """
        Get a pygments lexer for the given filename.
        
        Args:
            filename (str): Name of the file (can be full path or just filename)
            
        Returns:
            pygments lexer instance
        """
        if not filename:
            return self._get_text_lexer()
        
        # Extract the file extension
        _, extension = os.path.splitext(filename)
        
        return self.get_lexer_by_extension(extension)
    
    def _get_text_lexer(self):
        """Get a text lexer instance, using cache if available."""
        if 'text' not in self._lexer_cache:
            self._lexer_cache['text'] = TextLexer()
        return self._lexer_cache['text']
    
    def get_supported_extensions(self):
        """
        Get a list of all supported file extensions.
        
        Returns:
            list: List of supported file extensions
        """
        return list(self.extension_mapping.keys())
    
    def is_extension_supported(self, extension):
        """
        Check if a file extension is supported.
        
        Args:
            extension (str): File extension to check
            
        Returns:
            bool: True if extension is supported, False otherwise
        """
        if not extension:
            return False
        return extension.lower() in self.extension_mapping 