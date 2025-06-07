"""
Test suite for file size limits and warnings for very large files.

This module tests the file size limit functionality that warns users about
extremely large files and optionally prevents loading them based on size thresholds.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from io import StringIO

from src.code_editor import CodeEditor
from src.syntax_manager import SyntaxManager


@patch('src.code_editor.CodeView')
class TestFileSizeLimits(unittest.TestCase):
    """Test file size limits and warnings for very large files."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_parent = Mock()
        self.mock_scrollbar = Mock()
        self.mock_scrollbar.get.return_value = (0.0, 1.0)
        
        # Create a proper syntax manager instance
        self.syntax_manager = SyntaxManager()
        
        self.editor = CodeEditor(self.mock_parent, self.syntax_manager, scrollbar=self.mock_scrollbar)
        
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

    def generate_test_content(self, size_mb):
        """Generate test content of specified size in MB."""
        # Generate content with realistic structure
        base_content = "# This is a test file\n" + "x" * 1000 + "\n"
        target_size = size_mb * 1024 * 1024
        content_size = len(base_content.encode('utf-8'))
        repetitions = max(1, target_size // content_size)
        return base_content * repetitions

    def test_file_size_check_for_small_files(self, mock_codeview):
        """Test that small files pass size checks without warnings."""
        self._setup_mock_widget(mock_codeview)
        
        # Create a small test file (1KB)
        small_content = "Small file content" * 50  # ~1KB
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(small_content)
            temp_file = f.name
        
        try:
            # Check file size - should pass without warnings
            is_too_large, file_size, warning_message = self.editor.check_file_size_limits(temp_file)
            
            self.assertFalse(is_too_large, "Small file should not be flagged as too large")
            self.assertIsInstance(file_size, (int, float), "File size should be numeric")
            self.assertIsNone(warning_message, "Small file should not generate warnings")
            
        finally:
            os.unlink(temp_file)

    def test_file_size_check_for_medium_files(self, mock_codeview):
        """Test that medium files (5-10MB) generate warnings but are allowed."""
        self._setup_mock_widget(mock_codeview)
        
        # Test with content around 7MB
        medium_content = self.generate_test_content(7)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(medium_content)
            temp_file = f.name
        
        try:
            # Check file size - should generate warning but allow loading
            is_too_large, file_size, warning_message = self.editor.check_file_size_limits(temp_file)
            
            self.assertFalse(is_too_large, "Medium file should be allowed with warning")
            self.assertGreater(file_size, 5 * 1024 * 1024, "File size should be >5MB")
            self.assertIsNotNone(warning_message, "Medium file should generate warning message")
            self.assertIn("large", warning_message.lower(), "Warning should mention file is large")
            
        finally:
            os.unlink(temp_file)

    def test_file_size_check_for_large_files(self, mock_codeview):
        """Test that very large files (>10MB) are blocked by default."""
        self._setup_mock_widget(mock_codeview)
        
        # Test with content around 15MB
        large_content = self.generate_test_content(15)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(large_content)
            temp_file = f.name
        
        try:
            # Check file size - should be blocked
            is_too_large, file_size, warning_message = self.editor.check_file_size_limits(temp_file)
            
            self.assertTrue(is_too_large, "Very large file should be blocked")
            self.assertGreater(file_size, 10 * 1024 * 1024, "File size should be >10MB")
            self.assertIsNotNone(warning_message, "Large file should generate warning message")
            self.assertIn("too large", warning_message.lower(), "Warning should mention file is too large")
            
        finally:
            os.unlink(temp_file)

    def test_configurable_size_limits(self, mock_codeview):
        """Test that file size limits can be configured."""
        self._setup_mock_widget(mock_codeview)
        
        # Test with custom limits
        custom_warning_limit = 2 * 1024 * 1024  # 2MB warning
        custom_block_limit = 5 * 1024 * 1024    # 5MB block
        
        # Generate 3MB content
        medium_content = self.generate_test_content(3)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(medium_content)
            temp_file = f.name
        
        try:
            # Check with custom limits
            is_too_large, file_size, warning_message = self.editor.check_file_size_limits(
                temp_file, 
                warning_threshold=custom_warning_limit,
                block_threshold=custom_block_limit
            )
            
            self.assertFalse(is_too_large, "3MB file should be allowed with 5MB limit")
            self.assertIsNotNone(warning_message, "3MB file should generate warning with 2MB threshold")
            
        finally:
            os.unlink(temp_file)

    def test_size_limit_with_load_file_integration(self, mock_codeview):
        """Test that size limits are enforced when loading files."""
        self._setup_mock_widget(mock_codeview)
        
        # Create a large file that should be blocked
        large_content = self.generate_test_content(12)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(large_content)
            temp_file = f.name
        
        try:
            # Attempt to load large file
            success = self.editor.load_file(temp_file)
            
            # Should fail due to size limits
            self.assertFalse(success, "Large file should be rejected during load")
            
        finally:
            os.unlink(temp_file)

    def test_size_limit_with_user_override(self, mock_codeview):
        """Test that users can override size limits when explicitly requested."""
        self._setup_mock_widget(mock_codeview)
        
        # Create a large file
        large_content = self.generate_test_content(12)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(large_content)
            temp_file = f.name
        
        try:
            # Load file with override flag
            success = self.editor.load_file(temp_file, force_load=True)
            
            # Should succeed with override
            self.assertTrue(success, "Large file should load with force_load=True")
            
        finally:
            os.unlink(temp_file)

    def test_size_warning_message_formatting(self, mock_codeview):
        """Test that size warning messages are properly formatted."""
        self._setup_mock_widget(mock_codeview)
        
        # Test with 8MB file
        content = self.generate_test_content(8)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            is_too_large, file_size, warning_message = self.editor.check_file_size_limits(temp_file)
            
            # Verify message formatting
            self.assertIsNotNone(warning_message, "Should have warning message")
            self.assertIn("MB", warning_message, "Message should include size in MB")
            self.assertIn(os.path.basename(temp_file), warning_message, "Message should include filename")
            
            # Test that size is reasonably formatted
            formatted_size = self.editor.format_file_size(file_size)
            self.assertIn("MB", formatted_size, "Formatted size should include MB unit")
            self.assertTrue(formatted_size.startswith("8"), "Should show approximately 8MB")
            
        finally:
            os.unlink(temp_file)

    def test_size_check_with_nonexistent_file(self, mock_codeview):
        """Test size check behavior with non-existent files."""
        self._setup_mock_widget(mock_codeview)
        
        # Test with non-existent file
        nonexistent_file = "/path/that/does/not/exist.py"
        
        is_too_large, file_size, warning_message = self.editor.check_file_size_limits(nonexistent_file)
        
        # Should handle gracefully
        self.assertFalse(is_too_large, "Non-existent file should not be flagged as too large")
        self.assertEqual(file_size, 0, "Non-existent file should have 0 size")
        self.assertIsNone(warning_message, "Non-existent file should not generate warnings")

    def test_size_check_with_permission_errors(self, mock_codeview):
        """Test size check behavior with permission errors."""
        self._setup_mock_widget(mock_codeview)
        
        # Mock os.path.getsize to raise PermissionError
        with patch('os.path.getsize') as mock_getsize:
            mock_getsize.side_effect = PermissionError("Permission denied")
            
            is_too_large, file_size, warning_message = self.editor.check_file_size_limits("some_file.py")
            
            # Should handle gracefully
            self.assertFalse(is_too_large, "Permission error should not flag file as too large")
            self.assertEqual(file_size, 0, "Permission error should result in 0 size")
            self.assertIsNone(warning_message, "Permission error should not generate warnings")

    def test_size_formatting_accuracy(self, mock_codeview):
        """Test that file size formatting is accurate and readable."""
        self._setup_mock_widget(mock_codeview)
        
        # Test various file sizes
        test_sizes = [
            (1024, "1.0 KB"),
            (1024 * 1024, "1.0 MB"),
            (1024 * 1024 * 1024, "1.0 GB"),
            (1536, "1.5 KB"),
            (1572864, "1.5 MB"),  # 1.5 * 1024 * 1024
            (5242880, "5.0 MB"),  # 5 * 1024 * 1024
        ]
        
        for size_bytes, expected_format in test_sizes:
            formatted = self.editor.format_file_size(size_bytes)
            
            # Extract the numeric part and unit
            parts = formatted.split()
            self.assertEqual(len(parts), 2, f"Formatted size should have number and unit: {formatted}")
            
            number_part = float(parts[0])
            unit_part = parts[1]
            
            expected_parts = expected_format.split()
            expected_number = float(expected_parts[0])
            expected_unit = expected_parts[1]
            
            self.assertAlmostEqual(number_part, expected_number, places=1, 
                                 msg=f"Size formatting mismatch for {size_bytes} bytes")
            self.assertEqual(unit_part, expected_unit, 
                           f"Unit mismatch for {size_bytes} bytes")

    def test_memory_usage_with_size_checks(self, mock_codeview):
        """Test that size checking doesn't consume excessive memory."""
        self._setup_mock_widget(mock_codeview)
        
        # Create a reasonably large file for testing
        content = self.generate_test_content(5)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform multiple size checks
            for _ in range(10):
                is_too_large, file_size, warning_message = self.editor.check_file_size_limits(temp_file)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be minimal for size checking
            self.assertLess(memory_increase, 2, "Size checking should not consume significant memory")
            
        finally:
            os.unlink(temp_file)

    def test_size_limit_edge_cases(self, mock_codeview):
        """Test edge cases for file size limits."""
        self._setup_mock_widget(mock_codeview)
        
        # Test with empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_file = f.name  # Empty file
        
        try:
            is_too_large, file_size, warning_message = self.editor.check_file_size_limits(temp_file)
            
            self.assertFalse(is_too_large, "Empty file should not be flagged as too large")
            self.assertEqual(file_size, 0, "Empty file should have 0 size")
            self.assertIsNone(warning_message, "Empty file should not generate warnings")
            
        finally:
            os.unlink(temp_file)

    def test_load_file_with_size_warnings_callback(self, mock_codeview):
        """Test that load_file can accept a callback for handling size warnings."""
        self._setup_mock_widget(mock_codeview)
        
        # Create medium-sized file that triggers warning
        content = self.generate_test_content(7)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            # Mock warning callback
            warning_callback = Mock()
            warning_callback.return_value = True  # User chooses to proceed
            
            success = self.editor.load_file(temp_file, size_warning_callback=warning_callback)
            
            # Should succeed with user approval
            self.assertTrue(success, "File should load when user approves warning")
            warning_callback.assert_called_once()
            
            # Test with user rejection
            warning_callback.reset_mock()
            warning_callback.return_value = False  # User chooses to cancel
            
            success = self.editor.load_file(temp_file, size_warning_callback=warning_callback)
            
            # Should fail when user rejects
            self.assertFalse(success, "File should not load when user rejects warning")
            warning_callback.assert_called_once()
            
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main() 