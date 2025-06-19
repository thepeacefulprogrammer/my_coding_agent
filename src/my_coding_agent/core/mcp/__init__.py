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

from .connection_manager import ConnectionEvent, ConnectionManager, ConnectionMetrics
from .error_handler import (
    CircuitBreakerState,
    ErrorCategory,
    ErrorRecoveryStrategy,
    ErrorSeverity,
    MCPCircuitBreaker,
    MCPErrorContext,
    MCPErrorHandler,
    MCPErrorMetrics,
)
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
from .oauth2_auth import (
    OAuth2AuthenticationError,
    OAuth2Authenticator,
    OAuth2Config,
    OAuth2Error,
    OAuth2Token,
    OAuth2TokenExpiredError,
)
from .server_registry import MCPServerRegistry, ServerStatus, ToolRegistry

__all__ = [
    # Core client
    "MCPClient",
    "MCPTool",
    "MCPResource",
    # Exceptions
    "MCPError",
    "MCPConnectionError",
    "MCPProtocolError",
    "MCPTimeoutError",
    # Server registry
    "MCPServerRegistry",
    "ServerStatus",
    "ToolRegistry",
    # Connection management
    "ConnectionManager",
    "ConnectionMetrics",
    "ConnectionEvent",
    # Configuration
    "MCPConfig",
    "MCPServerConfig",
    "load_default_mcp_config",
    "create_sample_config",
    # OAuth 2.0 authentication
    "OAuth2Config",
    "OAuth2Token",
    "OAuth2Authenticator",
    "OAuth2Error",
    "OAuth2AuthenticationError",
    "OAuth2TokenExpiredError",
    # Error handling
    "MCPErrorHandler",
    "MCPErrorContext",
    "MCPErrorMetrics",
    "MCPCircuitBreaker",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorRecoveryStrategy",
    "CircuitBreakerState",
]
