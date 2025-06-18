"""AI Services package for modular AI functionality.

This package contains focused, single-responsibility services that were
extracted from the monolithic AIAgent class to improve testability and
maintainability.
"""

from .ai_messaging_service import AIMessagingService
from .core_ai_service import AIResponse, CoreAIService
from .mcp_connection_service import MCPConnectionService
from .memory_context_service import MemoryContextService
from .project_history_service import ProjectHistoryService
from .streaming_response_service import StreamingResponseService
from .tool_manager import ToolManager
from .tool_registration_service import ToolRegistrationService
from .workspace_service import FileOperationError, WorkspaceService

__all__ = [
    "AIMessagingService",
    "CoreAIService",
    "AIResponse",
    "MemoryContextService",
    "StreamingResponseService",
    "ToolManager",
    "MCPConnectionService",
    "ProjectHistoryService",
    "ToolRegistrationService",
    "WorkspaceService",
    "FileOperationError",
]
