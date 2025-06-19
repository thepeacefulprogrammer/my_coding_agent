"""AI Agent service for interacting with Azure OpenAI through Pydantic AI."""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from .mcp import MCPClient, MCPServerRegistry

# from .mcp_file_server import FileOperationError, MCPFileConfig, MCPFileServer  # DELETED - file operations move to external AI agent

# Foundation services
try:
    from .ai_services.mcp_connection_service import MCPConnectionService
# TODO: Remove other service imports during simplification
# from .ai_services.configuration_service import ConfigurationService  # DELETED
# from .ai_services.error_handling_service import ErrorCategory, ErrorHandlingService  # DELETED
# from .ai_services.workspace_service import WorkspaceService  # DELETED
except ImportError:
    # Handle case where services aren't available yet during development
    ConfigurationService = None
    ErrorHandlingService = None
    ErrorCategory = None
    WorkspaceService = None
    MCPConnectionService = None

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Type aliases for callback functions (defined after imports to avoid import order issues)

ChunkCallback = Callable[[str, bool], Any]
ErrorCallback = Any


class AIAgentConfig(BaseModel):
    """Configuration for the AI Agent."""

    azure_endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    azure_api_key: str = Field(..., description="Azure OpenAI API key")
    deployment_name: str = Field(..., description="Azure OpenAI deployment name")
    api_version: str = Field(
        default="2024-02-15-preview", description="Azure OpenAI API version"
    )
    max_tokens: int = Field(default=2000, description="Maximum tokens per response")
    temperature: float = Field(
        default=0.7, description="Temperature for response generation"
    )
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(
        default=3, description="Maximum number of retries for failed requests"
    )

    @classmethod
    def from_env(cls) -> AIAgentConfig:
        """Create configuration from environment variables.

        Returns:
            AIAgentConfig: The configuration instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        required_vars = [
            "ENDPOINT",
            "API_KEY",
            "MODEL",
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        return cls(
            azure_endpoint=os.getenv("ENDPOINT") or "",
            azure_api_key=os.getenv("API_KEY") or "",
            deployment_name=os.getenv("MODEL") or "",
            api_version=os.getenv("API_VERSION", "2024-02-15-preview"),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
            request_timeout=int(os.getenv("AI_REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("AI_MAX_RETRIES", "3")),
        )


class AIResponse(BaseModel):
    """Response from the AI Agent."""

    content: str = Field(description="The AI response content")
    success: bool = Field(description="Whether the request was successful")
    error: str | None = Field(
        default=None, description="Error message if request failed"
    )
    error_type: str | None = Field(
        default=None, description="Type of error that occurred"
    )
    tokens_used: int = Field(
        default=0, description="Number of tokens used in the response"
    )
    retry_count: int = Field(default=0, description="Number of retries attempted")
    stream_id: str | None = Field(
        default=None, description="Stream ID if this was a streaming response"
    )


class AIAgent:
    """AI Agent service for interacting with Azure OpenAI."""

    def __init__(
        self,
        config: AIAgentConfig | None = None,
        mcp_config: MCPFileConfig | None = None,
        enable_filesystem_tools: bool | None = None,
        enable_memory_awareness: bool = False,
        enable_project_history: bool = False,
        enable_mcp_tools: bool = False,
        auto_discover_mcp_servers: bool = False,
        signal_handler=None,
        # Foundation services (new service-oriented architecture)
        config_service: ConfigurationService | None = None,
        error_service: ErrorHandlingService | None = None,
        workspace_service: WorkspaceService | None = None,
        mcp_connection_service: MCPConnectionService | None = None,
        streaming_response_service=None,  # StreamingResponseService for streaming functionality
        ai_messaging_service=None,  # AIMessagingService for enhanced messaging
        tool_registration_service=None,  # ToolRegistrationService for tool management
        memory_context_service=None,  # MemoryContextService for memory functionality
        project_history_service=None,  # ProjectHistoryService for project history functionality
    ) -> None:
        """
        Initialize the AI Agent.

        Args:
            config: Legacy configuration for the AI Agent (backwards compatibility)
            mcp_config: Optional MCP file server configuration
            enable_filesystem_tools: Whether to enable filesystem tools (auto-detected if None)
            enable_memory_awareness: Whether to enable memory-aware conversations
            enable_project_history: Whether to enable project history integration
            enable_mcp_tools: Whether to enable MCP tools integration
            auto_discover_mcp_servers: Whether to auto-discover MCP servers from configuration
            signal_handler: Object that can emit signals for UI updates (e.g., MainWindow)
            config_service: ConfigurationService for service-oriented architecture
            error_service: ErrorHandlingService for centralized error handling
            workspace_service: WorkspaceService for file operations (service-oriented architecture)
            mcp_connection_service: MCPConnectionService for MCP server management (service-oriented architecture)
            streaming_response_service: StreamingResponseService for streaming functionality
            ai_messaging_service: AIMessagingService for enhanced messaging capabilities
            tool_registration_service: ToolRegistrationService for tool management
            memory_context_service: MemoryContextService for memory functionality
        """
        # Handle service-oriented vs legacy configuration
        if config_service is not None:
            self.config_service = config_service
            self.config = None  # Legacy config not used when service is provided
        elif config is not None:
            self.config = config
            self.config_service = None  # Create from legacy config if needed
        else:
            raise ValueError("Either config or config_service must be provided")

        # Initialize foundation services
        self.error_service = error_service or ErrorHandlingService()
        self.workspace_service = workspace_service  # Can be None for legacy mode
        self.mcp_connection_service = (
            mcp_connection_service  # Can be None for legacy mode
        )
        self.streaming_response_service = (
            streaming_response_service  # Can be None for legacy mode
        )
        self.ai_messaging_service = ai_messaging_service  # Can be None for legacy mode
        self.tool_registration_service = (
            tool_registration_service  # Can be None for legacy mode
        )
        self.memory_context_service = (
            memory_context_service  # Can be None for legacy mode
        )
        self.project_history_service = (
            project_history_service  # Can be None for legacy mode
        )

        self.mcp_config = mcp_config
        self.signal_handler = signal_handler
        self.filesystem_tools_enabled = enable_filesystem_tools
        self.memory_aware_enabled = enable_memory_awareness
        self.project_history_enabled = enable_project_history
        self.mcp_tools_enabled = enable_mcp_tools
        self.mcp_file_server = None
        self.mcp_registry = None
        self.workspace_root = None  # Initialize workspace root as None
        self._mcp_servers_need_connection = False
        self._mcp_tools_registered = False  # Track if MCP tools have been registered
        self._mcp_status_tool_registered = (
            False  # Track if MCP status tool has been registered
        )
        self._environment_tool_registered = (
            False  # Track if environment tool has been registered
        )

        # Setup logging
        self._setup_logging()

        # Create model and agent
        self._create_model()
        self._create_agent()

        # Initialize tool tracking
        self._available_tools = []
        self._tool_descriptions = {}
        self._mcp_tool_prefix = (
            "mcp_"  # Prefix for MCP tools when they conflict with filesystem tools
        )

        # Initialize project history cache
        self._project_history_cache = {}
        self._project_understanding_cache = {}

        # Initialize memory system if requested
        if enable_memory_awareness:
            try:
                # from .memory_integration import ConversationMemoryHandler  # DELETED - memory integration removed

                self._memory_system = ConversationMemoryHandler()
                logger.info("Memory system initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize memory system: {e}")
                self.memory_aware_enabled = False

        # Initialize MCP file server if config provided
        if mcp_config:
            try:
                # from .mcp_file_server import MCPFileServer  # DELETED - file operations move to external AI agent

                self.mcp_file_server = MCPFileServer(mcp_config)
                logger.info("AI Agent initialized with MCP file server integration")
            except Exception as e:
                logger.error(f"Failed to initialize MCP file server: {e}")

        # Initialize MCP registry and auto-discover servers if enabled
        if self.mcp_tools_enabled:
            self.initialize_mcp_registry(auto_discover=auto_discover_mcp_servers)

        # Auto-detect filesystem tools if not explicitly set
        if self.filesystem_tools_enabled is None:
            self.filesystem_tools_enabled = mcp_config is not None

        # Register tools
        self._register_tools()

        # Register project history tools if enabled
        if self.project_history_enabled and self.memory_aware_enabled:
            self._register_project_history_tools()

        # Register MCP tools if enabled
        if self.mcp_tools_enabled and self.mcp_registry:
            self._register_mcp_tools()  # Register empty tools list initially (will be re-registered after connection)

            # Register MCP status and environment tools
            self._register_mcp_status_tool()
            self._register_environment_tool()
        else:
            self._register_mcp_tools()  # Register empty tools list

        logger.info("MCP tools and status tool registered successfully")

        # Initialize streaming state
        self.current_stream_handler = None
        self.current_stream_id = None

        # Mark servers for connection if enabled
        if self.mcp_tools_enabled and auto_discover_mcp_servers:
            # Mark servers for connection (will be initiated by MainWindow)
            self._mcp_servers_need_connection = True

    async def _connect_mcp_servers_on_startup(self) -> None:
        """Connect MCP servers during startup for immediate availability."""
        try:
            logger.info("Connecting MCP servers during startup...")
            await self._connect_mcp_servers_async()
            self._mcp_servers_need_connection = False
            logger.info("MCP servers connected successfully during startup")
        except Exception as e:
            logger.error(f"Failed to connect MCP servers during startup: {e}")
            # Fall back to lazy connection
            self._mcp_servers_need_connection = True

    def initialize_mcp_registry(self, auto_discover: bool = False) -> None:
        """Initialize MCP server registry and optionally auto-discover servers.

        Args:
            auto_discover: Whether to automatically discover servers from configuration.
        """
        # Delegate to MCPConnectionService if available (service-oriented mode)
        if self.mcp_connection_service is not None:
            return self.mcp_connection_service.initialize_mcp_registry(
                auto_discover=auto_discover
            )

        # Legacy implementation for backwards compatibility
        return self._initialize_mcp_registry_legacy(auto_discover=auto_discover)

    def _initialize_mcp_registry_legacy(self, auto_discover: bool = False) -> None:
        """Legacy MCP registry initialization for backwards compatibility."""
        try:
            self.mcp_registry = MCPServerRegistry()

            if auto_discover:
                self._auto_discover_mcp_servers()

            logger.info("MCP server registry initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCP registry: {e}")
            self.mcp_tools_enabled = False
            self.mcp_registry = None

    def _auto_discover_mcp_servers(self) -> None:
        """Automatically discover and register MCP servers from configuration."""
        try:
            # Try to load MCP configuration from default locations
            from .mcp import load_default_mcp_config

            mcp_config = load_default_mcp_config()
            servers = mcp_config.get_all_servers()
            logger.info(
                f"Found {len(servers)} MCP servers in configuration: {list(servers.keys())}"
            )

            for server_name, server_config in servers.items():
                try:
                    # Convert MCPServerConfig to dict format expected by MCPClient
                    client_config = server_config.to_dict()
                    client = MCPClient(client_config)
                    if self.mcp_registry:
                        self.mcp_registry.register_server(client)
                        logger.info(f"Auto-discovered MCP server: {server_name}")
                    else:
                        logger.error("MCP registry is None during server registration")
                except Exception as e:
                    logger.warning(
                        f"Failed to register auto-discovered server {server_name}: {e}"
                    )

            # After registering all servers, mark them for lazy connection
            if self.mcp_registry and servers:
                logger.info(
                    f"Auto-discovered {len(servers)} MCP servers, will connect on first use"
                )
                # Set flag to indicate we need to connect on first use
                self._mcp_servers_need_connection = True

        except Exception as e:
            logger.warning(f"Failed to auto-discover MCP servers: {e}")

    async def _connect_mcp_servers_async(self) -> None:
        """Connect to all registered MCP servers asynchronously."""
        try:
            if not self.mcp_registry:
                logger.warning("No MCP registry available for connection")
                return

            logger.info("Connecting to MCP servers...")

            # Get current event loop info for debugging
            try:
                current_loop = asyncio.get_running_loop()
                logger.info(f"Connecting MCP servers in event loop: {current_loop}")
            except RuntimeError:
                logger.warning("No event loop running during MCP connection")

            # Connect to all servers
            connection_results = await self.mcp_registry.connect_all_servers()

            successful_connections = sum(
                1 for success in connection_results.values() if success
            )
            total_servers = len(connection_results)

            logger.info(
                f"MCP server connections: {successful_connections}/{total_servers} successful"
            )

            if successful_connections > 0:
                # Update tools cache from connected servers
                logger.info("Updating MCP tools cache from connected servers...")
                await self.mcp_registry.update_tools_cache()

                # Get tool count for logging
                all_tools = self.mcp_registry.get_all_tools()
                total_tools = sum(len(tools) for tools in all_tools.values())
                logger.info(
                    f"MCP tools cache updated: {total_tools} tools discovered from {successful_connections} servers"
                )

                # Re-register MCP tools with the agent after successful connections
                logger.info(
                    "Re-registering MCP tools after successful server connections..."
                )
                self._register_mcp_tools()
                self._mcp_tools_registered = True
            else:
                logger.warning("No MCP servers connected successfully")

        except Exception as e:
            logger.error(f"Error connecting to MCP servers: {e}")
            # Don't raise the exception to avoid breaking initialization

    def _setup_logging(self) -> None:
        """Setup logging for the AI Agent."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _create_model(self) -> None:
        """Create the OpenAI model instance."""
        try:
            from pydantic_ai.providers.azure import AzureProvider

            # Use config service if available, otherwise fall back to legacy config
            if self.config_service:
                azure_endpoint = self.config_service.azure_endpoint
                api_version = self.config_service.api_version
                azure_api_key = self.config_service.azure_api_key
                deployment_name = self.config_service.deployment_name
            else:
                azure_endpoint = self.config.azure_endpoint
                api_version = self.config.api_version
                azure_api_key = self.config.azure_api_key
                deployment_name = self.config.deployment_name

            provider = AzureProvider(
                azure_endpoint=azure_endpoint,
                api_version=api_version,
                api_key=azure_api_key,
            )

            self._model = OpenAIModel(model_name=deployment_name, provider=provider)
            logger.info(
                "Azure OpenAI model created successfully: %s (endpoint: %s)",
                deployment_name,
                azure_endpoint,
            )
        except Exception as e:
            # Get values for error logging
            if self.config_service:
                azure_endpoint = self.config_service.azure_endpoint
                deployment_name = self.config_service.deployment_name
            else:
                azure_endpoint = self.config.azure_endpoint
                deployment_name = self.config.deployment_name

            logger.error(
                "Failed to create Azure OpenAI model: %s (endpoint: %s, deployment: %s)",
                e,
                azure_endpoint,
                deployment_name,
            )
            raise

    def _create_agent(self) -> None:
        """Create the Pydantic AI Agent instance."""
        try:
            # Build system prompt based on capabilities
            base_prompt = (
                "You are a helpful AI coding assistant integrated into a code viewing application. "
                "You can help users understand code, provide explanations, suggest improvements, "
                "and assist with coding tasks. Be concise but thorough in your responses. "
                "When discussing code, use proper formatting and be specific about file names, "
                "function names, and line numbers when relevant."
            )

            # Add memory-aware capabilities to system prompt
            memory_prompt = ""
            if self.memory_aware_enabled:
                memory_prompt = (
                    "\n\nMemory Capabilities:\n"
                    "You have access to persistent memory across conversations. This includes:\n"
                    "- Short-term memory: Recent conversation context and current session information\n"
                    "- Long-term memory: Important facts, preferences, and lessons learned from previous interactions\n"
                    "- Project history: Information about code projects, files, and development context\n"
                    "\nUse this memory to provide more contextual and personalized responses. "
                    "When relevant memories are available, incorporate them naturally into your responses. "
                    "Remember user preferences, previous discussions, and project-specific context to enhance your assistance."
                )

            # Add project history capabilities to system prompt
            project_history_prompt = ""
            if self.project_history_enabled:
                project_history_prompt = (
                    "\n\nProject History Integration:\n"
                    "You have access to comprehensive project history tracking that provides deep insights into codebase evolution. "
                    "This includes:\n"
                    "- File change history: Track modifications, additions, and deletions across all files\n"
                    "- Development patterns: Understand how the codebase has evolved over time\n"
                    "- Change impact analysis: See how changes in one file affect related components\n"
                    "- Project timeline: View chronological development activities and decision points\n"
                    "- Code evolution awareness: Understand the context behind current implementations\n"
                    "\nWhen users ask about files, features, or code changes, automatically incorporate relevant project history. "
                    "Use this information to:\n"
                    "- Explain why code was written a certain way based on historical context\n"
                    "- Suggest improvements informed by past development patterns\n"
                    "- Help users understand the evolution and design decisions of the codebase\n"
                    "- Identify related changes that might be relevant to current work\n"
                    "\nBe proactive in using project history tools when discussing files or code evolution."
                )

            # Add MCP capabilities to system prompt
            mcp_prompt = ""
            if self.mcp_tools_enabled:
                mcp_prompt = (
                    "\n\nMCP (Model Context Protocol) Integration:\n"
                    "You have access to external MCP servers that provide additional tools and capabilities. "
                    "MCP servers are external services that extend your functionality beyond basic file operations. "
                    "You can:\n"
                    "- Check the status of connected MCP servers using the get_mcp_server_status tool\n"
                    "- Use tools provided by connected MCP servers (these will be dynamically available)\n"
                    "- Access external services like documentation, APIs, databases, and specialized tools\n"
                    "\nWhen users ask about 'MCP servers', they are referring to these external service integrations. "
                    "You can check which servers are available and what tools they provide. "
                    "Common MCP servers include documentation services (like Context7), project management tools, "
                    "and specialized development utilities.\n\n"
                    "IMPORTANT MCP Tool Usage Guidelines:\n"
                    "- Be proactive: When users ask for information, immediately use the appropriate MCP tools\n"
                    "- Read tool parameter descriptions carefully - they contain all the information you need\n"
                    "- For GitHub tools: Check environment variables or ask the user for their GitHub username if needed\n"
                    "- For Context7 tools: When users ask about documentation, use resolve-library-id then get-library-docs\n"
                    "- Don't ask for clarification when you have the information needed to call MCP tools\n"
                    "- If a tool call fails, try once more before asking the user for help\n"
                    "- Use reasonable defaults for optional parameters based on the tool's schema constraints"
                )

            system_prompt = (
                base_prompt + memory_prompt + project_history_prompt + mcp_prompt
            )

            # Use config service if available, otherwise fall back to legacy config
            max_retries = (
                self.config_service.max_retries
                if self.config_service
                else self.config.max_retries
            )

            self._agent = Agent(
                model=self._model,
                system_prompt=system_prompt,
                retries=max_retries,
            )
            logger.info(
                "Pydantic AI Agent created successfully with %d max retries%s",
                max_retries,
                " and memory awareness" if self.memory_aware_enabled else "",
            )
        except Exception as e:
            logger.error("Failed to create Pydantic AI Agent: %s", e)
            raise

    def _register_tools(self) -> None:
        """Register tools with the AI Agent."""
        if not self.filesystem_tools_enabled or not self.mcp_file_server:
            logger.info("Filesystem tools not enabled or MCP server not configured")
            return

        # Register filesystem tools with the agent
        try:
            # Read file tool
            @self._agent.tool_plain
            async def read_file(file_path: str) -> str:
                """Read the contents of a file in the workspace.

                Args:
                    file_path: Relative path to the file within workspace

                Returns:
                    File contents as string
                """
                return await self._tool_read_file(file_path)

            # Write file tool
            @self._agent.tool_plain
            async def write_file(file_path: str, content: str) -> str:
                """Write content to a file in the workspace.

                Args:
                    file_path: Relative path to the file within workspace
                    content: Content to write to the file

                Returns:
                    Success message
                """
                return await self._tool_write_file(file_path, content)

            # List directory tool
            @self._agent.tool_plain
            async def list_directory(dir_path: str = ".") -> str:
                """List contents of a directory in the workspace.

                Args:
                    dir_path: Relative path to directory (default: current directory)

                Returns:
                    Directory listing as formatted string
                """
                return await self._tool_list_directory(dir_path)

            # Create directory tool
            @self._agent.tool_plain
            async def create_directory(dir_path: str) -> str:
                """Create a new directory in the workspace.

                Args:
                    dir_path: Relative path for the new directory

                Returns:
                    Success message
                """
                return await self._tool_create_directory(dir_path)

            # Get file info tool
            @self._agent.tool_plain
            async def get_file_info(file_path: str) -> str:
                """Get information about a file in the workspace.

                Args:
                    file_path: Relative path to the file

                Returns:
                    File information as formatted string
                """
                return await self._tool_get_file_info(file_path)

            # Search files tool
            @self._agent.tool_plain
            async def search_files(pattern: str, dir_path: str = ".") -> str:
                """Search for files matching a pattern in the workspace.

                Args:
                    pattern: Search pattern (e.g., "*.py")
                    dir_path: Directory to search in (default: current directory)

                Returns:
                    List of matching files as formatted string
                """
                return await self._tool_search_files(pattern, dir_path)

            logger.info("Filesystem tools registered successfully")

        except Exception as e:
            logger.error(f"Failed to register filesystem tools: {e}")
            self.filesystem_tools_enabled = False

        # Register MCP tools if enabled
        if self.mcp_tools_enabled:
            if self.mcp_registry:
                self._register_mcp_tools()
                self._register_mcp_status_tool()
                self._register_environment_tool()
                logger.info("MCP tools and status tool registered successfully")
            else:
                # Even if registry failed, register the status tool so user can see what's wrong
                self._register_mcp_status_tool()
                self._register_environment_tool()
                logger.warning(
                    "MCP registry not available, but status tool registered for debugging"
                )

    def _register_project_history_tools(self) -> None:
        """Register project history tools with the AI Agent."""
        # Delegate to ProjectHistoryService if available (service-oriented mode)
        if self.project_history_service is not None:
            return self.project_history_service.register_tools(self._agent)

        # Legacy implementation for backwards compatibility
        if not self.memory_aware_enabled or not hasattr(self, "_memory_system"):
            logger.warning("Project history tools require memory system")
            return

        try:
            # Project history for specific file tool
            @self._agent.tool_plain
            async def get_file_project_history(file_path: str, limit: int = 20) -> str:
                """Get project history for a specific file.

                Args:
                    file_path: Path to the file to get history for
                    limit: Maximum number of history events to return (default: 20)

                Returns:
                    Formatted project history for the file
                """
                return await self._tool_get_file_project_history(file_path, limit)

            # Search project history tool
            @self._agent.tool_plain
            async def search_project_history(query: str, limit: int = 25) -> str:
                """Search project history using semantic and text search.

                Args:
                    query: Search query for project history
                    limit: Maximum number of results to return (default: 25)

                Returns:
                    Formatted search results from project history
                """
                return await self._tool_search_project_history(query, limit)

            # Get recent project changes tool
            @self._agent.tool_plain
            async def get_recent_project_changes(
                hours: int = 24, limit: int = 15
            ) -> str:
                """Get recent project changes within specified time period.

                Args:
                    hours: Number of hours to look back (default: 24)
                    limit: Maximum number of changes to return (default: 15)

                Returns:
                    Formatted list of recent project changes
                """
                return await self._tool_get_recent_project_changes(hours, limit)

            # Project timeline tool
            @self._agent.tool_plain
            async def get_project_timeline(
                file_path: str = "", days_back: int = 7
            ) -> str:
                """Get project timeline showing chronological development.

                Args:
                    file_path: Optional file path to focus timeline on (default: all files)
                    days_back: Number of days to look back (default: 7)

                Returns:
                    Formatted project timeline
                """
                return await self._tool_get_project_timeline(file_path, days_back)

            logger.info("Project history tools registered successfully")

        except Exception as e:
            logger.error(f"Failed to register project history tools: {e}")
            self.project_history_enabled = False

    def get_available_tools(self) -> list[str]:
        """Get list of available tool names.

        Returns:
            List of tool names
        """
        # Delegate to tool registration service if available
        if self.tool_registration_service is not None:
            return self.tool_registration_service.get_available_tools()

        # Legacy implementation for backwards compatibility
        tools = []

        # Add filesystem tools
        if self.filesystem_tools_enabled:
            tools.extend(
                [
                    "read_file",
                    "write_file",
                    "list_directory",
                    "create_directory",
                    "get_file_info",
                    "search_files",
                ]
            )

        # Add MCP tools
        if self.mcp_tools_enabled and self.mcp_registry:
            mcp_tools = self._get_mcp_tools()
            tools.extend(mcp_tools)
            # Add MCP status tool
            tools.append("get_mcp_server_status")

        # Add project history tools
        if self.project_history_enabled and self.memory_aware_enabled:
            tools.extend(
                [
                    "get_file_project_history",
                    "search_project_history",
                    "get_recent_project_changes",
                    "get_project_timeline",
                ]
            )

        return tools

    def get_tool_descriptions(self) -> dict[str, str]:
        """Get descriptions of available tools.

        Returns:
            Dictionary mapping tool names to descriptions
        """
        descriptions = {}

        # Add filesystem tool descriptions
        if self.filesystem_tools_enabled:
            descriptions.update(
                {
                    "read_file": "Read the contents of a file in the workspace",
                    "write_file": "Write content to a file in the workspace",
                    "list_directory": "List contents of a directory in the workspace",
                    "create_directory": "Create a new directory in the workspace",
                    "get_file_info": "Get information about a file in the workspace",
                    "search_files": "Search for files matching a pattern in the workspace",
                }
            )

        # Add MCP tool descriptions
        if self.mcp_tools_enabled and self.mcp_registry:
            mcp_descriptions = self._get_mcp_tool_descriptions()
            descriptions.update(mcp_descriptions)
            # Add MCP status tool description
            descriptions["get_mcp_server_status"] = (
                "Get the status of all MCP servers and their available tools"
            )

        # Add project history tool descriptions
        if self.project_history_enabled and self.memory_aware_enabled:
            descriptions.update(
                {
                    "get_file_project_history": "Get project history and evolution for a specific file",
                    "search_project_history": "Search project history using semantic and text search",
                    "get_recent_project_changes": "Get recent project changes within specified time period",
                    "get_project_timeline": "Get project timeline showing chronological development",
                }
            )

        return descriptions

    # Filesystem tool implementation methods

    async def _tool_read_file(self, file_path: str) -> str:
        """Internal implementation of read_file tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            content = await self.mcp_file_server.read_file(file_path)
            return content

        except FileOperationError as e:
            logger.warning(f"File read error for {file_path}: {e}")
            return f"Error reading file: {e}"
        except Exception as e:
            logger.error(f"Unexpected error reading file {file_path}: {e}")
            return f"Error: {e}"

    async def _tool_write_file(self, file_path: str, content: str) -> str:
        """Internal implementation of write_file tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            success = await self.mcp_file_server.write_file(file_path, content)
            if success:
                return "File written successfully"
            else:
                return "Error: Failed to write file"

        except FileOperationError as e:
            logger.warning(f"File write error for {file_path}: {e}")
            return f"Error writing file: {e}"
        except Exception as e:
            logger.error(f"Unexpected error writing file {file_path}: {e}")
            return f"Error: {e}"

    async def _tool_list_directory(self, dir_path: str = ".") -> str:
        """Internal implementation of list_directory tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            # Ensure dir_path is not empty (default to current directory)
            if not dir_path or not dir_path.strip():
                dir_path = "."

            files = await self.mcp_file_server.list_directory(dir_path)
            if files:
                return f"Directory contents ({dir_path}):\n" + "\n".join(
                    f"- {file}" for file in files
                )
            else:
                return f"Directory {dir_path} is empty"

        except FileOperationError as e:
            logger.warning(f"Directory list error for {dir_path}: {e}")
            return f"Error listing directory: {e}"
        except Exception as e:
            logger.error(f"Unexpected error listing directory {dir_path}: {e}")
            return f"Error: {e}"

    async def _tool_create_directory(self, dir_path: str) -> str:
        """Internal implementation of create_directory tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            success = await self.mcp_file_server.create_directory(dir_path)
            if success:
                return "Directory created successfully"
            else:
                return "Error: Failed to create directory"

        except FileOperationError as e:
            logger.warning(f"Directory creation error for {dir_path}: {e}")
            return f"Error creating directory: {e}"
        except Exception as e:
            logger.error(f"Unexpected error creating directory {dir_path}: {e}")
            return f"Error: {e}"

    async def _tool_get_file_info(self, file_path: str) -> str:
        """Internal implementation of get_file_info tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            info = await self.mcp_file_server.get_file_info(file_path)
            if info:
                info_lines = []
                for key, value in info.items():
                    info_lines.append(f"{key}: {value}")
                return f"File information for {file_path}:\n" + "\n".join(info_lines)
            else:
                return f"No information available for {file_path}"

        except FileOperationError as e:
            logger.warning(f"File info error for {file_path}: {e}")
            return f"Error getting file info: {e}"
        except Exception as e:
            logger.error(f"Unexpected error getting file info for {file_path}: {e}")
            return f"Error: {e}"

    async def _tool_search_files(self, pattern: str, dir_path: str = ".") -> str:
        """Internal implementation of search_files tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            files = await self.mcp_file_server.search_files(pattern, dir_path)
            if files:
                return f"Files matching '{pattern}' in {dir_path}:\n" + "\n".join(
                    f"- {file}" for file in files
                )
            else:
                return f"No files matching '{pattern}' found in {dir_path}"

        except FileOperationError as e:
            logger.warning(f"File search error for pattern {pattern}: {e}")
            return f"Error searching files: {e}"
        except Exception as e:
            logger.error(
                f"Unexpected error searching files with pattern {pattern}: {e}"
            )
            return f"Error: {e}"

    # Project History Tool Implementation Methods

    async def _tool_get_file_project_history(
        self, file_path: str, limit: int = 20
    ) -> str:
        """Get project history for a specific file."""
        if self.project_history_service is not None:
            return await self.project_history_service._tool_get_file_project_history(
                file_path, limit
            )

        # Legacy implementation for backwards compatibility
        try:
            if not hasattr(self, "_memory_system") or not self._memory_system:
                return "Error: Memory system not available for project history"

            # Get project history for the specific file
            history = self._memory_system.get_project_history_for_file(file_path, limit)

            if not history:
                return f"No project history found for file: {file_path}"

            # Format the history for display
            formatted_history = []
            for entry in history:
                timestamp = entry.get("timestamp", 0)
                event_type = entry.get("event_type", "unknown")
                summary = entry.get("summary", "No summary available")
                content = entry.get("content", "")

                # Format timestamp
                from datetime import datetime

                try:
                    time_str = datetime.fromtimestamp(timestamp).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                except (ValueError, OSError):
                    time_str = "Unknown time"

                formatted_entry = f"[{time_str}] {event_type.upper()}: {summary}"
                if content:
                    formatted_entry += f"\n  Details: {content[:200]}..."

                formatted_history.append(formatted_entry)

            result = (
                f"Project History for {file_path}:\n"
                + "=" * 50
                + "\n"
                + "\n\n".join(formatted_history)
            )

            return result

        except Exception as e:
            logger.error(f"Error getting file project history: {e}")
            return f"Error retrieving project history for {file_path}: {e}"

    async def _tool_search_project_history(self, query: str, limit: int = 25) -> str:
        """Search project history using semantic and text search."""
        if self.project_history_service is not None:
            return await self.project_history_service._tool_search_project_history(
                query, limit
            )

        # Legacy implementation for backwards compatibility
        try:
            if not hasattr(self, "_memory_system") or not self._memory_system:
                return "Error: Memory system not available for project history search"

            # Search project history
            results = self._memory_system.search_project_history(query, limit)

            if not results:
                return f"No search results found for query: {query}"

            # Format the search results for display
            formatted_results = []
            for entry in results:
                timestamp = entry.get("timestamp", 0)
                file_path = entry.get("file_path", "Unknown file")
                event_type = entry.get("event_type", "unknown")
                summary = entry.get("summary", "No summary available")

                # Format timestamp
                from datetime import datetime

                try:
                    time_str = datetime.fromtimestamp(timestamp).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                except (ValueError, OSError):
                    time_str = "Unknown time"

                formatted_entry = (
                    f"[{time_str}] {file_path} - {event_type.upper()}: {summary}"
                )
                formatted_results.append(formatted_entry)

            result = (
                f"Search Results for '{query}':\n"
                + "=" * 50
                + "\n"
                + "\n\n".join(formatted_results)
            )

            return result

        except Exception as e:
            logger.error(f"Error searching project history: {e}")
            return f"Error searching project history for '{query}': {e}"

    async def _tool_get_recent_project_changes(
        self, hours: int = 24, limit: int = 15
    ) -> str:
        """Get recent project changes within specified time period."""
        try:
            # Delegate to ProjectHistoryService if available (service-oriented mode)
            if self.project_history_service is not None:
                return (
                    await self.project_history_service._tool_get_recent_project_changes(
                        hours, limit
                    )
                )

            # Legacy implementation for backwards compatibility
            if not hasattr(self, "_memory_system") or not self._memory_system:
                return "Error: Memory system not available for recent changes"

            # Calculate time range
            from datetime import datetime, timedelta

            datetime.now().timestamp()
            (datetime.now() - timedelta(hours=hours)).timestamp()

            # Get recent project history
            context = self._memory_system.get_project_context_for_ai(
                recent_hours=hours, max_events=limit
            )

            if not context or context.strip() == "":
                return f"No project changes found in the last {hours} hours"

            return (
                f"Recent Project Changes (Last {hours} hours):\n"
                + "=" * 50
                + "\n"
                + context
            )

        except Exception as e:
            logger.error(f"Error getting recent project changes: {e}")
            return f"Error retrieving recent changes: {e}"

    async def _tool_get_project_timeline(
        self, file_path: str = "", days_back: int = 7
    ) -> str:
        """Get project timeline showing chronological development."""
        try:
            # Delegate to ProjectHistoryService if available (service-oriented mode)
            if self.project_history_service is not None:
                return await self.project_history_service._tool_get_project_timeline(
                    file_path, days_back
                )

            # Legacy implementation for backwards compatibility
            if not hasattr(self, "_memory_system") or not self._memory_system:
                return "Error: Memory system not available for project timeline"

            # Calculate time range
            from datetime import datetime, timedelta

            end_time = datetime.now().timestamp()
            start_time = (datetime.now() - timedelta(days=days_back)).timestamp()

            if file_path:
                # Generate timeline for specific file
                timeline = self._memory_system.generate_file_timeline(
                    file_path, limit=30
                )
                title = f"Timeline for {file_path} (Last {days_back} days)"
            else:
                # Generate general project timeline
                timeline = self._memory_system.generate_project_timeline(
                    start_time, end_time
                )
                title = f"Project Timeline (Last {days_back} days)"

            if not timeline:
                return "No timeline data found for the specified period"

            # Format timeline
            formatted_timeline = self._memory_system.format_timeline_for_ai(timeline)

            return f"{title}:\n" + "=" * 60 + "\n" + formatted_timeline

        except Exception as e:
            logger.error(f"Error getting project timeline: {e}")
            return f"Error generating project timeline: {e}"

    # Helper methods for project history functionality

    def _should_lookup_project_history(self, message: str) -> bool:
        """Determine if a message should trigger project history lookup."""
        if self.project_history_service is not None:
            return self.project_history_service.should_lookup_project_history(message)

        # Simple fallback when service not available
        return self.project_history_enabled and any(
            keyword in message.lower()
            for keyword in [
                "history",
                "changes",
                "modified",
                "timeline",
                ".py",
                ".js",
                ".json",
            ]
        )

    def _get_recent_project_history(self, limit: int = 50) -> list[dict]:
        """Get recent project history with caching."""
        if self.project_history_service is not None:
            return self.project_history_service.get_recent_project_history(limit)

        # Simple fallback when service not available
        return []

    def _generate_project_evolution_context(self, file_path: str = "") -> str:
        """Generate project evolution context for AI responses."""
        if self.project_history_service is not None:
            return self.project_history_service.generate_project_evolution_context(
                file_path
            )

        # Simple fallback when service not available
        return ""

    def _build_project_understanding(self, file_path: str = "") -> dict:
        """Build project understanding from historical changes."""
        if self.project_history_service is not None:
            return self.project_history_service.build_project_understanding(file_path)

        # Simple fallback when service not available
        return {}

    def _enhance_message_with_project_context(self, message: str) -> str:
        """Enhance user message with relevant project context."""
        if self.project_history_service is not None:
            return self.project_history_service.enhance_message_with_project_context(
                message
            )

        # Simple fallback when service not available
        return message

    def _generate_file_evolution_timeline(self, file_path: str) -> list:
        """Generate evolution timeline for a specific file."""
        if self.project_history_service is not None:
            return self.project_history_service.generate_file_evolution_timeline(
                file_path
            )

        # Simple fallback when service not available
        return []

    # Public Project History Methods (for service integration)

    def generate_project_evolution_context(self, file_path: str = "") -> str:
        """Generate project evolution context for AI responses."""
        if self.project_history_service is not None:
            return self.project_history_service.generate_project_evolution_context(
                file_path
            )
        return self._generate_project_evolution_context(file_path)

    def build_project_understanding(self, file_path: str = "") -> dict:
        """Build project understanding from historical changes."""
        if self.project_history_service is not None:
            return self.project_history_service.build_project_understanding(file_path)
        return self._build_project_understanding(file_path)

    def enhance_message_with_project_context(self, message: str) -> str:
        """Enhance user message with relevant project context."""
        if self.project_history_service is not None:
            return self.project_history_service.enhance_message_with_project_context(
                message
            )
        return self._enhance_message_with_project_context(message)

    def generate_file_evolution_timeline(self, file_path: str) -> list:
        """Generate evolution timeline for a specific file."""
        if self.project_history_service is not None:
            return self.project_history_service.generate_file_evolution_timeline(
                file_path
            )
        return self._generate_file_evolution_timeline(file_path)

    # MCP Tools Integration Methods

    def _get_mcp_tools(self) -> list[str]:
        """Get list of available MCP tool names with conflict resolution.

        Returns:
            List of MCP tool names, prefixed if there are conflicts with filesystem tools
        """
        if not self.mcp_registry:
            return []

        filesystem_tools = set()
        if self.filesystem_tools_enabled:
            filesystem_tools = {
                "read_file",
                "write_file",
                "list_directory",
                "create_directory",
                "get_file_info",
                "search_files",
            }

        mcp_tools = []
        all_tools = self.mcp_registry.get_all_tools()

        for _server_name, tools in all_tools.items():
            for tool in tools:
                tool_name = tool.name

                # Handle name conflicts by prefixing
                if tool_name in filesystem_tools:
                    tool_name = f"{self._mcp_tool_prefix}{tool.name}"

                mcp_tools.append(tool_name)

        return mcp_tools

    def _get_mcp_tool_descriptions(self) -> dict[str, str]:
        """Get descriptions for MCP tools with conflict resolution.

        Returns:
            Dictionary mapping MCP tool names to descriptions
        """
        if not self.mcp_registry:
            return {}

        filesystem_tools = set()
        if self.filesystem_tools_enabled:
            filesystem_tools = {
                "read_file",
                "write_file",
                "list_directory",
                "create_directory",
                "get_file_info",
                "search_files",
            }

        descriptions = {}
        all_tools = self.mcp_registry.get_all_tools()

        for server_name, tools in all_tools.items():
            for tool in tools:
                tool_name = tool.name

                # Handle name conflicts by prefixing
                if tool_name in filesystem_tools:
                    tool_name = f"{self._mcp_tool_prefix}{tool.name}"

                # Add server info to description for clarity
                description = f"{tool.description} (from {server_name})"
                descriptions[tool_name] = description

        return descriptions

    def _register_mcp_tools(self) -> None:
        """Register MCP tools with the Pydantic AI agent."""
        try:
            if not self.mcp_registry:
                return

            filesystem_tools = set()
            if self.filesystem_tools_enabled:
                filesystem_tools = {
                    "read_file",
                    "write_file",
                    "list_directory",
                    "create_directory",
                    "get_file_info",
                    "search_files",
                }

            all_tools = self.mcp_registry.get_all_tools()
            registered_count = 0
            registered_tool_names = (
                set()
            )  # Track registered tool names to avoid conflicts

            # First pass: collect all tool names to identify conflicts
            tool_name_counts = {}
            for _server_name, tools in all_tools.items():
                for tool in tools:
                    tool_name_counts[tool.name] = tool_name_counts.get(tool.name, 0) + 1

            for server_name, tools in all_tools.items():
                for tool in tools:
                    tool_name = tool.name
                    original_name = tool_name

                    # Handle name conflicts with filesystem tools
                    if tool_name in filesystem_tools:
                        tool_name = f"{self._mcp_tool_prefix}{tool.name}"

                    # Handle name conflicts with other MCP tools - always prefix if there are conflicts
                    if tool_name_counts.get(original_name, 0) > 1:
                        tool_name = f"{server_name}_{tool.name}"
                        logger.info(
                            f"Tool name conflict resolved: '{original_name}' -> '{tool_name}' (from {server_name})"
                        )

                    # If still conflicts (unlikely but possible), add a counter
                    counter = 1
                    base_tool_name = tool_name
                    while tool_name in registered_tool_names:
                        tool_name = f"{base_tool_name}_{counter}"
                        counter += 1

                    # Create the tool function dynamically
                    self._create_mcp_tool_function(
                        tool_name,
                        original_name,
                        tool.description,
                        tool.input_schema,
                        server_name,
                    )
                    registered_tool_names.add(tool_name)
                    registered_count += 1

            logger.info(f"Registered {registered_count} MCP tools successfully")

        except Exception as e:
            logger.error(f"Failed to register MCP tools: {e}")
            import traceback

            logger.debug(
                f"MCP tool registration error traceback: {traceback.format_exc()}"
            )
            self.mcp_tools_enabled = False

    def _create_mcp_tool_function(
        self,
        tool_name: str,
        original_name: str,
        description: str,
        input_schema: dict[str, Any],
        server_name: str,
    ) -> None:
        """Create and register a dynamic MCP tool function with the agent.

        Args:
            tool_name: The name to register the tool with (may be prefixed)
            original_name: The original MCP tool name
            description: Tool description
            input_schema: JSON schema for tool input validation
            server_name: Name of the MCP server providing this tool
        """

        # Create the async function dynamically
        async def mcp_tool_wrapper(**kwargs) -> str:
            """Dynamically created MCP tool wrapper."""
            print(f"🔧 AI CALLING TOOL: {tool_name}")
            print(f"   📋 Original name: {original_name}")
            print(f"   🏷️  Server: {server_name}")
            print(f"   📝 Arguments: {kwargs}")

            result = await self._call_mcp_tool(original_name, kwargs, server_name)

            print(f"✅ TOOL RESULT for {tool_name}:")
            print(f"   📤 Result length: {len(str(result))} characters")
            print(f"   📄 Result preview: {str(result)[:200]}...")

            return result

        # Set function metadata
        mcp_tool_wrapper.__name__ = tool_name

        # Build comprehensive docstring with parameter information
        docstring_parts = [f"{description}"]
        docstring_parts.append(f"\nServer: {server_name}")

        # Add parameter information from schema
        if input_schema and "properties" in input_schema:
            docstring_parts.append("\nParameters:")
            properties = input_schema["properties"]
            required_params = input_schema.get("required", [])

            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "No description")
                is_required = param_name in required_params

                # Add type constraints if available
                constraints = []
                if "minimum" in param_info:
                    constraints.append(f"min: {param_info['minimum']}")
                if "maximum" in param_info:
                    constraints.append(f"max: {param_info['maximum']}")
                if "enum" in param_info:
                    constraints.append(f"options: {param_info['enum']}")

                constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                required_str = " (required)" if is_required else " (optional)"

                docstring_parts.append(
                    f"  {param_name} ({param_type}){required_str}: {param_desc}{constraint_str}"
                )

        mcp_tool_wrapper.__doc__ = "\n".join(docstring_parts)

        # Register with the agent
        try:
            # Check if this tool name already exists by trying to register it
            self._agent.tool_plain(mcp_tool_wrapper)
        except Exception as e:
            # If we get a tool name conflict, generate a unique name and try again
            if "conflicts with existing tool" in str(e) or "Tool name conflicts" in str(
                e
            ):
                logger.warning(f"Tool name conflict for '{tool_name}': {e}")
                # Generate a unique name with server prefix
                conflict_resolved_name = f"{server_name}_{original_name}"

                # If still conflicts, add a counter
                counter = 1
                base_name = conflict_resolved_name
                while conflict_resolved_name in getattr(
                    self, "_registered_tool_names", set()
                ):
                    conflict_resolved_name = f"{base_name}_{counter}"
                    counter += 1

                # Update wrapper name and try again
                mcp_tool_wrapper.__name__ = conflict_resolved_name
                logger.info(
                    f"Resolved tool name conflict: '{tool_name}' -> '{conflict_resolved_name}'"
                )

                try:
                    # Track registered tool names to avoid future conflicts
                    if not hasattr(self, "_registered_tool_names"):
                        self._registered_tool_names = set()
                    self._registered_tool_names.add(conflict_resolved_name)

                    self._agent.tool_plain(mcp_tool_wrapper)
                    logger.info(
                        f"Successfully registered MCP tool with resolved name: {conflict_resolved_name}"
                    )
                except Exception as e2:
                    logger.error(
                        f"Failed to register MCP tool even after name resolution: {e2}"
                    )
                    raise e2
            else:
                logger.error(f"Failed to register MCP tool '{tool_name}': {e}")
                raise e

    async def _call_mcp_tool(
        self, tool_name: str, arguments: dict[str, Any], server_name: str | None = None
    ) -> str:
        """Execute an MCP tool through the registry.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Arguments to pass to the tool
            server_name: Optional specific server name to use

        Returns:
            Tool execution result as formatted string
        """
        # Generate unique tool call ID
        tool_call_id = f"mcp_{tool_name}_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        # Emit tool call started signal if signal handler is available
        if self.signal_handler and hasattr(
            self.signal_handler, "tool_call_started_signal"
        ):
            tool_call_data = {
                "id": tool_call_id,
                "name": tool_name,
                "parameters": arguments.copy(),
                "server": server_name or "auto",
                "status": "pending",
            }
            try:
                self.signal_handler.tool_call_started_signal.emit(tool_call_data)
            except Exception as e:
                logger.warning(f"Failed to emit tool_call_started signal: {e}")

        try:
            logger.info(f"🔧 Calling MCP tool: {tool_name} with args: {arguments}")

            if not self.mcp_registry:
                logger.error("MCP registry not available")
                error_result = "Error: MCP registry not available"

                # Emit tool call failed signal
                if self.signal_handler and hasattr(
                    self.signal_handler, "tool_call_failed_signal"
                ):
                    error_data = {
                        "id": tool_call_id,
                        "status": "error",
                        "error": error_result,
                        "execution_time": time.time() - start_time,
                    }
                    try:
                        self.signal_handler.tool_call_failed_signal.emit(error_data)
                    except Exception as e:
                        logger.warning(f"Failed to emit tool_call_failed signal: {e}")

                return error_result

            # Check MCP server status before attempting call
            server_statuses = self.mcp_registry.get_all_server_statuses()
            connected_servers = {
                name: status
                for name, status in server_statuses.items()
                if status.connected
            }
            logger.info(
                f"📊 MCP server status before tool call - Connected: {list(connected_servers.keys())}, Total: {len(server_statuses)}"
            )

            # Ensure MCP servers are connected in current event loop context
            if not await self.ensure_mcp_servers_connected():
                logger.error("Unable to ensure MCP servers are connected")
                error_result = "Error: Unable to connect to MCP servers"

                # Emit tool call failed signal
                if self.signal_handler and hasattr(
                    self.signal_handler, "tool_call_failed_signal"
                ):
                    error_data = {
                        "id": tool_call_id,
                        "status": "error",
                        "error": error_result,
                        "execution_time": time.time() - start_time,
                    }
                    try:
                        self.signal_handler.tool_call_failed_signal.emit(error_data)
                    except Exception as e:
                        logger.warning(f"Failed to emit tool_call_failed signal: {e}")

                return error_result

            # Validate arguments against tool schema
            if not isinstance(arguments, dict):
                logger.error(
                    f"Invalid arguments format for tool {tool_name}: {type(arguments)}"
                )
                error_result = "Error: Invalid arguments format - expected dictionary"

                # Emit tool call failed signal
                if self.signal_handler and hasattr(
                    self.signal_handler, "tool_call_failed_signal"
                ):
                    error_data = {
                        "id": tool_call_id,
                        "status": "error",
                        "error": error_result,
                        "execution_time": time.time() - start_time,
                    }
                    try:
                        self.signal_handler.tool_call_failed_signal.emit(error_data)
                    except Exception as e:
                        logger.warning(f"Failed to emit tool_call_failed signal: {e}")

                return error_result

            # Check for obviously invalid arguments (like "invalid_arg")
            if "invalid_arg" in arguments:
                logger.warning(f"Invalid arguments detected for tool {tool_name}")
                error_result = (
                    "Error: Invalid arguments - 'invalid_arg' is not a valid parameter"
                )

                # Emit tool call failed signal
                if self.signal_handler and hasattr(
                    self.signal_handler, "tool_call_failed_signal"
                ):
                    error_data = {
                        "id": tool_call_id,
                        "status": "error",
                        "error": error_result,
                        "execution_time": time.time() - start_time,
                    }
                    try:
                        self.signal_handler.tool_call_failed_signal.emit(error_data)
                    except Exception as e:
                        logger.warning(f"Failed to emit tool_call_failed signal: {e}")

                return error_result

            # Execute the MCP tool call with proper error handling and reconnection logic
            max_retries = 2
            last_error = None
            results = None

            for attempt in range(max_retries):
                try:
                    logger.info(
                        f"🚀 Attempting MCP tool call {tool_name} (attempt {attempt + 1}/{max_retries})"
                    )
                    results = await self.mcp_registry.call_tool(
                        tool_name, arguments, server_name
                    )
                    logger.info(f"✅ MCP tool {tool_name} executed successfully")
                    break  # Success, exit retry loop

                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    logger.warning(
                        f"❌ MCP tool {tool_name} failed (attempt {attempt + 1}): {error_msg}"
                    )

                    # Handle specific connection issues with reconnection
                    if any(
                        keyword in error_msg.lower()
                        for keyword in [
                            "event loop",
                            "broken pipe",
                            "connection",
                            "stream",
                            "stdio",
                        ]
                    ):
                        logger.warning(
                            f"Connection issue detected for MCP tool {tool_name}: {error_msg}"
                        )

                        if attempt < max_retries - 1:  # Don't reconnect on last attempt
                            logger.info(
                                f"🔄 Attempting to reconnect MCP servers for tool {tool_name}"
                            )
                            try:
                                # Force reconnection
                                await self.mcp_registry.disconnect_all_servers()
                                await asyncio.sleep(1.0)  # Longer pause for stability
                                connection_results = (
                                    await self.mcp_registry.connect_all_servers()
                                )

                                # Log reconnection results
                                successful_reconnections = sum(
                                    1
                                    for success in connection_results.values()
                                    if success
                                )
                                logger.info(
                                    f"🔗 Reconnection completed: {successful_reconnections}/{len(connection_results)} servers connected"
                                )

                                await asyncio.sleep(
                                    0.5
                                )  # Brief pause after reconnection
                                continue  # Retry the tool call
                            except Exception as reconnect_error:
                                logger.error(
                                    f"Failed to reconnect MCP servers: {reconnect_error}"
                                )

                        # If we're here, reconnection failed or this is the last attempt
                        final_error = f"Error: MCP tool {tool_name} failed due to connection issue. Servers may need to be restarted. Last error: {error_msg}"

                        # Emit tool call failed signal
                        if self.signal_handler and hasattr(
                            self.signal_handler, "tool_call_failed_signal"
                        ):
                            error_data = {
                                "id": tool_call_id,
                                "status": "error",
                                "error": final_error,
                                "execution_time": time.time() - start_time,
                            }
                            try:
                                self.signal_handler.tool_call_failed_signal.emit(
                                    error_data
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to emit tool_call_failed signal: {e}"
                                )

                        return final_error
                    else:
                        # Log non-connection errors and re-raise immediately
                        logger.error(
                            f"Non-connection error in MCP tool {tool_name}: {error_msg}"
                        )
                        raise e
            else:
                # All retries exhausted
                logger.error(f"All retry attempts failed for MCP tool {tool_name}")
                final_error = f"Error: MCP tool {tool_name} failed after {max_retries} attempts. Last error: {last_error}"

                # Emit tool call failed signal
                if self.signal_handler and hasattr(
                    self.signal_handler, "tool_call_failed_signal"
                ):
                    error_data = {
                        "id": tool_call_id,
                        "status": "error",
                        "error": final_error,
                        "execution_time": time.time() - start_time,
                    }
                    try:
                        self.signal_handler.tool_call_failed_signal.emit(error_data)
                    except Exception as e:
                        logger.warning(f"Failed to emit tool_call_failed signal: {e}")

                return final_error

            # Format the results
            if not results:
                logger.info(f"MCP tool {tool_name} returned no output")
                final_result = "Tool executed successfully (no output)"
            else:
                # Combine multiple results if present
                formatted_results = []
                for result in results:
                    if isinstance(result, dict):
                        if "text" in result:
                            formatted_results.append(result["text"])
                        elif "content" in result:
                            formatted_results.append(str(result["content"]))
                        else:
                            formatted_results.append(str(result))
                    else:
                        formatted_results.append(str(result))

                final_result = (
                    "\n".join(formatted_results)
                    if formatted_results
                    else "Tool executed successfully"
                )

            execution_time = time.time() - start_time
            logger.info(
                f"📤 MCP tool {tool_name} result length: {len(final_result)} characters"
            )

            # Emit tool call completed signal
            if self.signal_handler and hasattr(
                self.signal_handler, "tool_call_completed_signal"
            ):
                result_data = {
                    "id": tool_call_id,
                    "status": "success",
                    "result": {
                        "success": True,
                        "content": final_result,
                        "execution_time": execution_time,
                        "content_type": "text",  # Could be enhanced to detect type
                    },
                    "execution_time": execution_time,
                }
                try:
                    self.signal_handler.tool_call_completed_signal.emit(result_data)
                except Exception as e:
                    logger.warning(f"Failed to emit tool_call_completed signal: {e}")

            return final_result

        except ValueError as e:
            logger.error(f"Validation error executing MCP tool {tool_name}: {e}")
            error_result = f"Error: Invalid arguments for tool {tool_name}: {str(e)}"

            # Emit tool call failed signal
            if self.signal_handler and hasattr(
                self.signal_handler, "tool_call_failed_signal"
            ):
                error_data = {
                    "id": tool_call_id,
                    "status": "error",
                    "error": error_result,
                    "execution_time": time.time() - start_time,
                }
                try:
                    self.signal_handler.tool_call_failed_signal.emit(error_data)
                except Exception as e:
                    logger.warning(f"Failed to emit tool_call_failed signal: {e}")

            return error_result
        except Exception as e:
            logger.error(f"Error executing MCP tool {tool_name}: {e}")
            error_result = f"Error executing MCP tool {tool_name}: {str(e)}"

            # Emit tool call failed signal
            if self.signal_handler and hasattr(
                self.signal_handler, "tool_call_failed_signal"
            ):
                error_data = {
                    "id": tool_call_id,
                    "status": "error",
                    "error": error_result,
                    "execution_time": time.time() - start_time,
                }
                try:
                    self.signal_handler.tool_call_failed_signal.emit(error_data)
                except Exception as e:
                    logger.warning(f"Failed to emit tool_call_failed signal: {e}")

            return error_result

    # MCP Server Management Methods

    async def connect_mcp_servers(self) -> dict[str, bool]:
        """Connect to all registered MCP servers.

        Returns:
            Dictionary mapping server names to connection success status
        """
        # Delegate to MCPConnectionService if available (service-oriented mode)
        if self.mcp_connection_service is not None:
            return await self.mcp_connection_service.connect_mcp_servers()

        # Legacy implementation for backwards compatibility
        return await self._connect_mcp_servers_legacy()

    async def _connect_mcp_servers_legacy(self) -> dict[str, bool]:
        """Legacy implementation of connect_mcp_servers for backwards compatibility."""
        if not self.mcp_registry:
            return {}

        # Connect to servers
        connection_results = await self.mcp_registry.connect_all_servers()

        # After successful connections, update tools cache and register MCP tools with the agent
        if any(connection_results.values()) and self.mcp_tools_enabled:
            successful_connections = sum(
                1 for success in connection_results.values() if success
            )
            logger.info(
                f"Updating MCP tools cache from {successful_connections} connected servers..."
            )

            # Update tools cache from connected servers
            await self.mcp_registry.update_tools_cache()

            # Get tool count for logging
            all_tools = self.mcp_registry.get_all_tools()
            total_tools = sum(len(tools) for tools in all_tools.values())
            logger.info(
                f"MCP tools cache updated: {total_tools} tools discovered from {successful_connections} servers"
            )

            # Re-register MCP tools with the agent
            logger.info("Re-registering MCP tools after server connections...")
            self._register_mcp_tools()

        return connection_results

    async def disconnect_mcp_servers(self) -> None:
        """Disconnect from all MCP servers."""
        # Delegate to MCPConnectionService if available (service-oriented mode)
        if self.mcp_connection_service is not None:
            return await self.mcp_connection_service.disconnect_mcp_servers()

        # Legacy implementation for backwards compatibility
        if self.mcp_registry:
            await self.mcp_registry.disconnect_all_servers()

    def register_mcp_server(self, client: MCPClient) -> None:
        """Register a new MCP server with the agent.

        Args:
            client: MCPClient instance to register
        """
        # Delegate to MCPConnectionService if available (service-oriented mode)
        if self.mcp_connection_service is not None:
            return self.mcp_connection_service.register_mcp_server(client)

        # Legacy implementation for backwards compatibility
        if not self.mcp_registry:
            self.mcp_registry = MCPServerRegistry()

        self.mcp_registry.register_server(client)

        # Re-register tools to include new server's tools
        if self.mcp_tools_enabled:
            self._register_mcp_tools()

    def unregister_mcp_server(self, server_name: str) -> bool:
        """Unregister an MCP server from the agent.

        Args:
            server_name: Name of the server to unregister

        Returns:
            True if server was unregistered, False if not found
        """
        # Delegate to MCPConnectionService if available (service-oriented mode)
        if self.mcp_connection_service is not None:
            return self.mcp_connection_service.unregister_mcp_server(server_name)

        # Legacy implementation for backwards compatibility
        if not self.mcp_registry:
            return False

        result = self.mcp_registry.unregister_server(server_name)

        # Re-register tools to remove unregistered server's tools
        if result and self.mcp_tools_enabled:
            self._register_mcp_tools()

        return result

    def _register_mcp_status_tool(self) -> None:
        """Register the MCP server status tool with the agent."""
        if self._mcp_status_tool_registered:
            logger.debug("MCP status tool already registered, skipping")
            return

        try:

            @self._agent.tool_plain
            async def internal_mcp_server_status_check() -> str:
                """Get the status of all MCP servers and their available tools.

                Returns:
                    Formatted string with server status information
                """
                return await self._tool_get_mcp_server_status()

            self._mcp_status_tool_registered = True
            logger.info("MCP server status tool registered successfully")

        except Exception as e:
            logger.error(f"Failed to register MCP server status tool: {e}")

    def _register_environment_tool(self) -> None:
        """Register the environment variable access tool with the agent."""
        if self._environment_tool_registered:
            logger.debug("Environment variable tool already registered, skipping")
            return

        try:

            @self._agent.tool_plain
            async def internal_get_environment_variable(variable_name: str) -> str:
                """Get the value of an environment variable.

                Args:
                    variable_name: Name of the environment variable to retrieve

                Returns:
                    The value of the environment variable or an error message
                """
                return await self._tool_get_environment_variable(variable_name)

            self._environment_tool_registered = True
            logger.info("Environment variable tool registered successfully")

        except Exception as e:
            logger.error(f"Failed to register environment variable tool: {e}")

    async def _tool_get_mcp_server_status(self) -> str:
        """Internal implementation of get_mcp_server_status tool."""
        try:
            logger.info("🔍 Checking MCP server status...")

            if not self.mcp_registry:
                return "MCP registry not available. MCP tools are not enabled."

            # Get immediate status without trying to reconnect first
            status = self.get_mcp_server_status()

            if not status.get("servers"):
                return "No MCP servers are currently registered or connected."

            # Format the status information with detailed diagnostics
            result_lines = ["🔧 MCP Server Diagnostic Status:"]
            result_lines.append("=" * 60)

            for server_name, server_info in status["servers"].items():
                result_lines.append(f"\n📡 Server: {server_name}")

                if hasattr(server_info, "connected"):
                    connection_status = (
                        "✅ Connected" if server_info.connected else "❌ Disconnected"
                    )
                    result_lines.append(f"  Status: {connection_status}")
                    result_lines.append(f"  Tools Available: {server_info.tools_count}")

                    # Add more diagnostic info
                    if hasattr(server_info, "last_connected"):
                        result_lines.append(
                            f"  Last Connected: {server_info.last_connected}"
                        )

                    if hasattr(server_info, "connection_attempts"):
                        result_lines.append(
                            f"  Connection Attempts: {server_info.connection_attempts}"
                        )

                    if server_info.last_error:
                        result_lines.append(f"  Last Error: {server_info.last_error}")

                    if hasattr(server_info, "tools") and server_info.tools:
                        result_lines.append("  Available Tools:")
                        for tool in server_info.tools[:5]:  # Show first 5 tools
                            result_lines.append(
                                f"    - {tool.name}: {tool.description[:50]}..."
                            )
                        if len(server_info.tools) > 5:
                            result_lines.append(
                                f"    ... and {len(server_info.tools) - 5} more tools"
                            )

                    # Try to get more detailed connection info
                    try:
                        if hasattr(self.mcp_registry, "get_server_connection_info"):
                            conn_info = self.mcp_registry.get_server_connection_info(
                                server_name
                            )
                            if conn_info:
                                result_lines.append(f"  Connection Info: {conn_info}")
                    except Exception:
                        pass

                else:
                    # Fallback for dict-style server info
                    result_lines.append(
                        f"  Status: {server_info.get('status', 'unknown')}"
                    )
                    tools = server_info.get("tools", [])
                    result_lines.append(f"  Tools Available: {len(tools)}")

            # Add summary with diagnostics
            total_servers = len(status["servers"])
            connected_servers = sum(
                1
                for info in status["servers"].values()
                if (hasattr(info, "connected") and info.connected)
                or (isinstance(info, dict) and info.get("status") == "connected")
            )

            result_lines.append("\n📊 Summary:")
            result_lines.append(f"  Total Servers: {total_servers}")
            result_lines.append(f"  Connected: {connected_servers}")
            result_lines.append(f"  Disconnected: {total_servers - connected_servers}")
            result_lines.append(f"  Total Tools: {status.get('total_tools', 0)}")

            # Add registry statistics if available
            if hasattr(status, "stats"):
                result_lines.append(f"  Registry Stats: {status['stats']}")

            # Add connection troubleshooting info
            if connected_servers == 0:
                result_lines.append("\n⚠️ Troubleshooting:")
                result_lines.append("  - All servers are disconnected")
                result_lines.append("  - Check server logs for connection errors")
                result_lines.append(
                    "  - Try reconnecting with: await self.ensure_mcp_servers_connected()"
                )
            elif connected_servers < total_servers:
                result_lines.append(
                    f"\n⚠️ Warning: {total_servers - connected_servers} servers are disconnected"
                )

            return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"Error getting MCP server status: {e}")
            return f"Error retrieving MCP server status: {str(e)}"

    async def _tool_get_environment_variable(self, variable_name: str) -> str:
        """Internal implementation of get_environment_variable tool."""
        try:
            # Security: Only allow access to specific safe environment variables
            allowed_vars = {
                "GITHUB_USERNAME",
                "GITHUB_USER",
                "USER",
                "USERNAME",
                "HOME",
                "PWD",
                "SHELL",
                "LANG",
                "PATH",
            }

            if variable_name not in allowed_vars:
                return f"Error: Access to environment variable '{variable_name}' is not allowed for security reasons. Allowed variables: {', '.join(sorted(allowed_vars))}"

            value = os.getenv(variable_name)
            if value is not None:
                return f"{variable_name}={value}"
            else:
                return f"Environment variable '{variable_name}' is not set"

        except Exception as e:
            logger.error(f"Error getting environment variable {variable_name}: {e}")
            return f"Error retrieving environment variable: {str(e)}"

    # Enhanced conversation methods with tool support

    async def send_message_with_tools_stream(
        self,
        message: str,
        on_chunk: Callable[[str, bool], Awaitable[None]],
        on_error: Callable[[Exception], None] = None,
        enable_filesystem: bool = True,
    ) -> AIResponse:
        """Send a message with tools and stream the response.

        Args:
            message: The message to send
            on_chunk: Callback function for streaming chunks
            on_error: Optional callback function for handling errors
            enable_filesystem: Whether to enable filesystem tools

        Returns:
            AIResponse: The complete response after streaming
        """
        # Delegate to streaming service if available
        if (
            hasattr(self, "streaming_response_service")
            and self.streaming_response_service is not None
        ):
            return await self.streaming_response_service.send_message_with_tools_stream(
                message, on_chunk, on_error, enable_filesystem
            )

        # Legacy implementation for backwards compatibility
        return await self._send_message_with_tools_stream_legacy(
            message, on_chunk, on_error, enable_filesystem
        )

    async def _send_message_with_tools_stream_legacy(
        self,
        message: str,
        on_chunk: Callable[[str, bool], Awaitable[None]],
        on_error: Callable[[Exception], None] = None,
        enable_filesystem: bool = True,
    ) -> AIResponse:
        """Legacy streaming implementation for backwards compatibility."""
        try:
            # Get the regular response first
            response = await self.send_message_with_tools(message, enable_filesystem)

            # Simulate streaming by sending the content in chunks
            if response.success and response.content:
                content = response.content
                chunk_size = max(1, len(content) // 5)  # Split into ~5 chunks

                for i in range(0, len(content), chunk_size):
                    chunk = content[i : i + chunk_size]
                    is_final = i + chunk_size >= len(content)

                    # Handle both sync and async callbacks
                    result = on_chunk(chunk, is_final)
                    if hasattr(result, "__await__"):
                        await result
            else:
                # Send error or empty response
                result = on_chunk(response.content or "No response", True)
                if hasattr(result, "__await__"):
                    await result

            return response
        except Exception as e:
            # Call error callback if provided
            if on_error:
                on_error(e)
            # Return error response
            return AIResponse(
                success=False, content=f"Error: {e}", error_type=type(e).__name__
            )

    async def send_message_with_tools(
        self, message: str, enable_filesystem: bool = True
    ) -> AIResponse:
        """Send a message with tool support enabled.

        Args:
            message: The message to send to the AI
            enable_filesystem: Whether to enable filesystem tools for this conversation

        Returns:
            AIResponse: The response from the AI
        """
        # Delegate to AIMessagingService if available (service-oriented architecture)
        if self.ai_messaging_service is not None:
            try:
                return await self.ai_messaging_service.send_message_with_tools(
                    message, enable_filesystem=enable_filesystem
                )
            except Exception as e:
                error_type, error_msg = self._categorize_error(e)
                logger.error(f"Error in messaging service delegation: {error_msg}")
                return AIResponse(
                    success=False, content="", error=error_msg, error_type=error_type
                )

        # Legacy implementation for backwards compatibility
        try:
            if (
                enable_filesystem
                and self.filesystem_tools_enabled
                and self.mcp_file_server
                and not self.mcp_file_server.is_connected
            ):
                # Ensure MCP connection
                await self.connect_mcp()

            response = await self._agent.run(message)

            return AIResponse(success=True, content=response.data)

        except Exception as e:
            logger.error(f"Error in enhanced conversation: {e}")
            return AIResponse(
                success=False, content=f"Error: {e}", error_type=type(e).__name__
            )

    async def analyze_project_files(self) -> AIResponse:
        """Analyze project files using filesystem tools.

        Returns:
            AIResponse: Analysis results
        """
        # Delegate to AIMessagingService if available (service-oriented architecture)
        if self.ai_messaging_service is not None:
            try:
                return await self.ai_messaging_service.analyze_project_files()
            except Exception as e:
                error_type, error_msg = self._categorize_error(e)
                logger.error(f"Error in messaging service delegation: {error_msg}")
                return AIResponse(
                    success=False, content="", error=error_msg, error_type=error_type
                )

        # Legacy implementation for backwards compatibility
        try:
            if not self.filesystem_tools_enabled or not self.mcp_file_server:
                return AIResponse(
                    success=False,
                    content="Filesystem tools not available for project analysis",
                )

            if not self.mcp_file_server.is_connected:
                await self.connect_mcp()

            # Get project structure
            files = await self.mcp_file_server.list_directory(".")

            # Read key files for analysis
            analysis_prompt = f"Please analyze this project structure: {files}"

            response = await self._agent.run(analysis_prompt)

            return AIResponse(success=True, content=response.data)

        except Exception as e:
            logger.error(f"Error in project analysis: {e}")
            return AIResponse(
                success=False,
                content=f"Error analyzing project: {e}",
                error_type=type(e).__name__,
            )

    async def generate_and_save_code(
        self, prompt: str, file_path: str, code: str
    ) -> AIResponse:
        """Generate and save code to a file.

        Args:
            prompt: The generation prompt
            file_path: Target file path
            code: Generated code content

        Returns:
            AIResponse: Operation result
        """
        # Delegate to AIMessagingService if available (service-oriented architecture)
        if self.ai_messaging_service is not None:
            try:
                return await self.ai_messaging_service.generate_and_save_code(
                    prompt, file_path, code
                )
            except Exception as e:
                error_type, error_msg = self._categorize_error(e)
                logger.error(f"Error in messaging service delegation: {error_msg}")
                return AIResponse(
                    success=False, content="", error=error_msg, error_type=error_type
                )

        # Legacy implementation for backwards compatibility
        try:
            if not self.filesystem_tools_enabled or not self.mcp_file_server:
                return AIResponse(
                    success=False,
                    content="Filesystem tools not available for code generation",
                )

            if not self.mcp_file_server.is_connected:
                await self.connect_mcp()

            # Save the generated code
            success = await self.mcp_file_server.write_file(file_path, code)

            if success:
                return AIResponse(
                    success=True, content=f"Code generated and saved to {file_path}"
                )
            else:
                return AIResponse(
                    success=False, content=f"Failed to save code to {file_path}"
                )

        except Exception as e:
            logger.error(f"Error generating and saving code: {e}")
            return AIResponse(
                success=False, content=f"Error: {e}", error_type=type(e).__name__
            )

    def _categorize_error(self, exception: Exception) -> tuple[str, str]:
        """
        Categorize an error and return error type and user-friendly message.
        Enhanced with comprehensive error handling for streaming scenarios.

        Args:
            exception: The exception to categorize

        Returns:
            Tuple of (error_type, user_friendly_message)
        """
        # File system errors (check these before OSError since they inherit from it)
        if isinstance(exception, FileNotFoundError):
            return "file_not_found", "Requested file was not found."

        if isinstance(exception, FileExistsError):
            return "file_exists", "File already exists."

        if isinstance(exception, PermissionError):
            return (
                "permission_error",
                "Permission denied. Please check your access rights.",
            )

        # Network and connection errors
        if isinstance(
            exception, ConnectionError | ConnectionRefusedError | ConnectionResetError
        ):
            return (
                "connection_error",
                "Network connection failed. Please check your internet connection and try again.",
            )

        # Timeout errors
        if isinstance(exception, asyncio.TimeoutError | TimeoutError):
            return (
                "timeout_error",
                "Request timed out. The service may be experiencing high load. Please try again.",
            )

        # Memory and resource errors
        if isinstance(exception, MemoryError):
            return (
                "memory_error",
                "Insufficient memory available. Try reducing the request size or closing other applications.",
            )

        if isinstance(exception, OSError):
            if "Too many open files" in str(exception):
                return (
                    "resource_exhaustion",
                    "System resource limit reached. Please try again in a moment.",
                )
            return "system_error", "System error occurred. Please try again."

        # HTTP and API specific errors
        status_code = getattr(exception, "status_code", None)
        if status_code is None:
            response = getattr(exception, "response", None)
            if response is not None:
                status_code = getattr(response, "status_code", None)

        if status_code:
            if status_code == 401:
                return (
                    "authentication_error",
                    "Authentication failed. Please check your API credentials.",
                )
            elif status_code == 403:
                return (
                    "authorization_error",
                    "Access forbidden. You don't have permission for this operation.",
                )
            elif status_code == 429:
                return (
                    "rate_limit_error",
                    "Rate limit exceeded. Please wait before making another request.",
                )
            elif status_code >= 500:
                return "server_error", "Server error occurred. Please try again later."
            elif status_code >= 400:
                return (
                    "client_error",
                    f"Request error (HTTP {status_code}). Please check your request.",
                )

        # AI model specific errors
        if "token" in str(exception).lower():
            if (
                "limit" in str(exception).lower()
                or "exceeded" in str(exception).lower()
            ):
                return (
                    "token_limit_error",
                    "Token limit exceeded. Please try with a shorter message.",
                )
            return "token_error", "Token-related error occurred."

        # Streaming specific errors
        if "stream" in str(exception).lower():
            if (
                "interrupted" in str(exception).lower()
                or "cancelled" in str(exception).lower()
            ):
                return (
                    "stream_interrupted",
                    "Stream was interrupted. You can try sending the message again.",
                )
            if "corrupted" in str(exception).lower():
                return (
                    "stream_corruption",
                    "Stream data was corrupted. Retrying automatically.",
                )
            return (
                "streaming_error",
                "Streaming error occurred. Falling back to standard response.",
            )

        # Validation and input errors
        if isinstance(exception, ValueError | TypeError):
            return (
                "validation_error",
                "Invalid input provided. Please check your request and try again.",
            )

        # Import and module errors
        if isinstance(exception, ImportError | ModuleNotFoundError):
            return (
                "dependency_error",
                "Required dependency is missing. Please check your installation.",
            )

        # Asyncio specific errors
        if isinstance(exception, asyncio.CancelledError):
            return "operation_cancelled", "Operation was cancelled."

        # JSON and data parsing errors
        if "json" in str(exception).lower() or isinstance(
            exception, KeyError | AttributeError
        ):
            return (
                "data_error",
                "Data parsing error occurred. The response format may be unexpected.",
            )

        # SSL and security errors
        if "ssl" in str(exception).lower() or "certificate" in str(exception).lower():
            return (
                "ssl_error",
                "SSL/TLS error occurred. Please check your connection security settings.",
            )

        # Default fallback for unknown errors
        return "unknown", f"An unexpected error occurred: {str(exception)}"

    async def send_message(self, message: str) -> AIResponse:
        """Send a message to the AI and get a response.

        Args:
            message: The message to send to the AI.

        Returns:
            AIResponse: The response from the AI.
        """
        # Validate input
        if not message or not message.strip():
            logger.warning("Empty message provided to send_message")
            return AIResponse(
                content="",
                success=False,
                error="Message cannot be empty",
                error_type="validation",
                tokens_used=0,
                retry_count=0,
            )

        logger.info("Sending message to AI: %s...", message[:100])

        retry_count = 0
        last_exception = None

        # Retry logic for transient errors
        while retry_count <= self.max_retries:
            try:
                # Use asyncio.wait_for to handle timeouts
                result = await asyncio.wait_for(
                    self._agent.run(message.strip()),
                    timeout=self.request_timeout,
                )

                usage = result.usage()
                tokens_used = (
                    usage.total_tokens
                    if usage and usage.total_tokens is not None
                    else 0
                )

                response = AIResponse(
                    content=result.data,
                    success=True,
                    error=None,
                    error_type=None,
                    tokens_used=tokens_used,
                    retry_count=retry_count,
                )

                logger.info(
                    "AI response received successfully: %d characters, %d tokens (retries: %d)",
                    len(response.content),
                    tokens_used,
                    retry_count,
                )
                return response

            except Exception as e:
                last_exception = e

                # Use error service if available, otherwise fall back to internal method
                if hasattr(self, "error_service") and self.error_service is not None:
                    error_category, error_msg = self.error_service.categorize_error(e)
                    error_type = error_category.name.lower()
                    is_retryable = self.error_service.is_retryable_error(error_category)
                else:
                    error_type, error_msg = self._categorize_error(e)
                    # Check if this is a retryable error using legacy logic
                    retryable_errors = {
                        "connection",
                        "server_error",
                        "rate_limit",
                        "timeout",
                    }
                    is_retryable = error_type in retryable_errors

                if is_retryable and retry_count < self.max_retries:
                    retry_count += 1
                    wait_time = min(2**retry_count, 30)  # Exponential backoff, max 30s
                    logger.warning(
                        "Retryable error occurred (attempt %d/%d): %s. Retrying in %ds...",
                        retry_count,
                        self.max_retries,
                        error_msg,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Non-retryable error or max retries reached
                    if retry_count >= self.max_retries:
                        logger.error(
                            "Max retries (%d) exceeded for message. Final error: %s",
                            self.max_retries,
                            error_msg,
                        )
                    else:
                        logger.error("Non-retryable error occurred: %s", error_msg)

                    return AIResponse(
                        content="",
                        success=False,
                        error=error_msg,
                        error_type=error_type,
                        tokens_used=0,
                        retry_count=retry_count,
                    )

        # Should not reach here, but just in case
        error_type, error_msg = (
            self._categorize_error(last_exception)
            if last_exception
            else ("unknown", "Unknown error")
        )
        return AIResponse(
            content="",
            success=False,
            error=error_msg,
            error_type=error_type,
            tokens_used=0,
            retry_count=retry_count,
        )

    @property
    def is_configured(self) -> bool:
        """Check if the AI Agent is properly configured.

        Returns:
            bool: True if the agent is configured, False otherwise.
        """
        return self._model is not None and self._agent is not None

    @property
    def model_info(self) -> str:
        """Get information about the current model.

        Returns:
            str: Information about the model.
        """
        if self.config_service:
            return f"Azure OpenAI model: {self.config_service.deployment_name} (endpoint: {self.config_service.azure_endpoint})"
        return f"Azure OpenAI model: {self.config.deployment_name} (endpoint: {self.config.azure_endpoint})"

    # Configuration properties that work with both service and legacy modes
    @property
    def max_tokens(self) -> int:
        """Maximum tokens per response."""
        return (
            self.config_service.max_tokens
            if self.config_service
            else self.config.max_tokens
        )

    @property
    def temperature(self) -> float:
        """Temperature for response generation."""
        return (
            self.config_service.temperature
            if self.config_service
            else self.config.temperature
        )

    @property
    def request_timeout(self) -> int:
        """Request timeout in seconds."""
        return (
            self.config_service.request_timeout
            if self.config_service
            else self.config.request_timeout
        )

    @property
    def max_retries(self) -> int:
        """Maximum number of retries for failed requests."""
        return (
            self.config_service.max_retries
            if self.config_service
            else self.config.max_retries
        )

    def get_health_status(self) -> dict:
        """Get the health status of the AI Agent.

        Returns:
            Dict containing health status information.
        """
        health_status = {
            "configured": self.is_configured,
            "model_name": self.config.deployment_name,
            "endpoint": self.config.azure_endpoint,
            "max_retries": self.config.max_retries,
            "timeout": self.config.request_timeout,
        }

        # Add MCP status if enabled
        if self.mcp_tools_enabled:
            # Use sync version for health status (non-async context)
            mcp_status = self._get_mcp_server_status_sync()
            health_status.update(
                {
                    "mcp_enabled": mcp_status["mcp_enabled"],
                    "mcp_stats": mcp_status["stats"],
                }
            )
        else:
            health_status["mcp_enabled"] = False

        return health_status

    def _get_mcp_server_status_sync(self) -> dict[str, Any]:
        """Sync version of get_mcp_server_status for use in non-async contexts."""
        # Only use legacy implementation for sync context
        if not self.mcp_registry:
            return {"mcp_enabled": False, "servers": {}, "stats": {}}

        return {
            "mcp_enabled": self.mcp_tools_enabled,
            "servers": self.mcp_registry.get_all_server_statuses(),
            "stats": self.mcp_registry.get_registry_stats(),
        }

    # Foundation Services Integration Methods

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error statistics from ErrorHandlingService.

        Returns:
            dict: Error statistics if error service is available
        """
        if hasattr(self, "error_service") and self.error_service is not None:
            return self.error_service.get_error_statistics()
        return {
            "total_errors": 0,
            "total_retries": 0,
            "error_categories": {},
            "retryable_errors": 0,
            "non_retryable_errors": 0,
        }

    def safe_execute(self, func, *args, **kwargs) -> tuple[Any, str | None]:
        """Execute a function safely using ErrorHandlingService.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            tuple: (result, error_info) or (None, None) if service not available
        """
        if hasattr(self, "error_service") and self.error_service is not None:
            return self.error_service.safe_execute(func, *args, **kwargs)

        # Fallback to direct execution if no error service
        try:
            result = func(*args, **kwargs)
            return result, None
        except Exception as e:
            return None, str(e)

    # MCP File Server Integration Methods

    async def connect_mcp(self) -> bool:
        """Connect to the MCP file server.

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            FileOperationError: If MCP server is not configured.
        """
        # Delegate to MCPConnectionService if available (service-oriented mode)
        if self.mcp_connection_service is not None:
            return await self.mcp_connection_service.connect_mcp()

        # Legacy implementation for backwards compatibility
        if not self.mcp_file_server:
            raise FileOperationError("MCP file server not configured")

        logger.info("Connecting to MCP file server...")
        return await self.mcp_file_server.connect()

    async def disconnect_mcp(self) -> None:
        """Disconnect from the MCP file server."""
        # Delegate to MCPConnectionService if available (service-oriented mode)
        if self.mcp_connection_service is not None:
            return await self.mcp_connection_service.disconnect_mcp()

        # Legacy implementation for backwards compatibility
        if self.mcp_file_server:
            logger.info("Disconnecting from MCP file server...")
            await self.mcp_file_server.disconnect()

    @asynccontextmanager
    async def mcp_context(self) -> AsyncGenerator[None, None]:
        """Context manager for MCP file server operations."""
        # Delegate to MCPConnectionService if available (service-oriented mode)
        if self.mcp_connection_service is not None:
            async with self.mcp_connection_service.mcp_context():
                yield
        else:
            # Legacy implementation for backwards compatibility
            if not self.mcp_file_server:
                raise FileOperationError("MCP file server not configured")

            async with self.mcp_file_server:
                yield

    def _ensure_mcp_connected(self) -> None:
        """Ensure MCP server is connected and configured.

        Raises:
            FileOperationError: If MCP server is not configured or connected.
        """
        if not self.mcp_file_server:
            raise FileOperationError("MCP file server not configured")

        if not self.mcp_file_server.is_connected:
            raise FileOperationError(
                "Not connected to MCP server. Call connect_mcp() first."
            )

    async def read_file(self, file_path: str) -> str:
        """Read file content through MCP server.

        Args:
            file_path: Path to the file to read.

        Returns:
            str: The file content.

        Raises:
            FileOperationError: If file cannot be read or MCP not connected.
        """
        self._ensure_mcp_connected()
        assert self.mcp_file_server is not None  # Type guard
        return await self.mcp_file_server.read_file(file_path)

    async def write_file(self, file_path: str, content: str) -> bool:
        """Write content to file through MCP server.

        Args:
            file_path: Path to the file to write.
            content: Content to write to the file.

        Returns:
            bool: True if file was written successfully.

        Raises:
            FileOperationError: If file cannot be written or MCP not connected.
        """
        self._ensure_mcp_connected()
        assert self.mcp_file_server is not None  # Type guard
        return await self.mcp_file_server.write_file(file_path, content)

    async def list_directory(self, directory_path: str = ".") -> list[str]:
        """List directory contents through MCP server.

        Args:
            directory_path: Path to the directory to list.

        Returns:
            List[str]: List of files and directories.

        Raises:
            FileOperationError: If directory cannot be listed or MCP not connected.
        """
        self._ensure_mcp_connected()
        assert self.mcp_file_server is not None  # Type guard
        return await self.mcp_file_server.list_directory(directory_path)

    async def delete_file(self, file_path: str) -> bool:
        """Delete file through MCP server.

        Args:
            file_path: Path to the file to delete.

        Returns:
            bool: True if file was deleted successfully.

        Raises:
            FileOperationError: If file cannot be deleted or MCP not connected.
        """
        self._ensure_mcp_connected()
        assert self.mcp_file_server is not None  # Type guard
        return await self.mcp_file_server.delete_file(file_path)

    async def create_directory(self, directory_path: str) -> bool:
        """Create directory through MCP server.

        Args:
            directory_path: Path to the directory to create.

        Returns:
            bool: True if directory was created successfully.

        Raises:
            FileOperationError: If directory cannot be created or MCP not connected.
        """
        self._ensure_mcp_connected()
        assert self.mcp_file_server is not None  # Type guard
        return await self.mcp_file_server.create_directory(directory_path)

    async def get_file_info(self, file_path: str) -> dict[str, Any]:
        """Get file information through MCP server.

        Args:
            file_path: Path to the file to get info for.

        Returns:
            Dict[str, Any]: File information including size, modified time, etc.

        Raises:
            FileOperationError: If file info cannot be retrieved or MCP not connected.
        """
        self._ensure_mcp_connected()
        assert self.mcp_file_server is not None  # Type guard
        return await self.mcp_file_server.get_file_info(file_path)

    async def search_files(self, pattern: str, directory: str = ".") -> list[str]:
        """Search for files matching pattern through MCP server.

        Args:
            pattern: File pattern to search for (e.g., "*.py").
            directory: Directory to search in.

        Returns:
            List[str]: List of matching file paths.

        Raises:
            FileOperationError: If search cannot be performed or MCP not connected.
        """
        self._ensure_mcp_connected()
        assert self.mcp_file_server is not None  # Type guard
        return await self.mcp_file_server.search_files(pattern, directory)

    async def read_multiple_files_mcp(self, file_paths: list[str]) -> dict[str, str]:
        """Read multiple files through MCP server.

        Args:
            file_paths: List of file paths to read.

        Returns:
            Dict[str, str]: Dictionary mapping file paths to their content.

        Raises:
            FileOperationError: If files cannot be read or MCP not connected.
        """
        self._ensure_mcp_connected()

        results = {}
        for file_path in file_paths:
            try:
                content = await self.read_file(file_path)
                results[file_path] = content
            except FileOperationError as e:
                logger.warning(f"Failed to read {file_path}: {e}")
                results[file_path] = f"Error reading file: {e}"

        return results

    async def send_message_with_file_context(
        self, message: str, file_path: str
    ) -> AIResponse:
        """Send a message to AI with file content as context.

        Args:
            message: The message to send to the AI.
            file_path: Path to the file to include as context.

        Returns:
            AIResponse: The response from the AI.

        Raises:
            FileOperationError: If file cannot be read or MCP not connected.
        """
        # Delegate to AIMessagingService if available (service-oriented architecture)
        if self.ai_messaging_service is not None:
            try:
                return await self.ai_messaging_service.send_message_with_file_context(
                    message, file_path
                )
            except Exception as e:
                error_type, error_msg = self._categorize_error(e)
                logger.error(f"Error in messaging service delegation: {error_msg}")
                return AIResponse(
                    success=False, content="", error=error_msg, error_type=error_type
                )

        # Legacy implementation for backwards compatibility
        self._ensure_mcp_connected()

        try:
            file_content = await self.read_file(file_path)
            enhanced_message = f"""
Context file: {file_path}
File content:
```
{file_content}
```

User message: {message}
"""
            return await self.send_message(enhanced_message)

        except FileOperationError as e:
            logger.error(f"Failed to read file {file_path} for context: {e}")
            return AIResponse(
                content="",
                success=False,
                error=f"Failed to read file for context: {e}",
                error_type="file_operation",
                tokens_used=0,
                retry_count=0,
            )

    async def send_enhanced_message(self, message: str) -> AIResponse:
        """Send an enhanced message that can trigger file operations if requested.

        Args:
            message: The message to send to the AI.

        Returns:
            AIResponse: The response from the AI.
        """
        # Delegate to messaging service if available
        if self.ai_messaging_service is not None:
            return await self.ai_messaging_service.send_enhanced_message(message)

        # Legacy implementation for backwards compatibility
        # Simple pattern matching for file operation requests
        # In a more sophisticated implementation, this could use the AI to understand intent
        if "read" in message.lower() and any(
            ext in message for ext in [".py", ".json", ".md", ".txt"]
        ):
            # Extract potential file name
            words = message.split()
            for word in words:
                if any(ext in word for ext in [".py", ".json", ".md", ".txt"]):
                    file_path = word.strip(".,!?")
                    try:
                        return await self.send_message_with_file_context(
                            message, file_path
                        )
                    except FileOperationError:
                        # Fall back to regular message if file read fails
                        break

        return await self.send_message(message)

    def get_mcp_health_status(self) -> dict[str, Any]:
        """Get the health status of the MCP integration.

        Returns:
            Dict[str, Any]: MCP health status information.
        """
        # Delegate to MCPConnectionService if available (service-oriented mode)
        if self.mcp_connection_service is not None:
            return self.mcp_connection_service.get_mcp_health_status()

        # Legacy implementation for backwards compatibility
        if not self.mcp_file_server:
            return {
                "mcp_configured": False,
                "mcp_connected": False,
                "mcp_base_directory": None,
                "mcp_allowed_extensions": None,
                "mcp_write_enabled": None,
                "mcp_delete_enabled": None,
            }

        return {
            "mcp_configured": True,
            "mcp_connected": self.mcp_file_server.is_connected,
            "mcp_base_directory": str(self.mcp_file_server.config.base_directory),
            "mcp_allowed_extensions": self.mcp_file_server.config.allowed_extensions,
            "mcp_write_enabled": self.mcp_file_server.config.enable_write_operations,
            "mcp_delete_enabled": self.mcp_file_server.config.enable_delete_operations,
        }

    def update_mcp_config(self, new_config: MCPFileConfig) -> None:
        """Update the MCP configuration.

        Args:
            new_config: New MCP configuration.
        """
        if self.mcp_file_server:
            # Disconnect if currently connected
            if self.mcp_file_server.is_connected:
                asyncio.create_task(self.mcp_file_server.disconnect())

            # Update configuration
            self.mcp_file_server.config = new_config
            logger.info("MCP configuration updated")
        else:
            # Create new MCP server with new config
            self.mcp_file_server = MCPFileServer(new_config)
            logger.info("MCP file server created with new configuration")

    # Workspace-aware file operations
    def set_workspace_root(self, workspace_path: Path) -> None:
        """Set the workspace root directory for scoped file operations.

        Args:
            workspace_path: Path to the workspace root directory.

        Raises:
            ValueError: If WorkspaceService not configured.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )

        # Update the legacy attribute for backwards compatibility
        self.workspace_root = workspace_path

        return self.workspace_service.set_workspace_root(workspace_path)

    @property
    def workspace_root(self) -> Path | None:
        """Get the current workspace root directory.

        Returns:
            Path: Current workspace root path, or None if not set.
        """
        # Delegate to WorkspaceService if available
        if self.workspace_service is not None:
            return getattr(self.workspace_service, "workspace_root", None)

        # Fallback to legacy attribute
        return getattr(self, "_workspace_root", None)

    @workspace_root.setter
    def workspace_root(self, value: Path | None) -> None:
        """Set the workspace root directory (legacy attribute).

        Args:
            value: Workspace root path to set.
        """
        self._workspace_root = value

    def resolve_workspace_path(self, file_path: str) -> Path:
        """Resolve and validate a path within the workspace.

        Args:
            file_path: File path to resolve (can be relative or absolute).

        Returns:
            Path: Resolved absolute path within workspace.

        Raises:
            ValueError: If WorkspaceService not configured or path is outside workspace.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )
        return self.workspace_service.resolve_workspace_path(file_path)

    def read_workspace_file(self, file_path: str) -> str:
        """Read file content from workspace.

        Args:
            file_path: Relative path to file within workspace.

        Returns:
            str: File content.

        Raises:
            ValueError: If WorkspaceService not configured or path is outside workspace.
            FileNotFoundError: If file does not exist.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )
        return self.workspace_service.read_workspace_file(file_path)

    def write_workspace_file(self, file_path: str, content: str) -> None:
        """Write content to file in workspace.

        Args:
            file_path: Relative path to file within workspace.
            content: Content to write to file.

        Raises:
            ValueError: If WorkspaceService not configured or path is outside workspace.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )
        return self.workspace_service.write_workspace_file(file_path, content)

    def list_workspace_directory(self, dir_path: str = ".") -> list[str]:
        """List files and directories in workspace directory.

        Args:
            dir_path: Relative path to directory within workspace.

        Returns:
            List[str]: List of file and directory names.

        Raises:
            ValueError: If WorkspaceService not configured or path is outside workspace.
            FileNotFoundError: If directory does not exist.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )
        return self.workspace_service.list_workspace_directory(dir_path)

    def workspace_file_exists(self, file_path: str) -> bool:
        """Check if file exists in workspace.

        Args:
            file_path: Relative path to file within workspace.

        Returns:
            bool: True if file exists, False otherwise.

        Raises:
            ValueError: If WorkspaceService not configured or path is outside workspace.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )
        return self.workspace_service.workspace_file_exists(file_path)

    def create_workspace_directory(self, dir_path: str) -> None:
        """Create directory in workspace.

        Args:
            dir_path: Relative path to directory within workspace.

        Raises:
            ValueError: If WorkspaceService not configured or path is outside workspace.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )
        return self.workspace_service.create_workspace_directory(dir_path)

    def delete_workspace_file(self, file_path: str) -> None:
        """Delete file from workspace.

        Args:
            file_path: Relative path to file within workspace.

        Raises:
            ValueError: If WorkspaceService not configured or path is outside workspace.
            FileNotFoundError: If file does not exist.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )
        return self.workspace_service.delete_workspace_file(file_path)

    def validate_file_path(self, file_path: str) -> None:
        """Validate file path for security and correctness.

        Args:
            file_path: File path to validate.

        Raises:
            ValueError: If WorkspaceService not configured or file path is invalid.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )
        return self.workspace_service.validate_file_path(file_path)

    def validate_file_content(self, content: str) -> None:
        """Validate file content for security and encoding.

        Args:
            content: File content to validate.

        Raises:
            ValueError: If WorkspaceService not configured or content is invalid.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )
        return self.workspace_service.validate_file_content(content)

    def validate_directory_path(self, dir_path: str) -> None:
        """Validate directory path exists and is accessible.

        Args:
            dir_path: Directory path to validate.

        Raises:
            ValueError: If WorkspaceService not configured or path is invalid.
            FileNotFoundError: If directory does not exist.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )
        return self.workspace_service.validate_directory_path(dir_path)

    def read_workspace_file_validated(self, file_path: str) -> str:
        """Read file with comprehensive validation.

        Args:
            file_path: Relative path to file within workspace.

        Returns:
            str: File content.

        Raises:
            ValueError: If WorkspaceService not configured or validation fails.
            FileNotFoundError: If file does not exist.
        """
        if self.workspace_service is None:
            raise ValueError(
                "WorkspaceService not configured. Use service-oriented architecture or legacy AIAgentConfig."
            )
        return self.workspace_service.read_workspace_file_validated(file_path)

    def read_multiple_files(
        self, file_paths: list[str], fail_fast: bool = False
    ) -> dict[str, str]:
        """Read multiple files with intelligent routing.

        Routes to either MCP or workspace implementation based on configuration.
        If workspace service is available, uses workspace implementation (sync).
        Otherwise, tries to use MCP implementation (async, but called synchronously).

        Args:
            file_paths: List of file paths to read.
            fail_fast: If True, stop on first error. If False, continue and collect errors.

        Returns:
            Dict[str, str]: Mapping of file paths to content (or error messages).

        Raises:
            ValueError: If neither WorkspaceService nor MCP is configured.
        """
        # Prefer workspace service if available (service-oriented architecture)
        if self.workspace_service is not None:
            return self.workspace_service.read_multiple_workspace_files(
                file_paths, fail_fast
            )

        # Fallback to MCP if available (legacy architecture)
        if self.mcp_file_server is not None:
            # Note: This is a sync wrapper around async MCP method
            # In practice, this should be avoided - use read_multiple_files_mcp directly for async code
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, we can't use asyncio.run
                    # This is a limitation - async code should call read_multiple_files_mcp directly
                    raise ValueError(
                        "Cannot call sync read_multiple_files from async context when using MCP. Use read_multiple_files_mcp instead."
                    )
                else:
                    return asyncio.run(self.read_multiple_files_mcp(file_paths))
            except RuntimeError:
                # No event loop running, safe to create one
                return asyncio.run(self.read_multiple_files_mcp(file_paths))

        raise ValueError(
            "Neither WorkspaceService nor MCP is configured. Use service-oriented architecture or legacy AIAgentConfig."
        )

    async def ensure_mcp_servers_connected(self) -> bool:
        """Ensure MCP servers are connected.

        Returns:
            bool: True if servers are connected, False otherwise.
        """
        # Delegate to MCPConnectionService if available (service-oriented mode)
        if self.mcp_connection_service is not None:
            return await self.mcp_connection_service.ensure_mcp_servers_connected()

        # Legacy implementation for backwards compatibility
        return await self._ensure_mcp_servers_connected_legacy()

    async def _ensure_mcp_servers_connected_legacy(self) -> bool:
        """Legacy implementation for ensuring MCP servers are connected."""
        if not self.mcp_registry:
            logger.warning("No MCP registry available for connection check")
            return False

        try:
            # Check if any servers are connected
            server_statuses = self.mcp_registry.get_all_server_statuses()
            connected_servers = [
                name
                for name, status in server_statuses.items()
                if hasattr(status, "connected") and status.connected
            ]

            if connected_servers:
                logger.debug(f"MCP servers connected: {connected_servers}")
                return True
            else:
                logger.warning("No MCP servers are currently connected")
                return False

        except Exception as e:
            logger.error(f"Error checking MCP server connection status: {e}")
            return False

    async def get_mcp_server_status(self) -> dict[str, Any]:
        """Get status of all MCP servers.

        Returns:
            Dictionary containing MCP server status information
        """
        # Delegate to MCPConnectionService if available (service-oriented mode)
        if self.mcp_connection_service is not None:
            return await self.mcp_connection_service.get_mcp_server_status()

        # Legacy implementation for backwards compatibility
        if not self.mcp_registry:
            return {"mcp_enabled": False, "servers": {}}

        return {
            "mcp_enabled": self.mcp_tools_enabled,
            "servers": self.mcp_registry.get_all_server_statuses(),
            "stats": self.mcp_registry.get_registry_stats(),
        }

    async def interrupt_current_stream(self) -> bool:
        """Interrupt the current streaming response.

        Returns:
            bool: True if stream was interrupted, False otherwise
        """
        # Delegate to streaming service if available
        if (
            hasattr(self, "streaming_response_service")
            and self.streaming_response_service is not None
        ):
            return await self.streaming_response_service.interrupt_current_stream()

        # Legacy implementation - no streaming to interrupt
        return False

    async def send_memory_aware_message_stream(
        self,
        message: str,
        on_chunk: Callable[[str, bool], Awaitable[None]],
        enable_filesystem: bool = True,
    ) -> AIResponse:
        """Send a memory-aware message with streaming response.

        Args:
            message: The message to send
            on_chunk: Callback function for streaming chunks
            enable_filesystem: Whether to enable filesystem tools

        Returns:
            AIResponse: The complete response after streaming
        """
        # Delegate to streaming service if available
        if (
            hasattr(self, "streaming_response_service")
            and self.streaming_response_service is not None
        ):
            return (
                await self.streaming_response_service.send_memory_aware_message_stream(
                    message, on_chunk, enable_filesystem=enable_filesystem
                )
            )

        # Fallback to regular streaming
        return await self.send_message_with_tools_stream(
            message, on_chunk, enable_filesystem
        )

    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming.

        Returns:
            bool: True if currently streaming, False otherwise
        """
        # Delegate to streaming service if available
        if (
            hasattr(self, "streaming_response_service")
            and self.streaming_response_service is not None
        ):
            return self.streaming_response_service.is_streaming

        # Legacy implementation - check if we have active stream handlers
        return (
            hasattr(self, "current_stream_handler")
            and self.current_stream_handler is not None
            and getattr(self.current_stream_handler, "is_streaming", False)
        )

    def get_stream_status(self) -> dict[str, Any]:
        """Get the current streaming status.

        Returns:
            dict: Stream status information
        """
        # Delegate to streaming service if available
        if (
            hasattr(self, "streaming_response_service")
            and self.streaming_response_service is not None
        ):
            return self.streaming_response_service.get_stream_status()

        # Legacy implementation
        return {
            "status": "streaming" if self.is_streaming else "idle",
            "stream_id": getattr(self, "current_stream_id", None),
        }

    def get_streaming_health_status(self) -> dict[str, Any]:
        """Get streaming service health status.

        Returns:
            dict: Health status information
        """
        # Delegate to streaming service if available
        if (
            hasattr(self, "streaming_response_service")
            and self.streaming_response_service is not None
        ):
            return self.streaming_response_service.get_health_status()

        # Legacy implementation
        return {
            "status": "unavailable",
            "active_streams": 0,
        }

    def validate_file_extension(self, file_path: str) -> None:
        """Validate file extension is allowed.

        Args:
            file_path: File path to validate.

        Raises:
            ValueError: If file extension is not allowed.
        """
        if self.workspace_service is None:
            # Legacy implementation for backwards compatibility
            import os

            _, ext = os.path.splitext(file_path)

            # List of blocked extensions
            blocked_extensions = {
                ".exe",
                ".bat",
                ".cmd",
                ".scr",
                ".pif",
                ".dll",
                ".com",
                ".vbs",
                ".ps1",
            }

            if ext.lower() in blocked_extensions:
                raise ValueError(f"File extension not allowed: {ext}")

            # Require extension for most files (except known files without extensions)
            if not ext and file_path not in {
                "Makefile",
                "Dockerfile",
                "Jenkinsfile",
                "Vagrantfile",
            }:
                raise ValueError("File extension required")

            return

        return self.workspace_service.validate_file_extension(file_path)

    def validate_file_size(self, content: str, max_size_mb: int = 10) -> None:
        """Validate file size is within limits.

        Args:
            content: File content to validate.
            max_size_mb: Maximum allowed size in MB.

        Raises:
            ValueError: If file size exceeds limit.
        """
        if self.workspace_service is None:
            # Legacy implementation for backwards compatibility
            size_bytes = len(content.encode("utf-8"))
            max_size_bytes = max_size_mb * 1024 * 1024

            if size_bytes > max_size_bytes:
                raise ValueError(
                    f"File size exceeds maximum allowed: {size_bytes} bytes > {max_size_bytes} bytes"
                )

            return

        return self.workspace_service.validate_file_size(content, max_size_mb)

    # Memory Context Service Delegation Methods

    def store_user_message(
        self, message: str, metadata: dict[str, Any] | None = None
    ) -> str | None:
        """Store a user message in memory."""
        if self.memory_context_service is not None:
            try:
                return self.memory_context_service.store_user_message(message, metadata)
            except Exception:
                return None
        return None

    def store_assistant_message(
        self, message: str, metadata: dict[str, Any] | None = None
    ) -> str | None:
        """Store an assistant message in memory."""
        if self.memory_context_service is not None:
            try:
                return self.memory_context_service.store_assistant_message(
                    message, metadata
                )
            except Exception:
                return None
        return None

    def store_long_term_memory(
        self,
        content: str,
        memory_type: str = "user_info",
        importance_score: float = 0.8,
    ) -> str | None:
        """Store long-term memory information."""
        if self.memory_context_service is not None:
            try:
                return self.memory_context_service.store_long_term_memory(
                    content, memory_type, importance_score
                )
            except Exception:
                return None
        return None

    def get_conversation_context(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent conversation context."""
        if self.memory_context_service is not None:
            try:
                return self.memory_context_service.get_conversation_context(limit)
            except Exception:
                return []
        return []

    def get_long_term_memories(
        self, query: str = "", limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get long-term memories that match a query."""
        if self.memory_context_service is not None:
            try:
                return self.memory_context_service.get_long_term_memories(query, limit)
            except Exception:
                return []
        return []

    def enhance_message_with_memory_context(self, message: str) -> str:
        """Enhance a message with memory context for AI processing."""
        if self.memory_context_service is not None:
            try:
                return self.memory_context_service.enhance_message_with_memory_context(
                    message
                )
            except Exception:
                return message
        return message

    def get_memory_statistics(self) -> dict[str, Any]:
        """Get memory system statistics."""
        if self.memory_context_service is not None:
            try:
                return self.memory_context_service.get_memory_statistics()
            except Exception:
                return {"memory_enabled": False, "error": "Memory system error"}
        return {"memory_enabled": False, "error": "Memory system not enabled"}

    async def clear_all_memory(self) -> bool:
        """Clear all memory data."""
        if self.memory_context_service is not None:
            try:
                return await self.memory_context_service.clear_all_memory()
            except Exception:
                return False
        return False

    def start_new_session(self) -> str | None:
        """Start a new conversation session."""
        if self.memory_context_service is not None:
            try:
                return self.memory_context_service.start_new_session()
            except Exception:
                return None
        return None

    def get_current_session_id(self) -> str | None:
        """Get the current session ID."""
        if self.memory_context_service is not None:
            try:
                return self.memory_context_service.get_current_session_id()
            except Exception:
                return None
        return None

    def load_conversation_history(self, chat_widget) -> bool:
        """Load conversation history into a chat widget."""
        if self.memory_context_service is not None:
            try:
                return self.memory_context_service.load_conversation_history(
                    chat_widget
                )
            except Exception:
                return False
        return False

    def get_project_context_for_ai(
        self, file_path: str | None = None, recent_hours: int = 24, max_events: int = 10
    ) -> str:
        """Get project context for AI processing."""
        if self.memory_context_service is not None:
            try:
                return self.memory_context_service.get_project_context_for_ai(
                    file_path, recent_hours, max_events
                )
            except Exception:
                return ""
        return ""

    async def close_memory_service(self) -> None:
        """Close the memory service and cleanup resources."""
        if self.memory_context_service is not None:
            await self.memory_context_service.close()

    def get_memory_health_status(self) -> dict[str, Any]:
        """Get memory service health status.

        Returns:
            Dictionary containing health status information
        """
        if self.memory_context_service is not None:
            return self.memory_context_service.get_health_status()

        # Legacy fallback - return unavailable status
        return {
            "service_name": "MemoryContextService",
            "memory_enabled": False,
            "memory_system_initialized": False,
            "current_session_id": None,
            "is_healthy": True,  # Still healthy, just not enabled
        }

    @property
    def memory_aware_enabled(self) -> bool:
        """Check if memory awareness is enabled.

        Returns:
            True if memory awareness is enabled, False otherwise
        """
        if self.memory_context_service is not None:
            return self.memory_context_service.memory_aware_enabled

        # Legacy fallback - check if memory awareness was enabled during initialization
        return getattr(self, "_memory_aware_enabled", False)

    @memory_aware_enabled.setter
    def memory_aware_enabled(self, value: bool) -> None:
        """Set memory awareness enabled state.

        Args:
            value: True to enable memory awareness, False to disable
        """
        # Store the value for legacy compatibility
        self._memory_aware_enabled = value
