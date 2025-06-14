#!/usr/bin/env python3
"""
Debug script to test streaming integration and identify issues.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path before other imports (required for debug script)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig  # noqa: E402
from my_coding_agent.core.mcp_file_server import MCPFileConfig  # noqa: E402


async def test_streaming_functionality():
    """Test the streaming functionality with debug output."""
    print("🔍 Testing streaming integration...")

    try:
        # Create AI config
        config = AIAgentConfig.from_env()
        print(f"✅ AI Config created: {config.deployment_name}")

        # Create MCP config
        mcp_config = MCPFileConfig(
            base_directory=Path.cwd(),
            allowed_extensions=[".py", ".md", ".txt"],
            enable_write_operations=False,
            max_file_size=1024 * 1024,  # 1MB
        )
        print("✅ MCP Config created")

        # Create AI agent
        agent = AIAgent(
            config=config, mcp_config=mcp_config, enable_filesystem_tools=True
        )
        print("✅ AI Agent created")

        # Track streaming state
        chunks_received = []
        streaming_complete = False
        streaming_error = None

        def on_chunk(chunk: str, is_final: bool):
            """Handle streaming chunks."""
            print(f"📦 Chunk received: '{chunk}' (final: {is_final})")
            chunks_received.append((chunk, is_final))

            if is_final:
                nonlocal streaming_complete
                streaming_complete = True
                print("🏁 Streaming marked as complete!")

        def on_error(error: Exception):
            """Handle streaming errors."""
            nonlocal streaming_error
            streaming_error = error
            print(f"❌ Streaming error: {error}")

        # Test message
        test_message = "Hello! Please respond with a short greeting."
        print(f"💬 Sending message: '{test_message}'")

        # Start streaming
        response = await agent.send_message_with_tools_stream(
            message=test_message,
            on_chunk=on_chunk,
            on_error=on_error,
            enable_filesystem=False,  # Disable filesystem for simpler test
        )

        print(f"📋 Response received: success={response.success}")
        print(f"📋 Response content: '{response.content}'")
        print(f"📋 Stream ID: {response.stream_id}")
        print(f"📋 Retry count: {response.retry_count}")

        if response.error:
            print(f"❌ Response error: {response.error}")

        # Check streaming state
        print("\n📊 Streaming Results:")
        print(f"   - Chunks received: {len(chunks_received)}")
        print(f"   - Streaming complete: {streaming_complete}")
        print(f"   - Streaming error: {streaming_error}")

        if chunks_received:
            full_content = "".join(chunk for chunk, _ in chunks_received)
            print(f"   - Full content: '{full_content}'")

            # Check if we got final marker
            has_final = any(is_final for _, is_final in chunks_received)
            print(f"   - Has final marker: {has_final}")

        return response.success and streaming_complete

    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting streaming debug test...")
    success = asyncio.run(test_streaming_functionality())

    if success:
        print("✅ Streaming test PASSED!")
        sys.exit(0)
    else:
        print("❌ Streaming test FAILED!")
        sys.exit(1)
