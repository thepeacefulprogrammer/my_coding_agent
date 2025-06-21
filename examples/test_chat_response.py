#!/usr/bin/env python3
"""
Test Chat Response Integration

This script tests that chat responses are properly displayed in the GUI.
"""

import asyncio
import os
import sys

# Add the libs to the path
sys.path.insert(0, os.path.join(os.getcwd(), "libs", "agent_arch", "src"))
sys.path.insert(0, os.path.join(os.getcwd(), "libs", "code_viewer", "src"))

from code_viewer.core.main_window import MainWindow
from PyQt6.QtWidgets import QApplication


async def test_chat_response():
    """Test that chat responses work correctly."""
    print("🤖 Testing Chat Response Integration")
    print("=" * 50)

    # Create QApplication
    app = QApplication(sys.argv)

    # Create main window
    workspace_path = "/home/randy/workspace/personal/my_coding_agent"
    main_window = MainWindow(workspace_path)

    print("✅ Main window created")

    # Wait for agent initialization
    await asyncio.sleep(3)

    # Check if agent is connected
    if hasattr(main_window, "_agent_bridge") and main_window._agent_bridge:
        print(f"✅ Agent bridge available: {main_window._agent_bridge.is_connected}")
    else:
        print("❌ No agent bridge available")
        return False

    # Test sending a message through the chat widget
    test_message = "Hello, are you there?"
    print(f"📝 Testing message: '{test_message}'")

    try:
        # Get the chat widget
        chat_widget = main_window._chat_widget
        if not chat_widget:
            print("❌ No chat widget available")
            return False

        # Add a user message first
        user_msg_id = chat_widget.add_user_message(test_message)
        print(f"✅ User message added: {user_msg_id}")

        # Send the message to the agent through the chat widget
        if hasattr(chat_widget, "send_query_to_agent"):
            response_msg_id = await chat_widget.send_query_to_agent(test_message)
            print(f"✅ Agent query sent, response ID: {response_msg_id}")
        else:
            print("❌ Chat widget doesn't have send_query_to_agent method")
            return False

        # Wait a moment for the response
        await asyncio.sleep(2)

        # Check if there are messages in the chat widget
        messages = chat_widget.message_model.get_all_messages()
        print(f"📊 Total messages in chat: {len(messages)}")

        # Look for agent responses
        agent_messages = [msg for msg in messages if msg.role.value == "agent"]
        if agent_messages:
            print("✅ Agent response found!")
            latest_response = agent_messages[-1]
            print(f"   Response: {latest_response.content[:100]}...")
            return True
        else:
            print("❌ No agent response found")
            # Print all messages for debugging
            for i, msg in enumerate(messages):
                print(f"   Message {i}: {msg.role.value} - {msg.content[:50]}...")
            return False

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_chat_response())
    print(f"\n🎉 Test {'PASSED' if result else 'FAILED'}")
    sys.exit(0 if result else 1)
