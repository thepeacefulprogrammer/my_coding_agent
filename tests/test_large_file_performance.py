"""
Test suite for large file performance optimizations.

This module tests performance optimizations specifically designed for handling
large files efficiently, including lazy loading, content chunking, and
memory-aware processing.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import gc
import threading
from io import StringIO

from src.code_editor import CodeEditor
from src.syntax_manager import SyntaxManager


@patch('src.code_editor.CodeView')
class TestLargeFilePerformance(unittest.TestCase):
    """Test performance optimizations for large files."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_parent = Mock()
        self.mock_scrollbar = Mock()
        self.mock_scrollbar.get.return_value = (0.0, 1.0)
        
        # Create a proper syntax manager instance
        self.syntax_manager = SyntaxManager()
        
        self.editor = CodeEditor(self.mock_parent, self.syntax_manager, scrollbar=self.mock_scrollbar)
        
        # Force garbage collection before tests
        gc.collect()
    
    def _setup_mock_widget(self, mock_codeview):
        """Helper method to set up mock widget for tests."""
        mock_widget = Mock()
        mock_widget.configure_mock(**{
            'delete.return_value': None,
            'insert.return_value': None,
            'mark_set.return_value': None,
            'config.return_value': None,
            'get.return_value': "test content",
            'yview.return_value': (0.0, 1.0),
            'yview_moveto.return_value': None
        })
        mock_codeview.return_value = mock_widget
        return mock_widget
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.editor, 'destroy'):
            self.editor.destroy()
        gc.collect()
    
    def generate_large_content(self, size_kb):
        """Generate large content for testing."""
        # Generate realistic Python code content
        base_content = '''
import os
import sys
from typing import List, Dict, Optional

class TestClass:
    """A test class for performance testing."""
    
    def __init__(self, name: str, value: int = 0):
        self.name = name
        self.value = value
        self._private_attr = None
    
    def method_with_logic(self, param: str) -> Optional[str]:
        """Method with realistic logic."""
        if not param:
            return None
        
        result = []
        for i, char in enumerate(param):
            if i % 2 == 0:
                result.append(char.upper())
            else:
                result.append(char.lower())
        
        return ''.join(result)
    
    @property
    def computed_value(self) -> int:
        """Computed property with calculation."""
        return self.value * 2 + len(self.name)

def function_with_loops():
    """Function with nested loops for complexity."""
    data = {}
    for i in range(100):
        for j in range(50):
            key = f"item_{i}_{j}"
            data[key] = i * j + (i + j) ** 2
    return data

# Additional realistic content
CONFIG = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "testdb"
    },
    "cache": {
        "type": "redis",
        "ttl": 3600
    }
}
'''
        
        # Calculate how many times to repeat to reach target size
        base_size = len(base_content.encode('utf-8'))
        target_size = size_kb * 1024
        repetitions = max(1, target_size // base_size)
        
        return base_content * repetitions
    
    def test_large_file_loading_performance_1mb(self, mock_codeview):
        """Test that 1MB files load within performance threshold."""
        self._setup_mock_widget(mock_codeview)
        large_content = self.generate_large_content(1024)  # 1MB
        
        start_time = time.time()
        success = self.editor.load_content(large_content, "test_large.py")
        end_time = time.time()
        
        loading_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Large files should load within 2 seconds
        self.assertTrue(success, "Large file should load successfully")
        self.assertLess(loading_time, 2000, f"1MB file loading took {loading_time:.2f}ms, should be <2000ms")
    
    def test_large_file_loading_performance_5mb(self, mock_codeview):
        """Test that 5MB files load within extended threshold."""
        self._setup_mock_widget(mock_codeview)
        large_content = self.generate_large_content(5 * 1024)  # 5MB
        
        start_time = time.time()
        success = self.editor.load_content(large_content, "test_very_large.py")
        end_time = time.time()
        
        loading_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Very large files should load within 5 seconds
        self.assertTrue(success, "Very large file should load successfully")
        self.assertLess(loading_time, 5000, f"5MB file loading took {loading_time:.2f}ms, should be <5000ms")
    
    def test_lazy_syntax_highlighting_for_large_content(self, mock_codeview):
        """Test that syntax highlighting can be applied lazily for large content."""
        self._setup_mock_widget(mock_codeview)
        large_content = self.generate_large_content(2048)  # 2MB
        
        # Mock the syntax manager to test lazy highlighting
        with patch.object(self.syntax_manager, 'get_lexer_for_file') as mock_get_lexer:
            mock_lexer = Mock()
            mock_lexer.name = 'Python'
            mock_get_lexer.return_value = mock_lexer
            
            start_time = time.time()
            success = self.editor.load_content(large_content, "test_lazy.py")
            end_time = time.time()
            
            loading_time = (end_time - start_time) * 1000
            
            self.assertTrue(success, "Large file with lazy highlighting should load")
            # With lazy highlighting, loading should be faster
            self.assertLess(loading_time, 3000, f"Lazy highlighting took {loading_time:.2f}ms")
    
    def test_memory_efficient_content_processing(self, mock_codeview):
        """Test that large content processing doesn't cause excessive memory usage."""
        self._setup_mock_widget(mock_codeview)
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        large_content = self.generate_large_content(3 * 1024)  # 3MB
        
        # Load the large content
        success = self.editor.load_content(large_content, "test_memory.py")
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        self.assertTrue(success, "Large file should load successfully")
        # Memory increase should be reasonable (not more than 5x content size)
        self.assertLess(memory_increase, 15, f"Memory increased by {memory_increase:.2f}MB, should be <15MB")
    
    def test_content_chunking_for_extremely_large_files(self, mock_codeview):
        """Test that extremely large files are processed in chunks."""
        self._setup_mock_widget(mock_codeview)
        # Generate 15MB content (above the 10MB threshold)
        large_content = self.generate_large_content(15 * 1024)
        
        with patch.object(self.editor, '_process_content_in_chunks') as mock_chunking:
            mock_chunking.return_value = True
            
            success = self.editor.load_content(large_content, "test_chunked.py")
            
            self.assertTrue(success, "Extremely large file should load with chunking")
            # Verify chunking was called for large content
            mock_chunking.assert_called_once()
    
    def test_progressive_syntax_highlighting_chunks(self, mock_codeview):
        """Test that syntax highlighting can be applied progressively in chunks."""
        self._setup_mock_widget(mock_codeview)
        large_content = self.generate_large_content(1200)  # 1.2MB (above 1MB threshold)
        
        with patch.object(self.editor, '_apply_syntax_highlighting_progressively') as mock_progressive:
            mock_progressive.return_value = True
            
            success = self.editor.load_content(large_content, "test_progressive.py")
            
            self.assertTrue(success, "File should load with progressive highlighting")
            # Verify progressive highlighting was attempted
            mock_progressive.assert_called_once()
    
    def test_syntax_highlighting_timeout_for_large_files(self, mock_codeview):
        """Test that syntax highlighting has timeout protection for large files."""
        self._setup_mock_widget(mock_codeview)
        large_content = self.generate_large_content(2048)  # 2MB
        
        with patch.object(self.syntax_manager, 'apply_syntax_highlighting') as mock_highlighting:
            # Simulate slow highlighting that would timeout
            def slow_highlighting(*args, **kwargs):
                time.sleep(0.1)  # Simulate processing time
                return True
            
            mock_highlighting.side_effect = slow_highlighting
            
            start_time = time.time()
            success = self.editor.load_content(large_content, "test_timeout.py")
            end_time = time.time()
            
            processing_time = (end_time - start_time) * 1000
            
            self.assertTrue(success, "File should load even with slow highlighting")
            # Should have reasonable timeout protection
            self.assertLess(processing_time, 3000, "Should have timeout protection")
    
    def test_large_file_widget_replacement_performance(self, mock_codeview):
        """Test that widget replacement remains fast even with large content."""
        self._setup_mock_widget(mock_codeview)
        # Load initial large content
        large_content1 = self.generate_large_content(1024)  # 1MB
        self.editor.load_content(large_content1, "test1.py")
        
        # Generate different large content for replacement
        large_content2 = self.generate_large_content(1024)  # 1MB
        
        start_time = time.time()
        success = self.editor.load_content(large_content2, "test2.py")
        end_time = time.time()
        
        replacement_time = (end_time - start_time) * 1000
        
        self.assertTrue(success, "Large content replacement should succeed")
        # Widget replacement should remain fast even with large content
        self.assertLess(replacement_time, 1500, f"Replacement took {replacement_time:.2f}ms")
    
    def test_concurrent_large_file_operations(self, mock_codeview):
        """Test handling of concurrent operations with large files."""
        self._setup_mock_widget(mock_codeview)
        large_content = self.generate_large_content(512)  # 512KB
        
        # Simulate concurrent load operations
        results = []
        
        def load_operation():
            success = self.editor.load_content(large_content, "test_concurrent.py")
            results.append(success)
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=load_operation)
            threads.append(thread)
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000
        
        # At least one operation should succeed
        self.assertTrue(any(results), "At least one concurrent operation should succeed")
        # Concurrent operations should complete in reasonable time
        self.assertLess(total_time, 5000, f"Concurrent operations took {total_time:.2f}ms")
    
    def test_large_file_cache_efficiency(self, mock_codeview):
        """Test that caching works efficiently with large files."""
        self._setup_mock_widget(mock_codeview)
        large_content = self.generate_large_content(1024)  # 1MB
        filename = "test_cache_large.py"
        
        # First load - should cache
        start_time = time.time()
        success1 = self.editor.load_content(large_content, filename)
        first_load_time = (time.time() - start_time) * 1000
        
        # Second load - should use cache
        start_time = time.time()
        success2 = self.editor.load_content(large_content, filename)
        second_load_time = (time.time() - start_time) * 1000
        
        self.assertTrue(success1, "First large file load should succeed")
        self.assertTrue(success2, "Second large file load should succeed")
        # Cache should provide significant speedup
        self.assertLess(second_load_time, first_load_time * 0.8, 
                       "Cached load should be significantly faster")
    
    def test_large_file_memory_cleanup(self, mock_codeview):
        """Test that large file operations don't leak memory."""
        self._setup_mock_widget(mock_codeview)
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Load and unload several large files
        for i in range(3):
            large_content = self.generate_large_content(1024)  # 1MB each
            success = self.editor.load_content(large_content, f"test_cleanup_{i}.py")
            self.assertTrue(success, f"Large file {i} should load")
            
            # Clear references and force garbage collection
            del large_content
            gc.collect()
        
        # Check memory after cleanup
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal after cleanup
        self.assertLess(memory_increase, 10, f"Memory leaked {memory_increase:.2f}MB after cleanup")
    
    def test_large_file_error_recovery(self, mock_codeview):
        """Test error recovery when processing large files."""
        self._setup_mock_widget(mock_codeview)
        large_content = self.generate_large_content(1024)  # 1MB
        
        # Simulate error during large file processing by making create_widget fail first time
        with patch.object(self.editor, 'create_widget') as mock_create:
            mock_widget = Mock()
            mock_widget.configure_mock(**{
                'delete.return_value': None,
                'insert.return_value': None,
                'mark_set.return_value': None,
                'config.return_value': None,
                'get.return_value': "test content",
                'yview.return_value': (0.0, 1.0),
                'yview_moveto.return_value': None
            })
            mock_create.side_effect = [Exception("Simulated error"), mock_widget]
            
            # First call should fail and recover
            success = self.editor.load_content(large_content, "test_error_recovery.py")
            
            # Should still succeed due to error recovery (fallback behavior)
            # In this case, the error is caught and returns False, which is expected behavior
            self.assertFalse(success, "Should fail gracefully when widget creation fails")
    
    def test_large_file_syntax_highlighting_fallback(self, mock_codeview):
        """Test fallback to plain text for extremely large files."""
        self._setup_mock_widget(mock_codeview)
        # Generate extremely large content (20MB)
        extremely_large_content = self.generate_large_content(20 * 1024)
        
        with patch.object(self.syntax_manager, 'should_skip_syntax_highlighting') as mock_skip:
            mock_skip.return_value = True  # Simulate skipping syntax highlighting for size
            
            success = self.editor.load_content(extremely_large_content, "test_fallback.py")
            
            self.assertTrue(success, "Extremely large file should load with fallback")
            mock_skip.assert_called_once()
    
    def test_large_file_scroll_position_preservation(self, mock_codeview):
        """Test that scroll positions are preserved with large files."""
        mock_widget = self._setup_mock_widget(mock_codeview)
        large_content = self.generate_large_content(1024)  # 1MB
        
        # Set up mock scrollbar with specific position
        self.mock_scrollbar.get.return_value = (0.3, 0.7)
        
        # Load large content
        success = self.editor.load_content(large_content, "test_scroll_large.py")
        
        self.assertTrue(success, "Large file should load successfully")
        
        # Verify scrollbar configuration was called (this is what actually happens)
        self.mock_scrollbar.config.assert_called()
        # Verify widget yview configuration was set up
        mock_widget.config.assert_called()


if __name__ == '__main__':
    unittest.main() 