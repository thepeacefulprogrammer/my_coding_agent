## Relevant Files

- `src/my_coding_agent/core/ai_agent.py` - Main AI Agent orchestrator class with Pydantic AI integration
- `tests/test_ai_agent.py` - Unit tests for AI Agent functionality
- `src/my_coding_agent/core/mcp_file_server.py` - MCP server for file system operations
- `tests/test_mcp_file_server.py` - Unit tests for MCP file server
- `src/my_coding_agent/gui/chat_widget.py` - PyQt6 chat interface widget
- `tests/test_chat_widget.py` - Unit tests for chat widget
- `src/my_coding_agent/gui/main_window.py` - Modified main window with three-panel layout
- `tests/test_main_window.py` - Unit tests for main window modifications
- `src/my_coding_agent/core/workflow_manager.py` - Workflow automation system integration
- `tests/test_workflow_manager.py` - Unit tests for workflow manager
- `src/my_coding_agent/core/task_parser.py` - Markdown task file parser and updater
- `tests/test_task_parser.py` - Unit tests for task parser
- `requirements.txt` - Updated dependencies with Pydantic AI and MCP libraries
- `.env.example` - Example environment file for Azure AI configuration

### Notes

- Unit tests should typically be placed alongside the code files they are testing or in the `tests/` directory.
- Use `pytest [optional/path/to/test/file]` to run tests. Running without a path executes all tests found by the pytest configuration.
- Follow Test-Driven Development: write tests first, verify they fail, then implement code to make them pass.
- The MCP file server should follow the FastMCP pattern seen in the reference implementations.

## Tasks

- [ ] 1.0 Set up AI Agent Core Infrastructure
  - [ ] 1.1 Add Pydantic AI and Azure AI dependencies to requirements.txt
  - [ ] 1.2 Create .env.example with Azure AI configuration template
  - [ ] 1.3 Create AI Agent service class with Azure provider integration
  - [ ] 1.4 Implement basic chat functionality (send message, receive response)
  - [ ] 1.5 Add error handling and logging for AI service failures
  - [ ] 1.6 Write unit tests for AI Agent core functionality

- [ ] 2.0 Implement MCP File System Integration
  - [ ] 2.1 Create MCP server using FastMCP pattern for file operations
  - [ ] 2.2 Implement file reading capabilities (text files, markdown)
  - [ ] 2.3 Implement file writing capabilities with safety checks
  - [ ] 2.4 Implement file creation and deletion operations
  - [ ] 2.5 Add directory listing and navigation capabilities
  - [ ] 2.6 Integrate MCP server with AI Agent for file operations
  - [ ] 2.7 Write comprehensive unit tests for all file operations

- [ ] 3.0 Create Chat Interface UI Component
  - [ ] 3.1 Design and implement chat message model for PyQt6
  - [ ] 3.2 Create chat widget with message display area
  - [ ] 3.3 Implement message input field with send button functionality
  - [ ] 3.4 Add message bubbles with user/AI distinction styling
  - [ ] 3.5 Implement scrollable message history with auto-scroll
  - [ ] 3.6 Apply dark theme styling consistent with existing UI
  - [ ] 3.7 Add AI processing indicators (typing, loading states)
  - [ ] 3.8 Write unit tests for chat widget functionality

- [ ] 4.0 Restructure Application Layout for Three-Panel Design
  - [ ] 4.1 Modify main window to use three-panel QSplitter layout
  - [ ] 4.2 Integrate existing file tree widget as left panel (25% width)
  - [ ] 4.3 Maintain existing code viewer as center panel (45% width)
  - [ ] 4.4 Add chat widget as right panel (30% width)
  - [ ] 4.5 Implement adjustable splitter controls for panel resizing
  - [ ] 4.6 Ensure responsive design and minimum panel sizes
  - [ ] 4.7 Preserve existing keyboard shortcuts and functionality
  - [ ] 4.8 Write unit tests for layout changes and panel interactions

- [ ] 5.0 Integrate AI Agent with Workflow Automation System
  - [ ] 5.1 Create task markdown file parser to read/write task lists
  - [ ] 5.2 Implement PRD creation workflow automation (create-prd)
  - [ ] 5.3 Implement task generation workflow automation (generate-tasks)
  - [ ] 5.4 Implement task processing workflow automation (process-task-list)
  - [ ] 5.5 Add automatic task completion marking in markdown files
  - [ ] 5.6 Implement new task creation and relevant files section updates
  - [ ] 5.7 Create workflow manager to orchestrate all automation processes
  - [ ] 5.8 Integrate workflow manager with AI Agent chat interface
  - [ ] 5.9 Write comprehensive unit tests for all workflow automations
