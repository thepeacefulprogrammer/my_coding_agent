#!/usr/bin/env python3
"""
Test script to verify MCP tools work with context manager approach.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
from my_coding_agent.core.mcp_file_server import MCPFileConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mcp_context_manager():
    """Test that MCP tools work with context manager approach."""
    try:
        logger.info("Starting MCP context manager test...")

        # Load configuration
        config = AIAgentConfig.from_env()

        # Create MCP file server configuration
        mcp_config = MCPFileConfig(
            base_directory=str(Path(__file__).parent.parent),
            allowed_extensions=[".py", ".md", ".txt", ".json", ".yaml", ".yml"],
            max_file_size=10 * 1024 * 1024,  # 10MB
            enable_write_operations=True,
            enable_directory_operations=True,
        )

        # Record start time
        start_time = time.time()

        # Create AI agent with MCP tools enabled
        logger.info("Creating AI agent with MCP tools enabled...")
        agent = AIAgent(
            config=config,
            mcp_config=mcp_config,
            enable_mcp_tools=True,
            auto_discover_mcp_servers=True,
        )

        # Record initialization time
        init_time = time.time() - start_time
        logger.info(f"AI Agent initialization completed in {init_time:.2f} seconds")

        # Test MCP tool calls
        if agent.mcp_registry:
            server_statuses = agent.mcp_registry.get_all_server_statuses()
            connected_count = sum(
                1 for status in server_statuses.values() if status.connected
            )

            logger.info(
                f"MCP Server Status: {connected_count}/{len(server_statuses)} connected"
            )

            if connected_count > 0:
                # Test a simple tool call
                logger.info("Testing MCP tool call...")

                # Try to call a test_connection tool
                try:
                    # Get the first connected server
                    connected_server = None
                    for server_name, status in server_statuses.items():
                        if status.connected:
                            connected_server = server_name
                            break

                    if connected_server:
                        client = agent.mcp_registry.get_client(connected_server)
                        if client:
                            # Try to list tools first
                            tools = await client.list_tools()
                            logger.info(
                                f"Successfully listed {len(tools)} tools from {connected_server}"
                            )

                            # Try to call a tool if available
                            if tools:
                                tool_name = tools[0].name
                                logger.info(f"Testing tool call: {tool_name}")

                                # Call the tool with empty arguments
                                result = await client.call_tool(tool_name, {})
                                logger.info(f"Tool call successful: {result}")

                                logger.info(
                                    "✅ SUCCESS: MCP tools working with context manager!"
                                )
                                return True
                            else:
                                logger.warning("No tools available to test")
                                return False
                        else:
                            logger.error("Could not get client for connected server")
                            return False
                    else:
                        logger.error("No connected servers found")
                        return False

                except Exception as e:
                    logger.error(f"Tool call failed: {e}")
                    return False
            else:
                logger.error("❌ FAILURE: No MCP servers connected")
                return False
        else:
            logger.error("❌ FAILURE: No MCP registry available")
            return False

    except Exception as e:
        logger.error(f"❌ FAILURE: Error during test: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mcp_context_manager())
    sys.exit(0 if success else 1)
