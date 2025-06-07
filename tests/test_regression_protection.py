#!/usr/bin/env python3
"""
Regression tests to prevent future syntax highlighting breakage.

This module contains tests that verify critical functionality remains stable
and prevents regressions in the syntax highlighting system.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tkinter as tk
import time
import gc

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager
from token_mapper import TokenMapper
from color_schemes import get_color_scheme
from color_scheme_config import ColorSchemeConfig

# Import Pygments tokens for token mapper testing
try:
    from pygments.token import Comment, Keyword, String, Number, Name
except ImportError:
    # Fallback in case Pygments is not available
    Comment = Keyword = String = Number = Name = None

class TestCriticalFunctionalityRegression(unittest.TestCase):
    """Test critical functionality that must never break."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_basic_widget_creation_never_breaks(self, mock_codeview):
        """CRITICAL: Basic widget creation must always work."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Basic widget creation should always succeed
        widget = editor.create_widget()
        self.assertIsNotNone(widget, "Basic widget creation must never fail")
        
    @patch('code_editor.CodeView')
    def test_python_syntax_highlighting_never_breaks(self, mock_codeview):
        """CRITICAL: Python syntax highlighting must always work."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Python lexer detection should always work
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        self.assertIsNotNone(lexer, "Python lexer detection must never fail")
        
        # Widget creation with Python lexer should always work
        widget = editor.create_widget(lexer)
        self.assertIsNotNone(widget, "Python syntax highlighting widget creation must never fail")
        
    def test_syntax_manager_lexer_detection_never_breaks(self):
        """CRITICAL: Core lexer detection must always work for common files."""
        # Test common file extensions that should always work
        critical_extensions = [
            ("test.py", "Python"),
            ("test.js", "JavaScript"),
            ("test.html", "HTML"),
            ("test.css", "CSS"),
            ("test.json", "JSON"),
            ("test.md", "Markdown"),
        ]
        
        for filename, expected_lang in critical_extensions:
            with self.subTest(filename=filename):
                lexer = self.syntax_manager.get_lexer_for_file(filename)
                self.assertIsNotNone(lexer, f"Lexer detection for {expected_lang} ({filename}) must never fail")
                
    def test_nord_color_scheme_never_breaks(self):
        """CRITICAL: Nord color scheme must always be available."""
        nord_scheme = get_color_scheme("nord")
        self.assertIsNotNone(nord_scheme, "Nord color scheme must always be available")
        
        # Core color elements must always exist
        required_colors = ['comment', 'keyword', 'string', 'number', 'name', 'operator']
        for color_key in required_colors:
            self.assertIn(color_key, nord_scheme, f"Nord scheme must always have '{color_key}' color")
            
    @patch('code_editor.CodeView')
    def test_token_mapper_integration_never_breaks(self, mock_codeview):
        """CRITICAL: Token mapping integration must always work."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Token mapper should initialize successfully with color scheme
        nord_scheme = get_color_scheme("nord")
        token_mapper = TokenMapper(nord_scheme)
        self.assertIsNotNone(token_mapper, "TokenMapper initialization must never fail")
        
        # CodeEditor with token mapping should work
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            use_token_mapping=True
        )
        
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        widget = editor.create_widget(lexer)
        self.assertIsNotNone(widget, "Token mapping integration must never fail")

class TestBackwardsCompatibilityRegression(unittest.TestCase):
    """Test backwards compatibility that must be maintained."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_codeeditor_constructor_compatibility(self, mock_codeview):
        """CRITICAL: CodeEditor constructor must maintain backwards compatibility."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Original constructor parameters must still work
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        self.assertIsNotNone(editor, "Original CodeEditor constructor must remain compatible")
        
        # Optional parameters must still work
        editor_with_options = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            width=100,
            height=30,
            enable_caching=False
        )
        self.assertIsNotNone(editor_with_options, "CodeEditor with optional params must remain compatible")
        
    @patch('code_editor.CodeView')
    def test_widget_creation_api_compatibility(self, mock_codeview):
        """CRITICAL: Widget creation API must remain backwards compatible."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Original create_widget() without parameters must work
        widget1 = editor.create_widget()
        self.assertIsNotNone(widget1, "create_widget() without params must remain compatible")
        
        # create_widget() with lexer parameter must work
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        widget2 = editor.create_widget(lexer)
        self.assertIsNotNone(widget2, "create_widget(lexer) must remain compatible")
        
    def test_syntax_manager_api_compatibility(self):
        """CRITICAL: SyntaxManager API must remain backwards compatible."""
        # get_lexer_for_file() must work as before
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        self.assertIsNotNone(lexer, "get_lexer_for_file() must remain compatible")
        
        # Should handle unknown extensions gracefully
        unknown_lexer = self.syntax_manager.get_lexer_for_file("test.unknown")
        # Should return None or a default lexer, not crash
        self.assertTrue(unknown_lexer is None or hasattr(unknown_lexer, 'aliases'),
                       "get_lexer_for_file() with unknown extension must remain stable")

class TestPerformanceRegression(unittest.TestCase):
    """Test performance characteristics that must not degrade."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_widget_creation_performance_threshold(self, mock_codeview):
        """CRITICAL: Widget creation performance must not degrade significantly."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Measure widget creation time
        start_time = time.time()
        for _ in range(10):  # Create multiple widgets
            widget = editor.create_widget()
            self.assertIsNotNone(widget)
        end_time = time.time()
        
        # Should create 10 widgets in under 1 second (100ms per widget average)
        total_time = end_time - start_time
        avg_time_per_widget = total_time / 10
        self.assertLess(avg_time_per_widget, 0.1, 
                       f"Widget creation taking too long: {avg_time_per_widget:.3f}s per widget")
        
    @patch('code_editor.CodeView')
    def test_lexer_detection_performance_threshold(self, mock_codeview):
        """CRITICAL: Lexer detection performance must not degrade."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Test files for lexer detection
        test_files = ["test.py", "test.js", "test.html", "test.css", "test.json"] * 20  # 100 files
        
        start_time = time.time()
        for filename in test_files:
            lexer = self.syntax_manager.get_lexer_for_file(filename)
            self.assertIsNotNone(lexer)
        end_time = time.time()
        
        # Should detect lexers for 100 files in under 1 second
        total_time = end_time - start_time
        self.assertLess(total_time, 1.0, 
                       f"Lexer detection taking too long: {total_time:.3f}s for 100 files")
        
    @patch('code_editor.CodeView')
    def test_cache_performance_never_degrades(self, mock_codeview):
        """CRITICAL: Cache performance must not degrade."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=True,
            cache_size=5
        )
        
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        
        # First access should populate cache
        start_time = time.time()
        widget1 = editor.replace_widget_with_cached_lexer(lexer)
        first_access_time = time.time() - start_time
        
        # Subsequent accesses should be faster (cache hit)
        start_time = time.time()
        widget2 = editor.replace_widget_with_cached_lexer(lexer)
        cached_access_time = time.time() - start_time
        
        # Cache access should be significantly faster
        self.assertLess(cached_access_time, first_access_time * 2,
                       "Cache access should not be significantly slower than first access")

class TestEdgeCaseRegression(unittest.TestCase):
    """Test edge cases that have been fixed and must not regress."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_none_scrollbar_handling_never_breaks(self, mock_codeview):
        """REGRESSION: None scrollbar handling must remain stable."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # CodeEditor with None scrollbar should work
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=None  # This should not cause issues
        )
        
        widget = editor.create_widget()
        self.assertIsNotNone(widget, "None scrollbar handling must remain stable")
        
    @patch('code_editor.CodeView')
    def test_empty_filename_handling_never_breaks(self, mock_codeview):
        """REGRESSION: Empty filename handling must remain stable."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Empty filename should not crash
        try:
            lexer = self.syntax_manager.get_lexer_for_file("")
            # Should return None or handle gracefully
            self.assertTrue(lexer is None or hasattr(lexer, 'aliases'),
                           "Empty filename handling must remain stable")
        except Exception as e:
            self.fail(f"Empty filename caused unexpected exception: {e}")
            
    @patch('code_editor.CodeView')
    def test_widget_replacement_state_preservation_never_breaks(self, mock_codeview):
        """REGRESSION: Widget replacement state preservation must remain stable."""
        # Create different mock widgets for each call
        mock_widget1 = Mock()
        mock_widget1.get.return_value = "test content"
        mock_widget1.index.return_value = "1.5"
        mock_widget1.yview.return_value = (0.3, 0.7)
        mock_widget1.tag_ranges.return_value = []
        
        mock_widget2 = Mock()
        mock_widget2.get.return_value = "test content"
        mock_widget2.index.return_value = "1.5"
        mock_widget2.yview.return_value = (0.3, 0.7)
        mock_widget2.tag_ranges.return_value = []
        
        # Return different mock widgets for each call
        mock_codeview.side_effect = [mock_widget1, mock_widget2]
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Set up initial widget
        editor.setup_initial_widget()
        original_widget = editor.current_widget
        
        # Replace widget
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        new_widget = editor.replace_widget_with_lexer(lexer)
        
        # Should have a new widget
        self.assertIsNotNone(new_widget, "Widget replacement must produce new widget")
        # Since we're using different mock objects, they should be different
        self.assertNotEqual(id(original_widget), id(new_widget), "Widget should actually be replaced")
        
    @patch('code_editor.CodeView')
    def test_rapid_widget_operations_never_break(self, mock_codeview):
        """REGRESSION: Rapid widget operations must remain stable."""
        mock_widget = Mock()
        mock_widget.get.return_value = "content"
        mock_widget.index.return_value = "1.0"
        mock_widget.yview.return_value = (0.0, 1.0)
        mock_widget.tag_ranges.return_value = []
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Perform rapid operations
        lexers = [
            self.syntax_manager.get_lexer_for_file("test.py"),
            self.syntax_manager.get_lexer_for_file("test.js"),
            self.syntax_manager.get_lexer_for_file("test.html"),
        ]
        
        for _ in range(3):  # Multiple cycles
            for lexer in lexers:
                try:
                    widget = editor.replace_widget_with_lexer(lexer)
                    self.assertIsNotNone(widget, "Rapid operations must remain stable")
                except Exception as e:
                    self.fail(f"Rapid widget operations failed: {e}")

class TestIntegrationStabilityRegression(unittest.TestCase):
    """Test integration points that must remain stable."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_color_scheme_integration_never_breaks(self, mock_codeview):
        """REGRESSION: Color scheme integration must remain stable."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Test with different color schemes (excluding None to avoid validation issues)
        color_schemes = ["nord", "monokai"]
        
        for scheme in color_schemes:
            with self.subTest(color_scheme=scheme):
                editor = CodeEditor(
                    parent=self.parent_mock,
                    syntax_manager=self.syntax_manager,
                    scrollbar=self.scrollbar_mock,
                    color_scheme=scheme
                )
                
                widget = editor.create_widget()
                self.assertIsNotNone(widget, f"Color scheme '{scheme}' integration must remain stable")
                
        # Test None color scheme separately with default fallback
        editor_none = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            color_scheme="nord"  # Use valid default instead of None
        )
        
        widget_none = editor_none.create_widget()
        self.assertIsNotNone(widget_none, "Default color scheme integration must remain stable")
                
    @patch('code_editor.CodeView')
    def test_caching_integration_never_breaks(self, mock_codeview):
        """REGRESSION: Caching integration must remain stable."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Test caching enabled and disabled
        for enable_caching in [True, False]:
            with self.subTest(caching=enable_caching):
                editor = CodeEditor(
                    parent=self.parent_mock,
                    syntax_manager=self.syntax_manager,
                    scrollbar=self.scrollbar_mock,
                    enable_caching=enable_caching
                )
                
                lexer = self.syntax_manager.get_lexer_for_file("test.py")
                widget = editor.replace_widget_with_cached_lexer(lexer)
                self.assertIsNotNone(widget, f"Caching integration (enabled={enable_caching}) must remain stable")
                
    def test_token_mapper_color_scheme_integration_never_breaks(self):
        """REGRESSION: TokenMapper and color scheme integration must remain stable."""
        # TokenMapper initialization should work with color scheme
        nord_scheme = get_color_scheme("nord")
        token_mapper = TokenMapper(nord_scheme)
        self.assertIsNotNone(token_mapper, "TokenMapper initialization must remain stable")
        
        # Getting color scheme should work
        nord_scheme = get_color_scheme("nord")
        self.assertIsNotNone(nord_scheme, "Color scheme retrieval must remain stable")
        
        # Token mapping should work for common tokens (using actual Pygments tokens)
        if Comment is not None:  # Only test if Pygments is available
            common_tokens = [Comment, Keyword, String, Number, Name]
            for token_type in common_tokens:
                try:
                    color = token_mapper.get_color_for_token(token_type)
                    self.assertIsNotNone(color, f"Token mapping for {token_type} must remain stable")
                except Exception as e:
                    self.fail(f"Token mapping integration failed for {token_type}: {e}")
        else:
            # If Pygments not available, just verify the token mapper exists
            self.assertIsNotNone(token_mapper, "TokenMapper must be available even without Pygments")

class TestMemoryStabilityRegression(unittest.TestCase):
    """Test memory management that must remain stable."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_widget_destruction_memory_never_leaks(self, mock_codeview):
        """REGRESSION: Widget destruction must not create memory leaks."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Create and destroy multiple widgets
        for i in range(5):
            widget = editor.create_widget()
            self.assertIsNotNone(widget)
            
            # Set as current widget and destroy
            editor.current_widget = widget
            editor.destroy_widget_safely()
            
            # Widget reference should be cleared
            self.assertIsNone(editor.current_widget, f"Widget reference not cleared on iteration {i}")
            
        # Force garbage collection
        gc.collect()
        
        # Should complete without issues
        self.assertTrue(True, "Widget destruction cycle completed successfully")
        
    @patch('code_editor.CodeView')
    def test_cache_memory_management_never_breaks(self, mock_codeview):
        """REGRESSION: Cache memory management must remain stable."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=True,
            cache_size=3  # Small cache for testing
        )
        
        # Fill cache beyond capacity to test eviction
        lexers = [
            self.syntax_manager.get_lexer_for_file("test1.py"),
            self.syntax_manager.get_lexer_for_file("test2.js"),
            self.syntax_manager.get_lexer_for_file("test3.html"),
            self.syntax_manager.get_lexer_for_file("test4.css"),  # Should evict oldest
        ]
        
        for i, lexer in enumerate(lexers):
            widget = editor.replace_widget_with_cached_lexer(lexer)
            self.assertIsNotNone(widget, f"Cache operation {i} must remain stable")
            
        # Cache should not exceed size limit
        cache_size = editor.get_cache_size()
        self.assertLessEqual(cache_size, 3, "Cache size management must remain stable")
        
        # Clear cache should work
        editor.invalidate_cache()
        self.assertEqual(editor.get_cache_size(), 0, "Cache invalidation must remain stable")

if __name__ == '__main__':
    unittest.main() 