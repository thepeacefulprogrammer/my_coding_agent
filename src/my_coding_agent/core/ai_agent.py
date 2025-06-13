"""AI Agent service for interacting with Azure OpenAI through Pydantic AI."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from .mcp_file_server import FileOperationError, MCPFileConfig, MCPFileServer
from .streaming import StreamHandler

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


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
        config: AIAgentConfig,
        mcp_config: MCPFileConfig | None = None,
        enable_filesystem_tools: bool | None = None,
    ):
        """Initialize the AI Agent.

        Args:
            config: The configuration for the AI Agent.
            mcp_config: Optional MCP file server configuration.
            enable_filesystem_tools: Whether to enable filesystem tools (auto-detected if None).
        """
        self.config = config
        self.mcp_file_server: MCPFileServer | None = None
        self.workspace_root: Path | None = None
        self.current_stream_handler: StreamHandler | None = None
        self.current_stream_id: str | None = None

        # Auto-detect filesystem tools enablement
        if enable_filesystem_tools is None:
            self.filesystem_tools_enabled = mcp_config is not None
        else:
            self.filesystem_tools_enabled = (
                enable_filesystem_tools and mcp_config is not None
            )

        # Initialize MCP file server if config provided and tools enabled
        if mcp_config and self.filesystem_tools_enabled:
            self.mcp_file_server = MCPFileServer(mcp_config)
            logger.info("AI Agent initialized with MCP file server integration")

        # Initialize streaming handler
        self.stream_handler = StreamHandler()

        self._setup_logging()
        self._create_model()
        self._create_agent()
        self._register_tools()

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

            provider = AzureProvider(
                azure_endpoint=self.config.azure_endpoint,
                api_version=self.config.api_version,
                api_key=self.config.azure_api_key,
            )

            self._model = OpenAIModel(
                model_name=self.config.deployment_name, provider=provider
            )
            logger.info(
                "Azure OpenAI model created successfully: %s (endpoint: %s)",
                self.config.deployment_name,
                self.config.azure_endpoint,
            )
        except Exception as e:
            logger.error(
                "Failed to create Azure OpenAI model: %s (endpoint: %s, deployment: %s)",
                e,
                self.config.azure_endpoint,
                self.config.deployment_name,
            )
            raise

    def _create_agent(self) -> None:
        """Create the Pydantic AI Agent instance."""
        try:
            system_prompt = (
                "You are a helpful AI coding assistant integrated into a code viewing application. "
                "You can help users understand code, provide explanations, suggest improvements, "
                "and assist with coding tasks. Be concise but thorough in your responses. "
                "When discussing code, use proper formatting and be specific about file names, "
                "function names, and line numbers when relevant."
            )

            self._agent = Agent(
                model=self._model,
                system_prompt=system_prompt,
                retries=self.config.max_retries,
            )
            logger.info(
                "Pydantic AI Agent created successfully with %d max retries",
                self.config.max_retries,
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

    def get_available_tools(self) -> list[str]:
        """Get list of available tool names.

        Returns:
            List of tool names
        """
        tools = []
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
        return tools

    def get_tool_descriptions(self) -> dict[str, str]:
        """Get descriptions of available tools.

        Returns:
            Dictionary mapping tool names to descriptions
        """
        descriptions = {}
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

    # Enhanced conversation methods with tool support

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
        status_code = None
        if hasattr(exception, "status_code"):
            status_code = exception.status_code
        elif hasattr(exception, "response") and hasattr(
            exception.response, "status_code"
        ):
            status_code = exception.response.status_code

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
        while retry_count <= self.config.max_retries:
            try:
                # Use asyncio.wait_for to handle timeouts
                result = await asyncio.wait_for(
                    self._agent.run(message.strip()),
                    timeout=self.config.request_timeout,
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
                error_type, error_msg = self._categorize_error(e)

                # Check if this is a retryable error
                retryable_errors = {
                    "connection",
                    "server_error",
                    "rate_limit",
                    "timeout",
                }
                is_retryable = error_type in retryable_errors

                if is_retryable and retry_count < self.config.max_retries:
                    retry_count += 1
                    wait_time = min(2**retry_count, 30)  # Exponential backoff, max 30s
                    logger.warning(
                        "Retryable error occurred (attempt %d/%d): %s. Retrying in %ds...",
                        retry_count,
                        self.config.max_retries,
                        error_msg,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Non-retryable error or max retries reached
                    if retry_count >= self.config.max_retries:
                        logger.error(
                            "Max retries (%d) exceeded for message. Final error: %s",
                            self.config.max_retries,
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
        return f"Azure OpenAI model: {self.config.deployment_name} (endpoint: {self.config.azure_endpoint})"

    def get_health_status(self) -> dict:
        """Get the health status of the AI Agent.

        Returns:
            Dict containing health status information.
        """
        return {
            "configured": self.is_configured,
            "model_name": self.config.deployment_name,
            "endpoint": self.config.azure_endpoint,
            "max_retries": self.config.max_retries,
            "timeout": self.config.request_timeout,
        }

    # MCP File Server Integration Methods

    async def connect_mcp(self) -> bool:
        """Connect to the MCP file server.

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            FileOperationError: If MCP server is not configured.
        """
        if not self.mcp_file_server:
            raise FileOperationError("MCP file server not configured")

        logger.info("Connecting to MCP file server...")
        return await self.mcp_file_server.connect()

    async def disconnect_mcp(self) -> None:
        """Disconnect from the MCP file server."""
        if self.mcp_file_server:
            logger.info("Disconnecting from MCP file server...")
            await self.mcp_file_server.disconnect()

    @asynccontextmanager
    async def mcp_context(self) -> AsyncGenerator[None, None]:
        """Context manager for MCP file server operations."""
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

    async def read_multiple_files(self, file_paths: list[str]) -> dict[str, str]:
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
        """
        self.workspace_root = Path(workspace_path).resolve()
        logger.info(f"Workspace root set to: {self.workspace_root}")

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

    def create_workspace_directory(self, dir_path: str) -> None:
        """Create directory in workspace.

        Args:
            dir_path: Relative path to directory within workspace.

        Raises:
            ValueError: If path is outside workspace.
        """
        resolved_path = self.resolve_workspace_path(dir_path)
        resolved_path.mkdir(parents=True, exist_ok=True)

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

    # Validation methods
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

        path_parts = Path(file_path).parts
        for part in path_parts:
            name_without_ext = part.split(".")[0].upper()
            if name_without_ext in reserved_names:
                raise ValueError(f"Reserved file name: {part}")

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
        max_size = (
            self.mcp_file_server.config.max_file_size
            if self.mcp_file_server
            else 10 * 1024 * 1024
        )

        if len(content_bytes) > max_size:
            raise ValueError(
                f"File size exceeds maximum allowed: {len(content_bytes)} > {max_size} bytes"
            )

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

    # Enhanced file operations with validation
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

    # Batch operations
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

    # Retry mechanisms
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
                return await self.read_file(file_path)
            except FileOperationError as e:
                last_error = e
                if attempt < max_retries:
                    # Wait before retry (exponential backoff)
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    logger.warning(
                        f"Read failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}"
                    )
                else:
                    logger.error(f"Read failed after {max_retries} retries: {e}")
                    break

        if last_error:
            raise last_error
        raise RuntimeError("Unexpected error in retry logic")

    async def write_file_with_retry(
        self, file_path: str, content: str, max_retries: int = 3
    ) -> bool:
        """Write file with automatic retry on transient errors.

        Args:
            file_path: Path to file to write.
            content: Content to write.
            max_retries: Maximum number of retry attempts.

        Returns:
            bool: True if successful.

        Raises:
            FileOperationError: If all retries are exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return await self.write_file(file_path, content)
            except FileOperationError as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    logger.warning(
                        f"Write failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}"
                    )
                else:
                    logger.error(f"Write failed after {max_retries} retries: {e}")
                    break

        if last_error:
            raise last_error
        raise RuntimeError("Unexpected error in retry logic")

    # Enhanced error handling for workspace operations
    def safe_read_workspace_file(self, file_path: str) -> tuple[str | None, str | None]:
        """Safely read workspace file with error capture.

        Args:
            file_path: Relative path to file within workspace.

        Returns:
            Tuple[Optional[str], Optional[str]]: (content, error_message)
        """
        try:
            content = self.read_workspace_file(file_path)
            return content, None
        except Exception as e:
            return None, str(e)

    def safe_write_workspace_file(self, file_path: str, content: str) -> str | None:
        """Safely write workspace file with error capture.

        Args:
            file_path: Relative path to file within workspace.
            content: Content to write to file.

        Returns:
            Optional[str]: Error message if failed, None if successful.
        """
        try:
            self.write_workspace_file(file_path, content)
            return None
        except Exception as e:
            return str(e)

    # Health checks and diagnostics
    def check_workspace_health(self) -> dict[str, Any]:
        """Check workspace health and accessibility.

        Returns:
            Dict[str, Any]: Health status information.
        """
        health: dict[str, Any] = {
            "workspace_set": self.workspace_root is not None,
            "workspace_accessible": False,
            "workspace_writable": False,
            "mcp_configured": self.mcp_file_server is not None,
            "mcp_connected": False,
            "errors": [],
        }

        if self.workspace_root:
            try:
                health["workspace_accessible"] = (
                    self.workspace_root.exists() and self.workspace_root.is_dir()
                )

                # Test write permissions
                test_file = self.workspace_root / ".write_test"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    health["workspace_writable"] = True
                except Exception as e:
                    health["errors"].append(f"Workspace not writable: {e}")

            except Exception as e:
                health["errors"].append(f"Workspace access error: {e}")

        if self.mcp_file_server:
            health["mcp_connected"] = self.mcp_file_server.is_connected
            if not health["mcp_connected"]:
                health["errors"].append("MCP server not connected")

        return health

    async def send_message_with_tools_stream(
        self,
        message: str,
        on_chunk,
        on_error=None,
        enable_filesystem: bool = True,
    ) -> AIResponse:
        """Send a message with tool support and streaming output.

        Args:
            message: The message to send to the AI
            on_chunk: Callback function called for each chunk (chunk: str, is_final: bool)
            on_error: Optional callback function called on errors (error: Exception)
            enable_filesystem: Whether to enable filesystem tools for this conversation

        Returns:
            AIResponse: The response from the AI with stream_id populated
        """
        max_retries = self.config.max_retries
        retry_count = 0
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                if (
                    enable_filesystem
                    and self.filesystem_tools_enabled
                    and self.mcp_file_server
                    and not self.mcp_file_server.is_connected
                ):
                    # Ensure MCP connection
                    await self.connect_mcp()

                # Create and track stream handler
                if not hasattr(self, "_stream_handler"):
                    self._stream_handler = StreamHandler()

                stream_handler = self._stream_handler
                self.current_stream_handler = stream_handler

                # Start streaming with our handler
                stream_id = await stream_handler.start_stream(
                    on_chunk, on_error=on_error
                )
                self.current_stream_id = stream_id

                try:
                    # Use Pydantic AI's streaming capabilities
                    async with self._agent.run_stream(message) as response:
                        # Stream the response text in real-time
                        full_content = []
                        chunk_count = 0

                        # Stream chunks as they arrive
                        async for chunk in response.stream_text():
                            full_content.append(chunk)
                            chunk_count += 1

                            # Call the external callback directly for each chunk
                            try:
                                # We don't know if this is the final chunk yet, so pass False
                                callback_result = on_chunk(chunk, False)
                                if hasattr(callback_result, "__await__"):
                                    await callback_result
                            except Exception as callback_error:
                                logger.error(
                                    f"Error in streaming callback: {callback_error}"
                                )
                                if on_error:
                                    with suppress(Exception):
                                        on_error(callback_error)

                        # After all chunks are streamed, send a final empty chunk to mark completion
                        try:
                            callback_result = on_chunk(
                                "", True
                            )  # Empty chunk with is_final=True
                            if hasattr(callback_result, "__await__"):
                                await callback_result
                        except Exception as callback_error:
                            logger.error(
                                f"Error in final streaming callback: {callback_error}"
                            )

                        # Get the final output
                        final_output = await response.get_output()
                        full_text = "".join(full_content)

                        # Complete the stream in our handler (for internal tracking only)
                        if stream_handler:
                            await stream_handler.complete_stream(stream_id)

                        # Clear current stream tracking
                        self.current_stream_handler = None
                        self.current_stream_id = None

                        return AIResponse(
                            success=True,
                            content=final_output or full_text,
                            stream_id=stream_id,
                            retry_count=retry_count,
                        )

                except Exception as stream_error:
                    # Handle streaming errors
                    await stream_handler.handle_error(stream_id, stream_error)
                    # Clear current stream tracking on error
                    self.current_stream_handler = None
                    self.current_stream_id = None
                    raise stream_error

            except Exception as e:
                last_error = e
                retry_count = attempt

                # Don't retry on the last attempt
                if attempt < max_retries:
                    # Calculate exponential backoff: 2^attempt seconds
                    backoff_time = 2**attempt
                    logger.warning(
                        f"Streaming attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {backoff_time}s (attempt {attempt + 2}/{max_retries + 1})"
                    )

                    # Wait before retrying with exponential backoff
                    await asyncio.sleep(backoff_time)

                    # Check if stream was interrupted during backoff
                    if (
                        hasattr(self, "current_stream_handler")
                        and self.current_stream_handler
                        and hasattr(self.current_stream_handler, "_interrupt_event")
                        and self.current_stream_handler._interrupt_event.is_set()
                    ):
                        logger.info("Stream was interrupted during retry backoff")
                        break
                else:
                    logger.error(
                        f"All streaming attempts failed after {max_retries} retries. Final error: {e}"
                    )

        # All retries exhausted - return failure response
        if last_error:
            error_type, error_message = self._categorize_error(last_error)

            # Call error callback if provided
            if on_error:
                try:
                    on_error(last_error)
                except Exception as callback_error:
                    logger.error(f"Error in error callback: {callback_error}")

            return AIResponse(
                success=False,
                content=error_message,
                error=str(last_error),
                error_type=error_type,
                retry_count=retry_count,
                stream_id=getattr(locals(), "stream_id", None),
            )

        # This should not be reached, but handle edge case
        return AIResponse(
            success=False,
            content="Unexpected error in retry logic",
            error="No error captured in retry loop",
            error_type="unknown",
            retry_count=retry_count,
        )

    async def interrupt_current_stream(self) -> bool:
        """Interrupt the current stream if it exists.

        Returns:
            bool: True if a stream was interrupted, False if no active stream
        """
        if self.current_stream_handler and self.current_stream_id:
            await self.current_stream_handler.interrupt_stream(self.current_stream_id)
            self.current_stream_handler = None
            self.current_stream_id = None
            return True
        return False
