#!/usr/bin/env python3
"""Test the simple chatbot functionality with streaming accumulation."""

import os
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

# Add the libs to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs', 'code_viewer', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs', 'agent_arch', 'src'))

from code_viewer.core.main_window import MainWindow


def test_simple_chatbot():
    """Test the simple chatbot with streaming accumulation."""
    print("🤖 Testing simple chatbot with streaming...")

    app = QApplication(sys.argv)

    # Use current directory as the directory path
    current_dir = os.getcwd()
    main_window = MainWindow(directory_path=current_dir)
    main_window.show()

    # Wait for initialization, then send a test message
    QTimer.singleShot(1000, lambda: send_test_message(main_window))

    # Close after some time to see the streaming in action
    QTimer.singleShot(10000, app.quit)

    return app.exec()

def send_test_message(main_window):
    """Send a test message to verify streaming works."""
    try:
        chat_widget = main_window._chat_widget

        # Check agent bridge status
        if hasattr(main_window, '_agent_bridge') and main_window._agent_bridge:
            bridge = main_window._agent_bridge
            print(f"🔗 Agent bridge connected: {bridge.is_connected}")
            print(f"🤖 Agent available: {bridge.agent_available}")

        # Add a user message manually to the chat
        user_msg_id = chat_widget.add_user_message("Hi! Tell me a very short joke.")
        print(f"📝 User message added: {user_msg_id}")

        # Trigger the message handling manually
        if hasattr(main_window, '_handle_chat_message'):
            main_window._handle_chat_message("Hi! Tell me a very short joke.")
            print("🚀 Message sent to agent for processing")
            print("👀 Watch the GUI to see streaming chunks accumulate!")
        else:
            print("❌ Could not find _handle_chat_message method")

    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    exit_code = test_simple_chatbot()
    sys.exit(exit_code)
