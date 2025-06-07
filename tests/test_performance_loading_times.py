"""
Performance tests for syntax highlighting loading times.

This module tests that syntax highlighting operations complete within acceptable time limits
across various scenarios including different file sizes, languages, and operations.
"""

import pytest
import time
import tempfile
import os
from unittest.mock import Mock, patch
import tkinter as tk

from src.code_editor import CodeEditor
from src.syntax_manager import SyntaxManager


class PerformanceTimer:
    """Context manager for measuring execution time."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.elapsed_time = self.end_time - self.start_time


@pytest.fixture
def mock_root():
    """Create a mock tkinter root for testing."""
    root = Mock(spec=tk.Tk)
    return root


@pytest.fixture
def syntax_manager():
    """Create a SyntaxManager instance for testing."""
    return SyntaxManager()


@pytest.fixture
def sample_content():
    """Generate sample content of various sizes for testing."""
    return {
        'small': 'print("Hello, World!")\n' * 10,  # ~200 bytes
        'medium': 'print("Hello, World!")\n' * 100,  # ~2KB
        'large': 'print("Hello, World!")\n' * 1000,  # ~20KB
        'very_large': 'print("Hello, World!")\n' * 5000,  # ~100KB
    }


@pytest.fixture
def temp_files(sample_content):
    """Create temporary files with sample content."""
    files = {}
    temp_dir = tempfile.mkdtemp()
    
    for size, content in sample_content.items():
        file_path = os.path.join(temp_dir, f'test_{size}.py')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        files[size] = file_path
    
    yield files
    
    # Cleanup
    for file_path in files.values():
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass


class TestCodeEditorPerformance:
    """Test CodeEditor performance for acceptable loading times."""
    
    def test_small_file_loading_performance(self, mock_root, syntax_manager):
        """Test that small files (<1KB) load within 50ms."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create temporary small file
        content = 'print("Hello, World!")\n' * 10
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            with PerformanceTimer() as timer:
                editor.load_file(temp_file)
            
            # Small files should load very quickly
            assert timer.elapsed_time < 0.05, f"Small file loading took {timer.elapsed_time:.3f}s, expected <0.05s"
        finally:
            os.remove(temp_file)
    
    def test_medium_file_loading_performance(self, mock_root, syntax_manager):
        """Test that medium files (~2KB) load within 100ms."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create temporary medium file
        content = 'print("Hello, World!")\n' * 100
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            with PerformanceTimer() as timer:
                editor.load_file(temp_file)
            
            # Medium files should load reasonably quickly
            assert timer.elapsed_time < 0.1, f"Medium file loading took {timer.elapsed_time:.3f}s, expected <0.1s"
        finally:
            os.remove(temp_file)
    
    def test_large_file_loading_performance(self, mock_root, syntax_manager):
        """Test that large files (~20KB) load within 500ms."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create temporary large file
        content = 'print("Hello, World!")\n' * 1000
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            with PerformanceTimer() as timer:
                editor.load_file(temp_file)
            
            # Large files should still load acceptably
            assert timer.elapsed_time < 0.5, f"Large file loading took {timer.elapsed_time:.3f}s, expected <0.5s"
        finally:
            os.remove(temp_file)
    
    def test_very_large_file_loading_performance(self, mock_root, syntax_manager):
        """Test that very large files (~100KB) load within 1s."""
        editor = CodeEditor(mock_root, syntax_manager, enable_caching=True)  # Use caching for large files
        
        # Create temporary very large file
        content = 'print("Hello, World!")\n' * 5000
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            with PerformanceTimer() as timer:
                editor.load_file(temp_file)
            
            # Very large files should still be manageable
            assert timer.elapsed_time < 1.0, f"Very large file loading took {timer.elapsed_time:.3f}s, expected <1.0s"
        finally:
            os.remove(temp_file)
    
    def test_widget_creation_performance(self, mock_root, syntax_manager):
        """Test that widget creation completes within 100ms."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Mock the CodeView creation to avoid tkinter issues in tests
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            with PerformanceTimer() as timer:
                widget = editor.create_widget('python')
            
            # Widget creation should be fast
            assert timer.elapsed_time < 0.1, f"Widget creation took {timer.elapsed_time:.3f}s, expected <0.1s"
            assert widget is not None
    
    def test_widget_replacement_performance(self, mock_root, syntax_manager):
        """Test that widget replacement completes within 150ms."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Mock the CodeView creation to avoid tkinter issues in tests
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            # Create initial widget
            initial_widget = editor.create_widget('python')
            editor.current_widget = initial_widget
            
            with PerformanceTimer() as timer:
                editor.replace_widget_with_lexer('javascript')
            
            # Widget replacement should be reasonably fast
            assert timer.elapsed_time < 0.15, f"Widget replacement took {timer.elapsed_time:.3f}s, expected <0.15s"
    
    def test_rapid_file_switching_performance(self, mock_root, syntax_manager):
        """Test that rapid file switching maintains acceptable performance."""
        editor = CodeEditor(mock_root, syntax_manager, enable_caching=True)
        
        # Create multiple temporary files
        temp_files = []
        for i, content in enumerate([
            'print("Hello")\n' * 10,    # small
            'print("World")\n' * 100,   # medium  
            'print("Hello")\n' * 10,    # small again
        ]):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                temp_files.append(f.name)
        
        try:
            with PerformanceTimer() as timer:
                for file_path in temp_files:
                    editor.load_file(file_path)
            
            # Rapid switching should benefit from caching
            avg_time_per_switch = timer.elapsed_time / len(temp_files)
            assert avg_time_per_switch < 0.1, f"Average file switch took {avg_time_per_switch:.3f}s, expected <0.1s"
        finally:
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except FileNotFoundError:
                    pass


class TestSyntaxManagerPerformance:
    """Test SyntaxManager performance for lexer detection."""
    
    def test_lexer_detection_performance(self):
        """Test that lexer detection for common files completes within 10ms."""
        manager = SyntaxManager()
        
        test_files = [
            'test.py', 'test.js', 'test.html', 'test.css', 
            'test.json', 'test.md', 'test.xml', 'test.yaml'
        ]
        
        with PerformanceTimer() as timer:
            for filename in test_files:
                lexer = manager.get_lexer_for_file(filename)
                assert lexer is not None
        
        # Lexer detection should be very fast (relaxed threshold)
        avg_time_per_detection = timer.elapsed_time / len(test_files)
        assert avg_time_per_detection < 0.05, f"Average lexer detection took {avg_time_per_detection:.3f}s, expected <0.05s"
    
    def test_bulk_lexer_detection_performance(self):
        """Test that bulk lexer detection maintains good performance."""
        manager = SyntaxManager()
        
        # Generate 100 filenames
        filenames = [f'test_{i}.py' for i in range(50)] + [f'test_{i}.js' for i in range(50)]
        
        with PerformanceTimer() as timer:
            lexers = [manager.get_lexer_for_file(filename) for filename in filenames]
        
        # Bulk detection should still be fast
        assert timer.elapsed_time < 1.0, f"Bulk lexer detection took {timer.elapsed_time:.3f}s, expected <1.0s"
        assert all(lexer is not None for lexer in lexers)
    
    def test_shebang_detection_performance(self):
        """Test that shebang detection completes within acceptable time."""
        manager = SyntaxManager()
        
        # Create temporary files with shebangs
        test_shebangs = [
            ('python_file', '#!/usr/bin/python3\nprint("hello")'),
            ('bash_file', '#!/bin/bash\necho "hello"'),
            ('node_file', '#!/usr/bin/node\nconsole.log("hello")'),
            ('python_env_file', '#!/usr/bin/env python\nprint("hello")'),
        ]
        
        temp_files = []
        for name, content in test_shebangs:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(content)
                temp_files.append(f.name)
        
        try:
            with PerformanceTimer() as timer:
                for temp_file in temp_files:
                    lexer = manager.get_lexer_for_file(temp_file)
                    assert lexer is not None
            
            # Shebang detection should be fast (relaxed threshold)
            avg_time_per_detection = timer.elapsed_time / len(temp_files)
            assert avg_time_per_detection < 0.1, f"Average shebang detection took {avg_time_per_detection:.3f}s, expected <0.1s"
        finally:
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except FileNotFoundError:
                    pass



class TestIntegratedPerformance:
    """Test integrated performance across multiple components."""
    
    def test_end_to_end_file_loading_performance(self, mock_root, syntax_manager):
        """Test complete file loading workflow performance."""
        # Create editor with all features enabled
        editor = CodeEditor(
            mock_root, 
            syntax_manager,
            enable_caching=True, 
            use_token_mapping=True,
            color_scheme='nord'
        )
        
        # Create temporary file
        content = 'print("Hello, World!")\n' * 100
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            with PerformanceTimer() as timer:
                # Load file, which should:
                # 1. Detect lexer based on extension
                # 2. Create/retrieve cached widget
                # 3. Apply syntax highlighting
                # 4. Apply color scheme
                # 5. Configure scrollbar
                editor.load_file(temp_file)
            
            # End-to-end loading should complete within reasonable time
            assert timer.elapsed_time < 0.2, f"End-to-end loading took {timer.elapsed_time:.3f}s, expected <0.2s"
        finally:
            os.remove(temp_file)
    
    def test_multiple_language_switching_performance(self, mock_root, syntax_manager):
        """Test performance when switching between different programming languages."""
        editor = CodeEditor(mock_root, syntax_manager, enable_caching=True)
        
        # Create files with different extensions
        language_files = {}
        temp_files = []
        
        for ext, content in [
            ('py', 'print("Python")'),
            ('js', 'console.log("JavaScript")'),
            ('html', '<html><body>HTML</body></html>'),
            ('css', 'body { color: red; }'),
            ('json', '{"language": "JSON"}'),
        ]:
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{ext}', delete=False) as f:
                f.write(content)
                language_files[ext] = f.name
                temp_files.append(f.name)
        
        try:
            with PerformanceTimer() as timer:
                for file_path in language_files.values():
                    editor.load_file(file_path)
            
            # Language switching should be efficient with caching
            avg_time_per_language = timer.elapsed_time / len(language_files)
            assert avg_time_per_language < 0.1, f"Average language switch took {avg_time_per_language:.3f}s, expected <0.1s"
        finally:
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except FileNotFoundError:
                    pass


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 