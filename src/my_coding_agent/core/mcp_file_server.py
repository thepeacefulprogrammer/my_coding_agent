"""MCP File Server implementation for AI Agent integration."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

try:
    from mcp.client.session import ClientSession
except ImportError:
    # Fallback for testing or when MCP is not available
    ClientSession = None


class FileOperationError(Exception):
    """Exception raised for file operation errors."""

    def __init__(self, message: str, file_path_or_cause: str | Exception | None = None):
        self.message = message

        # Handle both file_path string and exception cause
        if isinstance(file_path_or_cause, Exception):
            self.file_path = None
            self.__cause__ = file_path_or_cause
        else:
            self.file_path = file_path_or_cause

        super().__init__(self.message)


class MCPFileConfig(BaseModel):
    """Configuration for MCP file server operations."""

    base_directory: Path = Field(
        default_factory=lambda: Path.cwd(),
        description="Base directory for file operations",
    )
    allowed_extensions: list[str] | None = Field(
        default=[".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg"],
        description="List of allowed file extensions (None = all allowed)",
    )
    enable_write_operations: bool = Field(
        default=True, description="Whether write operations are allowed"
    )
    enable_delete_operations: bool = Field(
        default=False, description="Whether delete operations are allowed"
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum file size in bytes",
    )
    max_directory_depth: int = Field(
        default=10, description="Maximum directory traversal depth"
    )
    follow_symlinks: bool = Field(
        default=False, description="Whether to follow symbolic links"
    )
    enforce_workspace_boundaries: bool = Field(
        default=True, description="Whether to enforce workspace boundaries"
    )
    blocked_paths: list[str] = Field(
        default_factory=lambda: ["secrets/*", ".env", "*.key", "private/*"],
        description="List of blocked path patterns",
    )

    @field_validator("base_directory")
    @classmethod
    def validate_base_directory(cls, v):
        """Validate base directory exists and is accessible."""
        # Check for empty or None values before creating Path
        if v is None:
            raise ValueError("Base directory must be specified")

        # Convert to string and check for empty/whitespace-only strings
        v_str = str(v).strip()
        if v_str == "" or v_str == ".":
            raise ValueError("Base directory must be specified")

        path = Path(v).resolve()
        if not path.exists():
            # For testing, create directory if it doesn't exist
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(
                    f"Base directory does not exist and cannot be created: {path}"
                ) from e
        if not path.is_dir():
            raise ValueError(f"Base directory is not a directory: {path}")
        return path

    @field_validator("allowed_extensions")
    @classmethod
    def validate_allowed_extensions(cls, v):
        """Validate allowed extensions."""
        if v is not None and len(v) == 0:
            raise ValueError("At least one file extension must be allowed")
        return v

    @field_validator("max_file_size")
    @classmethod
    def validate_max_file_size(cls, v):
        """Validate max file size."""
        if v <= 0:
            raise ValueError("Max file size must be positive")
        return v

    @classmethod
    def create_secure_default(cls, base_directory: str) -> MCPFileConfig:
        """Create a secure default configuration.

        Args:
            base_directory: Base directory for file operations

        Returns:
            MCPFileConfig: Secure default configuration
        """
        return cls(
            base_directory=Path(base_directory),
            allowed_extensions=[".py", ".md", ".txt", ".json", ".yaml", ".yml"],
            enable_write_operations=False,
            enable_delete_operations=False,
            max_file_size=1024 * 1024,  # 1MB
            max_directory_depth=5,
            follow_symlinks=False,
            enforce_workspace_boundaries=True,
            blocked_paths=["secrets/*", ".env", "*.key", "private/*", "production.*"],
        )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MCPFileServer:
    """MCP File Server for handling file operations with proper security and validation."""

    def __init__(self, config: MCPFileConfig):
        """Initialize MCP file server.

        Args:
            config: Configuration for the file server
        """
        self.config = config
        self.is_connected = False
        self.client_session = None
        self._read_stream = None
        self._write_stream = None
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging for the MCP file server."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

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
        return self.config.enable_write_operations

    async def connect(self) -> bool:
        """Connect to the MCP file server (initialize resources).

        Returns:
            bool: True if connection successful
        """
        try:
            # Validate base directory is accessible
            if not self.config.base_directory.exists():
                raise FileOperationError(
                    f"Base directory not accessible: {self.config.base_directory}"
                )

            # Test read permissions
            if not os.access(self.config.base_directory, os.R_OK):
                raise FileOperationError(
                    f"No read permission for base directory: {self.config.base_directory}"
                )

            # Test write permissions if write operations enabled
            if self.config.enable_write_operations and not os.access(
                self.config.base_directory, os.W_OK
            ):
                raise FileOperationError(
                    f"No write permission for base directory: {self.config.base_directory}"
                )

            # Try to establish MCP connection if ClientSession is available
            if ClientSession is not None:
                try:
                    # Try to import and use MCP client
                    from mcp.client.stdio import stdio_client

                    # Attempt to create MCP connection
                    read_stream, write_stream = await stdio_client().__aenter__()
                    self._read_stream = read_stream
                    self._write_stream = write_stream

                    # Create and initialize session
                    session = ClientSession(read_stream, write_stream)
                    await session.__aenter__()
                    await session.initialize()
                    self.client_session = session

                except Exception as e:
                    # MCP connection failed, but we can still operate without it
                    self.logger.warning(
                        f"MCP connection failed, falling back to direct file operations: {e}"
                    )
                    self.client_session = None
                    self._read_stream = None
                    self._write_stream = None

            self.is_connected = True
            self.logger.info(
                f"MCP file server connected to: {self.config.base_directory}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect MCP file server: {e}")
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from the MCP file server (cleanup resources)."""
        self.is_connected = False
        self.client_session = None
        self._read_stream = None
        self._write_stream = None
        self.logger.info("MCP file server disconnected")

    async def __aenter__(self):
        """Async context manager entry."""
        success = await self.connect()
        if not success:
            raise FileOperationError("Failed to connect to MCP server")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path relative to base directory with security checks.

        Args:
            file_path: Relative file path

        Returns:
            Path: Resolved absolute path

        Raises:
            FileOperationError: If path is invalid or outside base directory
        """
        if not file_path or file_path.strip() == "":
            raise FileOperationError("File path cannot be empty")

        # Check for absolute paths first
        if file_path.startswith("/") or file_path.startswith("\\"):
            logger.warning(
                f"Security violation: absolute path not allowed: {file_path}"
            )
            raise FileOperationError(
                "Access denied: absolute path not allowed", file_path
            )

        # Check for path traversal patterns
        if ".." in file_path or "\\" in file_path:
            logger.warning(
                f"Security violation: path traversal attempt detected: {file_path}"
            )
            raise FileOperationError(
                "Access denied: path traversal not allowed", file_path
            )

        # Convert to Path and resolve
        path = Path(file_path)

        # Double-check if absolute path (shouldn't happen after above check)
        if path.is_absolute():
            logger.warning(
                f"Security violation: absolute path not allowed: {file_path}"
            )
            raise FileOperationError(
                "Access denied: absolute path not allowed", file_path
            )

        # Resolve relative to base directory
        resolved_path = (self.config.base_directory / path).resolve()

        # Security check: ensure resolved path is within base directory
        try:
            resolved_path.relative_to(self.config.base_directory)
        except ValueError:
            logger.warning(f"Security violation: path outside workspace: {file_path}")
            raise FileOperationError(
                "Access denied: path traversal not allowed", file_path
            ) from None

        return resolved_path

    def _validate_file_extension(self, file_path: str) -> None:
        """Validate file extension is allowed.

        Args:
            file_path: File path to validate

        Raises:
            FileOperationError: If extension not allowed
        """
        if self.config.allowed_extensions is None:
            return  # All extensions allowed

        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in self.config.allowed_extensions:
            raise FileOperationError(
                f"File extension {extension} not allowed", file_path
            )

    def _validate_file_size(self, content: str) -> None:
        """Validate file content size.

        Args:
            content: File content to validate

        Raises:
            FileOperationError: If file too large
        """
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > self.config.max_file_size:
            raise FileOperationError(
                f"File size ({len(content_bytes)} bytes) exceeds limit "
                f"({self.config.max_file_size} bytes)"
            )

    def _ensure_connected(self) -> None:
        """Ensure MCP server is connected.

        Raises:
            FileOperationError: If not connected
        """
        if not self.is_connected:
            raise FileOperationError("Not connected to MCP server")

    async def read_file(self, file_path: str) -> str:
        """Read file content.

        Args:
            file_path: Relative path to file

        Returns:
            str: File content

        Raises:
            FileOperationError: If file cannot be read
        """
        self._ensure_connected()

        try:
            # Validate file path (includes security checks, blocked paths, and extension validation)
            self._validate_file_path(file_path)
            resolved_path = self._resolve_path(file_path)

            # Use MCP protocol if client session is available
            if self.client_session:
                result = await self.client_session.call_tool(
                    "read_file", {"path": str(resolved_path)}
                )
                if result.content and len(result.content) > 0:
                    content_item = result.content[0]
                    if hasattr(content_item, "text"):
                        return content_item.text
                    else:
                        raise FileOperationError(
                            f"Unsupported content type for file: {file_path}", file_path
                        )
                else:
                    raise FileOperationError(
                        f"No content returned for file: {file_path}", file_path
                    )

            # Fall back to direct file operations
            if not resolved_path.exists():
                raise FileOperationError(f"File not found: {file_path}", file_path)

            if not resolved_path.is_file():
                raise FileOperationError(f"Path is not a file: {file_path}", file_path)

            # Check file size before reading
            file_size = resolved_path.stat().st_size
            if file_size > self.config.max_file_size:
                raise FileOperationError(
                    f"File size ({file_size} bytes) exceeds limit "
                    f"({self.config.max_file_size} bytes)",
                    file_path,
                )

            content = resolved_path.read_text(encoding="utf-8")
            self.logger.debug(f"Read file: {file_path} ({len(content)} chars)")
            return content

        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(f"Failed to read file: {e}", file_path) from e

    async def write_file(self, file_path: str, content: str) -> bool:
        """Write content to file.

        Args:
            file_path: Relative path to file
            content: Content to write

        Returns:
            bool: True if successful

        Raises:
            FileOperationError: If file cannot be written
        """
        self._ensure_connected()

        if not self.config.enable_write_operations:
            raise FileOperationError("Write operations not permitted")

        try:
            resolved_path = self._resolve_path(file_path)
            self._validate_file_extension(file_path)
            self._validate_file_size(content)

            # Use MCP protocol if client session is available
            if self.client_session:
                await self.client_session.call_tool(
                    "write_file", {"path": str(resolved_path), "content": content}
                )
                return True

            # Fall back to direct file operations
            # Ensure parent directory exists
            resolved_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file
            resolved_path.write_text(content, encoding="utf-8")
            self.logger.debug(f"Wrote file: {file_path} ({len(content)} chars)")
            return True

        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(f"Failed to write file: {e}", file_path) from e

    async def list_directory(self, directory_path: str = ".") -> list[str]:
        """List directory contents.

        Args:
            directory_path: Relative path to directory

        Returns:
            list[str]: List of file and directory names

        Raises:
            FileOperationError: If directory cannot be listed
        """
        self._ensure_connected()

        try:
            resolved_path = self._resolve_path(directory_path)

            # Use MCP protocol if client session is available
            if self.client_session:
                result = await self.client_session.call_tool(
                    "list_directory", {"path": str(resolved_path)}
                )
                if result.content and len(result.content) > 0:
                    # Parse the directory listing from the response
                    content = result.content[0].text
                    files = [
                        line.strip() for line in content.split("\n") if line.strip()
                    ]
                    return files
                else:
                    return []

            # Fall back to direct file operations
            if not resolved_path.exists():
                raise FileOperationError(
                    f"Directory not found: {directory_path}", directory_path
                )

            if not resolved_path.is_dir():
                raise FileOperationError(
                    f"Path is not a directory: {directory_path}", directory_path
                )

            # List directory contents
            files = []
            for item in resolved_path.iterdir():
                if item.is_dir():
                    files.append(f"{item.name}/")
                else:
                    files.append(item.name)

            files.sort()
            self.logger.debug(
                f"Listed directory: {directory_path} ({len(files)} items)"
            )
            return files

        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(
                f"Failed to list directory: {e}", directory_path
            ) from e

    async def create_directory(self, directory_path: str) -> bool:
        """Create directory.

        Args:
            directory_path: Relative path to directory

        Returns:
            bool: True if successful

        Raises:
            FileOperationError: If directory cannot be created
        """
        self._ensure_connected()

        if not self._can_create_directories():
            raise FileOperationError("Directory creation not permitted")

        try:
            resolved_path = self._resolve_path(directory_path)

            # Use MCP protocol if client session is available
            if self.client_session:
                await self.client_session.call_tool(
                    "create_directory", {"path": str(resolved_path)}
                )
                return True

            # Fall back to direct file operations
            resolved_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created directory: {directory_path}")
            return True

        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(
                f"Failed to create directory: {e}", directory_path
            ) from e

    async def delete_file(self, file_path: str) -> bool:
        """Delete file.

        Args:
            file_path: Relative path to file

        Returns:
            bool: True if successful

        Raises:
            FileOperationError: If file cannot be deleted
        """
        self._ensure_connected()

        if not self.config.enable_delete_operations:
            raise FileOperationError("Delete operations not permitted")

        try:
            resolved_path = self._resolve_path(file_path)
            self._validate_file_extension(file_path)

            # Use MCP protocol if client session is available
            if self.client_session:
                await self.client_session.call_tool(
                    "delete_file", {"path": str(resolved_path)}
                )
                return True

            # Fall back to direct file operations
            if not resolved_path.exists():
                raise FileOperationError(f"File not found: {file_path}", file_path)

            if not resolved_path.is_file():
                raise FileOperationError(f"Path is not a file: {file_path}", file_path)

            resolved_path.unlink()
            self.logger.debug(f"Deleted file: {file_path}")
            return True

        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(f"Failed to delete file: {e}", file_path) from e

    async def get_file_info(self, file_path: str) -> dict[str, Any]:
        """Get file information.

        Args:
            file_path: Relative path to file

        Returns:
            dict[str, Any]: File information

        Raises:
            FileOperationError: If file info cannot be retrieved
        """
        self._ensure_connected()

        try:
            resolved_path = self._resolve_path(file_path)

            # Use MCP protocol if client session is available
            if self.client_session:
                result = await self.client_session.call_tool(
                    "get_file_info", {"path": str(resolved_path)}
                )
                if result.content and len(result.content) > 0:
                    import json

                    info_json = result.content[0].text
                    return json.loads(info_json)
                else:
                    raise FileOperationError(
                        f"No file info returned for: {file_path}", file_path
                    )

            # Fall back to direct file operations
            if not resolved_path.exists():
                raise FileOperationError(f"File not found: {file_path}", file_path)

            stat = resolved_path.stat()

            info = {
                "path": file_path,
                "absolute_path": str(resolved_path),
                "size": stat.st_size,
                "modified_time": stat.st_mtime,
                "is_file": resolved_path.is_file(),
                "is_directory": resolved_path.is_dir(),
                "is_symlink": resolved_path.is_symlink(),
            }

            if resolved_path.is_file():
                info["extension"] = resolved_path.suffix

            self.logger.debug(f"Got file info: {file_path}")
            return info

        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(f"Failed to get file info: {e}", file_path) from e

    async def search_files(self, pattern: str, directory: str = ".") -> list[str]:
        """Search for files matching pattern.

        Args:
            pattern: Search pattern (glob-style)
            directory: Directory to search in

        Returns:
            list[str]: List of matching file paths

        Raises:
            FileOperationError: If search cannot be performed
        """
        self._ensure_connected()

        try:
            resolved_dir = self._resolve_path(directory)

            # Use MCP protocol if client session is available
            if self.client_session:
                result = await self.client_session.call_tool(
                    "search_files", {"pattern": pattern, "base_path": str(resolved_dir)}
                )
                if result.content and len(result.content) > 0:
                    content = result.content[0].text
                    files = [
                        line.strip() for line in content.split("\n") if line.strip()
                    ]
                    return files
                else:
                    return []

            # Fall back to direct file operations
            if not resolved_dir.exists():
                raise FileOperationError(f"Directory not found: {directory}", directory)

            if not resolved_dir.is_dir():
                raise FileOperationError(
                    f"Path is not a directory: {directory}", directory
                )

            # Search for files using glob
            matches = []
            for match in resolved_dir.glob(pattern):
                if match.is_file():
                    # Return relative path from the search directory
                    rel_path = match.relative_to(resolved_dir)
                    matches.append(str(rel_path))

            matches.sort()
            self.logger.debug(
                f"Found {len(matches)} files matching '{pattern}' in {directory}"
            )
            return matches

        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(f"Failed to search files: {e}", directory) from e

    def _validate_file_path(self, file_path: str) -> None:
        """Validate file path for security and extension checks.

        Args:
            file_path: File path to validate

        Raises:
            FileOperationError: If path is invalid
        """
        # First check path resolution and security - this will raise path traversal errors
        try:
            self._resolve_path(file_path)  # This will raise if path is invalid
        except Exception:
            raise

        # Check blocked paths
        self._check_blocked_paths(file_path)

        # Only check extension if path is valid
        self._validate_file_extension(file_path)

    def _check_blocked_paths(self, file_path: str) -> None:
        """Check if file path matches any blocked patterns.

        Args:
            file_path: File path to check

        Raises:
            FileOperationError: If path is blocked
        """
        import fnmatch

        for blocked_pattern in self.config.blocked_paths:
            if fnmatch.fnmatch(file_path, blocked_pattern):
                logger.warning(
                    f"Security violation: access to blocked path: {file_path}"
                )
                raise FileOperationError(
                    f"Access denied: path '{file_path}' is blocked", file_path
                )

    def _get_absolute_path(self, file_path: str) -> str:
        """Get absolute path for a relative file path.

        Args:
            file_path: Relative file path

        Returns:
            str: Absolute path
        """
        resolved_path = self._resolve_path(file_path)
        return str(resolved_path)

    def get_health_status(self) -> dict[str, Any]:
        """Get server health and configuration status.

        Returns:
            dict[str, Any]: Server status information
        """
        return {
            "connected": self.is_connected,
            "base_directory": str(self.config.base_directory),
            "allowed_extensions": self.config.allowed_extensions,
            "max_file_size": self.config.max_file_size,
            "write_enabled": self.config.enable_write_operations,
            "delete_enabled": self.config.enable_delete_operations,
            "follow_symlinks": self.config.follow_symlinks,
            "max_directory_depth": self.config.max_directory_depth,
        }
