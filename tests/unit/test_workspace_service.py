"""
Unit tests for WorkspaceService.

Tests workspace management functionality including:
- Workspace root management and path resolution
- File and directory operations
- Validation methods
- Enhanced operations with retry mechanisms
- Error handling and edge cases
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from src.my_coding_agent.core.ai_services.workspace_service import (
    FileOperationError,
    WorkspaceService,
)


class TestWorkspaceService:
    """Test cases for WorkspaceService."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            yield workspace

    @pytest.fixture
    def service(self):
        """Create WorkspaceService instance for testing."""
        return WorkspaceService()

    @pytest.fixture
    def service_with_workspace(self, temp_workspace):
        """Create WorkspaceService with a temporary workspace."""
        service = WorkspaceService()
        service.set_workspace_root(temp_workspace)
        return service

    def test_initialization(self, service):
        """Test WorkspaceService initialization."""
        assert service.workspace_root is None
        assert service.max_file_size == 10 * 1024 * 1024  # 10MB default
        assert hasattr(service, "logger")

    def test_initialization_with_custom_max_size(self):
        """Test WorkspaceService initialization with custom max file size."""
        custom_size = 5 * 1024 * 1024  # 5MB
        service = WorkspaceService(max_file_size=custom_size)
        assert service.max_file_size == custom_size

    def test_set_workspace_root(self, service, temp_workspace):
        """Test setting workspace root."""
        service.set_workspace_root(temp_workspace)
        assert service.workspace_root == temp_workspace.resolve()

    def test_resolve_workspace_path_no_root_set(self, service):
        """Test resolving path when workspace root is not set."""
        with pytest.raises(ValueError, match="Workspace root not set"):
            service.resolve_workspace_path("test.txt")

    def test_resolve_workspace_path_relative(
        self, service_with_workspace, temp_workspace
    ):
        """Test resolving relative paths within workspace."""
        resolved = service_with_workspace.resolve_workspace_path("test.txt")
        expected = temp_workspace / "test.txt"
        assert resolved == expected.resolve()

    def test_resolve_workspace_path_absolute_within_workspace(
        self, service_with_workspace, temp_workspace
    ):
        """Test resolving absolute paths within workspace."""
        abs_path = temp_workspace / "subdir" / "test.txt"
        resolved = service_with_workspace.resolve_workspace_path(str(abs_path))
        assert resolved == abs_path.resolve()

    def test_resolve_workspace_path_outside_workspace(self, service_with_workspace):
        """Test resolving paths outside workspace raises error."""
        with pytest.raises(ValueError, match="Path is outside workspace"):
            service_with_workspace.resolve_workspace_path("/etc/passwd")

    def test_resolve_workspace_path_parent_traversal(self, service_with_workspace):
        """Test resolving paths with parent directory traversal."""
        with pytest.raises(ValueError, match="Path is outside workspace"):
            service_with_workspace.resolve_workspace_path("../../../etc/passwd")

    def test_read_workspace_file_success(self, service_with_workspace, temp_workspace):
        """Test reading existing file successfully."""
        test_file = temp_workspace / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        content = service_with_workspace.read_workspace_file("test.txt")
        assert content == test_content

    def test_read_workspace_file_not_found(self, service_with_workspace):
        """Test reading non-existent file raises error."""
        with pytest.raises(FileNotFoundError, match="File not found: nonexistent.txt"):
            service_with_workspace.read_workspace_file("nonexistent.txt")

    def test_read_workspace_file_is_directory(
        self, service_with_workspace, temp_workspace
    ):
        """Test reading directory instead of file raises error."""
        test_dir = temp_workspace / "testdir"
        test_dir.mkdir()

        with pytest.raises(ValueError, match="Path is not a file: testdir"):
            service_with_workspace.read_workspace_file("testdir")

    def test_write_workspace_file_success(self, service_with_workspace, temp_workspace):
        """Test writing file successfully."""
        test_content = "Hello, World!"
        service_with_workspace.write_workspace_file("test.txt", test_content)

        test_file = temp_workspace / "test.txt"
        assert test_file.exists()
        assert test_file.read_text() == test_content

    def test_write_workspace_file_create_directories(
        self, service_with_workspace, temp_workspace
    ):
        """Test writing file creates parent directories."""
        test_content = "Hello, World!"
        service_with_workspace.write_workspace_file("subdir/test.txt", test_content)

        test_file = temp_workspace / "subdir" / "test.txt"
        assert test_file.exists()
        assert test_file.read_text() == test_content

    def test_delete_workspace_file_success(
        self, service_with_workspace, temp_workspace
    ):
        """Test deleting file successfully."""
        test_file = temp_workspace / "test.txt"
        test_file.write_text("content")

        assert test_file.exists()
        service_with_workspace.delete_workspace_file("test.txt")
        assert not test_file.exists()

    def test_delete_workspace_file_not_found(self, service_with_workspace):
        """Test deleting non-existent file raises error."""
        with pytest.raises(FileNotFoundError, match="File not found: nonexistent.txt"):
            service_with_workspace.delete_workspace_file("nonexistent.txt")

    def test_delete_workspace_directory_empty(
        self, service_with_workspace, temp_workspace
    ):
        """Test deleting empty directory successfully."""
        test_dir = temp_workspace / "testdir"
        test_dir.mkdir()

        assert test_dir.exists()
        service_with_workspace.delete_workspace_file("testdir")
        assert not test_dir.exists()

    def test_workspace_file_exists_true(self, service_with_workspace, temp_workspace):
        """Test checking existing file returns True."""
        test_file = temp_workspace / "test.txt"
        test_file.write_text("content")

        assert service_with_workspace.workspace_file_exists("test.txt") is True

    def test_workspace_file_exists_false(self, service_with_workspace):
        """Test checking non-existent file returns False."""
        assert service_with_workspace.workspace_file_exists("nonexistent.txt") is False

    def test_list_workspace_directory_success(
        self, service_with_workspace, temp_workspace
    ):
        """Test listing directory contents successfully."""
        # Create test files and directories
        (temp_workspace / "file1.txt").write_text("content1")
        (temp_workspace / "file2.txt").write_text("content2")
        (temp_workspace / "subdir").mkdir()

        contents = service_with_workspace.list_workspace_directory(".")
        assert set(contents) == {"file1.txt", "file2.txt", "subdir"}

    def test_list_workspace_directory_not_found(self, service_with_workspace):
        """Test listing non-existent directory raises error."""
        with pytest.raises(FileNotFoundError, match="Directory not found: nonexistent"):
            service_with_workspace.list_workspace_directory("nonexistent")

    def test_list_workspace_directory_is_file(
        self, service_with_workspace, temp_workspace
    ):
        """Test listing file instead of directory raises error."""
        test_file = temp_workspace / "test.txt"
        test_file.write_text("content")

        with pytest.raises(ValueError, match="Path is not a directory: test.txt"):
            service_with_workspace.list_workspace_directory("test.txt")

    def test_create_workspace_directory_success(
        self, service_with_workspace, temp_workspace
    ):
        """Test creating directory successfully."""
        service_with_workspace.create_workspace_directory("newdir")

        new_dir = temp_workspace / "newdir"
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_workspace_directory_nested(
        self, service_with_workspace, temp_workspace
    ):
        """Test creating nested directories successfully."""
        service_with_workspace.create_workspace_directory("parent/child/grandchild")

        nested_dir = temp_workspace / "parent" / "child" / "grandchild"
        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_validate_file_path_empty(self, service):
        """Test validating empty file path raises error."""
        with pytest.raises(ValueError, match="File path cannot be empty"):
            service.validate_file_path("")

    def test_validate_file_path_invalid_chars(self, service):
        """Test validating file path with invalid characters raises error."""
        invalid_paths = [
            "file<name.txt",
            "file>name.txt",
            "file|name.txt",
            'file"name.txt',
        ]

        for path in invalid_paths:
            with pytest.raises(ValueError, match="Invalid characters in file path"):
                service.validate_file_path(path)

    def test_validate_file_path_too_long(self, service):
        """Test validating overly long file path raises error."""
        long_path = "a" * 256  # Exceeds 255 character limit
        with pytest.raises(ValueError, match="File path too long"):
            service.validate_file_path(long_path)

    def test_validate_file_path_reserved_names(self, service):
        """Test validating reserved file names raises error."""
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]

        for name in reserved_names:
            with pytest.raises(ValueError, match="Reserved file name not allowed"):
                service.validate_file_path(name)

    def test_validate_file_extension_blocked(self, service):
        """Test validating blocked file extensions raises error."""
        blocked_files = ["script.exe", "malware.bat", "virus.dll", "script.vbs"]

        for file_path in blocked_files:
            with pytest.raises(ValueError, match="File extension not allowed"):
                service.validate_file_extension(file_path)

    def test_validate_file_extension_no_extension_allowed(self, service):
        """Test validating files without extension (allowed ones)."""
        allowed_files = ["Makefile", "Dockerfile", "LICENSE", "README"]

        for file_path in allowed_files:
            # Should not raise exception
            service.validate_file_extension(file_path)

    def test_validate_file_extension_no_extension_not_allowed(self, service):
        """Test validating files without extension (not allowed ones)."""
        with pytest.raises(ValueError, match="File extension required"):
            service.validate_file_extension("randomfile")

    def test_validate_file_size_within_limit(self, service):
        """Test validating file size within limit."""
        small_content = "Hello, World!"
        # Should not raise exception
        service.validate_file_size(small_content)

    def test_validate_file_size_exceeds_limit(self, service):
        """Test validating file size exceeding limit raises error."""
        # Create content larger than default 10MB limit
        large_content = "x" * (11 * 1024 * 1024)  # 11MB
        with pytest.raises(ValueError, match="File size exceeds maximum allowed"):
            service.validate_file_size(large_content)

    def test_validate_file_content_valid_utf8(self, service):
        """Test validating valid UTF-8 content."""
        valid_content = "Hello, World! 🌍"
        # Should not raise exception
        service.validate_file_content(valid_content)

    def test_validate_file_content_dangerous_patterns(self, service):
        """Test validating content with dangerous patterns raises error."""
        dangerous_contents = [
            "eval(user_input)",
            "exec(malicious_code)",
            "subprocess.call(['rm', '-rf', '/'])",
            "os.system('dangerous command')",
        ]

        for content in dangerous_contents:
            with pytest.raises(
                ValueError, match="Potentially dangerous content detected"
            ):
                service.validate_file_content(content)

    def test_validate_directory_path_success(
        self, service_with_workspace, temp_workspace
    ):
        """Test validating existing directory path."""
        test_dir = temp_workspace / "testdir"
        test_dir.mkdir()

        # Should not raise exception
        service_with_workspace.validate_directory_path("testdir")

    def test_validate_directory_path_not_found(self, service_with_workspace):
        """Test validating non-existent directory raises error."""
        with pytest.raises(FileNotFoundError, match="Directory does not exist"):
            service_with_workspace.validate_directory_path("nonexistent")

    def test_validate_directory_path_is_file(
        self, service_with_workspace, temp_workspace
    ):
        """Test validating file instead of directory raises error."""
        test_file = temp_workspace / "test.txt"
        test_file.write_text("content")

        with pytest.raises(ValueError, match="Path is not a directory"):
            service_with_workspace.validate_directory_path("test.txt")

    def test_read_workspace_file_validated_success(
        self, service_with_workspace, temp_workspace
    ):
        """Test reading file with validation successfully."""
        test_file = temp_workspace / "test.py"
        test_content = "print('Hello, World!')"
        test_file.write_text(test_content)

        content = service_with_workspace.read_workspace_file_validated("test.py")
        assert content == test_content

    def test_read_workspace_file_validated_invalid_extension(
        self, service_with_workspace
    ):
        """Test reading file with invalid extension raises error."""
        with pytest.raises(ValueError, match="File extension not allowed"):
            service_with_workspace.read_workspace_file_validated("malware.exe")

    def test_write_workspace_file_validated_success(
        self, service_with_workspace, temp_workspace
    ):
        """Test writing file with validation successfully."""
        test_content = "print('Hello, World!')"
        service_with_workspace.write_workspace_file_validated("test.py", test_content)

        test_file = temp_workspace / "test.py"
        assert test_file.exists()
        assert test_file.read_text() == test_content

    def test_write_workspace_file_validated_dangerous_content(
        self, service_with_workspace
    ):
        """Test writing file with dangerous content raises error."""
        dangerous_content = "eval(user_input)"

        with pytest.raises(ValueError, match="Potentially dangerous content detected"):
            service_with_workspace.write_workspace_file_validated(
                "test.py", dangerous_content
            )

    def test_read_multiple_workspace_files_success(
        self, service_with_workspace, temp_workspace
    ):
        """Test reading multiple files successfully."""
        # Create test files
        (temp_workspace / "file1.txt").write_text("content1")
        (temp_workspace / "file2.txt").write_text("content2")

        results = service_with_workspace.read_multiple_workspace_files(
            ["file1.txt", "file2.txt"]
        )

        assert results["file1.txt"] == "content1"
        assert results["file2.txt"] == "content2"

    def test_read_multiple_workspace_files_with_errors_continue(
        self, service_with_workspace, temp_workspace
    ):
        """Test reading multiple files with errors (continue mode)."""
        # Create only one test file
        (temp_workspace / "file1.txt").write_text("content1")

        results = service_with_workspace.read_multiple_workspace_files(
            ["file1.txt", "nonexistent.txt"], fail_fast=False
        )

        assert results["file1.txt"] == "content1"
        assert "Error:" in results["nonexistent.txt"]

    def test_read_multiple_workspace_files_with_errors_fail_fast(
        self, service_with_workspace, temp_workspace
    ):
        """Test reading multiple files with errors (fail fast mode)."""
        # Create only one test file
        (temp_workspace / "file1.txt").write_text("content1")

        with pytest.raises(FileNotFoundError):
            service_with_workspace.read_multiple_workspace_files(
                ["file1.txt", "nonexistent.txt"], fail_fast=True
            )

    @pytest.mark.asyncio
    async def test_read_file_with_retry_success(
        self, service_with_workspace, temp_workspace
    ):
        """Test reading file with retry mechanism successfully."""
        test_file = temp_workspace / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        content = await service_with_workspace.read_file_with_retry("test.txt")
        assert content == test_content

    @pytest.mark.asyncio
    async def test_read_file_with_retry_transient_error(self, service_with_workspace):
        """Test reading file with retry on transient errors."""
        call_count = 0

        def mock_read_side_effect(file_path):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError("Transient error")
            return "Success after retries"

        with patch.object(
            service_with_workspace,
            "read_workspace_file",
            side_effect=mock_read_side_effect,
        ):
            content = await service_with_workspace.read_file_with_retry(
                "test.txt", max_retries=3
            )
            assert content == "Success after retries"
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_read_file_with_retry_exhausted(self, service_with_workspace):
        """Test reading file with retry exhausted raises error."""
        with patch.object(
            service_with_workspace,
            "read_workspace_file",
            side_effect=OSError("Persistent error"),
        ):
            with pytest.raises(
                FileOperationError, match="File read failed after .* retries"
            ):
                await service_with_workspace.read_file_with_retry(
                    "test.txt", max_retries=2
                )

    @pytest.mark.asyncio
    async def test_read_file_with_retry_non_retryable_error(
        self, service_with_workspace
    ):
        """Test reading file with non-retryable error."""
        with patch.object(
            service_with_workspace,
            "read_workspace_file",
            side_effect=ValueError("Invalid path"),
        ):
            with pytest.raises(
                FileOperationError, match="File read failed: Invalid path"
            ):
                await service_with_workspace.read_file_with_retry("test.txt")

    @pytest.mark.asyncio
    async def test_write_file_with_retry_success(
        self, service_with_workspace, temp_workspace
    ):
        """Test writing file with retry mechanism successfully."""
        test_content = "Hello, World!"
        await service_with_workspace.write_file_with_retry("test.txt", test_content)

        test_file = temp_workspace / "test.txt"
        assert test_file.exists()
        assert test_file.read_text() == test_content

    @pytest.mark.asyncio
    async def test_write_file_with_retry_transient_error(self, service_with_workspace):
        """Test writing file with retry on transient errors."""
        call_count = 0

        def mock_write_side_effect(file_path, content):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError("Transient error")
            return None  # Success

        with patch.object(
            service_with_workspace,
            "write_workspace_file",
            side_effect=mock_write_side_effect,
        ):
            await service_with_workspace.write_file_with_retry(
                "test.txt", "content", max_retries=3
            )
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_write_file_with_retry_exhausted(self, service_with_workspace):
        """Test writing file with retry exhausted raises error."""
        with patch.object(
            service_with_workspace,
            "write_workspace_file",
            side_effect=OSError("Persistent error"),
        ):
            with pytest.raises(
                FileOperationError, match="File write failed after .* retries"
            ):
                await service_with_workspace.write_file_with_retry(
                    "test.txt", "content", max_retries=2
                )

    def test_safe_read_workspace_file_success(
        self, service_with_workspace, temp_workspace
    ):
        """Test safely reading file successfully."""
        test_file = temp_workspace / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        content, error = service_with_workspace.safe_read_workspace_file("test.txt")
        assert content == test_content
        assert error is None

    def test_safe_read_workspace_file_error(self, service_with_workspace):
        """Test safely reading file with error."""
        content, error = service_with_workspace.safe_read_workspace_file(
            "nonexistent.txt"
        )
        assert content is None
        assert "File not found" in error

    def test_safe_write_workspace_file_success(
        self, service_with_workspace, temp_workspace
    ):
        """Test safely writing file successfully."""
        test_content = "Hello, World!"
        error = service_with_workspace.safe_write_workspace_file(
            "test.txt", test_content
        )

        assert error is None
        test_file = temp_workspace / "test.txt"
        assert test_file.exists()
        assert test_file.read_text() == test_content

    def test_safe_write_workspace_file_error(self, service):
        """Test safely writing file with error (no workspace set)."""
        error = service.safe_write_workspace_file("test.txt", "content")
        assert "Workspace root not set" in error

    def test_check_workspace_health_no_workspace(self, service):
        """Test checking workspace health when no workspace is set."""
        health = service.check_workspace_health()

        assert health["workspace_set"] is False
        assert health["workspace_accessible"] is False
        assert health["workspace_writable"] is False
        assert health["workspace_path"] is None

    def test_check_workspace_health_healthy_workspace(
        self, service_with_workspace, temp_workspace
    ):
        """Test checking workspace health with healthy workspace."""
        health = service_with_workspace.check_workspace_health()

        assert health["workspace_set"] is True
        assert health["workspace_accessible"] is True
        assert health["workspace_writable"] is True
        assert health["workspace_path"] == str(temp_workspace)

    def test_check_workspace_health_non_existent_workspace(self, service):
        """Test checking workspace health with non-existent workspace."""
        non_existent = Path("/non/existent/path")
        service.set_workspace_root(non_existent)

        health = service.check_workspace_health()

        assert health["workspace_set"] is True
        assert health["workspace_accessible"] is False
        assert health["workspace_writable"] is False
