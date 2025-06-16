"""
FastMCP integration module for AI Agent.

This module provides comprehensive Model Context Protocol (MCP) support including:
- FastMCP client wrapper with enhanced functionality
- Configuration management for MCP servers
- Server registry for multi-server management
- Tool and resource discovery across servers
- Connection lifecycle management
- Error handling and recovery
"""

from .mcp_client import (
    MCPClient,
    MCPConnectionError,
    MCPError,
    MCPProtocolError,
    MCPResource,
    MCPTimeoutError,
    MCPTool,
)
from .mcp_config import (
    MCPConfig,
    MCPServerConfig,
    create_sample_config,
    load_default_mcp_config,
)
from .server_registry import (
    MCPServerRegistry,
    ResourceRegistry,
    ServerStatus,
    ToolRegistry,
)

__all__ = [
    # Client classes
    "MCPClient",
    "MCPTool",
    "MCPResource",
    # Exceptions
    "MCPError",
    "MCPConnectionError",
    "MCPProtocolError",
    "MCPTimeoutError",
    # Configuration
    "MCPConfig",
    "MCPServerConfig",
    "load_default_mcp_config",
    "create_sample_config",
    # Registry
    "MCPServerRegistry",
    "ServerStatus",
    "ToolRegistry",
    "ResourceRegistry",
]
