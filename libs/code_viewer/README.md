# Code Viewer Library

A PyQt6-based code viewer application with chat interface for AI agent integration.

## Features

- **Code Viewing**: Syntax-highlighted code viewer with file tree navigation
- **Chat Interface**: Interactive chat widget for communicating with AI agents
- **MCP Integration**: Support for Model Context Protocol servers
- **Agent Integration**: Bridge to external agent architecture libraries
- **Theme Support**: Dark and light themes with customizable styling

## Installation

```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Usage

```bash
# Run the code viewer
code-viewer

# Or as a module
python -m code_viewer
```

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=code_viewer

# Type checking
mypy src/code_viewer

# Code formatting
black src/ tests/
isort src/ tests/
```

## Architecture

The code viewer is designed to work with external agent architecture libraries:

- **Agent Bridge**: Connects to external agent libraries
- **File Change Handler**: Monitors and responds to file changes from agents
- **Chat Integration**: Provides UI for agent communication
- **MCP Support**: Connects to MCP servers for additional tools

## Agent Integration

The code viewer expects an external `agent_arch` library with:

```python
from agent_arch import AgentOrchestrator

# The orchestrator should have these methods:
orchestrator = AgentOrchestrator(working_directory=".")
response = await orchestrator.process_query("analyze this code")
``` 
