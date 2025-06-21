#!/usr/bin/env python3
"""
Test GUI Chat Functionality

This script tests the chat functionality in the actual GUI application.
"""

import asyncio
import os
import sys

# Add the libs to the path
sys.path.insert(0, os.path.join(os.getcwd(), 'libs', 'agent_arch', 'src'))
sys.path.insert(0, os.path.join(os.getcwd(), 'libs', 'code_viewer', 'src'))

from code_viewer.core.main_window import MainWindow
from PyQt6.QtWidgets import QApplication


class ChatTester:
    """Test the chat functionality in the GUI."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = None
        self.test_passed = False

    async def run_test(self):
        """Run the chat test."""
        print("🤖 Testing GUI Chat Functionality")
        print("=" * 50)

        # Create main window
        workspace_path = "/home/randy/workspace/personal/my_coding_agent"
        self.main_window = MainWindow(workspace_path)
        self.main_window.show()

        print("✅ Main window created and shown")

        # Wait for initialization
        await asyncio.sleep(3)

        # Check agent bridge
        if hasattr(self.main_window, '_agent_bridge') and self.main_window._agent_bridge:
            print(f"✅ Agent bridge: {self.main_window._agent_bridge.is_connected}")
        else:
            print("❌ No agent bridge")
            return False

        # Get chat widget
        chat_widget = self.main_window._chat_widget
        if not chat_widget:
            print("❌ No chat widget")
            return False

        print("✅ Chat widget available")

        # Test sending a message
        test_message = "Hello, can you help me?"
        print(f"📝 Sending test message: '{test_message}'")

        # Add user message
        user_msg_id = chat_widget.add_user_message(test_message)
        print(f"✅ User message added: {user_msg_id}")

        # Send to agent
        try:
            response_msg_id = await chat_widget.send_query_to_agent(test_message)
            print(f"✅ Agent response ID: {response_msg_id}")

            # Wait for response
            await asyncio.sleep(3)

            # Check messages
            messages = chat_widget.message_model.get_all_messages()
            print(f"📊 Total messages: {len(messages)}")

            # Find agent responses
            agent_responses = [msg for msg in messages if msg.role.value == 'agent']
            if agent_responses:
                print("✅ Agent response received!")
                latest = agent_responses[-1]
                print(f"   Response: {latest.content[:80]}...")
                self.test_passed = True
                return True
            else:
                print("❌ No agent response found")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def cleanup(self):
        """Clean up the test."""
        if self.main_window:
            self.main_window.close()
        self.app.quit()


async def main():
    """Main test function."""
    tester = ChatTester()

    try:
        success = await tester.run_test()

        if success:
            print("\n🎉 GUI Chat test PASSED!")
            print("The chat is working correctly in the application.")
        else:
            print("\n💥 GUI Chat test FAILED!")

        # Keep the window open for a few seconds to see the result
        await asyncio.sleep(2)

        return success

    except Exception as e:
        print(f"\n💥 Test error: {e}")
        return False
    finally:
        tester.cleanup()


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
        sys.exit(1)
