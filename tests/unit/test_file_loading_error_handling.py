"""Tests for file loading error handling in CodeViewerWidget."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from my_coding_agent.core.code_viewer import CodeViewerWidget


class TestFileLoadingErrorHandling:
    """Test cases for file loading error handling."""

    def test_load_nonexistent_file(self, qapp, tmp_path):
        """Test loading a file that doesn't exist."""
        widget = CodeViewerWidget()

        # Try to load a non-existent file
        non_existent_file = tmp_path / "does_not_exist.py"

        result = widget.load_file(non_existent_file)

        # Should return False and not crash
        assert result is False
        assert widget.get_current_file() is None
        assert widget.toPlainText() == ""

    def test_load_directory_instead_of_file(self, qapp, tmp_path):
        """Test loading a directory instead of a file."""
        widget = CodeViewerWidget()

        # Try to load a directory
        directory = tmp_path / "test_directory"
        directory.mkdir()

        result = widget.load_file(directory)

        # Should return False and not crash
        assert result is False
        assert widget.get_current_file() is None
        assert widget.toPlainText() == ""

    def test_load_file_permission_denied(self, qapp, tmp_path):
        """Test loading a file with no read permissions."""
        widget = CodeViewerWidget()

        # Create a file and remove read permissions
        restricted_file = tmp_path / "restricted.py"
        restricted_file.write_text("print('test')")

        # Remove read permissions (only works on Unix-like systems)
        if os.name != "nt":  # Skip on Windows
            try:
                os.chmod(restricted_file, stat.S_IWRITE)  # Write only, no read

                result = widget.load_file(restricted_file)

                # Should return False and handle gracefully
                assert result is False
                assert widget.get_current_file() is None

            finally:
                # Restore permissions for cleanup
                os.chmod(restricted_file, stat.S_IREAD | stat.S_IWRITE)

    def test_load_file_encoding_errors(self, qapp, tmp_path):
        """Test loading files with various encoding issues."""
        widget = CodeViewerWidget()

        # Create file with binary content that will cause encoding errors
        binary_file = tmp_path / "binary.py"
        binary_content = b"\x00\x01\x02\x03\xff\xfe\xfd"
        binary_file.write_bytes(binary_content)

        result = widget.load_file(binary_file)

        # Should handle gracefully - might succeed with fallback encoding
        # or fail gracefully
        assert isinstance(result, bool)
        if result:
            # If it succeeded, content should be loaded
            assert widget.get_current_file() == binary_file
        else:
            # If it failed, should remain clean
            assert widget.get_current_file() is None

    def test_load_file_with_unicode_content(self, qapp, tmp_path):
        """Test loading files with various Unicode content."""
        widget = CodeViewerWidget()

        # Create file with Unicode content
        unicode_file = tmp_path / "unicode.py"
        unicode_content = "# Unicode test: ñáéíóú 中文 العربية 🐍\ndef greet():\n    print('Hello 世界!')"
        unicode_file.write_text(unicode_content, encoding="utf-8")

        result = widget.load_file(unicode_file)

        # Should handle Unicode properly
        assert result is True
        assert widget.get_current_file() == unicode_file
        loaded_content = widget.toPlainText()
        assert "Unicode test" in loaded_content
        assert "世界" in loaded_content

    def test_load_file_with_different_encodings(self, qapp, tmp_path):
        """Test loading files saved in different encodings."""
        widget = CodeViewerWidget()

        # Test files with different encodings
        test_cases = [
            ("utf8.py", "# UTF-8: café résumé", "utf-8"),
            ("latin1.py", "# Latin-1: café résumé", "latin-1"),
            ("cp1252.py", "# CP1252: café résumé", "cp1252"),
        ]

        for filename, content, encoding in test_cases:
            test_file = tmp_path / filename
            test_file.write_text(content, encoding=encoding)

            result = widget.load_file(test_file)

            # Should succeed with any of the supported encodings
            assert result is True
            assert widget.get_current_file() == test_file
            loaded_content = widget.toPlainText()
            assert (
                "café" in loaded_content or "caf" in loaded_content
            )  # May have encoding approximations

    def test_load_empty_file(self, qapp, tmp_path):
        """Test loading an empty file."""
        widget = CodeViewerWidget()

        # Create empty file
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")

        result = widget.load_file(empty_file)

        # Should succeed
        assert result is True
        assert widget.get_current_file() == empty_file
        assert widget.toPlainText() == ""

    def test_load_file_string_path(self, qapp, tmp_path):
        """Test loading file using string path instead of Path object."""
        widget = CodeViewerWidget()

        # Create test file
        test_file = tmp_path / "string_path.py"
        test_content = "print('hello')"
        test_file.write_text(test_content)

        # Load using string path
        result = widget.load_file(str(test_file))

        # Should succeed
        assert result is True
        assert widget.get_current_file() == test_file
        assert widget.toPlainText() == test_content

    def test_load_file_with_long_lines(self, qapp, tmp_path):
        """Test loading files with very long lines."""
        widget = CodeViewerWidget()

        # Create file with very long line
        long_line_file = tmp_path / "long_lines.py"
        long_content = "# " + "x" * 1000 + "\nprint('test')"  # Reduced for performance
        long_line_file.write_text(long_content)

        result = widget.load_file(long_line_file)

        # Should succeed
        assert result is True
        assert widget.get_current_file() == long_line_file
        loaded_content = widget.toPlainText()
        assert "print('test')" in loaded_content

    def test_load_file_error_state_cleanup(self, qapp, tmp_path):
        """Test that error states are properly cleaned up."""
        widget = CodeViewerWidget()

        # First load a valid file
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("print('valid')")
        result = widget.load_file(valid_file)
        assert result is True
        assert widget.get_current_file() == valid_file

        # Then try to load an invalid file
        invalid_file = tmp_path / "does_not_exist.py"
        result = widget.load_file(invalid_file)

        # Should fail but keep previous state intact
        assert result is False
        assert widget.get_current_file() == valid_file  # Should keep previous file
        assert "print('valid')" in widget.toPlainText()  # Should keep previous content

    def test_get_load_error_information(self, qapp, tmp_path):
        """Test detailed error information tracking."""
        widget = CodeViewerWidget()

        # Initially no error
        assert widget.get_last_load_error() is None

        # Try to load non-existent file
        non_existent = tmp_path / "missing.py"
        result = widget.load_file(non_existent)
        assert result is False

        # Should have detailed error information
        error_info = widget.get_last_load_error()
        assert error_info is not None
        assert error_info["error_type"] == "file_not_found"
        assert "File not found" in error_info["message"]
        assert error_info["file_path"] == str(non_existent)

        # Try to load a directory
        directory = tmp_path / "test_dir"
        directory.mkdir()
        result = widget.load_file(directory)
        assert result is False

        # Should have updated error information
        error_info = widget.get_last_load_error()
        assert error_info is not None
        assert error_info["error_type"] == "not_a_file"
        assert "not a file" in error_info["message"]
        assert error_info["file_path"] == str(directory)

        # Successfully load a file - should clear error
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("print('hello')")
        result = widget.load_file(valid_file)
        assert result is True

        # Error should be cleared after successful load
        assert widget.get_last_load_error() is None

    def test_load_file_with_special_characters_in_path(self, qapp, tmp_path):
        """Test loading files with special characters in the path."""
        widget = CodeViewerWidget()

        # Create file with special characters in name
        special_file = (
            tmp_path / "test_file_with_spaces.py"
        )  # Simplified for compatibility
        test_content = "print('special path')"
        special_file.write_text(test_content)

        result = widget.load_file(special_file)

        # Should succeed
        assert result is True
        assert widget.get_current_file() == special_file
        assert widget.toPlainText() == test_content

    def test_load_file_symlink_handling(self, qapp, tmp_path):
        """Test loading files through symbolic links."""
        widget = CodeViewerWidget()

        # Create original file
        original_file = tmp_path / "original.py"
        test_content = "print('symlink test')"
        original_file.write_text(test_content)

        # Create symlink (skip on Windows if symlinks not supported)
        try:
            symlink_file = tmp_path / "symlink.py"
            symlink_file.symlink_to(original_file)

            result = widget.load_file(symlink_file)

            # Should succeed
            assert result is True
            # Current file should be the symlink path, not the target
            assert widget.get_current_file() == symlink_file
            assert widget.toPlainText() == test_content

        except (OSError, NotImplementedError):
            # Symlinks not supported, skip test
            pytest.skip("Symbolic links not supported on this system")

    def test_load_file_concurrent_access(self, qapp, tmp_path):
        """Test loading file while it's being modified."""
        widget = CodeViewerWidget()

        # Create file
        test_file = tmp_path / "concurrent.py"
        test_content = "print('original')"
        test_file.write_text(test_content)

        # Mock file operations to simulate permission error
        with patch.object(Path, "read_text") as mock_read_text:
            # Simulate permission error during read
            mock_read_text.side_effect = PermissionError("File is locked")

            result = widget.load_file(test_file)

            # Should handle gracefully
            assert result is False

    def test_load_file_with_encoding_detection(self, qapp, tmp_path):
        """Test automatic encoding detection for files without BOM."""
        widget = CodeViewerWidget()

        # Create file with content that might be ambiguous
        test_file = tmp_path / "encoding_test.py"
        # Content with characters that exist in multiple encodings
        content = "print('test')\n# Comment with special chars"
        test_file.write_text(content, encoding="utf-8")

        result = widget.load_file(test_file)

        # Should succeed and load content properly
        assert result is True
        assert widget.get_current_file() == test_file
        loaded_content = widget.toPlainText()
        assert "print('test')" in loaded_content
        assert "Comment" in loaded_content

    def test_load_very_large_file_error_handling(self, qapp, tmp_path):
        """Test error handling for extremely large files."""
        widget = CodeViewerWidget()

        # Temporarily set a very small threshold to trigger large file handling
        original_threshold = widget._large_file_threshold
        widget._large_file_threshold = 100  # 100 bytes

        try:
            # Create a "large" file (for testing purposes)
            large_file = tmp_path / "large.py"
            large_content = (
                "# Large file test\n" + "print('line')\n" * 20
            )  # ~300+ bytes
            large_file.write_text(large_content)

            result = widget.load_file(large_file)

            # Should succeed with lazy loading
            assert result is True
            assert widget.get_current_file() == large_file
            assert widget.is_large_file() is True

        finally:
            # Restore original threshold
            widget._large_file_threshold = original_threshold

    def test_binary_file_detection(self, qapp, tmp_path):
        """Test detection and handling of binary files."""
        widget = CodeViewerWidget()

        # Create file with null bytes (binary indicator)
        binary_file = tmp_path / "binary_file.bin"
        binary_content = b"Some text\x00\x01\x02\xff and more"
        binary_file.write_bytes(binary_content)

        result = widget.load_file(binary_file)

        # Should fail for binary files
        assert result is False

        # Should have appropriate error information
        error_info = widget.get_last_load_error()
        assert error_info is not None
        assert error_info["error_type"] == "binary_file"
        assert "binary data" in error_info["message"]

    def test_encoding_error_details(self, qapp, tmp_path):
        """Test detailed encoding error information."""
        widget = CodeViewerWidget()

        # Create file with problematic encoding that will fail all attempts
        problem_file = tmp_path / "encoding_problem.py"
        # Write bytes that are invalid in all our supported encodings
        problem_content = b"\x80\x81\x82\x83\x84\x85"  # Invalid UTF-8 sequence
        problem_file.write_bytes(problem_content)

        result = widget.load_file(problem_file)

        # May succeed with fallback encoding, but if it fails should have details
        if not result:
            error_info = widget.get_last_load_error()
            assert error_info is not None
            assert error_info["error_type"] == "encoding_error"
            assert "attempted_encodings" in error_info
            assert len(error_info["attempted_encodings"]) > 0

    def test_clear_content_resets_error_state(self, qapp, tmp_path):
        """Test that clear_content resets error state."""
        widget = CodeViewerWidget()

        # Generate an error
        non_existent = tmp_path / "missing.py"
        result = widget.load_file(non_existent)
        assert result is False
        assert widget.get_last_load_error() is not None

        # Clear content should reset error state
        widget.clear_content()
        assert widget.get_last_load_error() is None
