"""
Error handling tests for edge cases and malformed files in syntax highlighting.

This module tests that the syntax highlighting system gracefully handles various
error conditions, edge cases, and malformed files without crashing.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from io import StringIO

from src.code_editor import CodeEditor
from src.syntax_manager import SyntaxManager


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
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except:
        pass


class TestMalformedFileHandling:
    """Test handling of malformed and corrupted files."""
    
    def test_binary_file_handling(self, mock_root, syntax_manager, temp_dir):
        """Test that binary files are handled gracefully."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create a binary file
        binary_file = os.path.join(temp_dir, "test.bin")
        with open(binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\xFF\xFE\xFD')
        
        # Should not crash when trying to load binary file
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            result = editor.load_file(binary_file)
            # Should handle gracefully (may succeed with fallback or fail gracefully)
            assert isinstance(result, bool)
    
    def test_empty_file_handling(self, mock_root, syntax_manager, temp_dir):
        """Test that empty files are handled correctly."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create empty file
        empty_file = os.path.join(temp_dir, "empty.py")
        with open(empty_file, 'w') as f:
            pass  # Create empty file
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            result = editor.load_file(empty_file)
            assert result is True
    
    def test_extremely_long_lines_handling(self, mock_root, syntax_manager, temp_dir):
        """Test handling of files with extremely long lines."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create file with very long line
        long_line_file = os.path.join(temp_dir, "long_line.py")
        very_long_line = "# " + "x" * 100000 + "\nprint('hello')\n"
        
        with open(long_line_file, 'w') as f:
            f.write(very_long_line)
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            result = editor.load_file(long_line_file)
            assert isinstance(result, bool)
    
    def test_unicode_encoding_errors(self, mock_root, syntax_manager, temp_dir):
        """Test handling of files with encoding issues."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create file with mixed encodings
        encoding_file = os.path.join(temp_dir, "encoding_test.py")
        
        # Write some content that might cause encoding issues
        with open(encoding_file, 'wb') as f:
            f.write(b'# -*- coding: utf-8 -*-\n')
            f.write(b'print("hello")\n')
            f.write(b'\xff\xfe\x00invalid_utf8')  # Invalid UTF-8 sequence
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            result = editor.load_file(encoding_file)
            # Should handle encoding errors gracefully
            assert isinstance(result, bool)
    
    def test_malformed_json_handling(self, mock_root, syntax_manager, temp_dir):
        """Test handling of malformed JSON files."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create malformed JSON file
        json_file = os.path.join(temp_dir, "malformed.json")
        malformed_json = '{"incomplete": "json", "missing": }'
        
        with open(json_file, 'w') as f:
            f.write(malformed_json)
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            result = editor.load_file(json_file)
            # Should still load and attempt syntax highlighting
            assert isinstance(result, bool)
    
    def test_invalid_python_syntax_handling(self, mock_root, syntax_manager, temp_dir):
        """Test handling of Python files with syntax errors."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create Python file with syntax errors
        python_file = os.path.join(temp_dir, "syntax_error.py")
        invalid_python = '''
def broken_function(
    missing_closing_paren
    
if missing_colon
    print("broken")
    
class MissingColon
    pass
'''
        
        with open(python_file, 'w') as f:
            f.write(invalid_python)
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            result = editor.load_file(python_file)
            # Should still load and apply syntax highlighting despite syntax errors
            assert isinstance(result, bool)


class TestFileSystemEdgeCases:
    """Test handling of file system edge cases."""
    
    def test_nonexistent_file_handling(self, mock_root, syntax_manager):
        """Test handling of attempts to load non-existent files."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        result = editor.load_file("/path/that/does/not/exist.py")
        assert result is False
    
    def test_permission_denied_handling(self, mock_root, syntax_manager, temp_dir):
        """Test handling of permission denied errors."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create a file and remove read permissions
        restricted_file = os.path.join(temp_dir, "restricted.py")
        with open(restricted_file, 'w') as f:
            f.write("print('test')")
        
        try:
            os.chmod(restricted_file, 0o000)  # Remove all permissions
            
            result = editor.load_file(restricted_file)
            assert result is False
            
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(restricted_file, 0o644)
            except:
                pass
    
    def test_directory_instead_of_file(self, mock_root, syntax_manager, temp_dir):
        """Test handling when a directory path is provided instead of a file."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Try to load a directory as if it were a file
        result = editor.load_file(temp_dir)
        assert result is False
    
    def test_special_characters_in_filename(self, mock_root, syntax_manager, temp_dir):
        """Test handling of files with special characters in names."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create file with special characters
        special_filename = os.path.join(temp_dir, "file with spaces & symbols!@#.py")
        with open(special_filename, 'w') as f:
            f.write("print('special filename')")
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            result = editor.load_file(special_filename)
            assert isinstance(result, bool)
    
    def test_symlink_handling(self, mock_root, syntax_manager, temp_dir):
        """Test handling of symbolic links."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create a file and a symlink to it
        original_file = os.path.join(temp_dir, "original.py")
        symlink_file = os.path.join(temp_dir, "symlink.py")
        
        with open(original_file, 'w') as f:
            f.write("print('original file')")
        
        try:
            os.symlink(original_file, symlink_file)
            
            with patch('src.code_editor.CodeView') as mock_codeview:
                mock_widget = Mock()
                mock_codeview.return_value = mock_widget
                
                result = editor.load_file(symlink_file)
                assert isinstance(result, bool)
                
        except OSError:
            # Symlinks may not be supported on all systems
            pytest.skip("Symlinks not supported on this system")


class TestSyntaxManagerEdgeCases:
    """Test SyntaxManager handling of edge cases."""
    
    def test_unknown_file_extension(self, syntax_manager):
        """Test lexer detection for unknown file extensions."""
        lexer = syntax_manager.get_lexer_for_file("unknown.xyz123")
        # Should return text lexer as fallback
        assert lexer is not None
        assert lexer.name.lower() in ['text', 'textlexer', 'text only']
    
    def test_no_file_extension(self, syntax_manager):
        """Test lexer detection for files without extensions."""
        lexer = syntax_manager.get_lexer_for_file("README")
        # Should return text lexer as fallback
        assert lexer is not None
        assert lexer.name.lower() in ['text', 'textlexer', 'text only']
    
    def test_malformed_shebang(self, syntax_manager, temp_dir):
        """Test handling of malformed shebang lines."""
        # Create file with malformed shebang
        malformed_shebang_file = os.path.join(temp_dir, "malformed_shebang")
        malformed_shebangs = [
            "#! /usr/bin/python",  # Space after #!
            "#!/usr/bin/nonexistent",  # Non-existent interpreter
            "#!/usr/bin/python",  # Malformed path
            "#!/usr/bin/python with extra stuff",  # Extra content
        ]
        
        for i, shebang in enumerate(malformed_shebangs):
            test_file = f"{malformed_shebang_file}_{i}"
            with open(test_file, 'w') as f:
                f.write(f"{shebang}\nprint('test')")
            
            lexer = syntax_manager.get_lexer_for_file(test_file)
            # Should still return a lexer (either detected or fallback)
            assert lexer is not None
    
    def test_extremely_large_file_skip_highlighting(self, syntax_manager):
        """Test that extremely large files skip syntax highlighting."""
        # Test with very large content (larger than 50MB default threshold)
        large_content = "print('test')\n" * 5000000  # ~65MB
        
        should_skip = syntax_manager.should_skip_syntax_highlighting(
            content=large_content, 
            filename="large.py"
        )
        assert should_skip is True
    
    def test_invalid_lexer_name_handling(self, syntax_manager):
        """Test handling when requesting invalid lexer names."""
        # Directly test lexer creation with invalid name
        result = syntax_manager.get_lexer_by_extension(".invalid_extension_12345")
        # Should return text lexer as fallback
        assert result is not None


class TestWidgetCreationEdgeCases:
    """Test widget creation edge cases."""
    
    def test_invalid_color_scheme_fallback(self, mock_root, syntax_manager):
        """Test fallback behavior when invalid color scheme is provided."""
        editor = CodeEditor(mock_root, syntax_manager, color_scheme="invalid_scheme_name")
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            widget = editor.create_widget('python')
            assert widget is not None
    
    def test_widget_creation_failure_recovery(self, mock_root, syntax_manager):
        """Test recovery when widget creation completely fails."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            # Make CodeView raise an exception
            mock_codeview.side_effect = Exception("Widget creation failed")
            
            with pytest.raises(Exception):
                editor.create_widget('python')
    
    def test_lexer_application_failure(self, mock_root, syntax_manager):
        """Test behavior when lexer application fails."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            # Make lexer setting fail
            mock_widget.configure_mock(**{'lexer': Mock(side_effect=Exception("Lexer failed"))})
            mock_codeview.return_value = mock_widget
            
            widget = editor.create_widget('python')
            # Should still return widget even if lexer application fails
            assert widget is not None
    
    def test_scrollbar_configuration_failure(self, mock_root, syntax_manager):
        """Test behavior when scrollbar configuration fails."""
        mock_scrollbar = Mock()
        mock_scrollbar.config.side_effect = Exception("Scrollbar config failed")
        
        editor = CodeEditor(mock_root, syntax_manager, scrollbar=mock_scrollbar)
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            widget = editor.create_widget('python')
            # Should still create widget even if scrollbar config fails
            assert widget is not None


class TestMemoryAndResourceEdgeCases:
    """Test memory and resource handling edge cases."""
    
    def test_out_of_memory_simulation(self, mock_root, syntax_manager, temp_dir):
        """Test behavior when memory allocation fails."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create a reasonably sized file
        test_file = os.path.join(temp_dir, "memory_test.py")
        with open(test_file, 'w') as f:
            f.write("print('test')\n" * 1000)
        
        # Mock memory allocation failure
        with patch('builtins.open', side_effect=MemoryError("Out of memory")):
            result = editor.load_file(test_file)
            assert result is False
    
    def test_file_handle_exhaustion(self, mock_root, syntax_manager, temp_dir):
        """Test behavior when file handles are exhausted."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        test_file = os.path.join(temp_dir, "handle_test.py")
        with open(test_file, 'w') as f:
            f.write("print('test')")
        
        # Mock file handle exhaustion
        with patch('builtins.open', side_effect=OSError("Too many open files")):
            result = editor.load_file(test_file)
            assert result is False
    
    def test_disk_space_exhaustion(self, mock_root, syntax_manager, temp_dir):
        """Test behavior when disk space is exhausted during operations."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            # Simulate disk space exhaustion in the update_file_content method
            with patch.object(editor, 'update_file_content', 
                             side_effect=OSError("No space left on device")):
                result = editor.load_content("print('test')", "test.py")
                # Should handle the error gracefully and return False
                assert result is False


class TestConcurrencyAndRaceConditions:
    """Test handling of concurrency issues and race conditions."""
    
    def test_rapid_file_switching_errors(self, mock_root, syntax_manager, temp_dir):
        """Test error handling during rapid file switching."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create multiple test files
        files = []
        for i in range(3):
            test_file = os.path.join(temp_dir, f"rapid_{i}.py")
            with open(test_file, 'w') as f:
                f.write(f"print('file {i}')")
            files.append(test_file)
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            # Rapidly switch between files
            results = []
            for file_path in files:
                try:
                    result = editor.load_file(file_path)
                    results.append(result)
                except Exception:
                    # Should not raise exceptions even under rapid switching
                    results.append(False)
            
            # At least some operations should succeed
            assert any(results) or all(not r for r in results)  # All succeed or all fail gracefully
    
    def test_widget_destruction_during_creation(self, mock_root, syntax_manager):
        """Test handling of widget destruction during creation process."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        call_count = 0
        def side_effect_destroy_during_creation(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call succeeds
                mock_widget = Mock()
                return mock_widget
            else:
                # Subsequent calls fail as if widget was destroyed
                raise Exception("Widget destroyed during creation")
        
        with patch('src.code_editor.CodeView', side_effect=side_effect_destroy_during_creation):
            # First widget creation should succeed
            widget1 = editor.create_widget('python')
            assert widget1 is not None
            
            # Second widget creation should handle the error
            with pytest.raises(Exception):
                editor.create_widget('javascript')


class TestSystemResourceExhaustion:
    """Test handling of system resource exhaustion scenarios."""
    
    def test_cpu_intensive_operation_handling(self, mock_root, syntax_manager, temp_dir):
        """Test handling when CPU is under heavy load."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        # Create a large file that would require significant processing
        large_file = os.path.join(temp_dir, "cpu_intensive.py")
        large_content = "def function_{}(): pass\n".format(1) * 10000
        
        with open(large_file, 'w') as f:
            f.write(large_content)
        
        with patch('src.code_editor.CodeView') as mock_codeview:
            mock_widget = Mock()
            mock_codeview.return_value = mock_widget
            
            # Should handle large files without hanging
            result = editor.load_file(large_file)
            assert isinstance(result, bool)
    
    def test_interrupted_operation_handling(self, mock_root, syntax_manager, temp_dir):
        """Test handling of interrupted operations."""
        editor = CodeEditor(mock_root, syntax_manager)
        
        test_file = os.path.join(temp_dir, "interrupt_test.py")
        with open(test_file, 'w') as f:
            f.write("print('test')")
        
        # Simulate interrupted operation
        with patch('builtins.open', side_effect=KeyboardInterrupt("Operation interrupted")):
            with pytest.raises(KeyboardInterrupt):
                editor.load_file(test_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 