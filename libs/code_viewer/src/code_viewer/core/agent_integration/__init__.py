"""
Agent Integration Package

This package provides the core functionality for integrating with external
agent architecture libraries and managing agent interactions.
"""

from typing import Any, Dict, List, Optional

# Type aliases for agent integration
AgentResponse = dict[str, Any]
AgentConfig = dict[str, Any]


class AgentIntegrationError(Exception):
    """Base exception for agent integration errors."""

    pass


class ConfigManager:
    """Configuration manager for agent integration settings."""

    pass


# Import implementations after defining base types
from .agent_bridge import AgentBridge
from .file_change_handler import FileChangeHandler

# Public API exports
__all__ = [
    "AgentBridge",
    "AgentIntegrationError",
    "FileChangeHandler",
    "ConfigManager",
    "AgentResponse",
    "AgentConfig",
]
