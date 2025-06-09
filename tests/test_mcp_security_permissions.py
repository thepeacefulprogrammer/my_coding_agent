"""Unit tests for MCP file system security and permissions."""

import asyncio
import contextlib
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from my_coding_agent.core.mcp_file_server import (
    FileOperationError,
    MCPFileConfig,
    MCPFileServer,
)


class TestMCPSecurityPermissions:
    """Test MCP file system security and permissions."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a secure temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create workspace structure
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir()

            # Create some test files
            (workspace / "allowed.py").write_text("print('Hello')")
            (workspace / "config.json").write_text('{"key": "value"}')
            (workspace / "README.md").write_text("# Project")
            (workspace / "blocked.exe").write_text("binary content")

            # Create subdirectories
            subdir = workspace / "subdir"
            subdir.mkdir()
            (subdir / "nested.py").write_text("def nested(): pass")

            # Create external directory (outside workspace)
            external = Path(temp_dir) / "external"
            external.mkdir()
            (external / "secret.txt").write_text("secret data")

            yield {
                "workspace": str(workspace),
                "external": str(external),
                "temp_dir": temp_dir,
            }

    @pytest.fixture
    def secure_config(self, temp_workspace):
        """Create a secure MCP configuration."""
        return MCPFileConfig(
            base_directory=temp_workspace["workspace"],
            allowed_extensions=[".py", ".json", ".md", ".txt"],
            max_file_size=1024 * 1024,  # 1MB
            enable_write_operations=True,
            enable_delete_operations=False,
            allow_directory_creation=True,
            enforce_workspace_boundaries=True,
            blocked_paths=["secrets/*", ".env", "*.key", "private/*"],
        )

    @pytest.fixture
    def restricted_config(self, temp_workspace):
        """Create a restricted MCP configuration."""
        return MCPFileConfig(
            base_directory=temp_workspace["workspace"],
            allowed_extensions=[".md"],  # Only markdown files
            max_file_size=1024,  # 1KB only
            enable_write_operations=False,
            enable_delete_operations=False,
            allow_directory_creation=False,
            enforce_workspace_boundaries=True,
            blocked_paths=["*"],  # Block all paths
        )

    def test_secure_config_initialization(self, secure_config):
        """Test secure configuration initialization."""
        server = MCPFileServer(secure_config)

        assert server.config.enforce_workspace_boundaries is True
        assert ".py" in server.config.allowed_extensions
        assert server.config.enable_write_operations is True
        assert server.config.enable_delete_operations is False

    def test_restricted_config_initialization(self, restricted_config):
        """Test restricted configuration initialization."""
        server = MCPFileServer(restricted_config)

        assert server.config.allowed_extensions == [".md"]
        assert server.config.max_file_size == 1024
        assert server.config.enable_write_operations is False
        assert server.config.enable_delete_operations is False

    @pytest.mark.asyncio
    async def test_path_traversal_protection(self, secure_config):
        """Test protection against path traversal attacks."""
        server = MCPFileServer(secure_config)

        # Mock connection
        server.is_connected = True

        # Test various path traversal attempts
        traversal_attempts = [
            "../external/secret.txt",
            "../../etc/passwd",
            "../../../root/.ssh/id_rsa",
            "subdir/../../../external/secret.txt",
            "./../external/secret.txt",
            "workspace/../external/secret.txt",
        ]

        for malicious_path in traversal_attempts:
            with pytest.raises(FileOperationError, match="path traversal not allowed"):
                await server.read_file(malicious_path)

    @pytest.mark.asyncio
    async def test_workspace_boundary_enforcement(self, secure_config, temp_workspace):
        """Test workspace boundary enforcement."""
        server = MCPFileServer(secure_config)
        server.is_connected = True

        # Test absolute paths outside workspace
        external_file = Path(temp_workspace["external"]) / "secret.txt"

        with pytest.raises(FileOperationError, match="absolute path not allowed"):
            await server.read_file(str(external_file))

    @pytest.mark.asyncio
    async def test_file_extension_validation(self, secure_config):
        """Test file extension validation."""
        server = MCPFileServer(secure_config)
        server.is_connected = True

        # Test blocked extensions
        blocked_files = [
            "malware.exe",
            "script.bat",
            "virus.com",
            "trojan.scr",
            "backdoor.dll",
        ]

        for blocked_file in blocked_files:
            with pytest.raises(
                FileOperationError, match="File extension .* not allowed"
            ):
                await server.read_file(blocked_file)

    @pytest.mark.asyncio
    async def test_file_size_limits(self, secure_config):
        """Test file size limit enforcement."""
        server = MCPFileServer(secure_config)
        server.is_connected = True

        # Mock a large file read operation
        large_content = "x" * (2 * 1024 * 1024)  # 2MB content

        with patch.object(server, "_validate_file_size") as mock_validate:
            mock_validate.side_effect = FileOperationError("File size exceeds limit")

            with pytest.raises(FileOperationError, match="File size exceeds limit"):
                await server.write_file("large_file.py", large_content)

    @pytest.mark.asyncio
    async def test_blocked_paths_enforcement(self, secure_config):
        """Test blocked paths enforcement."""
        server = MCPFileServer(secure_config)
        server.is_connected = True

        blocked_files = [
            "secrets/api_key.py",  # Use allowed extension
            ".env",  # No extension
            "production.key",  # Blocked by pattern
            "private/credentials.json",  # Use allowed extension
        ]

        for blocked_file in blocked_files:
            with pytest.raises(
                FileOperationError,
                match="Access denied.*blocked|File extension.*not allowed",
            ):
                await server.read_file(blocked_file)

    @pytest.mark.asyncio
    async def test_write_operation_permissions(self, secure_config, restricted_config):
        """Test write operation permissions."""
        # Test with write enabled
        server_write_enabled = MCPFileServer(secure_config)
        server_write_enabled.is_connected = True

        # Should allow write operations
        assert server_write_enabled._can_write() is True

        # Test with write disabled
        server_write_disabled = MCPFileServer(restricted_config)
        server_write_disabled.is_connected = True

        with pytest.raises(FileOperationError, match="Write operations not permitted"):
            await server_write_disabled.write_file("test.md", "content")

    @pytest.mark.asyncio
    async def test_delete_operation_permissions(self, secure_config, restricted_config):
        """Test delete operation permissions."""
        # Test with delete disabled (secure_config has delete_operations=False)
        server_delete_disabled = MCPFileServer(secure_config)
        server_delete_disabled.is_connected = True

        with pytest.raises(FileOperationError, match="Delete operations not permitted"):
            await server_delete_disabled.delete_file("allowed.py")

    @pytest.mark.asyncio
    async def test_directory_creation_permissions(
        self, secure_config, restricted_config
    ):
        """Test directory creation permissions."""
        # Test with directory creation enabled
        server_dir_enabled = MCPFileServer(secure_config)
        server_dir_enabled.is_connected = True

        # Should allow directory creation
        assert server_dir_enabled._can_create_directories() is True

        # Test with directory creation disabled
        server_dir_disabled = MCPFileServer(restricted_config)
        server_dir_disabled.is_connected = True

        with pytest.raises(
            FileOperationError, match="Directory creation not permitted"
        ):
            await server_dir_disabled.create_directory("new_dir")

    @pytest.mark.asyncio
    async def test_safe_file_operations(self, secure_config, temp_workspace):
        """Test safe file operations within boundaries."""
        server = MCPFileServer(secure_config)
        server.is_connected = True

        # Mock successful operations for allowed files
        with patch.object(server, "client_session") as mock_session:
            mock_session.call_tool = AsyncMock(
                return_value=Mock(content=[Mock(type="text", text="print('Hello')")])
            )

            # Should successfully read allowed files
            content = await server.read_file("allowed.py")
            assert content == "print('Hello')"

            # Should successfully read files in subdirectories
            content = await server.read_file("subdir/nested.py")
            assert content == "print('Hello')"

    @pytest.mark.asyncio
    async def test_security_audit_logging(self, secure_config):
        """Test security audit logging for violations."""
        server = MCPFileServer(secure_config)
        server.is_connected = True

        with patch("my_coding_agent.core.mcp_file_server.logger") as mock_logger:
            # Attempt path traversal
            with contextlib.suppress(FileOperationError):
                await server.read_file("../external/secret.txt")

            # Verify security violation is logged
            mock_logger.warning.assert_called()
            assert "Security violation" in str(mock_logger.warning.call_args)

    def test_configuration_validation(self, temp_workspace):
        """Test configuration validation for security settings."""
        # Test invalid configurations
        with pytest.raises(ValueError, match="Base directory must be specified"):
            MCPFileConfig(
                base_directory="",
                allowed_extensions=[".py"],
                max_file_size=1024,
                enable_write_operations=True,
                enable_delete_operations=False,
            )

        with pytest.raises(
            ValueError, match="At least one file extension must be allowed"
        ):
            MCPFileConfig(
                base_directory=temp_workspace["workspace"],
                allowed_extensions=[],
                max_file_size=1024,
                enable_write_operations=True,
                enable_delete_operations=False,
            )

        with pytest.raises(ValueError, match="Max file size must be positive"):
            MCPFileConfig(
                base_directory=temp_workspace["workspace"],
                allowed_extensions=[".py"],
                max_file_size=0,
                enable_write_operations=True,
                enable_delete_operations=False,
            )

    @pytest.mark.asyncio
    async def test_concurrent_access_safety(self, secure_config):
        """Test concurrent access safety and resource protection."""
        server = MCPFileServer(secure_config)
        server.is_connected = True

        # Mock multiple concurrent read operations
        with patch.object(server, "client_session") as mock_session:
            mock_session.call_tool = AsyncMock(
                return_value=Mock(content=[Mock(type="text", text="content")])
            )

            # Run multiple concurrent operations
            tasks = [
                server.read_file("allowed.py"),
                server.read_file("config.json"),
                server.read_file("README.md"),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All operations should succeed
            for result in results:
                assert isinstance(result, str)
                assert result == "content"

    @pytest.mark.asyncio
    async def test_permission_escalation_prevention(self, secure_config):
        """Test prevention of permission escalation attacks."""
        server = MCPFileServer(secure_config)
        server.is_connected = True

        # Test attempts to modify configuration at runtime

        # Attempt to modify configuration
        malicious_config = MCPFileConfig(
            base_directory="/",  # Try to access entire filesystem
            allowed_extensions=[".*"],  # Try to allow all files
            max_file_size=999999999,  # Try to set very large size limits
            enable_write_operations=True,
            enable_delete_operations=True,
            enforce_workspace_boundaries=False,  # Try to disable security
        )

        # Configuration should not be modifiable after initialization
        server.config = malicious_config

        # Security checks should still use original configuration
        with pytest.raises(FileOperationError):
            await server.read_file("/etc/passwd")

    def test_secure_default_configuration(self):
        """Test that default configuration is secure by default."""
        config = MCPFileConfig.create_secure_default("/tmp/workspace")

        assert config.enforce_workspace_boundaries is True
        assert config.enable_delete_operations is False
        assert len(config.allowed_extensions) > 0
        assert config.max_file_size > 0
        assert "secrets/*" in config.blocked_paths
        assert ".env" in config.blocked_paths

    @pytest.mark.asyncio
    async def test_input_sanitization(self, secure_config):
        """Test input sanitization and validation."""
        server = MCPFileServer(secure_config)
        server.is_connected = True

        # Test malicious inputs
        malicious_inputs = [
            "",  # Empty input
            "file\x00name.py",  # Null byte injection
            "file\nname.py",  # Newline injection
            "file\rname.py",  # Carriage return injection
            "file\tname.py",  # Tab injection
            "con.py",  # Windows reserved name
            "aux.py",  # Windows reserved name
            "prn.py",  # Windows reserved name
        ]

        for malicious_input in malicious_inputs:
            with pytest.raises((FileOperationError, ValueError, TypeError)):
                await server.read_file(malicious_input)

        # Test None input separately - this should raise TypeError
        with pytest.raises(TypeError):
            await server.read_file(None)  # type: ignore

    def test_security_configuration_immutability(self, secure_config):
        """Test that security configuration cannot be modified after creation."""
        server = MCPFileServer(secure_config)

        # Original configuration should be preserved
        original_boundaries = server.config.enforce_workspace_boundaries
        original_blocked_paths = server.config.blocked_paths.copy()

        # Attempt to modify security settings
        with pytest.raises(AttributeError):
            server.config.enforce_workspace_boundaries = False

        with pytest.raises(AttributeError):
            server.config.blocked_paths.clear()

        # Verify original configuration is preserved
        assert server.config.enforce_workspace_boundaries == original_boundaries
        assert server.config.blocked_paths == original_blocked_paths

    @pytest.mark.asyncio
    async def test_security_boundary_enforcement(self, secure_config):
        """Test that security boundaries cannot be bypassed."""
        server = MCPFileServer(secure_config)
        server.is_connected = True

        # Original configuration should be preserved
        original_boundaries = server.config.enforce_workspace_boundaries
        original_blocked_paths = server.config.blocked_paths.copy()

        # Attempt to modify security settings
        with pytest.raises((AttributeError, TypeError)):
            server.config.enforce_workspace_boundaries = False

        with pytest.raises((AttributeError, TypeError)):
            server.config.blocked_paths.clear()

        # Verify security settings remain intact
        assert server.config.enforce_workspace_boundaries == original_boundaries
        assert server.config.blocked_paths == original_blocked_paths
