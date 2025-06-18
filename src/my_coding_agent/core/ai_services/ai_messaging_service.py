"""AI Messaging Service for enhanced communication with AI.

This service extends the basic CoreAIService with advanced messaging capabilities
including tool support, file context integration, project analysis, and intelligent
message routing based on intent detection.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .core_ai_service import AIResponse, CoreAIService

logger = logging.getLogger(__name__)


class AIMessagingService(CoreAIService):
    """Enhanced AI messaging service with tool support and context awareness."""

    def __init__(
        self, config, mcp_connection_service=None, workspace_service=None
    ) -> None:
        """Initialize the AI messaging service.

        Args:
            config: AIAgentConfig instance with Azure OpenAI settings
            mcp_connection_service: Optional MCP connection service for filesystem tools
            workspace_service: Optional workspace service for file operations
        """
        super().__init__(config)
        self._mcp_connection_service = mcp_connection_service
        self._workspace_service = workspace_service
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

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
            # Ensure MCP connection if filesystem tools are requested
            if (
                enable_filesystem
                and self._mcp_connection_service
                and not self._mcp_connection_service.is_connected()
            ):
                await self._mcp_connection_service.connect()

            response = await self._agent.run(message)

            return AIResponse(success=True, content=response.data)

        except Exception as e:
            error_type, error_msg = self._categorize_error(e)
            self.logger.error(f"Error in enhanced conversation: {error_msg}")
            return AIResponse(
                success=False, content="", error=error_msg, error_type=error_type
            )

    async def analyze_project_files(self) -> AIResponse:
        """Analyze project files using filesystem tools.

        Returns:
            AIResponse: Analysis results
        """
        try:
            if not self._mcp_connection_service:
                return AIResponse(
                    success=False,
                    content="Filesystem tools not available for project analysis",
                )

            if not self._mcp_connection_service.is_connected():
                await self._mcp_connection_service.connect()

            # Get project structure
            files = await self._mcp_connection_service.list_directory(".")

            # Read key files for analysis
            analysis_prompt = f"Please analyze this project structure: {files}"

            response = await self._agent.run(analysis_prompt)

            return AIResponse(success=True, content=response.data)

        except Exception as e:
            error_type, error_msg = self._categorize_error(e)
            self.logger.error(f"Error in project analysis: {error_msg}")
            return AIResponse(
                success=False,
                content="",
                error=error_msg,
                error_type=error_type,
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
            if not self._mcp_connection_service:
                return AIResponse(
                    success=False,
                    content="Filesystem tools not available for code generation",
                )

            if not self._mcp_connection_service.is_connected():
                await self._mcp_connection_service.connect()

            # Save the generated code
            success = await self._mcp_connection_service.write_file(file_path, code)

            if success:
                return AIResponse(
                    success=True, content=f"Code generated and saved to {file_path}"
                )
            else:
                return AIResponse(
                    success=False, content=f"Failed to save code to {file_path}"
                )

        except Exception as e:
            error_type, error_msg = self._categorize_error(e)
            self.logger.error(f"Error generating and saving code: {error_msg}")
            return AIResponse(
                success=False, content="", error=error_msg, error_type=error_type
            )

    async def send_message_with_file_context(
        self, message: str, file_path: str
    ) -> AIResponse:
        """Send a message to AI with file content as context.

        Args:
            message: The message to send to the AI.
            file_path: Path to the file to include as context.

        Returns:
            AIResponse: The response from the AI.
        """
        try:
            if not self._workspace_service:
                return AIResponse(
                    success=False,
                    content="Workspace service not available for file context",
                    error_type="service_unavailable",
                )

            # Read file content using workspace service
            file_content = self._workspace_service.read_workspace_file(file_path)

            enhanced_message = f"""
Context file: {file_path}
File content:
```
{file_content}
```

User message: {message}
"""
            return await self.send_message(enhanced_message)

        except Exception as e:
            error_type, error_msg = self._categorize_error(e)
            self.logger.error(
                f"Failed to read file {file_path} for context: {error_msg}"
            )
            return AIResponse(
                success=False,
                content="",
                error=f"Failed to read file for context: {error_msg}",
                error_type=error_type,
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
                        result = await self.send_message_with_file_context(
                            message, file_path
                        )
                        # Check if the result is successful or if we should fall back
                        if result.success:
                            return result
                        else:
                            # Fall back to regular message if file context failed
                            self.logger.warning(
                                f"File context failed for {file_path}: {result.error}"
                            )
                            break
                    except Exception as e:
                        # Fall back to regular message if file read fails
                        self.logger.warning(f"Failed to read file {file_path}: {e}")
                        break

        return await self.send_message(message)

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

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of the AI messaging service."""
        base_status = super().get_health_status()

        # Add messaging-specific status
        messaging_status = {
            "service": "AIMessagingService",
            "mcp_connection_available": self._mcp_connection_service is not None,
            "workspace_service_available": self._workspace_service is not None,
        }

        if self._mcp_connection_service:
            messaging_status["mcp_connected"] = (
                self._mcp_connection_service.is_connected()
            )

        if self._workspace_service:
            messaging_status["workspace_configured"] = (
                self._workspace_service.is_configured()
            )

        return {**base_status, **messaging_status}
