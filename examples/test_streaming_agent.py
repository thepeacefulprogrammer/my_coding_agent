#!/usr/bin/env python3
"""
Test script to verify streaming agent functionality without GUI.
"""

import asyncio
import sys
from pathlib import Path

# Add the source directories to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "code_viewer" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "agent_arch" / "src"))

from code_viewer.core.agent_integration.agent_bridge import AgentBridge


async def test_streaming_agent():
    """Test streaming agent functionality."""
    print("🧪 Testing streaming agent functionality...")

    # Initialize agent bridge
    workspace_path = Path(__file__).parent.parent
    agent_bridge = AgentBridge(workspace_path)

    try:
        # Connect to agent
        print("🔗 Connecting to agent...")
        await agent_bridge.initialize_connection()

        print(f"✅ Agent connected: {agent_bridge.is_connected}")
        print(f"🤖 Agent available: {agent_bridge.agent_available}")
        print(f"📊 Status: {agent_bridge.status}")

        if not agent_bridge.is_connected:
            print("❌ Agent connection failed")
            return

        # Test streaming query
        query = "Tell me a very short story about a robot learning to code"
        print(f"\n💬 Testing streaming query: '{query}'")

        # Collect streaming chunks
        chunks = []

        def chunk_callback(chunk: str):
            """Callback to collect streaming chunks."""
            print(f"📦 Received chunk: '{chunk.strip()}'")
            chunks.append(chunk)

        # Send streaming query
        print("🌊 Starting streaming query...")
        await agent_bridge.process_streaming_query(query, chunk_callback)

        # Show results
        print("\n✅ Streaming completed!")
        print(f"📊 Total chunks received: {len(chunks)}")
        full_response = "".join(chunks).strip()
        print(f"📝 Full response: '{full_response}'")

        # Test regular query for comparison
        print("\n🔄 Testing regular query for comparison...")
        response = await agent_bridge.process_query(query)
        content = response.response if hasattr(response, "response") else str(response)
        print(f"📝 Regular response: '{content}'")

    except Exception as e:
        print(f"❌ Error during streaming test: {e}")
    finally:
        # Cleanup
        await agent_bridge.cleanup_connection()
        print("🧹 Agent connection cleaned up")


if __name__ == "__main__":
    asyncio.run(test_streaming_agent())
