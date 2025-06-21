#!/usr/bin/env python3
"""
Debug test to see what's happening in the GUI chat.
"""

import sys
from pathlib import Path

# Add the source directories to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "code_viewer" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "agent_arch" / "src"))

from code_viewer.core.main_window import MainWindow
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication


def test_debug_gui_chat():
    """Debug GUI chat functionality."""
    print("🔍 Debugging GUI chat functionality...")

    app = QApplication(sys.argv)

    # Create main window
    workspace_path = Path(__file__).parent.parent
    main_window = MainWindow(str(workspace_path))
    main_window.show()

    # Wait for initialization, then debug
    QTimer.singleShot(3000, lambda: debug_chat_state(main_window))

    # Send a test message after initialization
    QTimer.singleShot(5000, lambda: send_debug_message(main_window))

    # Exit after testing
    QTimer.singleShot(15000, app.quit)

    print("🎬 Starting application...")
    return app.exec()


def debug_chat_state(main_window):
    """Debug the chat state and connections."""
    print("\n🔍 Debugging chat state...")

    # Check main window components
    print(f"📱 Main window: {main_window}")
    print(f"💬 Chat widget: {main_window.chat_widget}")

    # Check agent bridge
    if hasattr(main_window, "_agent_bridge"):
        bridge = main_window._agent_bridge
        print(f"🔗 Agent bridge: {bridge}")
        if bridge:
            print(f"   - Connected: {bridge.is_connected}")
            print(f"   - Available: {bridge.agent_available}")
            print(f"   - Status: {bridge.status}")
        else:
            print("   - Bridge is None")
    else:
        print("❌ No _agent_bridge attribute found")

    # Check chat widget methods
    chat_widget = main_window.chat_widget
    if chat_widget:
        print("🔧 Chat widget methods:")
        print(
            f"   - has send_streaming_query_to_agent: {hasattr(chat_widget, 'send_streaming_query_to_agent')}"
        )
        print(
            f"   - has send_query_to_agent: {hasattr(chat_widget, 'send_query_to_agent')}"
        )
        print(f"   - has _agent_bridge: {hasattr(chat_widget, '_agent_bridge')}")

        if hasattr(chat_widget, "_agent_bridge"):
            widget_bridge = chat_widget._agent_bridge
            print(f"   - widget bridge: {widget_bridge}")
            if widget_bridge:
                print(f"     - bridge connected: {widget_bridge.is_connected}")

    # Check signal connections
    print("🔗 Signal connections:")
    print(f"   - message_sent signal: {hasattr(chat_widget, 'message_sent')}")

    # Check main window handler method
    print("🎯 Main window handlers:")
    print(
        f"   - has _handle_chat_message: {hasattr(main_window, '_handle_chat_message')}"
    )
    print(
        f"   - has _handle_agent_message: {hasattr(main_window, '_handle_agent_message')}"
    )
    print(
        f"   - has _process_agent_message: {hasattr(main_window, '_process_agent_message')}"
    )


def send_debug_message(main_window):
    """Send a debug message and trace the flow."""
    print("\n📨 Sending debug message...")

    chat_widget = main_window.chat_widget
    if not chat_widget:
        print("❌ No chat widget available")
        return

    # Add some debug hooks
    original_handle_chat = getattr(main_window, "_handle_chat_message", None)
    original_handle_agent = getattr(main_window, "_handle_agent_message", None)
    original_process_agent = getattr(main_window, "_process_agent_message", None)

    def debug_handle_chat(message):
        print(f"🎯 _handle_chat_message called with: '{message}'")
        if original_handle_chat:
            return original_handle_chat(message)

    def debug_handle_agent(message):
        print(f"🤖 _handle_agent_message called with: '{message}'")
        if original_handle_agent:
            return original_handle_agent(message)

    async def debug_process_agent(message):
        print(f"⚙️ _process_agent_message called with: '{message}'")
        if original_process_agent:
            return await original_process_agent(message)

    # Patch methods for debugging
    if original_handle_chat:
        main_window._handle_chat_message = debug_handle_chat
    if original_handle_agent:
        main_window._handle_agent_message = debug_handle_agent
    if original_process_agent:
        main_window._process_agent_message = debug_process_agent

    # Send test message
    test_message = "Hello, this is a debug test message"
    print(f"💬 Sending message: '{test_message}'")

    # Simulate user input
    chat_widget.input_text.setText(test_message)
    chat_widget.send_message()

    print("✅ Message sent - watching for debug output...")


if __name__ == "__main__":
    exit_code = test_debug_gui_chat()
    sys.exit(exit_code)
