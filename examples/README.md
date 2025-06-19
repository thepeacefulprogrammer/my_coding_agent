# Examples

This directory contains example code demonstrating how to use My Coding Agent.

## Structure

- `basic_usage/` - Simple examples for common use cases
- `advanced/` - More complex examples showing advanced features
- `demo_ai_chat.py` - AI service integration with Azure OpenAI
- Various MCP and UI demos

## Running Examples

Each example can be run independently:

```bash
# From the project root
python examples/basic_usage/example_name.py
```

## Prerequisites

Make sure you have installed the project in development mode:

```bash
pip install -e .[dev]
```

### AI Service Examples

For AI service examples (like `demo_ai_chat.py`), you'll need Azure OpenAI credentials:

```bash
# Required environment variables
export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'
export AZURE_OPENAI_API_KEY='your-api-key-here'

# Optional configuration
export AZURE_OPENAI_API_VERSION='2024-07-01-preview'
export AZURE_OPENAI_DEPLOYMENT='gpt-4o'
```

AI service examples include:
- `demo_ai_chat.py` - Basic AI chat functionality with streaming responses
- `basic_usage/ai_service_config_example.py` - Configuration setup guide

## Contributing Examples

When adding new examples:
1. Choose the appropriate subdirectory (basic_usage or advanced)
2. Include docstrings explaining what the example demonstrates
3. Add any necessary comments for clarity
4. Update this README if you add new categories
