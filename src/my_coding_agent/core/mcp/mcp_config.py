"""
MCP configuration management system.

This module provides functionality to read, parse, and validate MCP server
configurations from JSON files following the MCP protocol specification.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server.

    Servers are enabled by default (disabled=False). If a server is included
    in the configuration file, it will be used unless explicitly disabled.
    """

    name: str
    transport: str
    command: str | None = None
    args: list[str] | None = None
    url: str | None = None
    env: dict[str, str] | None = None
    headers: dict[str, str] | None = None
    timeout: float | None = None
    keep_alive: bool = True
    disabled: bool = (
        False  # Default to enabled - servers are active unless explicitly disabled
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        config = {
            "server_name": self.name,
            "transport": self.transport,
            "keep_alive": self.keep_alive,
        }

        # Only include disabled field if it's True (since False is the default)
        if self.disabled:
            config["disabled"] = self.disabled

        if self.command is not None:
            config["command"] = self.command
        if self.args is not None:
            config["args"] = self.args
        if self.url is not None:
            config["url"] = self.url
        if self.env is not None:
            config["env"] = self.env
        if self.headers is not None:
            config["headers"] = self.headers
        if self.timeout is not None:
            config["timeout"] = self.timeout

        return config

    @classmethod
    def from_dict(cls, name: str, config_dict: "dict[str, Any]") -> "MCPServerConfig":
        """Create MCPServerConfig from dictionary.

        Servers are enabled by default - if a server is included in the configuration,
        it will be enabled unless explicitly marked as disabled=true.
        """
        # Determine transport type
        transport = "stdio"  # default

        if "url" in config_dict:
            url = config_dict["url"]
            if url.startswith("ws://") or url.startswith("wss://"):
                transport = "websocket"
            elif "/sse" in url:
                transport = "sse"
            else:
                transport = "http"
        elif "command" in config_dict:
            transport = "stdio"

        return cls(
            name=name,
            transport=transport,
            command=config_dict.get("command"),
            args=config_dict.get("args"),
            url=config_dict.get("url"),
            env=config_dict.get("env"),
            headers=config_dict.get("headers"),
            timeout=config_dict.get("timeout"),
            keep_alive=config_dict.get("keep_alive", True),
            disabled=config_dict.get("disabled", False),  # Default to enabled
        )

    def validate(self) -> "list[str]":
        """Validate server configuration and return list of errors."""
        errors = []

        if not self.name:
            errors.append("Server name is required")

        if self.transport == "stdio":
            if not self.command:
                errors.append(
                    f"Command is required for stdio transport (server: {self.name})"
                )
        elif self.transport in ["http", "sse", "websocket"]:
            if not self.url:
                errors.append(
                    f"URL is required for {self.transport} transport (server: {self.name})"
                )
            elif self.transport == "websocket" and not (
                self.url.startswith("ws://") or self.url.startswith("wss://")
            ):
                errors.append(
                    f"WebSocket URL must start with ws:// or wss:// (server: {self.name})"
                )
            elif self.transport == "sse" and "/sse" not in self.url:
                errors.append(
                    f"SSE URL should contain '/sse' path (server: {self.name})"
                )

        if self.timeout is not None and self.timeout <= 0:
            errors.append(f"Timeout must be positive (server: {self.name})")

        return errors


class MCPConfig:
    """
    MCP configuration manager for reading and validating MCP server configurations.

    This class handles loading MCP configurations from JSON files and provides
    validation and access to server configurations.
    """

    def __init__(self, config_data: dict[str, Any] | None = None):
        """
        Initialize MCP configuration.

        Args:
            config_data: Optional configuration dictionary. If None, creates empty config.
        """
        self._config_data = config_data or {}
        self._servers: dict[str, MCPServerConfig] = {}
        self._validation_errors: list[str] = []

        if config_data:
            self._parse_config()

    @classmethod
    def from_file(cls, config_path: str | Path) -> "MCPConfig":
        """
        Load MCP configuration from JSON file.

        Args:
            config_path: Path to the MCP configuration file

        Returns:
            MCPConfig instance loaded from file

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If JSON is invalid
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"MCP config file not found: {config_path}")

        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}") from e

        logger.info(f"Loaded MCP configuration from: {config_path}")
        return cls(config_data)

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "MCPConfig":
        """
        Create MCP configuration from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            MCPConfig instance
        """
        return cls(config_dict)

    def _parse_config(self) -> None:
        """Parse the configuration data and extract server configurations."""
        self._validation_errors = []
        self._servers = {}

        # Handle both old and new MCP config formats
        mcp_servers = self._config_data.get("mcpServers", {})

        if not mcp_servers:
            # Try alternative format
            mcp_servers = self._config_data.get("servers", {})

        if not mcp_servers:
            self._validation_errors.append("No MCP servers found in configuration")
            return

        for server_name, server_config in mcp_servers.items():
            try:
                parsed_config = MCPServerConfig.from_dict(server_name, server_config)

                # Skip disabled servers
                if parsed_config.disabled:
                    logger.info(f"Skipping disabled server: {server_name}")
                    continue

                self._servers[server_name] = parsed_config
                logger.debug(f"Parsed server configuration: {server_name}")
            except Exception as e:
                error_msg = f"Invalid configuration for server '{server_name}': {e}"
                self._validation_errors.append(error_msg)
                logger.error(error_msg)

    def is_valid(self) -> bool:
        """
        Check if the configuration is valid.

        Returns:
            True if configuration is valid, False otherwise
        """
        return len(self._validation_errors) == 0

    def get_validation_errors(self) -> list[str]:
        """
        Get list of validation errors.

        Returns:
            List of validation error messages
        """
        return self._validation_errors.copy()

    def get_server_config(self, server_name: str) -> MCPServerConfig | None:
        """
        Get configuration for a specific server.

        Args:
            server_name: Name of the server

        Returns:
            MCPServerConfig if found, None otherwise
        """
        return self._servers.get(server_name)

    def get_all_servers(self) -> dict[str, MCPServerConfig]:
        """
        Get all server configurations.

        Returns:
            Dictionary mapping server names to their configurations
        """
        return self._servers.copy()

    def get_server_names(self) -> list[str]:
        """
        Get list of all server names.

        Returns:
            List of server names
        """
        return list(self._servers.keys())

    def add_server(self, server_config: MCPServerConfig) -> None:
        """
        Add a server configuration.

        Args:
            server_config: Server configuration to add
        """
        self._servers[server_config.name] = server_config
        logger.info(f"Added server configuration: {server_config.name}")

    def remove_server(self, server_name: str) -> bool:
        """
        Remove a server configuration.

        Args:
            server_name: Name of server to remove

        Returns:
            True if server was removed, False if not found
        """
        if server_name in self._servers:
            del self._servers[server_name]
            logger.info(f"Removed server configuration: {server_name}")
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to dictionary format.

        Returns:
            Configuration as dictionary
        """
        return {
            "mcpServers": {
                name: config.to_dict() for name, config in self._servers.items()
            }
        }

    def save_to_file(self, config_path: str | Path) -> None:
        """
        Save configuration to JSON file.

        Args:
            config_path: Path where to save the configuration
        """
        config_path = Path(config_path)

        config_dict = self.to_dict()

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved MCP configuration to: {config_path}")

    @property
    def servers(self) -> dict[str, MCPServerConfig]:
        """Get all servers (property for backward compatibility)."""
        return self._servers

    def validate_server_config(self, server_config: MCPServerConfig) -> list[str]:
        """
        Validate a single server configuration.

        Args:
            server_config: Server configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate server name
        if not server_config.name:
            errors.append("Server name is required")

        # Validate transport-specific requirements
        if server_config.transport == "stdio":
            if not server_config.command:
                errors.append(
                    f"Command is required for stdio transport (server: {server_config.name})"
                )
        elif server_config.transport in ["http", "sse", "websocket"]:
            if not server_config.url:
                errors.append(
                    f"URL is required for {server_config.transport} transport (server: {server_config.name})"
                )
            elif server_config.transport == "websocket" and not (
                server_config.url.startswith("ws://")
                or server_config.url.startswith("wss://")
            ):
                errors.append(
                    f"WebSocket URL must start with ws:// or wss:// (server: {server_config.name})"
                )
            elif server_config.transport == "sse" and "/sse" not in server_config.url:
                errors.append(
                    f"SSE URL should contain '/sse' path (server: {server_config.name})"
                )
        else:
            errors.append(
                f"Unsupported transport type: {server_config.transport} (server: {server_config.name})"
            )

        # Validate timeout value
        if server_config.timeout is not None and server_config.timeout <= 0:
            errors.append(f"Timeout must be positive (server: {server_config.name})")

        return errors

    def validate_all_servers(self) -> list[str]:
        """
        Validate all server configurations.

        Returns:
            List of all validation errors across all servers
        """
        all_errors = []

        for server_config in self._servers.values():
            errors = self.validate_server_config(server_config)
            all_errors.extend(errors)

        return all_errors


def load_default_mcp_config() -> MCPConfig:
    """
    Load MCP configuration from default locations.

    Searches for mcp.json in:
    1. Current directory
    2. User's home directory
    3. User's config directory
    4. User's .cursor directory (for Cursor IDE)

    Returns:
        MCPConfig instance, empty if no config found
    """
    search_paths = [
        Path.cwd() / "mcp.json",
        Path.home() / "mcp.json",
        Path.home() / ".config" / "mcp.json",
        Path.home() / ".cursor" / "mcp.json",
    ]

    for config_path in search_paths:
        if config_path.exists():
            try:
                return MCPConfig.from_file(config_path)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
                continue

    logger.info("No MCP configuration file found, using empty configuration")
    return MCPConfig()


def create_sample_config() -> dict[str, Any]:
    """
    Create a sample MCP configuration.

    Returns:
        Sample configuration dictionary
    """
    return {
        "mcpServers": {
            "filesystem": {
                "command": "python",
                "args": ["mcp_server_filesystem.py"],
                "env": {"DEBUG": "false"},
            },
            "weather_api": {
                "url": "https://weather-api.example.com/mcp",
                "headers": {"Authorization": "Bearer your-api-key"},
                "timeout": 30.0,
            },
            "local_assistant": {"url": "http://localhost:8000/sse", "keep_alive": True},
        }
    }
