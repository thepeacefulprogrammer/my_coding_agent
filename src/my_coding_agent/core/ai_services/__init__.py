"""AI Services package for both MCP communication and direct AI model integration.

This package contains:
- MCP client services for connecting to external AI agent architectures via Model Context Protocol
- Direct AI service integration for Azure OpenAI and other AI models via REST APIs
- Streaming response handlers for real-time AI interactions
"""

from .mcp_connection_service import MCPConnectionService
from .streaming_response_service import StreamingResponseService

# AI Service components (to be implemented)
# from .ai_service_adapter import AIServiceAdapter
# from .azure_openai_provider import AzureOpenAIProvider
# from .streaming_handler import AIStreamingHandler

__all__ = [
    # MCP Services
    "MCPConnectionService",
    "StreamingResponseService",
    # AI Services (to be added)
    # "AIServiceAdapter",
    # "AzureOpenAIProvider",
    # "AIStreamingHandler",
]
