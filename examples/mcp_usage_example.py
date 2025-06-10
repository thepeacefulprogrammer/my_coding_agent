#!/usr/bin/env python3
"""
Example demonstrating how to use MCP (Model Context Protocol) with the AI Agent.

This example shows:
1. How to configure MCP file server
2. How to initialize AI Agent with MCP support
3. How to use filesystem tools through the agent
4. Error handling and best practices
"""

import asyncio
import logging
import os
from pathlib import Path

from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
from my_coding_agent.core.mcp_file_server import FileOperationError, MCPFileConfig


async def setup_mcp_example():
    """Set up MCP configuration and AI Agent."""

    # 1. Configure the AI Agent (requires Azure OpenAI credentials)
    try:
        ai_config = AIAgentConfig.from_env()
        print("✅ AI Agent configuration loaded from environment")
    except ValueError as e:
        print(f"❌ Missing environment variables: {e}")
        print("Please set: ENDPOINT, API_KEY, MODEL")
        return None, None

    # 2. Configure MCP File Server
    workspace_path = Path.cwd()  # Use current directory as workspace

    mcp_config = MCPFileConfig(
        base_directory=workspace_path,
        allowed_extensions=[".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml"],
        enable_write_operations=True,
        enable_delete_operations=False,  # Safer to keep this disabled
        max_file_size=5 * 1024 * 1024,  # 5MB limit
    )

    print(f"✅ MCP configured for workspace: {workspace_path}")

    # 3. Initialize AI Agent with MCP support
    agent = AIAgent(
        config=ai_config, mcp_config=mcp_config, enable_filesystem_tools=True
    )

    print(f"✅ AI Agent initialized with {len(agent.get_available_tools())} tools")
    print(f"Available tools: {', '.join(agent.get_available_tools())}")

    return agent, mcp_config


async def demonstrate_mcp_operations(agent: AIAgent):
    """Demonstrate various MCP operations."""

    print("\n" + "=" * 50)
    print("DEMONSTRATING MCP OPERATIONS")
    print("=" * 50)

    try:
        # Connect to MCP server
        print("\n1. Connecting to MCP server...")
        connected = await agent.connect_mcp()
        if not connected:
            print("❌ Failed to connect to MCP server")
            return
        print("✅ Connected to MCP server")

        # Get MCP health status
        health = agent.get_mcp_health_status()
        print(f"📊 MCP Status: {health}")

        # List current directory
        print("\n2. Listing current directory...")
        files = await agent.list_directory(".")
        print(f"📁 Found {len(files)} items:")
        for file in files[:10]:  # Show first 10 items
            print(f"   - {file}")
        if len(files) > 10:
            print(f"   ... and {len(files) - 10} more")

        # Read a specific file (if it exists)
        print("\n3. Reading a file...")
        try:
            if await agent.workspace_file_exists("README.md"):
                content = await agent.read_file("README.md")
                print(f"📄 README.md ({len(content)} characters):")
                print(f"   First 200 chars: {content[:200]}...")
            else:
                print("   README.md not found, creating example file...")
                await agent.write_file(
                    "example.txt", "Hello from MCP!\nThis is a test file."
                )
                print("✅ Created example.txt")
        except FileOperationError as e:
            print(f"❌ File operation failed: {e}")

        # Search for Python files
        print("\n4. Searching for Python files...")
        try:
            py_files = await agent.search_files("*.py", ".")
            print(f"🐍 Found {len(py_files)} Python files:")
            for py_file in py_files[:5]:  # Show first 5
                print(f"   - {py_file}")
            if len(py_files) > 5:
                print(f"   ... and {len(py_files) - 5} more")
        except FileOperationError as e:
            print(f"❌ Search failed: {e}")

        # Create a directory
        print("\n5. Creating a test directory...")
        try:
            await agent.create_directory("test_mcp_dir")
            print("✅ Created test_mcp_dir/")

            # Write a file in the new directory
            test_content = """# Test File
This file was created by the MCP example.

## Features
- File operations through MCP
- Secure path validation
- Error handling
"""
            await agent.write_file("test_mcp_dir/test_file.md", test_content)
            print("✅ Created test_mcp_dir/test_file.md")

        except FileOperationError as e:
            print(f"❌ Directory/file creation failed: {e}")

        # Get file information
        print("\n6. Getting file information...")
        try:
            if await agent.workspace_file_exists("test_mcp_dir/test_file.md"):
                info = await agent.get_file_info("test_mcp_dir/test_file.md")
                print("📋 File info:")
                for key, value in info.items():
                    print(f"   {key}: {value}")
        except FileOperationError as e:
            print(f"❌ Get file info failed: {e}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    finally:
        # Disconnect MCP server
        print("\n7. Disconnecting from MCP server...")
        await agent.disconnect_mcp()
        print("✅ Disconnected from MCP server")


async def demonstrate_ai_with_mcp(agent: AIAgent):
    """Demonstrate AI Agent using MCP tools."""

    print("\n" + "=" * 50)
    print("DEMONSTRATING AI + MCP INTEGRATION")
    print("=" * 50)

    try:
        # Connect to MCP
        await agent.connect_mcp()

        # Use AI with filesystem tools
        print("\n1. Asking AI to analyze project structure...")

        response = await agent.send_message_with_tools(
            "Please analyze the current project structure. "
            "List the main directories and files, and provide a brief overview "
            "of what this project appears to be.",
            enable_filesystem=True,
        )

        if response.success:
            print(f"🤖 AI Response ({response.tokens_used} tokens):")
            print(f"   {response.content}")
        else:
            print(f"❌ AI request failed: {response.error}")

        # Ask AI to read and summarize a specific file
        print("\n2. Asking AI to read and summarize a file...")

        response = await agent.send_message_with_tools(
            "Please read the pyproject.toml file and summarize the project configuration, "
            "including dependencies and project metadata.",
            enable_filesystem=True,
        )

        if response.success:
            print(f"🤖 AI Response ({response.tokens_used} tokens):")
            print(f"   {response.content}")
        else:
            print(f"❌ AI request failed: {response.error}")

        # Use context manager for operations
        print("\n3. Using MCP context manager...")
        async with agent.mcp_context():
            # Batch file operations
            files_to_check = ["pyproject.toml", "README.md", "requirements.txt"]
            results = await agent.read_multiple_files(files_to_check)

            found_files = [
                f for f, content in results.items() if not content.startswith("Error")
            ]
            print(f"📚 Successfully read {len(found_files)} files:")
            for file in found_files:
                content_length = len(results[file])
                print(f"   - {file}: {content_length} characters")

    except Exception as e:
        print(f"❌ AI + MCP demonstration failed: {e}")

    finally:
        await agent.disconnect_mcp()


async def demonstrate_error_handling(agent: AIAgent):
    """Demonstrate error handling with MCP operations."""

    print("\n" + "=" * 50)
    print("DEMONSTRATING ERROR HANDLING")
    print("=" * 50)

    await agent.connect_mcp()

    # Test reading non-existent file
    print("\n1. Testing non-existent file...")
    try:
        content = await agent.read_file("non_existent_file.txt")
        print(f"Unexpected success: {content}")
    except FileOperationError as e:
        print(f"✅ Expected error caught: {e}")

    # Test writing file with invalid extension (if restrictions enabled)
    print("\n2. Testing file validation...")
    try:
        # This should work with current config
        await agent.write_file("test.txt", "Test content")
        print("✅ Valid file operation succeeded")

        # Clean up
        if agent.workspace_file_exists("test.txt"):
            os.remove("test.txt")
    except FileOperationError as e:
        print(f"File validation error: {e}")

    # Test reading from outside workspace (security check)
    print("\n3. Testing security boundaries...")
    try:
        content = await agent.read_file("../../../etc/passwd")  # Should fail
        print(f"⚠️  Security issue: read succeeded: {content[:50]}...")
    except FileOperationError as e:
        print(f"✅ Security check passed: {e}")

    await agent.disconnect_mcp()


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["ENDPOINT", "API_KEY", "MODEL"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print("Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set these variables in your .env file or environment:")
        print("  ENDPOINT=https://your-azure-openai-endpoint.openai.azure.com/")
        print("  API_KEY=your-api-key-here")
        print("  MODEL=your-deployment-name")
        return False

    return True


async def main():
    """Main example function."""

    print("MCP (Model Context Protocol) Usage Example")
    print("=" * 50)

    # Check environment
    if not check_environment():
        return

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Set up MCP and AI Agent
    agent, mcp_config = await setup_mcp_example()
    if not agent:
        return

    try:
        # Run demonstrations
        await demonstrate_mcp_operations(agent)
        await demonstrate_ai_with_mcp(agent)
        await demonstrate_error_handling(agent)

        print("\n" + "=" * 50)
        print("🎉 MCP Example completed successfully!")
        print("=" * 50)

        # Show final status
        health = agent.check_workspace_health()
        print(f"📊 Final workspace health: {health}")

    except KeyboardInterrupt:
        print("\n⚠️  Example interrupted by user")
    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
