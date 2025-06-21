# Agent Architecture Library

A comprehensive multi-agent architecture for coding assistance and automation.

## Features

- **Agent Orchestrator**: Coordinates multiple specialized agents
- **Specialized Agents**: Code analysis, refactoring, test generation, documentation
- **Task Routing**: Intelligent routing of tasks to appropriate agents
- **File Change Notifications**: Real-time file change handling
- **Extensible Architecture**: Easy to add new agent types

## Installation

```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Usage

### Command Line

```bash
# Analyze code
agent-orchestrator --query "analyze this code" --files src/main.py

# Generate tests
agent-orchestrator --query "generate tests for this module" --files src/utils.py
```

### Python API

```python
from agent_arch import AgentOrchestrator

# Initialize orchestrator
orchestrator = AgentOrchestrator(working_directory=".")
await orchestrator.start_all_agents()

# Process a query
response = await orchestrator.process_query(
    query="refactor this code to improve readability",
    files=["src/main.py"]
)

print(f"Agent: {response.agent_type.value}")
print(f"Result: {response.content}")

# Cleanup
await orchestrator.stop_all_agents()
```

## Agent Types

### Code Analysis Agent
- Analyzes code structure and patterns
- Identifies code quality issues
- Provides metrics and insights

### Refactoring Agent
- Handles code refactoring tasks
- Improves code structure and readability
- Applies best practices

### Test Generation Agent
- Generates unit and integration tests
- Creates test suites
- Ensures code coverage

### Documentation Agent
- Generates and maintains documentation
- Creates docstrings and API docs
- Updates README files

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=agent_arch

# Type checking
mypy src/agent_arch

# Code formatting
black src/ tests/
isort src/ tests/
```

## Architecture

The library uses a multi-agent architecture with:

1. **Orchestrator**: Central coordinator that routes tasks
2. **Base Agent**: Abstract base class for all agents
3. **Specialized Agents**: Domain-specific agents for different tasks
4. **Type System**: Comprehensive type definitions for agent communication

## Extending

To add a new agent type:

1. Create a new agent class inheriting from `BaseAgent`
2. Implement `can_handle_task()` and `process_task()` methods
3. Add the agent type to the enum
4. Register the agent in the orchestrator

```python
from agent_arch.agents import BaseAgent
from agent_arch.types import AgentType, TaskContext, AgentResponse

class MyCustomAgent(BaseAgent):
    async def can_handle_task(self, context: TaskContext) -> bool:
        return "my_task" in context.user_query.lower()
    
    async def process_task(self, context: TaskContext) -> AgentResponse:
        # Implement your logic here
        return self.create_response("Task completed")
``` 
