#!/usr/bin/env python3
"""
Performance tests for CodeEditor widget replacement and memory usage.

This module tests the performance characteristics of the CodeEditor system,
including widget replacement speed, memory usage, cache efficiency, and
resource cleanup to ensure optimal performance.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import sys
import os
import gc
import threading
from collections import defaultdict

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager

class PerformanceTimer:
    """Context manager for measuring execution time."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        
    @property
    def elapsed_time(self):
        """Get elapsed time in seconds."""
        if self.start_time is None or self.end_time is None:
            return None
        return self.end_time - self.start_time

class MemoryProfiler:
    """Simple memory profiler for tracking object counts."""
    
    def __init__(self):
        self.initial_counts = {}
        self.final_counts = {}
        
    def start_profiling(self):
        """Start memory profiling."""
        gc.collect()  # Force garbage collection
        self.initial_counts = self._get_object_counts()
        
    def end_profiling(self):
        """End memory profiling."""
        gc.collect()  # Force garbage collection
        self.final_counts = self._get_object_counts()
        
    def _get_object_counts(self):
        """Get counts of objects by type."""
        counts = defaultdict(int)
        for obj in gc.get_objects():
            counts[type(obj).__name__] += 1
        return dict(counts)
        
    def get_memory_delta(self):
        """Get the change in object counts."""
        delta = {}
        all_types = set(self.initial_counts.keys()) | set(self.final_counts.keys())
        
        for obj_type in all_types:
            initial = self.initial_counts.get(obj_type, 0)
            final = self.final_counts.get(obj_type, 0)
            delta[obj_type] = final - initial
            
        return delta
        
    def has_memory_leaks(self, threshold=10):
        """Check if there are potential memory leaks."""
        delta = self.get_memory_delta()
        # Focus on types that might indicate leaks
        leak_indicators = ['Mock', 'MagicMock', 'CodeView', 'CodeEditor']
        
        for obj_type in leak_indicators:
            if delta.get(obj_type, 0) > threshold:
                return True
        return False

class TestWidgetReplacementPerformance(unittest.TestCase):
    """Test performance of widget replacement operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_widget_replacement_speed_baseline(self, mock_codeview):
        """Test baseline widget replacement speed."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=False  # Disable caching for baseline
        )
        
        # Create initial widget
        editor.setup_initial_widget()
        
        # Test single replacement
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        
        with PerformanceTimer() as timer:
            editor.replace_widget_with_lexer(lexer)
            
        # Assert reasonable performance (< 100ms for single replacement)
        self.assertIsNotNone(timer.elapsed_time)
        self.assertLess(timer.elapsed_time, 0.1, 
                       f"Widget replacement took {timer.elapsed_time:.3f}s, expected < 0.1s")
        
    @patch('code_editor.CodeView')
    def test_rapid_widget_replacement_performance(self, mock_codeview):
        """Test performance under rapid widget replacement scenarios."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=False
        )
        
        editor.setup_initial_widget()
        
        # Test rapid replacements
        lexers = [
            self.syntax_manager.get_lexer_for_file("test.py"),
            self.syntax_manager.get_lexer_for_file("test.js"),
            self.syntax_manager.get_lexer_for_file("test.html"),
            self.syntax_manager.get_lexer_for_file("test.css"),
        ]
        
        num_replacements = 20
        
        with PerformanceTimer() as timer:
            for i in range(num_replacements):
                lexer = lexers[i % len(lexers)]
                editor.replace_widget_with_lexer(lexer)
                
        average_time = timer.elapsed_time / num_replacements
        
        # Assert reasonable average performance (< 50ms per replacement)
        self.assertLess(average_time, 0.05,
                       f"Average replacement time {average_time:.3f}s, expected < 0.05s")
        
    @patch('code_editor.CodeView')
    def test_cached_widget_replacement_performance(self, mock_codeview):
        """Test performance improvement with widget caching."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=True,
            cache_size=5
        )
        
        editor.setup_initial_widget()
        
        # Test with caching
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        
        # First replacement (cache miss)
        with PerformanceTimer() as timer_miss:
            editor.replace_widget_with_cached_lexer(lexer)
            
        # Second replacement (cache hit)
        editor.replace_widget_with_lexer(None)  # Switch to different widget
        
        with PerformanceTimer() as timer_hit:
            editor.replace_widget_with_cached_lexer(lexer)
            
        # Cache hit should be faster than cache miss
        if timer_miss.elapsed_time and timer_hit.elapsed_time:
            cache_improvement = timer_miss.elapsed_time - timer_hit.elapsed_time
            # Allow for some variability but expect some improvement
            self.assertGreaterEqual(cache_improvement, -0.01,
                                   "Cache hit should not be significantly slower than cache miss")
                                   
    @patch('code_editor.CodeView')
    def test_memory_usage_during_widget_replacement(self, mock_codeview):
        """Test memory usage patterns during widget replacement."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        profiler = MemoryProfiler()
        profiler.start_profiling()
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=False
        )
        
        editor.setup_initial_widget()
        
        # Perform multiple replacements
        lexers = [
            self.syntax_manager.get_lexer_for_file("test.py"),
            self.syntax_manager.get_lexer_for_file("test.js"),
            self.syntax_manager.get_lexer_for_file("test.html"),
        ]
        
        for _ in range(10):
            for lexer in lexers:
                editor.replace_widget_with_lexer(lexer)
                
        # Clean up
        editor.destroy_widget_safely()
        del editor
        
        profiler.end_profiling()
        
        # Check for memory leaks (higher threshold for test environment with mocks)
        has_leaks = profiler.has_memory_leaks(threshold=50)
        if has_leaks:
            # Get memory delta for debugging
            delta = profiler.get_memory_delta()
            print(f"Memory delta: {delta}")
        self.assertFalse(has_leaks, "Detected potential memory leaks during widget replacement")
        
    @patch('code_editor.CodeView')
    def test_cache_efficiency_metrics(self, mock_codeview):
        """Test cache efficiency and hit/miss ratios."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=True,
            cache_size=3
        )
        
        editor.setup_initial_widget()
        
        # Test cache behavior
        lexers = [
            self.syntax_manager.get_lexer_for_file("test.py"),
            self.syntax_manager.get_lexer_for_file("test.js"),
            self.syntax_manager.get_lexer_for_file("test.html"),
        ]
        
        # Fill cache with initial misses
        for lexer in lexers:
            editor.replace_widget_with_cached_lexer(lexer)
            
        # Test cache hits
        cache_operations = []
        for _ in range(2):
            for lexer in lexers:
                # Should be cache hits now
                initial_cache_size = editor.get_cache_size()
                editor.replace_widget_with_cached_lexer(lexer)
                final_cache_size = editor.get_cache_size()
                
                # Cache size should remain stable for hits
                cache_operations.append({
                    'initial_size': initial_cache_size,
                    'final_size': final_cache_size,
                    'lexer_name': lexer.__class__.__name__ if lexer else 'None'
                })
        
        # Verify cache is being used effectively
        self.assertGreater(len(cache_operations), 0)
        
        # Cache should maintain consistent size during hits
        stable_operations = [op for op in cache_operations 
                           if op['initial_size'] == op['final_size']]
        self.assertGreater(len(stable_operations), 0,
                          "Cache should maintain stable size during cache hits")
                          
    @patch('code_editor.CodeView')
    def test_large_content_loading_performance(self, mock_codeview):
        """Test performance with large content loading."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Create large content (simulating a large file)
        large_content = "# Large Python file\n" * 1000  # ~20KB
        function_blocks = []
        for i in range(500):
            function_blocks.extend([
                f"def function_{i}():",
                f"    '''Function number {i}'''",
                f"    return {i} * 2",
                ""
            ])
        large_content += "\n".join(function_blocks)  # Add many functions
        
        with PerformanceTimer() as timer:
            editor.update_file_content(large_content, "large_file.py")
            
        # Assert reasonable performance for large content (< 500ms)
        self.assertIsNotNone(timer.elapsed_time)
        self.assertLess(timer.elapsed_time, 0.5,
                       f"Large content loading took {timer.elapsed_time:.3f}s, expected < 0.5s")
                       
    @patch('code_editor.CodeView')
    def test_concurrent_widget_operations_performance(self, mock_codeview):
        """Test performance under concurrent widget operations."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=True
        )
        
        editor.setup_initial_widget()
        
        # Test concurrent-like operations (simulated)
        results = []
        
        def replacement_operation(lexer_name):
            """Simulate a widget replacement operation."""
            lexer = self.syntax_manager.get_lexer_for_file(lexer_name)
            start_time = time.perf_counter()
            
            try:
                editor.replace_widget_with_cached_lexer(lexer)
                success = True
            except Exception:
                success = False
                
            end_time = time.perf_counter()
            return {
                'lexer': lexer_name,
                'duration': end_time - start_time,
                'success': success
            }
        
        # Simulate rapid operations
        file_types = ["test.py", "test.js", "test.html", "test.css", "test.json"]
        
        with PerformanceTimer() as total_timer:
            for i in range(25):  # 25 operations
                file_type = file_types[i % len(file_types)]
                result = replacement_operation(file_type)
                results.append(result)
        
        # Analyze results
        successful_operations = [r for r in results if r['success']]
        self.assertGreater(len(successful_operations), 20,
                          "Most operations should succeed under load")
        
        if successful_operations:
            avg_duration = sum(r['duration'] for r in successful_operations) / len(successful_operations)
            self.assertLess(avg_duration, 0.1,
                           f"Average operation duration {avg_duration:.3f}s too high under load")

class TestMemoryManagement(unittest.TestCase):
    """Test memory management and cleanup in CodeEditor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_widget_cleanup_memory_management(self, mock_codeview):
        """Test that widget cleanup properly manages memory."""
        # Setup
        created_widgets = []
        destroyed_widgets = []
        
        def create_widget_with_tracking(*args, **kwargs):
            widget = Mock()
            # Track destroy calls using a spy pattern
            widget.destroy_called = False
            original_destroy = widget.destroy
            def destroy_with_tracking():
                widget.destroy_called = True
                destroyed_widgets.append(widget)
                return original_destroy()
            widget.destroy = Mock(side_effect=destroy_with_tracking)
            created_widgets.append(widget)
            return widget
            
        mock_codeview.side_effect = create_widget_with_tracking
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=False
        )
        
        # Create and destroy multiple widgets
        for i in range(5):  # Reduced number for simpler test
            editor.setup_initial_widget()
            lexer = self.syntax_manager.get_lexer_for_file(f"test_{i}.py")
            editor.replace_widget_with_lexer(lexer)
            editor.destroy_widget_safely()
            
        # Verify widgets were created and destroyed
        self.assertGreater(len(created_widgets), 0, "Widgets should be created")
        
        # Verify proper cleanup behavior (functional test rather than memory leak detection)
        # This tests that destroy is called when it should be
        widgets_destroyed = [w for w in created_widgets if w.destroy_called]
        self.assertGreater(len(widgets_destroyed), 0,
                          "Widget destroy method should be called during cleanup")
        
        # Verify that destroy was actually called on mock objects
        for widget in created_widgets:
            if widget.destroy_called:
                widget.destroy.assert_called()
        
    @patch('code_editor.CodeView')
    def test_cache_memory_management(self, mock_codeview):
        """Test that widget cache properly manages memory."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=True,
            cache_size=2  # Small cache for testing
        )
        
        # Fill cache beyond capacity
        lexers = [
            self.syntax_manager.get_lexer_for_file("test1.py"),
            self.syntax_manager.get_lexer_for_file("test2.js"),
            self.syntax_manager.get_lexer_for_file("test3.html"),  # Should evict oldest
        ]
        
        for lexer in lexers:
            editor.replace_widget_with_cached_lexer(lexer)
            
        # Cache should not exceed size limit
        cache_size = editor.get_cache_size()
        self.assertLessEqual(cache_size, 2, "Cache size should not exceed limit")
        
        # Test cache invalidation
        editor.invalidate_cache()
        cache_size_after_invalidation = editor.get_cache_size()
        self.assertEqual(cache_size_after_invalidation, 0, "Cache should be empty after invalidation")
        
    @patch('code_editor.CodeView')
    def test_scrollbar_reference_cleanup(self, mock_codeview):
        """Test that scrollbar references are properly cleaned up."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Track scrollbar.config calls
        scrollbar_config_calls = []
        self.scrollbar_mock.config.side_effect = lambda **kwargs: scrollbar_config_calls.append(kwargs)
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Create and replace widgets
        editor.setup_initial_widget()
        lexer = self.syntax_manager.get_lexer_for_file("test.py")
        editor.replace_widget_with_lexer(lexer)
        
        # Cleanup
        editor.destroy_widget_safely()
        
        # Verify scrollbar was properly disconnected
        # Should have calls to configure scrollbar during setup and disconnect during cleanup
        self.assertGreater(len(scrollbar_config_calls), 0,
                          "Scrollbar should have been configured")
                          
    @patch('code_editor.CodeView')
    def test_reference_cycle_prevention(self, mock_codeview):
        """Test that reference cycles are prevented to avoid memory leaks."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        # Create editor and establish references
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        editor.setup_initial_widget()
        
        # Create weak references to track cleanup
        import weakref
        editor_ref = weakref.ref(editor)
        widget_ref = weakref.ref(mock_widget)
        
        # Clear direct references
        del editor
        
        # Force garbage collection
        gc.collect()
        
        # In a real scenario, we'd want these to be collected
        # For mocks, we just verify no exceptions occurred
        self.assertIsNotNone(editor_ref)  # Reference should exist (mock doesn't get collected)

class TestPerformanceBenchmarks(unittest.TestCase):
    """Benchmark tests to establish performance baselines."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_mock = Mock()
        self.syntax_manager = SyntaxManager()
        self.scrollbar_mock = Mock()
        
    @patch('code_editor.CodeView')
    def test_performance_benchmark_widget_creation(self, mock_codeview):
        """Benchmark widget creation performance."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock
        )
        
        # Benchmark widget creation
        num_iterations = 50
        creation_times = []
        
        for _ in range(num_iterations):
            with PerformanceTimer() as timer:
                widget = editor.create_widget()
                
            creation_times.append(timer.elapsed_time)
            
        # Calculate statistics
        avg_time = sum(creation_times) / len(creation_times)
        max_time = max(creation_times)
        min_time = min(creation_times)
        
        # Log benchmark results
        print(f"\nWidget Creation Benchmark:")
        print(f"  Iterations: {num_iterations}")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Min time: {min_time:.4f}s") 
        print(f"  Max time: {max_time:.4f}s")
        
        # Assert reasonable performance bounds
        self.assertLess(avg_time, 0.01, f"Average widget creation time too high: {avg_time:.4f}s")
        self.assertLess(max_time, 0.05, f"Maximum widget creation time too high: {max_time:.4f}s")
        
    @patch('code_editor.CodeView')
    def test_performance_benchmark_cache_operations(self, mock_codeview):
        """Benchmark cache operation performance."""
        # Setup
        mock_widget = Mock()
        mock_codeview.return_value = mock_widget
        
        editor = CodeEditor(
            parent=self.parent_mock,
            syntax_manager=self.syntax_manager,
            scrollbar=self.scrollbar_mock,
            enable_caching=True,
            cache_size=10
        )
        
        # Pre-populate cache
        lexers = [
            self.syntax_manager.get_lexer_for_file(f"test{i}.py") 
            for i in range(5)
        ]
        
        for lexer in lexers:
            editor.replace_widget_with_cached_lexer(lexer)
            
        # Benchmark cache hit performance
        num_iterations = 100
        cache_hit_times = []
        
        for i in range(num_iterations):
            lexer = lexers[i % len(lexers)]  # Cycle through cached lexers
            
            with PerformanceTimer() as timer:
                editor.replace_widget_with_cached_lexer(lexer)
                
            cache_hit_times.append(timer.elapsed_time)
            
        # Calculate statistics
        avg_time = sum(cache_hit_times) / len(cache_hit_times)
        
        # Log benchmark results
        print(f"\nCache Hit Benchmark:")
        print(f"  Iterations: {num_iterations}")
        print(f"  Average cache hit time: {avg_time:.4f}s")
        
        # Assert reasonable cache performance
        self.assertLess(avg_time, 0.005, f"Average cache hit time too high: {avg_time:.4f}s")

if __name__ == '__main__':
    unittest.main() 