## Relevant Files

- `src/my_coding_agent/core/ai_agent.py` - Main AI Agent orchestrator class with Pydantic AI integration and filesystem tools
- `tests/test_ai_agent.py` - Unit tests for AI Agent functionality
- `src/my_coding_agent/core/mcp_file_server.py` - MCP server for file system operations with security enhancements
- `tests/test_mcp_file_server.py` - Unit tests for MCP file server
- `tests/test_mcp_security_permissions.py` - Comprehensive security and permissions tests for MCP file server
- `tests/test_ai_agent_mcp_integration.py` - Unit tests for AI Agent MCP integration
- `tests/test_ai_agent_filesystem_tools.py` - Unit tests for AI Agent filesystem tools integration
- `tests/test_ai_agent_workspace_operations.py` - Unit tests for workspace-aware file operations with security boundaries
- `tests/test_ai_agent_error_handling.py` - Comprehensive error handling and validation tests for file operations
- `tests/test_mcp_integration_comprehensive.py` - Comprehensive MCP integration tests covering edge cases and complete scenarios
- `src/my_coding_agent/gui/chat_message_model.py` - Chat message data model with enums, data classes, and PyQt6 model for message management
- `tests/test_chat_message_model.py` - Comprehensive unit tests for chat message model functionality
- `src/my_coding_agent/gui/chat_widget.py` - PyQt6 chat interface widget with message display area, message bubbles, scrolling, input field, and send button functionality
- `tests/test_chat_widget.py` - Comprehensive unit tests for chat widget functionality (60/60 tests passing - 100% success rate)
- `examples/demo_chat_dark_theme.py` - Demo script showcasing dark theme chat widget functionality
- `examples/demo_ai_processing_indicators.py` - Demo script showcasing AI processing indicators with different states and animations
- `src/my_coding_agent/core/main_window.py` - Modified main window with three-panel layout (left: file tree 25%, center: code viewer 45%, right: chat widget 30%)
- `tests/test_main_window.py` - Unit tests for main window modifications including three-panel layout functionality
- `src/my_coding_agent/core/workflow_manager.py` - Workflow automation system integration
- `tests/test_workflow_manager.py` - Unit tests for workflow manager
- `src/my_coding_agent/core/task_parser.py` - Markdown task file parser and updater
- `tests/test_task_parser.py` - Unit tests for task parser (21/21 tests passing - 100% success rate)
- `pyproject.toml` - Updated dependencies with Pydantic AI and MCP libraries
- `.env_example` - Updated environment file with Azure AI configuration

### Notes

- Unit tests should typically be placed alongside the code files they are testing or in the `tests/` directory.
- Use `pytest [optional/path/to/test/file]` to run tests. Running without a path executes all tests found by the pytest configuration.
- Follow Test-Driven Development: write tests first, verify they fail, then implement code to make them pass.
- The MCP file server should follow the FastMCP pattern seen in the reference implementations.
- **Current Test Status**: All tests passing! Fixed all 7 failing tests related to health status, retry mechanisms, context managers, input sanitization, and security configuration expectations. Also fixed 2 MCP file server tests by patching stdio_client at the correct import location.
- **Current Linting Status**: All linting issues resolved! Fixed 135+ linting errors including modern Python type annotations (UP006, UP007, UP035), exception chaining (B904), nested if statements (SIM102), unused variables (F841), and code formatting.
- **CI Status**: ✅ COMPLETELY RESOLVED! All async test failures fixed with pytest-asyncio dependency and configuration. All linting issues resolved. All test failures fixed. CI should now pass 100%.

## Tasks

- [x] 1.0 Set up AI Agent Core Infrastructure
  - [x] 1.1 Add Pydantic AI and Azure AI dependencies to requirements.txt
  - [x] 1.2 Create .env.example with Azure AI configuration template
  - [x] 1.3 Create AI Agent service class with Azure provider integration
  - [x] 1.4 Implement basic chat functionality (send message, receive response)
  - [x] 1.5 Add error handling and logging for AI service failures
  - [x] 1.6 Write unit tests for AI Agent core functionality

- [x] 2.0 Integrate with MCP File System Server
  - [x] 2.1 Install and configure the official MCP filesystem server
  - [x] 2.2 Set up MCP client integration in AI Agent
  - [x] 2.3 Configure file system permissions and security boundaries
  - [x] 2.4 Integrate MCP filesystem tools with AI Agent capabilities
  - [x] 2.5 Add workspace-aware file operations (scoped to project directory)
  - [x] 2.6 Implement file operation error handling and validation
  - [x] 2.7 Write unit tests for MCP client integration and file operations

- [x] 3.0 Create Chat Interface UI Component
  - [x] 3.1 Design and implement chat message model for PyQt6
  - [x] 3.2 Create chat widget with message display area
  - [x] 3.3 Implement message input field with send button functionality
  - [x] 3.4 Add message bubbles with user/AI distinction styling
  - [x] 3.5 Implement scrollable message history with auto-scroll
  - [x] 3.6 Apply dark theme styling consistent with existing UI
  - [x] 3.7 Add AI processing indicators (typing, loading states)
  - [x] 3.8 Write unit tests for chat widget functionality

- [x] 4.0 Restructure Application Layout for Three-Panel Design
  - [x] 4.1 Modify main window to use three-panel QSplitter layout
  - [x] 4.2 Integrate existing file tree widget as left panel (25% width)
  - [x] 4.3 Maintain existing code viewer as center panel (45% width)
  - [x] 4.4 Add chat widget as right panel (30% width)
  - [x] 4.5 Implement adjustable splitter controls for panel resizing
  - [x] 4.6 Ensure responsive design and minimum panel sizes
  - [x] 4.7 Preserve existing keyboard shortcuts and functionality
  - [x] 4.8 Write unit tests for layout changes and panel interactions

- [ ] 5.0 Integrate AI Agent with Workflow Automation System
  - [x] 5.1 Create task markdown file parser to read/write task lists
  - [ ] 5.2 Implement PRD creation workflow automation (create-prd)
  - [ ] 5.3 Implement task generation workflow automation (generate-tasks)
  - [ ] 5.4 Implement task processing workflow automation (process-task-list)
  - [ ] 5.5 Add automatic task completion marking in markdown files
  - [ ] 5.6 Implement new task creation and relevant files section updates
  - [ ] 5.7 Create workflow manager to orchestrate all automation processes
  - [ ] 5.8 Integrate workflow manager with AI Agent chat interface
  - [ ] 5.9 Write comprehensive unit tests for all workflow automations
