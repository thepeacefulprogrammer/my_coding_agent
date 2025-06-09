"""MCP File Server integration for workspace-aware file operations."""

import json
import logging
import os
from pathlib import Path
from typing import Any

from mcp.client.session import ClientSession
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class FileOperationError(Exception):
    """Exception raised for file operation errors."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        if cause:
            self.__cause__ = cause


class MCPFileConfig(BaseModel):
    """Configuration for MCP File Server integration."""

    base_directory: str = Field(
        default_factory=lambda: str(Path.cwd()),
        description="Base directory for file operations",
    )
    allowed_extensions: list[str] = Field(
        default=[".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg"],
        description="List of allowed file extensions",
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum file size in bytes",
    )
    enable_write_operations: bool = Field(
        default=True, description="Enable file write operations"
    )
    enable_delete_operations: bool = Field(
        default=False, description="Enable file delete operations"
    )
    follow_symlinks: bool = Field(default=False, description="Follow symbolic links")
    enforce_workspace_boundaries: bool = Field(
        default=True, description="Whether to enforce workspace boundaries"
    )
    allow_directory_creation: bool = Field(
        default=True, description="Whether to allow directory creation"
    )
    blocked_paths: list[str] = Field(
        default_factory=lambda: ["secrets/*", ".env", "*.key", "private/*"],
        description="List of blocked paths and patterns",
    )

    @field_validator("base_directory")
    @classmethod
    def validate_base_directory(cls, v: str) -> str:
        """Validate base directory is not empty."""
        if not v or not v.strip():
            raise ValueError("Base directory must be specified")
        return v.strip()

    @field_validator("allowed_extensions")
    @classmethod
    def validate_allowed_extensions(cls, v: list[str]) -> list[str]:
        """Validate at least one extension is allowed."""
        if not v:
            raise ValueError("At least one file extension must be allowed")
        return v

    @field_validator("max_file_size")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        """Validate max file size is positive."""
        if v <= 0:
            raise ValueError("Max file size must be positive")
        return v

    @classmethod
    def create_secure_default(cls, base_directory: str) -> "MCPFileConfig":
        """Create a secure default configuration.

        Args:
            base_directory: Base directory for file operations.

        Returns:
            MCPFileConfig: Secure default configuration.
        """
        return cls(
            base_directory=base_directory,
            allowed_extensions=[".py", ".json", ".md", ".txt", ".yml", ".yaml"],
            max_file_size=1024 * 1024,  # 1MB
            enable_write_operations=False,
            enable_delete_operations=False,
            follow_symlinks=False,
            enforce_workspace_boundaries=True,
            allow_directory_creation=False,
            blocked_paths=[
                "secrets/*",
                "private/*",
                ".env",
                "*.key",
                "*.pem",
                "*.p12",
                "*.keystore",
                "config/secrets/*",
                ".ssh/*",
                "*.cert",
            ],
        )


class MCPFileServer:
    """MCP File Server client for workspace-aware file operations."""

    def __init__(self, config: MCPFileConfig):
        """Initialize MCP File Server client.

        Args:
            config: Configuration for the MCP file server
        """
        self.config = config
        self.is_connected = False
        self.client_session: ClientSession | None = None
        self._read_stream: Any | None = None
        self._write_stream: Any | None = None

        # Normalize base directory path
        self.config.base_directory = os.path.abspath(self.config.base_directory)

        logger.info(
            f"Initialized MCP File Server with base directory: {self.config.base_directory}"
        )

    async def connect(self) -> bool:
        """Connect to the MCP file server.

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            FileOperationError: If connection configuration is invalid.
        """
        try:
            from mcp.client.stdio import StdioServerParameters, stdio_client

            # For now, we'll use a built-in filesystem MCP server
            # In the future, this could connect to an external MCP server
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "mcp.filesystem"],  # Built-in filesystem server
                env={
                    "MCP_FILESYSTEM_BASE_DIR": self.config.base_directory,
                    "MCP_FILESYSTEM_MAX_SIZE": str(self.config.max_file_size),
                },
            )

            # Connect via stdio
            client_context = stdio_client(server_params)
            self._read_stream, self._write_stream = await client_context.__aenter__()

            # Create session
            session_context = ClientSession(self._read_stream, self._write_stream)
            self.client_session = await session_context.__aenter__()

            # Initialize the session
            await self.client_session.initialize()

            # Verify connection by listing available tools
            await self.client_session.list_tools()
            logger.info("Connected to MCP server with tools available")

            self.is_connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from the MCP file server."""
        try:
            if self.client_session:
                await self.client_session.__aexit__(None, None, None)
                self.client_session = None

            if self._read_stream or self._write_stream:
                # Close the streams if needed
                self._read_stream = None
                self._write_stream = None

            self.is_connected = False
            logger.info("Disconnected from MCP server")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            self.is_connected = False

    async def __aenter__(self):
        """Async context manager entry."""
        success = await self.connect()
        if not success:
            raise FileOperationError("Failed to connect to MCP server")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    def _validate_file_path(self, file_path: str) -> None:
        """Validate file path for security and allowed extensions.

        Args:
            file_path: Relative file path to validate

        Raises:
            FileOperationError: If path is invalid or not allowed
        """
        # Sanitize input
        if not file_path or file_path != file_path.strip():
            logger.warning(f"Security violation: invalid file path input '{file_path}'")
            raise FileOperationError(f"Invalid file path: '{file_path}'")

        # Check for null bytes and control characters
        if "\x00" in file_path or any(ord(c) < 32 for c in file_path if c not in "\t"):
            logger.warning(
                f"Security violation: null byte or control character injection '{file_path}'"
            )
            raise FileOperationError(f"Invalid characters in file path: '{file_path}'")

        # Check for Windows reserved names
        reserved_names = (
            ["con", "prn", "aux", "nul"]
            + [f"com{i}" for i in range(1, 10)]
            + [f"lpt{i}" for i in range(1, 10)]
        )
        path_parts = file_path.split("/")
        for part in path_parts:
            if part.lower().split(".")[0] in reserved_names:
                logger.warning(
                    f"Security violation: Windows reserved name '{file_path}'"
                )
                raise FileOperationError(f"Reserved name not allowed: '{file_path}'")

        # Check for absolute paths and Windows drive letters with combined condition
        if (
            file_path.startswith("/") or (os.name == "nt" and ":" in file_path)
        ) and self.config.enforce_workspace_boundaries:
            logger.warning(
                f"Security violation: absolute path access attempt '{file_path}'"
            )
            raise FileOperationError(
                f"Access denied: absolute path not allowed '{file_path}'"
            )

        # Check for path traversal attempts
        if ".." in file_path:
            logger.warning(f"Security violation: path traversal attempt '{file_path}'")
            raise FileOperationError(
                f"Access denied: path traversal not allowed '{file_path}'"
            )

        # Check blocked paths
        self._check_blocked_paths(file_path)

        # Normalize and check if path would escape base directory
        if self.config.enforce_workspace_boundaries:
            abs_path = self._get_absolute_path(file_path)
            try:
                # Check if the resolved path is within base directory
                Path(abs_path).resolve().relative_to(
                    Path(self.config.base_directory).resolve()
                )
            except ValueError as e:
                logger.warning(
                    f"Security violation: path outside workspace '{file_path}'"
                )
                raise FileOperationError(
                    f"Access denied: path '{file_path}' outside workspace boundaries"
                ) from e

        # Check file extension for files (not directories)
        ext = Path(file_path).suffix.lower()
        if ext and ext not in self.config.allowed_extensions:
            logger.warning(
                f"Security violation: blocked file extension '{ext}' for '{file_path}'"
            )
            raise FileOperationError(f"File extension {ext} not allowed")

    def _get_absolute_path(self, file_path: str) -> str:
        """Get absolute path within base directory.

        Args:
            file_path: Relative file path

        Returns:
            Absolute path within base directory
        """
        return os.path.join(self.config.base_directory, file_path)

    def _check_blocked_paths(self, file_path: str) -> None:
        """Check if file path matches any blocked patterns.

        Args:
            file_path: File path to check

        Raises:
            FileOperationError: If path is blocked
        """
        import fnmatch

        for blocked_pattern in self.config.blocked_paths:
            if fnmatch.fnmatch(file_path, blocked_pattern) or fnmatch.fnmatch(
                file_path.lower(), blocked_pattern.lower()
            ):
                logger.warning(
                    f"Security violation: blocked path pattern '{blocked_pattern}' matches '{file_path}'"
                )
                raise FileOperationError(
                    f"Access denied: path blocked by pattern '{blocked_pattern}'"
                )

    def _validate_file_size(self, content: str) -> None:
        """Validate file size against limits.

        Args:
            content: File content to validate

        Raises:
            FileOperationError: If file size exceeds limits
        """
        content_size = len(content.encode("utf-8"))
        if content_size > self.config.max_file_size:
            logger.warning(
                f"Security violation: file size {content_size} exceeds limit {self.config.max_file_size}"
            )
            raise FileOperationError(
                f"File size {content_size} bytes exceeds limit of {self.config.max_file_size} bytes"
            )

    def _can_write(self) -> bool:
        """Check if write operations are allowed.

        Returns:
            bool: True if write operations are allowed
        """
        return self.config.enable_write_operations

    def _can_delete(self) -> bool:
        """Check if delete operations are allowed.

        Returns:
            bool: True if delete operations are allowed
        """
        return self.config.enable_delete_operations

    def _can_create_directories(self) -> bool:
        """Check if directory creation is allowed.

        Returns:
            bool: True if directory creation is allowed
        """
        return self.config.allow_directory_creation

    async def read_file(self, file_path: str) -> str:
        """Read file contents.

        Args:
            file_path: Relative path to file within workspace

        Returns:
            File contents as string

        Raises:
            FileOperationError: If file cannot be read
        """
        if not self.is_connected:
            raise FileOperationError("Not connected to MCP server")

        self._validate_file_path(file_path)
        abs_path = self._get_absolute_path(file_path)

        try:
            result = await self.client_session.call_tool(
                "read_file", {"path": abs_path}
            )

            # Extract text content from result
            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return ""

        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise FileOperationError(f"Failed to read file: {e}") from e

    async def write_file(self, file_path: str, content: str) -> bool:
        """Write content to file.

        Args:
            file_path: Relative path to file within workspace
            content: Content to write

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be written
        """
        if not self.is_connected:
            raise FileOperationError("Not connected to MCP server")

        if not self._can_write():
            raise FileOperationError("Write operations not permitted")

        self._validate_file_path(file_path)
        self._validate_file_size(content)
        abs_path = self._get_absolute_path(file_path)

        try:
            await self.client_session.call_tool(
                "write_file", {"path": abs_path, "content": content}
            )

            # Check if operation was successful
            return True

        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            raise FileOperationError(f"Failed to write file: {e}") from e

    async def list_directory(self, dir_path: str = ".") -> list[str]:
        """List directory contents.

        Args:
            dir_path: Relative directory path within workspace

        Returns:
            List of file and directory names

        Raises:
            FileOperationError: If directory cannot be listed
        """
        if not self.is_connected:
            raise FileOperationError("Not connected to MCP server")

        # Special handling for current directory
        if dir_path == ".":
            abs_path = self.config.base_directory
        else:
            self._validate_file_path(dir_path)
            abs_path = self._get_absolute_path(dir_path)

        try:
            result = await self.client_session.call_tool(
                "list_directory", {"path": abs_path}
            )

            # Parse directory listing
            if result.content and len(result.content) > 0:
                content = result.content[0].text
                return [line.strip() for line in content.split("\n") if line.strip()]
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to list directory {dir_path}: {e}")
            raise FileOperationError(f"Failed to list directory: {e}") from e

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file.

        Args:
            file_path: Relative path to file within workspace

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be deleted
        """
        if not self.is_connected:
            raise FileOperationError("Not connected to MCP server")

        if not self._can_delete():
            raise FileOperationError("Delete operations not permitted")

        self._validate_file_path(file_path)
        abs_path = self._get_absolute_path(file_path)

        try:
            await self.client_session.call_tool("delete_file", {"path": abs_path})

            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise FileOperationError(f"Failed to delete file: {e}") from e

    async def create_directory(self, dir_path: str) -> bool:
        """Create a directory.

        Args:
            dir_path: Relative directory path within workspace

        Returns:
            True if successful

        Raises:
            FileOperationError: If directory cannot be created
        """
        if not self.is_connected:
            raise FileOperationError("Not connected to MCP server")

        if not self._can_create_directories():
            raise FileOperationError("Directory creation not permitted")

        # Use basic path validation for directories (no extension check)
        if ".." in dir_path or dir_path.startswith("/"):
            raise FileOperationError(
                f"Access denied: invalid directory path '{dir_path}'"
            )

        abs_path = self._get_absolute_path(dir_path)

        try:
            await self.client_session.call_tool("create_directory", {"path": abs_path})

            return True

        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise FileOperationError(f"Failed to create directory: {e}") from e

    async def get_file_info(self, file_path: str) -> dict[str, Any]:
        """Get file information.

        Args:
            file_path: Relative path to file within workspace

        Returns:
            Dictionary with file information

        Raises:
            FileOperationError: If file info cannot be retrieved
        """
        if not self.is_connected:
            raise FileOperationError("Not connected to MCP server")

        self._validate_file_path(file_path)
        abs_path = self._get_absolute_path(file_path)

        try:
            result = await self.client_session.call_tool(
                "get_file_info", {"path": abs_path}
            )

            # Parse JSON response
            if result.content and len(result.content) > 0:
                info_str = result.content[0].text
                return json.loads(info_str)
            else:
                return {}

        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            raise FileOperationError(f"Failed to get file info: {e}") from e

    async def search_files(self, pattern: str, dir_path: str = ".") -> list[str]:
        """Search for files matching a pattern.

        Args:
            pattern: Search pattern (e.g., "*.py")
            dir_path: Directory to search in

        Returns:
            List of matching file paths

        Raises:
            FileOperationError: If search cannot be performed
        """
        if not self.is_connected:
            raise FileOperationError("Not connected to MCP server")

        # Special handling for current directory
        if dir_path == ".":
            abs_base_path = self.config.base_directory
        else:
            abs_base_path = self._get_absolute_path(dir_path)

        try:
            result = await self.client_session.call_tool(
                "search_files", {"pattern": pattern, "base_path": abs_base_path}
            )

            # Parse search results
            if result.content and len(result.content) > 0:
                content = result.content[0].text
                return [line.strip() for line in content.split("\n") if line.strip()]
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to search files with pattern {pattern}: {e}")
            raise FileOperationError(f"Failed to search files: {e}") from e

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of the MCP file server.

        Returns:
            Dictionary with health status information
        """
        return {
            "connected": self.is_connected,
            "base_directory": self.config.base_directory,
            "allowed_extensions": self.config.allowed_extensions,
            "max_file_size": self.config.max_file_size,
            "write_enabled": self.config.enable_write_operations,
            "delete_enabled": self.config.enable_delete_operations,
            "follow_symlinks": self.config.follow_symlinks,
        }
