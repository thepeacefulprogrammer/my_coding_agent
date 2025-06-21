"""
Agent Bridge Implementation

This module provides the main AgentBridge class that connects the code viewer
to external agent architecture libraries. It handles query forwarding,
connection management, and file change notifications.
"""

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def import_agent_orchestrator():
    """
    Import agent orchestrator from external agent architecture library.

    This function attempts to import the agent architecture library and
    return the Orchestrator class. It's designed to work with the
    external agent_arch library when available.

    Returns:
        The Orchestrator class from agent architecture library

    Raises:
        ImportError: If agent architecture library is not available
    """
    try:
        # Try to import from the expected agent architecture library
        from agent_arch import AgentOrchestrator, AgentResponse
        return AgentOrchestrator, AgentResponse
    except ImportError as e:
        logger.debug(f"Agent architecture library not available: {e}")
        raise ImportError("Agent architecture library not found") from e


class AgentIntegrationError(Exception):
    """Base exception for agent integration errors."""
    pass


# Type aliases for configuration
AgentConfig = dict[str, Any]


class AgentBridge:
    """
    Bridge class for connecting to agent architecture library.

    This class manages the connection to an external agent architecture library,
    forwards queries to the agent orchestrator, handles file change notifications,
    and provides comprehensive error handling and retry logic.
    """

    def __init__(
        self,
        workspace_path: Path,
        file_change_callback: Callable[[str, str], None] | None = None,
        config: AgentConfig | None = None
    ):
        """
        Initialize the agent bridge.

        Args:
            workspace_path: Path to the workspace directory
            file_change_callback: Optional callback for file change notifications
            config: Optional configuration dictionary
        """
        self.workspace_path = Path(workspace_path)
        self.file_change_callback = file_change_callback
        self.config = self._validate_config(config or {})

        # Connection state
        self._is_connected = False
        self._agent_available = False
        self._orchestrator: Any | None = None

        logger.info(f"AgentBridge initialized for workspace: {workspace_path}")

    def _validate_config(self, config: AgentConfig) -> AgentConfig:
        """
        Validate and normalize configuration.

        Args:
            config: Raw configuration dictionary

        Returns:
            Validated configuration with defaults applied
        """
        defaults = {
            "agent_timeout": 30,
            "retry_attempts": 3,
            "enable_streaming": True
        }

        validated = defaults.copy()

        # Validate each config value
        for key, value in config.items():
            if key == "agent_timeout":
                if isinstance(value, (int, float)) and value > 0:
                    validated[key] = value
                else:
                    logger.warning(f"Invalid agent_timeout: {value}, using default")
            elif key == "retry_attempts":
                if isinstance(value, int) and value >= 0:
                    validated[key] = value
                else:
                    logger.warning(f"Invalid retry_attempts: {value}, using default")
            elif key == "enable_streaming":
                if isinstance(value, bool):
                    validated[key] = value
                else:
                    logger.warning(f"Invalid enable_streaming: {value}, using default")
            else:
                validated[key] = value

        return validated

    @property
    def is_connected(self) -> bool:
        """Check if bridge is connected to agent architecture."""
        return self._is_connected

    @property
    def agent_available(self) -> bool:
        """Check if agent architecture is available and ready."""
        return self._agent_available

    @property
    def status(self) -> str:
        """Get current connection status."""
        if self._is_connected and self._agent_available:
            return "connected"
        else:
            return "disconnected"

    async def initialize_connection(self) -> None:
        """
        Initialize connection to agent architecture.

        Attempts to import and initialize the agent orchestrator from
        the external agent architecture library.

        Raises:
            AgentIntegrationError: If connection initialization fails
        """
        try:
            logger.info("Initializing connection to agent architecture...")

            # Import agent orchestrator
            orchestrator_class, agent_response_class = import_agent_orchestrator()

            # Initialize orchestrator (simplified version doesn't take parameters)
            self._orchestrator = orchestrator_class()

            self._is_connected = True
            self._agent_available = True

            logger.info("Successfully connected to agent architecture")

        except ImportError as e:
            error_msg = f"Failed to import agent architecture: {e}"
            logger.error(error_msg)
            raise AgentIntegrationError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize agent connection: {e}"
            logger.error(error_msg)
            raise AgentIntegrationError(error_msg) from e

    async def cleanup_connection(self) -> None:
        """
        Clean up connection to agent architecture.

        Properly closes the connection and cleans up resources.
        """
        try:
            if self._orchestrator and hasattr(self._orchestrator, 'cleanup'):
                cleanup_method = self._orchestrator.cleanup
                if asyncio.iscoroutinefunction(cleanup_method):
                    await cleanup_method()
                else:
                    cleanup_method()

            self._orchestrator = None
            self._is_connected = False
            self._agent_available = False

            logger.info("Agent connection cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during connection cleanup: {e}")
            # Even if cleanup fails, reset the connection state
            self._orchestrator = None
            self._is_connected = False
            self._agent_available = False

    async def process_query(self, query: str) -> Any:
        """
        Process a query through the agent orchestrator.

        Args:
            query: The query string to process

        Returns:
            Response from the agent orchestrator

        Raises:
            AgentIntegrationError: If query processing fails
        """
        if not self._is_connected or not self._orchestrator:
            raise AgentIntegrationError("Agent bridge is not connected")

            try:
            logger.debug(f"Processing query: {query[:100]}...")

            # Process the query through the orchestrator (expects string message)
            response = await self._orchestrator.process_request(query)

            logger.debug("Query processed successfully")
            return response

            except Exception as e:
            error_msg = f"Failed to process query: {e}"
            logger.error(error_msg)
            raise AgentIntegrationError(error_msg) from e

    async def process_streaming_query(self, query: str, callback: Callable[[str], None]) -> None:
        """
        Process a query with streaming response chunks.

        Args:
            query: The query string to process
            callback: Function to call with each response chunk

        Raises:
            AgentIntegrationError: If query processing fails
        """
        if not self._is_connected or not self._orchestrator:
            raise AgentIntegrationError("Agent bridge is not connected")

        try:
            logger.debug(f"Processing streaming query: {query[:100]}...")

            # Get the full response first
            response = await self.process_query(query)

            # Extract content from response
            if hasattr(response, 'response'):
                content = response.response
            elif hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, dict):
                content = response.get('content', str(response))
            else:
                content = str(response)

            # Simulate streaming by sending chunks word by word
            words = content.split()
            current_chunk = ""

            for i, word in enumerate(words):
                current_chunk += word + " "

                # Send chunk every 2-3 words or at the end
                if (i + 1) % 3 == 0 or i == len(words) - 1:
                    callback(current_chunk)
                    current_chunk = ""

                    # Small delay to simulate real streaming
                    await asyncio.sleep(0.1)

            logger.debug("Streaming query processed successfully")

        except Exception as e:
            error_msg = f"Failed to process streaming query: {e}"
        logger.error(error_msg)
            raise AgentIntegrationError(error_msg) from e

    def _handle_file_change(self, filepath: str, action: str) -> None:
        """
        Handle file change notifications from agent architecture.

        This method is called internally by the agent architecture when
        files are modified during agent operations.

        Args:
            filepath: Path to the changed file
            action: Type of change (modified, created, deleted)
        """
        if self.file_change_callback:
            try:
                self.file_change_callback(filepath, action)
                logger.debug(f"File change callback executed for {filepath} ({action})")
            except Exception as e:
                logger.error(f"Error in file change callback: {e}")
        else:
            logger.debug(f"No file change callback registered for {filepath} ({action})")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup_connection()
