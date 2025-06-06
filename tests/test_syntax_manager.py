import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock


class TestSyntaxManager(unittest.TestCase):
    """Test the SyntaxManager class for lexer detection and management"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Will import SyntaxManager once implemented
        pass
    
    def test_syntax_manager_class_exists(self):
        """Test that SyntaxManager class can be imported"""
        try:
            from src.syntax_manager import SyntaxManager
            self.assertTrue(True, "SyntaxManager class should be importable")
        except ImportError:
            self.fail("SyntaxManager class should be importable from src.syntax_manager")
    
    def test_syntax_manager_can_be_instantiated(self):
        """Test that SyntaxManager can be instantiated"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        self.assertIsNotNone(manager, "SyntaxManager should be instantiable")
    
    def test_syntax_manager_has_get_lexer_for_file_method(self):
        """Test that SyntaxManager has get_lexer_for_file method"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        self.assertTrue(hasattr(manager, 'get_lexer_for_file'), 
                       "SyntaxManager should have get_lexer_for_file method")
        self.assertTrue(callable(manager.get_lexer_for_file),
                       "get_lexer_for_file should be callable")
    
    def test_syntax_manager_has_get_lexer_by_extension_method(self):
        """Test that SyntaxManager has get_lexer_by_extension method"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        self.assertTrue(hasattr(manager, 'get_lexer_by_extension'), 
                       "SyntaxManager should have get_lexer_by_extension method")
        self.assertTrue(callable(manager.get_lexer_by_extension),
                       "get_lexer_by_extension should be callable")
    
    def test_get_lexer_by_extension_python_files(self):
        """Test lexer detection for Python files"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        # Test various Python extensions
        python_extensions = ['.py', '.pyw', '.pyi']
        for ext in python_extensions:
            lexer = manager.get_lexer_by_extension(ext)
            self.assertIsNotNone(lexer, f"Should return lexer for {ext}")
            # Check if it's a Python lexer (basic check)
            self.assertIn('python', str(type(lexer)).lower(), 
                         f"Should return Python lexer for {ext}")
    
    def test_get_lexer_by_extension_javascript_files(self):
        """Test lexer detection for JavaScript files"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        js_extensions = ['.js', '.jsx']
        for ext in js_extensions:
            lexer = manager.get_lexer_by_extension(ext)
            self.assertIsNotNone(lexer, f"Should return lexer for {ext}")
    
    def test_get_lexer_by_extension_web_files(self):
        """Test lexer detection for web files"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        web_extensions = ['.html', '.css', '.json']
        for ext in web_extensions:
            lexer = manager.get_lexer_by_extension(ext)
            self.assertIsNotNone(lexer, f"Should return lexer for {ext}")
    
    def test_get_lexer_by_extension_unknown_extension(self):
        """Test lexer detection for unknown file extensions"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        # Should return None or TextLexer for unknown extensions
        unknown_extensions = ['.xyz', '.unknown', '.randomext']
        for ext in unknown_extensions:
            lexer = manager.get_lexer_by_extension(ext)
            # Either None (fallback to text) or TextLexer or similar fallback
            if lexer is not None:
                # If it returns a lexer, it should be TextLexer or similar fallback
                self.assertIn('text', str(type(lexer)).lower(), 
                             f"Unknown extension {ext} should fallback to text lexer")
    
    def test_get_lexer_for_file_with_extension(self):
        """Test file-based lexer detection using file extensions"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        test_files = [
            'test.py',
            'script.js', 
            'style.css',
            'page.html',
            'data.json'
        ]
        
        for filename in test_files:
            lexer = manager.get_lexer_for_file(filename)
            self.assertIsNotNone(lexer, f"Should return lexer for {filename}")
    
    def test_get_lexer_for_file_without_extension(self):
        """Test file-based lexer detection for files without extensions"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        # Files without extensions should fallback gracefully
        extensionless_files = ['README', 'Makefile', 'script']
        for filename in extensionless_files:
            lexer = manager.get_lexer_for_file(filename)
            # Should return a fallback lexer (text or None)
            if lexer is not None:
                self.assertIn('text', str(type(lexer)).lower(),
                             f"File without extension {filename} should use text lexer")
    
    def test_get_lexer_for_file_handles_case_insensitive(self):
        """Test that file extension detection is case insensitive"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        # Test uppercase extensions
        upper_files = ['TEST.PY', 'SCRIPT.JS', 'STYLE.CSS']
        for filename in upper_files:
            lexer = manager.get_lexer_for_file(filename)
            self.assertIsNotNone(lexer, f"Should handle case insensitive {filename}")
    
    def test_syntax_manager_extension_mapping_comprehensive(self):
        """Test that SyntaxManager has comprehensive file extension mapping"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        # Test comprehensive list of common programming languages
        expected_extensions = {
            '.py': 'python',
            '.js': 'javascript', 
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown',
            '.txt': 'text',
            '.xml': 'xml',
            '.sql': 'sql',
            '.sh': 'bash'
        }
        
        for ext, expected_lang in expected_extensions.items():
            lexer = manager.get_lexer_by_extension(ext)
            self.assertIsNotNone(lexer, f"Should have lexer for {ext}")
    
    def test_get_lexer_for_file_with_python_shebang(self):
        """Test lexer detection for files with Python shebang"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        # Create temporary files with Python shebangs
        python_shebangs = [
            '#!/usr/bin/python',
            '#!/usr/bin/env python',
            '#!/usr/bin/python3',
            '#!/usr/bin/env python3',
            '#! /usr/bin/python',
            '#! /usr/bin/env python3'
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, shebang in enumerate(python_shebangs):
                filename = os.path.join(temp_dir, f'script_{i}')
                with open(filename, 'w') as f:
                    f.write(f'{shebang}\nprint("hello world")\n')
                
                lexer = manager.get_lexer_for_file(filename)
                self.assertIsNotNone(lexer, f"Should detect lexer for Python shebang: {shebang}")
                # Check if it's a Python lexer
                lexer_name = str(type(lexer)).lower()
                self.assertIn('python', lexer_name, 
                             f"Should return Python lexer for shebang: {shebang}")
    
    def test_get_lexer_for_file_with_bash_shebang(self):
        """Test lexer detection for files with bash shebang"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        bash_shebangs = [
            '#!/bin/bash',
            '#!/usr/bin/bash',
            '#!/bin/sh',
            '#!/usr/bin/sh',
            '#!/usr/bin/env bash'
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, shebang in enumerate(bash_shebangs):
                filename = os.path.join(temp_dir, f'script_{i}')
                with open(filename, 'w') as f:
                    f.write(f'{shebang}\necho "hello world"\n')
                
                lexer = manager.get_lexer_for_file(filename)
                self.assertIsNotNone(lexer, f"Should detect lexer for bash shebang: {shebang}")
                # Check if it's a bash lexer
                lexer_name = str(type(lexer)).lower()
                self.assertIn('bash', lexer_name, 
                             f"Should return bash lexer for shebang: {shebang}")
    
    def test_get_lexer_for_file_with_other_shebangs(self):
        """Test lexer detection for files with other common shebangs"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        other_shebangs = [
            ('#!/usr/bin/env node', 'javascript'),
            ('#!/usr/bin/ruby', 'ruby'),
            ('#!/usr/bin/perl', 'perl'),
            ('#!/usr/bin/env php', 'php')
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, (shebang, expected_lang) in enumerate(other_shebangs):
                filename = os.path.join(temp_dir, f'script_{i}')
                with open(filename, 'w') as f:
                    f.write(f'{shebang}\n// sample code\n')
                
                lexer = manager.get_lexer_for_file(filename)
                self.assertIsNotNone(lexer, f"Should detect lexer for {expected_lang} shebang: {shebang}")
    
    def test_get_lexer_for_file_without_shebang_fallback(self):
        """Test that files without shebangs fallback gracefully"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.join(temp_dir, 'no_shebang_file')
            with open(filename, 'w') as f:
                f.write('some content without shebang\n')
            
            lexer = manager.get_lexer_for_file(filename)
            # Should fallback to text lexer
            if lexer is not None:
                lexer_name = str(type(lexer)).lower()
                self.assertIn('text', lexer_name, 
                             "File without shebang should use text lexer")
    
    def test_get_lexer_for_file_empty_file(self):
        """Test lexer detection for empty files"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.join(temp_dir, 'empty_file')
            with open(filename, 'w') as f:
                pass  # Create empty file
            
            lexer = manager.get_lexer_for_file(filename)
            # Should handle empty files gracefully
            if lexer is not None:
                lexer_name = str(type(lexer)).lower()
                self.assertIn('text', lexer_name, 
                             "Empty file should use text lexer")
    
    def test_get_lexer_for_file_shebang_case_insensitive(self):
        """Test that shebang detection is case insensitive where appropriate"""
        from src.syntax_manager import SyntaxManager
        manager = SyntaxManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.join(temp_dir, 'case_test')
            with open(filename, 'w') as f:
                f.write('#!/usr/bin/env Python3\nprint("test")\n')
            
            lexer = manager.get_lexer_for_file(filename)
            self.assertIsNotNone(lexer, "Should handle case variations in shebangs")


if __name__ == '__main__':
    unittest.main() 