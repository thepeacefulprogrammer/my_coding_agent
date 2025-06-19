"""AI Services package for both MCP communication and direct AI model integration.

This package contains:
- MCP client services for connecting to external AI agent architectures via Model Context Protocol
- Direct AI service integration for Azure OpenAI and other AI models via REST APIs
- Streaming response handlers for real-time AI interactions
"""

# Import modules (needed for test patching)
from . import (
    ai_service_adapter,
    mcp_connection_service,
    query_processor,
    streaming_response_service,
)
from .ai_service_adapter import (
    AIResponse,
    AIServiceAdapter,
    AIServiceConfig,
    AIServiceConnectionError,
    AIServiceError,
    AIServiceRateLimitError,
    AIServiceTimeoutError,
    AIStreamingResponse,
)

# Import classes for direct use
from .mcp_connection_service import MCPConnectionService
from .query_processor import (
    QueryContext,
    QueryProcessor,
    QueryRequest,
    ResponseValidator,
    RetryPolicy,
)
from .streaming_response_service import StreamingResponseService

# AI Service components (to be implemented)
# from .azure_openai_provider import AzureOpenAIProvider
# from .streaming_handler import AIStreamingHandler

__all__ = [
    # Modules (for test patching)
    "mcp_connection_service",
    "streaming_response_service",
    "ai_service_adapter",
    "query_processor",
    # MCP Services
    "MCPConnectionService",
    "StreamingResponseService",
    # AI Service Core Components
    "AIServiceAdapter",
    "AIServiceConfig",
    "AIResponse",
    "AIStreamingResponse",
    "AIServiceError",
    "AIServiceConnectionError",
    "AIServiceTimeoutError",
    "AIServiceRateLimitError",
    # Query Processing Components
    "QueryProcessor",
    "QueryRequest",
    "QueryContext",
    "RetryPolicy",
    "ResponseValidator",
    # AI Services (to be added)
    # "AzureOpenAIProvider",
    # "AIStreamingHandler",
]
