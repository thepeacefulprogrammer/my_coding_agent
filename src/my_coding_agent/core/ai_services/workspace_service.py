"""
Workspace management service for AI Agent.

This service handles:
- Workspace root management and path resolution
- Secure file and directory operations within workspace bounds
- Comprehensive validation for file paths, extensions, size, and content
- Enhanced operations with validation, retry mechanisms, and error handling
- Workspace health monitoring
"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FileOperationError(Exception):
    """Exception raised for file operation errors."""

    pass


class WorkspaceService:
    """Service for managing workspace operations and file system interactions."""

    def __init__(self, max_file_size: int = 10 * 1024 * 1024) -> None:
        """
        Initialize the Workspace Service.

        Args:
            max_file_size: Maximum allowed file size in bytes (default: 10MB)
        """
        self.workspace_root: Path | None = None
        self.max_file_size = max_file_size

        # Initialize logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for the workspace service."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    # Workspace Root Management
    def set_workspace_root(self, workspace_path: Path) -> None:
        """Set the workspace root directory for scoped file operations.

        Args:
            workspace_path: Path to the workspace root directory.
        """
        self.workspace_root = Path(workspace_path).resolve()
        self.logger.info(f"Workspace root set to: {self.workspace_root}")

    def resolve_workspace_path(self, file_path: str) -> Path:
        """Resolve and validate a path within the workspace.

        Args:
            file_path: File path to resolve (can be relative or absolute).

        Returns:
            Path: Resolved absolute path within workspace.

        Raises:
            ValueError: If workspace root not set or path is outside workspace.
        """
        if self.workspace_root is None:
            raise ValueError("Workspace root not set")

        # Convert to Path object
        path = Path(file_path)

        # If relative path, make it relative to workspace root
        if not path.is_absolute():
            path = self.workspace_root / path

        # Resolve the path (handles .., ., symlinks)
        try:
            resolved_path = path.resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid path: {e}") from e

        # Check if the resolved path is within workspace
        try:
            resolved_path.relative_to(self.workspace_root)
        except ValueError as e:
            raise ValueError(f"Path is outside workspace: {resolved_path}") from e

        return resolved_path

    # Basic File Operations
    def read_workspace_file(self, file_path: str) -> str:
        """Read file content from workspace.

        Args:
            file_path: Relative path to file within workspace.

        Returns:
            str: File content.

        Raises:
            ValueError: If path is outside workspace.
            FileNotFoundError: If file does not exist.
        """
        resolved_path = self.resolve_workspace_path(file_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not resolved_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        return resolved_path.read_text(encoding="utf-8")

    def write_workspace_file(self, file_path: str, content: str) -> None:
        """Write content to file in workspace.

        Args:
            file_path: Relative path to file within workspace.
            content: Content to write to file.

        Raises:
            ValueError: If path is outside workspace.
        """
        resolved_path = self.resolve_workspace_path(file_path)

        # Create parent directories if they don't exist
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        resolved_path.write_text(content, encoding="utf-8")

    def delete_workspace_file(self, file_path: str) -> None:
        """Delete file from workspace.

        Args:
            file_path: Relative path to file within workspace.

        Raises:
            ValueError: If path is outside workspace.
            FileNotFoundError: If file does not exist.
        """
        resolved_path = self.resolve_workspace_path(file_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if resolved_path.is_file():
            resolved_path.unlink()
        elif resolved_path.is_dir():
            resolved_path.rmdir()  # Only removes empty directories
        else:
            raise ValueError(f"Path is neither file nor directory: {file_path}")

    def workspace_file_exists(self, file_path: str) -> bool:
        """Check if file exists in workspace.

        Args:
            file_path: Relative path to file within workspace.

        Returns:
            bool: True if file exists, False otherwise.

        Raises:
            ValueError: If path is outside workspace.
        """
        resolved_path = self.resolve_workspace_path(file_path)
        return resolved_path.exists()

    # Directory Operations
    def list_workspace_directory(self, dir_path: str = ".") -> list[str]:
        """List files and directories in workspace directory.

        Args:
            dir_path: Relative path to directory within workspace.

        Returns:
            List[str]: List of file and directory names.

        Raises:
            ValueError: If path is outside workspace.
            FileNotFoundError: If directory does not exist.
        """
        resolved_path = self.resolve_workspace_path(dir_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        if not resolved_path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")

        return [item.name for item in resolved_path.iterdir()]

    def create_workspace_directory(self, dir_path: str) -> None:
        """Create directory in workspace.

        Args:
            dir_path: Relative path to directory within workspace.

        Raises:
            ValueError: If path is outside workspace.
        """
        resolved_path = self.resolve_workspace_path(dir_path)
        resolved_path.mkdir(parents=True, exist_ok=True)

    # Validation Methods
    def validate_file_path(self, file_path: str) -> None:
        """Validate file path for security and correctness.

        Args:
            file_path: File path to validate.

        Raises:
            ValueError: If file path is invalid.
        """
        if not file_path or not file_path.strip():
            raise ValueError("File path cannot be empty")

        file_path = file_path.strip()

        # Check for invalid characters
        invalid_chars = ["\x00", "<", ">", "|", '"', "*", "?"]
        for char in invalid_chars:
            if char in file_path:
                raise ValueError(f"Invalid characters in file path: {char}")

        # Check path length
        if len(file_path) > 255:
            raise ValueError("File path too long (max 255 characters)")

        # Check for reserved names (Windows compatibility)
        reserved_names = [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        ]

        path_name = Path(file_path).name.upper()
        if path_name in reserved_names:
            raise ValueError(f"Reserved file name not allowed: {path_name}")

    def validate_file_extension(self, file_path: str) -> None:
        """Validate file extension for security.

        Args:
            file_path: File path to validate.

        Raises:
            ValueError: If file extension is not allowed.
        """
        path = Path(file_path)

        # Blocked extensions for security
        blocked_extensions = [
            ".exe",
            ".bat",
            ".cmd",
            ".scr",
            ".pif",
            ".dll",
            ".vbs",
            ".js",
            ".jar",
            ".msi",
            ".app",
            ".deb",
            ".rpm",
        ]

        if path.suffix.lower() in blocked_extensions:
            raise ValueError(f"File extension not allowed: {path.suffix}")

        # Files without extension - only allow specific known files
        if not path.suffix:
            allowed_no_ext = [
                "Makefile",
                "Dockerfile",
                "Jenkinsfile",
                "Rakefile",
                "Gemfile",
                "Procfile",
                "LICENSE",
                "CHANGELOG",
                "README",
            ]
            if path.name not in allowed_no_ext:
                raise ValueError("File extension required for this file type")

    def validate_file_size(self, content: str) -> None:
        """Validate file size is within limits.

        Args:
            content: File content to validate.

        Raises:
            ValueError: If file size exceeds limits.
        """
        content_bytes = content.encode("utf-8")

        if len(content_bytes) > self.max_file_size:
            raise ValueError(
                f"File size exceeds maximum allowed: {len(content_bytes)} > {self.max_file_size} bytes"
            )

    def validate_file_content(self, content: str) -> None:
        """Validate file content for security and encoding.

        Args:
            content: File content to validate.

        Raises:
            ValueError: If content is invalid or potentially dangerous.
        """
        # Check encoding
        try:
            content.encode("utf-8")
        except UnicodeEncodeError as e:
            raise ValueError("Invalid file content encoding (must be UTF-8)") from e

        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__",
            r"subprocess\.call",
            r"os\.system",
            r'open\s*\([^)]*["\']w["\']',  # Writing to files
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                raise ValueError("Potentially dangerous content detected")

    def validate_directory_path(self, dir_path: str) -> None:
        """Validate directory path exists and is accessible.

        Args:
            dir_path: Directory path to validate.

        Raises:
            ValueError: If path is invalid.
            FileNotFoundError: If directory does not exist.
        """
        resolved_path = self.resolve_workspace_path(dir_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {dir_path}")

        if not resolved_path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")

    # Enhanced Operations with Validation
    def read_workspace_file_validated(self, file_path: str) -> str:
        """Read file with comprehensive validation.

        Args:
            file_path: Relative path to file within workspace.

        Returns:
            str: File content.

        Raises:
            ValueError: If validation fails.
            FileNotFoundError: If file does not exist.
        """
        self.validate_file_path(file_path)
        self.validate_file_extension(file_path)
        return self.read_workspace_file(file_path)

    def write_workspace_file_validated(self, file_path: str, content: str) -> None:
        """Write file with comprehensive validation.

        Args:
            file_path: Relative path to file within workspace.
            content: Content to write to file.

        Raises:
            ValueError: If validation fails.
        """
        self.validate_file_path(file_path)
        self.validate_file_extension(file_path)
        self.validate_file_size(content)
        self.validate_file_content(content)
        self.write_workspace_file(file_path, content)

    def read_multiple_workspace_files(
        self, file_paths: list[str], fail_fast: bool = False
    ) -> dict[str, str]:
        """Read multiple files with error handling.

        Args:
            file_paths: List of file paths to read.
            fail_fast: If True, stop on first error. If False, continue and collect errors.

        Returns:
            Dict[str, str]: Mapping of file paths to content (or error messages).

        Raises:
            FileNotFoundError: If fail_fast=True and a file is not found.
        """
        results = {}

        for file_path in file_paths:
            try:
                content = self.read_workspace_file(file_path)
                results[file_path] = content
            except Exception as e:
                if fail_fast:
                    raise
                results[file_path] = f"Error: {str(e)}"

        return results

    # Retry Mechanisms
    async def read_file_with_retry(self, file_path: str, max_retries: int = 3) -> str:
        """Read file with automatic retry on transient errors.

        Args:
            file_path: Path to file to read.
            max_retries: Maximum number of retry attempts.

        Returns:
            str: File content.

        Raises:
            FileOperationError: If all retries are exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return self.read_workspace_file(file_path)
            except OSError as e:
                last_error = e
                if attempt < max_retries:
                    # Exponential backoff
                    wait_time = 2**attempt * 0.1
                    await asyncio.sleep(wait_time)
                    self.logger.warning(
                        f"Retrying file read (attempt {attempt + 1}): {e}"
                    )
                continue
            except Exception as e:
                # Non-retryable errors
                raise FileOperationError(f"File read failed: {e}") from e

        raise FileOperationError(
            f"File read failed after {max_retries} retries: {last_error}"
        )

    async def write_file_with_retry(
        self, file_path: str, content: str, max_retries: int = 3
    ) -> None:
        """Write file with automatic retry on transient errors.

        Args:
            file_path: Path to file to write.
            content: Content to write to file.
            max_retries: Maximum number of retry attempts.

        Raises:
            FileOperationError: If all retries are exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                self.write_workspace_file(file_path, content)
                return
            except OSError as e:
                last_error = e
                if attempt < max_retries:
                    # Exponential backoff
                    wait_time = 2**attempt * 0.1
                    await asyncio.sleep(wait_time)
                    self.logger.warning(
                        f"Retrying file write (attempt {attempt + 1}): {e}"
                    )
                continue
            except Exception as e:
                # Non-retryable errors
                raise FileOperationError(f"File write failed: {e}") from e

        raise FileOperationError(
            f"File write failed after {max_retries} retries: {last_error}"
        )

    # Safe Operations
    def safe_read_workspace_file(self, file_path: str) -> tuple[str | None, str | None]:
        """Safely read workspace file with error handling.

        Args:
            file_path: Path to file to read.

        Returns:
            tuple: (content, error_message) - One will be None
        """
        try:
            content = self.read_workspace_file(file_path)
            return content, None
        except Exception as e:
            return None, str(e)

    def safe_write_workspace_file(self, file_path: str, content: str) -> str | None:
        """Safely write workspace file with error handling.

        Args:
            file_path: Path to file to write.
            content: Content to write.

        Returns:
            str | None: Error message if failed, None if successful.
        """
        try:
            self.write_workspace_file(file_path, content)
            return None
        except Exception as e:
            return str(e)

    # Health Checking
    def check_workspace_health(self) -> dict[str, Any]:
        """Check workspace health and accessibility.

        Returns:
            Dict[str, Any]: Health status information.
        """
        health = {
            "workspace_set": self.workspace_root is not None,
            "workspace_accessible": False,
            "workspace_writable": False,
            "workspace_path": str(self.workspace_root) if self.workspace_root else None,
        }

        if self.workspace_root:
            # Check accessibility
            health["workspace_accessible"] = (
                self.workspace_root.exists() and self.workspace_root.is_dir()
            )

            # Check writability
            try:
                test_file = self.workspace_root / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                health["workspace_writable"] = True
            except Exception:
                health["workspace_writable"] = False

        return health
