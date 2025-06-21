#!/usr/bin/env python3
"""
Test Agent Integration

This script tests the connection between the code viewer and the agent architecture.
It demonstrates how to set up the agent bridge and send queries to the orchestrator.
"""

import asyncio
import sys
from pathlib import Path

# Add the code_viewer library to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "code_viewer" / "src"))

from code_viewer.core.agent_integration import AgentBridge, AgentIntegrationError


async def test_agent_connection():
    """Test the agent bridge connection."""
    print("🤖 Testing Agent Architecture Integration")
    print("=" * 50)

    # Current workspace directory
    workspace_path = Path(__file__).parent.parent
    print(f"Workspace: {workspace_path}")

    # Create agent bridge
    try:
        agent_bridge = AgentBridge(
            workspace_path=workspace_path,
            config={"agent_timeout": 30, "retry_attempts": 3, "enable_streaming": True},
        )
        print("✅ Agent bridge created successfully")
    except Exception as e:
        print(f"❌ Failed to create agent bridge: {e}")
        return False

    # Test connection
    try:
        await agent_bridge.initialize_connection()
        print("✅ Agent connection initialized successfully")
        print(f"   Status: {agent_bridge.status}")
        print(f"   Connected: {agent_bridge.is_connected}")
        print(f"   Agent Available: {agent_bridge.agent_available}")
    except AgentIntegrationError as e:
        print(f"❌ Failed to initialize agent connection: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during connection: {e}")
        return False

    # Test query processing
    test_queries = [
        "Hello, can you help me analyze some code?",
        "What can you do for me?",
        "Analyze the structure of this project",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test Query {i}: {query}")
        try:
            response = await agent_bridge.process_query(query)
            print("✅ Response received:")
            print(f"   Type: {type(response)}")

            # Handle different response formats
            if hasattr(response, "response"):
                print(f"   Content: {response.response[:100]}...")
            elif hasattr(response, "content"):
                print(f"   Content: {response.content[:100]}...")
            elif isinstance(response, dict):
                content = response.get("content", str(response))
                print(f"   Content: {content[:100]}...")
            else:
                print(f"   Content: {str(response)[:100]}...")

        except AgentIntegrationError as e:
            print(f"❌ Agent integration error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

    # Cleanup
    try:
        await agent_bridge.cleanup_connection()
        print("\n✅ Agent connection cleaned up successfully")
    except Exception as e:
        print(f"⚠️ Warning during cleanup: {e}")

    return True


async def main():
    """Main test function."""
    print("Starting Agent Architecture Integration Test")
    print("This will test the connection between code_viewer and agent_arch libraries")
    print()

    success = await test_agent_connection()

    if success:
        print("\n🎉 Agent integration test completed successfully!")
        print(
            "The chat widget should now be able to communicate with the agent architecture."
        )
    else:
        print("\n💥 Agent integration test failed!")
        print("Please check that the agent_arch library is properly installed.")

    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
