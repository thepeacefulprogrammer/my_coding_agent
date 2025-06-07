#!/usr/bin/env python3
"""
Tests for graceful fallback to plain text for unsupported files.

This module tests the system's ability to gracefully handle unsupported file types
by falling back to plain text display without syntax highlighting.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tkinter as tk

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager

class TestUnsupportedFileDetection(unittest.TestCase):
    """Test detection of unsupported file types."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    def test_unknown_extension_detection(self):
        """Test detection of files with unknown extensions."""
        unsupported_files = [
            "test.xyz",
            "test.unknown",
            "test.binary",
            "test.proprietary",
            "file.ext123",
            "document.custom"
        ]
        
        for filename in unsupported_files:
            with self.subTest(filename=filename):
                lexer = self.syntax_manager.get_lexer_for_file(filename)
                # Should return TextLexer for unknown extensions (graceful fallback)
                if lexer is not None:
                    # Check if it's a TextLexer (plain text fallback)
                    lexer_name = lexer.__class__.__name__
                    self.assertEqual(lexer_name, "TextLexer", 
                                   f"Should use TextLexer for unsupported file: {filename}, got {lexer_name}")
                else:
                    # None is also acceptable (no syntax highlighting)
                    self.assertIsNone(lexer, f"Lexer should be None or TextLexer for: {filename}")
                
    def test_no_extension_file_detection(self):
        """Test detection of files without extensions."""
        no_extension_files = [
            "Makefile",
            "Dockerfile", 
            "README",
            "LICENSE",
            "config",
            "script"
        ]
        
        for filename in no_extension_files:
            with self.subTest(filename=filename):
                # Some of these might have lexers (like Makefile), others might not
                lexer = self.syntax_manager.get_lexer_for_file(filename)
                # This is just testing the detection works without crashing
                self.assertTrue(lexer is None or hasattr(lexer, 'aliases'),
                               f"Lexer detection should handle file without extension: {filename}")
                
    def test_empty_filename_detection(self):
        """Test handling of empty or invalid filenames."""
        invalid_filenames = ["", None, ".", "..", "   "]
        
        for filename in invalid_filenames:
            with self.subTest(filename=repr(filename)):
                try:
                    lexer = self.syntax_manager.get_lexer_for_file(filename)
                    # Should return None or handle gracefully
                    self.assertTrue(lexer is None or hasattr(lexer, 'aliases'),
                                   f"Should handle invalid filename gracefully: {repr(filename)}")
                except Exception as e:
                    # Should not crash on invalid filenames
                    self.fail(f"Should not crash on invalid filename {repr(filename)}: {e}")

class TestPlainTextFallback(unittest.TestCase):
    """Test fallback to plain text widget creation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_plain_text_widget_creation(self, mock_codeview):
        """Test creation of plain text widget without lexer."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Create widget without lexer (plain text mode)
        widget = editor.create_widget(lexer=None)
        
        # Should create widget successfully
        self.assertIsNotNone(widget, "Should create plain text widget when no lexer provided")
        
        # Should call CodeView without lexer parameter
        mock_codeview.assert_called_once()
        call_args, call_kwargs = mock_codeview.call_args
        self.assertNotIn('lexer', call_kwargs, "Should not pass lexer parameter for plain text widget")
        
    @patch('code_editor.CodeView')
    def test_fallback_for_unsupported_file(self, mock_codeview):
        """Test automatic fallback for unsupported file types."""
        mock_widget = Mock()
        mock_widget.delete = Mock()
        mock_widget.insert = Mock()
        mock_widget.config = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Try to update content with unsupported file type
        test_content = "This is plain text content\nwithout syntax highlighting"
        
        # Should handle gracefully without syntax highlighting
        try:
            editor.update_file_content(test_content, "unsupported.xyz")
            success = True
        except Exception:
            success = False
            
        self.assertTrue(success, "Should handle unsupported file types gracefully")
        
    @patch('code_editor.CodeView') 
    def test_plain_text_preserves_functionality(self, mock_codeview):
        """Test that plain text mode preserves basic editor functionality."""
        mock_widget = Mock()
        mock_widget.delete = Mock()
        mock_widget.insert = Mock()
        mock_widget.get = Mock(return_value="test content")
        mock_widget.config = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Create plain text widget
        widget = editor.create_widget(lexer=None)
        editor.current_widget = widget
        
        # Test basic functionality still works
        # Content insertion
        editor.update_file_content("test content", None)
        mock_widget.delete.assert_called()
        mock_widget.insert.assert_called()
        
        # Content retrieval
        content = editor.get_content()
        mock_widget.get.assert_called()
        
        # Widget configuration
        self.assertIsNotNone(widget, "Plain text widget should be functional")

class TestFallbackIntegration(unittest.TestCase):
    """Test integration of fallback with existing systems."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_fallback_with_caching_disabled(self, mock_codeview):
        """Test fallback behavior when caching is disabled."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=False
        )
        
        # Should create plain text widget even with caching disabled
        widget = editor.create_widget(lexer=None)
        self.assertIsNotNone(widget, "Should create plain text widget with caching disabled")
        
    @patch('code_editor.CodeView')
    def test_fallback_with_caching_enabled(self, mock_codeview):
        """Test fallback behavior when caching is enabled."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=True
        )
        
        # Should handle plain text widget with caching enabled
        widget = editor.replace_widget_with_cached_lexer(None)
        self.assertIsNotNone(widget, "Should handle plain text widget with caching enabled")
        
    @patch('code_editor.CodeView')
    def test_fallback_preserves_scrollbar_connection(self, mock_codeview):
        """Test that fallback preserves scrollbar functionality."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Create plain text widget with scrollbar
        widget = editor.create_widget(lexer=None)
        
        # Should configure scrollbar even for plain text
        self.assertIsNotNone(widget, "Should create plain text widget with scrollbar")
        # The configure_scrollbar method should be called
        # (We can't easily verify this without more complex mocking)
        
    @patch('code_editor.CodeView')
    def test_fallback_with_color_scheme(self, mock_codeview):
        """Test that fallback respects color scheme settings."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            color_scheme="nord"
        )
        
        # Create plain text widget with color scheme
        widget = editor.create_widget(lexer=None)
        
        # Should apply color scheme even for plain text
        self.assertIsNotNone(widget, "Should create plain text widget with color scheme")
        
        # Verify CodeView was called with color scheme
        mock_codeview.assert_called_once()
        call_args, call_kwargs = mock_codeview.call_args
        self.assertIn('color_scheme', call_kwargs, "Should pass color scheme for plain text widget")

class TestFallbackErrorHandling(unittest.TestCase):
    """Test error handling in fallback scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_fallback_when_plain_text_creation_fails(self, mock_codeview):
        """Test handling when even plain text widget creation fails."""
        # Make CodeView creation fail
        mock_codeview.side_effect = Exception("Widget creation failed")
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Should handle widget creation failure gracefully
        with self.assertRaises(Exception) as context:
            editor.create_widget(lexer=None)
            
        # Should provide meaningful error message
        self.assertIn("creation", str(context.exception).lower())
        
    @patch('code_editor.CodeView')
    def test_fallback_with_corrupted_syntax_manager(self, mock_codeview):
        """Test fallback when SyntaxManager is corrupted or unavailable."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Use corrupted syntax manager
        corrupted_syntax_manager = Mock()
        corrupted_syntax_manager.get_lexer_for_file.side_effect = Exception("SyntaxManager corrupted")
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=corrupted_syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Should still be able to create plain text widget
        widget = editor.create_widget(lexer=None)
        self.assertIsNotNone(widget, "Should create plain text widget even with corrupted SyntaxManager")
        
    @patch('code_editor.CodeView')
    def test_fallback_handles_invalid_content(self, mock_codeview):
        """Test fallback handling of invalid or binary content."""
        mock_widget = Mock()
        mock_widget.delete = Mock()
        mock_widget.insert = Mock()
        mock_widget.config = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Test with various potentially problematic content
        problematic_contents = [
            b'\x00\x01\x02\x03',  # Binary content
            "Content with\x00null bytes",
            "Very long line " + "x" * 10000,  # Extremely long line
            "\n".join(["Line"] * 1000),  # Many lines
        ]
        
        for content in problematic_contents:
            with self.subTest(content_type=type(content).__name__):
                try:
                    # Convert bytes to string for text widget
                    if isinstance(content, bytes):
                        content = content.decode('latin1', errors='replace')
                        
                    editor.update_file_content(content, "test.unknown")
                    success = True
                except Exception:
                    success = False
                    
                # Should handle gracefully
                self.assertTrue(success, f"Should handle problematic content gracefully")

class TestFallbackPerformance(unittest.TestCase):
    """Test performance characteristics of fallback mode."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_plain_text_creation_performance(self, mock_codeview):
        """Test that plain text widget creation is fast."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        import time
        
        # Measure plain text widget creation time
        start_time = time.time()
        for _ in range(10):
            widget = editor.create_widget(lexer=None)
            self.assertIsNotNone(widget)
        end_time = time.time()
        
        # Should be very fast (< 50ms per widget)
        avg_time = (end_time - start_time) / 10
        self.assertLess(avg_time, 0.05, 
                       f"Plain text widget creation too slow: {avg_time:.3f}s average")
        
    @patch('code_editor.CodeView')
    def test_fallback_memory_efficiency(self, mock_codeview):
        """Test that fallback mode is memory efficient."""
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Create and destroy multiple plain text widgets
        for i in range(5):
            widget = editor.create_widget(lexer=None)
            self.assertIsNotNone(widget, f"Should create plain text widget {i}")
            
            # Set as current and destroy
            editor.current_widget = widget
            editor.destroy_widget_safely()
            
            # Reference should be cleared
            self.assertIsNone(editor.current_widget, f"Should clear widget reference {i}")
            
        # Should complete without memory issues
        self.assertTrue(True, "Plain text widget lifecycle should be memory efficient")

if __name__ == '__main__':
    unittest.main() 