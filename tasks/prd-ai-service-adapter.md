# Product Requirements Document: AI Service Adapter

## Introduction/Overview

The AI Service Adapter is a foundational component that will enable the MCP client interface to communicate with external AI services, specifically Azure OpenAI GPT-based models. This feature establishes a clean interface for AI interactions while maintaining separation from the existing MCP client architecture. The adapter will provide a streamlined chat interface for developers ("vibe coders") to interact with AI models through a simple query-in, stream-out response pattern.

**Problem Statement:** The current MCP client interface lacks AI capabilities, and developers need a way to interact with AI models directly within the application. This adapter will serve as the foundation for future AI agent architecture while providing immediate value through chat functionality.

## Goals

1. **Enable AI Chat Functionality:** Provide a working chat interface that can send queries to Azure OpenAI and receive streaming responses
2. **Establish AI Service Interface:** Create a clean, extensible interface for AI service communication that can support future AI agent architecture
3. **Configuration Flexibility:** Support both environment variables and configuration files for API endpoints, keys, and model settings
4. **Streaming Response Support:** Implement real-time streaming responses for better user experience
5. **Azure OpenAI Integration:** Specifically target GPT-based models hosted on Azure infrastructure

## User Stories

1. **As a developer**, I want to send chat queries to AI models so that I can get assistance with coding problems
2. **As a developer**, I want to see AI responses stream in real-time so that I don't have to wait for complete responses
3. **As a system administrator**, I want to configure AI endpoints and API keys through configuration files so that I can manage deployments easily
4. **As a developer**, I want the AI service to be separate from MCP functionality so that I can use both independently
5. **As a future user**, I want the AI interface to be extensible so that advanced AI agent features can be added later

## Functional Requirements

### Core AI Service Adapter
1. **F1:** The system must provide an `AIServiceAdapter` class that handles communication with Azure OpenAI services
2. **F2:** The adapter must support sending text queries and receiving streaming text responses
3. **F3:** The adapter must use the OpenAI standard REST API format for compatibility
4. **F4:** The adapter must support Azure OpenAI authentication using API keys
5. **F5:** The adapter must handle connection errors and provide meaningful error messages

### Configuration Management
6. **F6:** The system must support configuration via environment variables (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_API_VERSION`)
7. **F7:** The system must support configuration via configuration files (extend existing settings system)
8. **F8:** The system must allow runtime configuration of AI model parameters (temperature, max_tokens, etc.)
9. **F9:** The system must validate configuration parameters on startup

### Chat Interface Integration
10. **F10:** The system must integrate with the existing chat widget to display AI responses
11. **F11:** The system must clearly distinguish AI responses from MCP tool responses in the UI
12. **F12:** The system must support streaming display of AI responses as they arrive
13. **F13:** The system must maintain conversation context within a single chat session

### PydanticAI Integration
14. **F14:** The system must use PydanticAI library for structured AI interactions
15. **F15:** The system must implement Azure OpenAI provider using PydanticAI's `AzureProvider`
16. **F16:** The system must support both direct API calls and PydanticAI Agent patterns
17. **F17:** The system must provide type-safe response handling using Pydantic models

### Error Handling & Reliability
18. **F18:** The system must handle network timeouts gracefully
19. **F19:** The system must provide fallback behavior when AI services are unavailable
20. **F20:** The system must log AI service interactions for debugging purposes
21. **F21:** The system must respect rate limits and implement appropriate backoff strategies

## Non-Goals (Out of Scope)

1. **Advanced AI Agent Features:** Complex AI agents, tool calling, or multi-step workflows (reserved for future iterations)
2. **Multiple AI Provider Support:** Only Azure OpenAI support in initial version (OpenAI, Anthropic, etc. can be added later)
3. **Conversation Persistence:** Chat history will not be saved between application sessions
4. **File Upload/Analysis:** No support for uploading documents or files to AI models
5. **Custom Model Fine-tuning:** No support for training or fine-tuning custom models
6. **MCP Integration:** AI Service Adapter will remain separate from MCP client functionality

## Design Considerations

### Architecture
- **Separation of Concerns:** AI Service Adapter operates independently from MCP Client Coordinator
- **Plugin Architecture:** Design interface to support future AI providers and advanced features
- **Streaming First:** All AI interactions should support streaming responses by default

### UI Integration
- **Chat Widget Enhancement:** Extend existing chat widget to handle both MCP and AI responses
- **Visual Distinction:** AI responses should be visually distinct from MCP tool outputs
- **Streaming Indicators:** Show appropriate loading/typing indicators during AI response generation

### Configuration Structure
```yaml
ai_service:
  provider: "azure_openai"
  azure_openai:
    endpoint: "https://your-resource.openai.azure.com/"
    api_key: "${AZURE_OPENAI_API_KEY}"
    api_version: "2024-07-01-preview"
    deployment_name: "gpt-4o"
    model_params:
      temperature: 0.7
      max_tokens: 1000
      stream: true
```

## Technical Considerations

### Dependencies
- **PydanticAI:** Primary library for AI interactions (`pydantic-ai-slim[openai]`)
- **Azure OpenAI:** Use PydanticAI's `AzureProvider` for authentication
- **Async Support:** All AI operations must be asynchronous to prevent UI blocking

### Integration Points
- **Settings System:** Extend `src/my_coding_agent/config/settings.py` for AI configuration
- **Chat Widget:** Modify existing chat components to handle AI responses
- **Theme System:** Ensure AI responses respect current theme (dark/light mode)

### Testing Strategy
- **Unit Tests:** Test AI service adapter functionality with mocked responses
- **Integration Tests:** Test full AI service flow with test Azure OpenAI endpoints
- **UI Tests:** Verify chat widget integration and streaming display

## Success Metrics

1. **Functionality:** AI chat interface successfully sends queries and receives streaming responses
2. **Response Time:** AI responses begin streaming within 2 seconds of query submission
3. **Error Handling:** Graceful handling of network errors, API rate limits, and invalid configurations
4. **User Experience:** Developers can have natural conversations with AI models through the interface
5. **Code Quality:** Maintain current test coverage levels (>90%) with new AI service components
6. **Configuration:** Easy setup process with clear documentation for Azure OpenAI configuration

## Open Questions

1. **Authentication:** Should we support Azure AD authentication in addition to API keys?
2. **Model Selection:** Should users be able to switch between different GPT models at runtime?
3. **Context Window:** How should we handle conversation context that exceeds model token limits?
4. **Logging:** What level of detail should be logged for AI interactions (privacy considerations)?
5. **Future Integration:** How should this interface evolve to support the planned AI agent architecture?

## Implementation Notes

This PRD establishes the foundation for AI integration while maintaining focus on immediate value through chat functionality. The design prioritizes simplicity and extensibility, ensuring that future AI agent features can be built upon this foundation without requiring significant refactoring.

The separation from MCP functionality ensures that both systems can evolve independently while sharing the same UI infrastructure.
