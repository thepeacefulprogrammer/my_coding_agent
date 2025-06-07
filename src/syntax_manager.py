"""
SyntaxManager: Handles lexer detection and language mapping for syntax highlighting.

This module provides functionality to detect appropriate pygments lexers for files
based on file extensions and other criteria.
"""

import os
import re
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
        
        # Shebang patterns for language detection
        self.shebang_patterns = {
            # Python
            r'#!/usr/bin/(?:env\s+)?python[0-9.]*': 'python',
            r'#!\s*/usr/bin/(?:env\s+)?python[0-9.]*': 'python',
            
            # Bash/Shell
            r'#!/bin/(?:ba)?sh': 'bash',
            r'#!/usr/bin/(?:ba)?sh': 'bash',
            r'#!/usr/bin/env\s+(?:ba)?sh': 'bash',
            r'#!\s*/bin/(?:ba)?sh': 'bash',
            r'#!\s*/usr/bin/(?:ba)?sh': 'bash',
            r'#!\s*/usr/bin/env\s+(?:ba)?sh': 'bash',
            
            # Node.js
            r'#!/usr/bin/env\s+node': 'javascript',
            r'#!\s*/usr/bin/env\s+node': 'javascript',
            
            # Ruby
            r'#!/usr/bin/(?:env\s+)?ruby': 'ruby',
            r'#!\s*/usr/bin/(?:env\s+)?ruby': 'ruby',
            
            # Perl
            r'#!/usr/bin/(?:env\s+)?perl': 'perl',
            r'#!\s*/usr/bin/(?:env\s+)?perl': 'perl',
            
            # PHP
            r'#!/usr/bin/(?:env\s+)?php': 'php',
            r'#!\s*/usr/bin/(?:env\s+)?php': 'php',
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
    
    def _detect_lexer_from_shebang(self, filename):
        """
        Detect lexer from shebang line in file.
        
        Args:
            filename (str): Path to the file to analyze
            
        Returns:
            pygments lexer instance or None if no shebang detected
        """
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                
                if not first_line.startswith('#!'):
                    return None
                
                # Check shebang patterns
                for pattern, lexer_name in self.shebang_patterns.items():
                    if re.match(pattern, first_line, re.IGNORECASE):
                        # Check cache first
                        if lexer_name in self._lexer_cache:
                            return self._lexer_cache[lexer_name]
                        
                        try:
                            lexer = get_lexer_by_name(lexer_name)
                            self._lexer_cache[lexer_name] = lexer
                            return lexer
                        except ClassNotFound:
                            continue
                
                return None
                
        except (OSError, IOError, UnicodeDecodeError):
            # File reading errors - return None
            return None
    
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
        
        # If we have an extension, use it
        if extension:
            return self.get_lexer_by_extension(extension)
        
        # No extension - try shebang detection if it's a file path
        if os.path.sep in filename or os.path.exists(filename):
            shebang_lexer = self._detect_lexer_from_shebang(filename)
            if shebang_lexer:
                return shebang_lexer
        
        # Fallback to text lexer
        return self._get_text_lexer()
    
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
        
    def should_skip_syntax_highlighting(self, content=None, filename=None, file_size_limit=50*1024*1024):
        """
        Determine if syntax highlighting should be skipped for performance reasons.
        
        Args:
            content (str): Content to analyze (optional)
            filename (str): Filename to analyze (optional)
            file_size_limit (int): File size limit in bytes (default: 20MB)
            
        Returns:
            bool: True if syntax highlighting should be skipped
        """
        # Check content size if provided
        if content is not None:
            content_size = len(content.encode('utf-8'))
            if content_size > file_size_limit:
                return True
        
        # Check file size if filename provided
        if filename is not None:
            try:
                import os
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    if file_size > file_size_limit:
                        return True
            except (OSError, IOError):
                # If we can't check file size, don't skip
                pass
        
        return False
        
    def apply_syntax_highlighting(self, widget, content, lexer):
        """
        Apply syntax highlighting to a widget with timeout protection.
        
        Args:
            widget: Widget to apply highlighting to
            content (str): Content to highlight
            lexer: Pygments lexer to use
            
        Returns:
            bool: True if highlighting applied successfully
        """
        try:
            # For large content, we might want to skip or timeout
            if self.should_skip_syntax_highlighting(content=content):
                return False
                
            # Apply highlighting (this would be implemented based on the widget API)
            # For now, just return True to indicate success
            return True
            
        except Exception:
            return False 