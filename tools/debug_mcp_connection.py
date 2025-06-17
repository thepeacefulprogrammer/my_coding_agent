#!/usr/bin/env python3
"""Debug script for MCP connection issues."""

import asyncio
import logging
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
from my_coding_agent.core.mcp_file_server import MCPFileConfig

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_mcp_connections():
    """Test MCP server connections with detailed logging."""
    logger.info("🔍 Starting MCP connection debug...")

    try:
        # Initialize AI agent with MCP support
        config = AIAgentConfig.from_env()

        # Set up MCP configuration for filesystem tools
        from pathlib import Path

        workspace_path = Path.cwd()
        mcp_config = MCPFileConfig(
            base_directory=workspace_path,
            allowed_extensions=[".py", ".md", ".txt"],
            enable_write_operations=True,
            enable_delete_operations=False,
            max_file_size=5 * 1024 * 1024,
        )

        # Create agent with MCP tools enabled
        agent = AIAgent(
            config=config,
            mcp_config=mcp_config,
            enable_mcp_tools=True,
            auto_discover_mcp_servers=True,
        )

        logger.info("✅ AI Agent created successfully")

        # Get initial server status
        if agent.mcp_registry:
            server_statuses = agent.mcp_registry.get_all_server_statuses()
            logger.info(f"📊 Found {len(server_statuses)} servers:")
            for name, status in server_statuses.items():
                logger.info(
                    f"   - {name}: connected={status.connected}, attempts={status.connection_attempts}"
                )
                if status.last_error:
                    logger.error(f"     Last error: {status.last_error}")
        else:
            logger.error("❌ No MCP registry available")
            return

        # Try to connect explicitly
        logger.info("🔗 Attempting to connect to MCP servers...")
        connection_results = await agent.connect_mcp_servers()

        logger.info(f"📈 Connection results: {connection_results}")

        # Get updated server status
        server_statuses = agent.mcp_registry.get_all_server_statuses()
        logger.info("📊 Updated server status:")
        for name, status in server_statuses.items():
            logger.info(
                f"   - {name}: connected={status.connected}, attempts={status.connection_attempts}"
            )
            if status.last_error:
                logger.error(f"     Last error: {status.last_error}")

        # Test terminal-mcp-server specifically
        if "terminal-mcp-server" in server_statuses:
            terminal_status = server_statuses["terminal-mcp-server"]
            logger.info("🖥️  Terminal MCP Server Status:")
            logger.info(f"   Connected: {terminal_status.connected}")
            logger.info(f"   Attempts: {terminal_status.connection_attempts}")
            logger.info(f"   Transport: {terminal_status.transport_type}")
            if terminal_status.last_error:
                logger.error(f"   Error: {terminal_status.last_error}")

        # Try to get tools from terminal server
        if agent.mcp_registry:
            all_tools = agent.mcp_registry.get_all_tools()
            logger.info("🔧 Available tools by server:")
            for server_name, tools in all_tools.items():
                logger.info(f"   {server_name}: {len(tools)} tools")
                for tool in tools[:3]:  # Show first 3 tools
                    logger.info(f"     - {tool.name}: {tool.description}")

    except Exception as e:
        logger.error(f"❌ Error during MCP connection test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_connections())
