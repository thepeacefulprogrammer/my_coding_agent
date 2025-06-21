#!/usr/bin/env python3
"""
Test script to verify streaming chat functionality with agent responses.
"""

import sys
from pathlib import Path

# Add the source directories to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "code_viewer" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "agent_arch" / "src"))

from code_viewer.core.main_window import MainWindow
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication


def test_streaming_chat():
    """Test streaming chat functionality."""
    print("🧪 Testing streaming chat functionality...")

    app = QApplication(sys.argv)

    # Create main window
    workspace_path = Path(__file__).parent.parent
    main_window = MainWindow(str(workspace_path))
    main_window.show()

    # Wait for initialization
    QTimer.singleShot(2000, lambda: test_streaming_message(main_window))

    # Set up exit timer
    QTimer.singleShot(15000, app.quit)

    print("🎬 Starting application...")
    return app.exec()


def test_streaming_message(main_window):
    """Test sending a streaming message."""
    print("📨 Testing streaming message...")

    chat_widget = main_window.chat_widget
    if not chat_widget:
        print("❌ No chat widget available")
        return

    # Check agent bridge connection
    if hasattr(main_window, "_agent_bridge") and main_window._agent_bridge:
        bridge = main_window._agent_bridge
        print(f"🔗 Agent bridge connected: {bridge.is_connected}")
        print(f"🤖 Agent available: {bridge.agent_available}")
        print(f"📊 Status: {bridge.status}")
    else:
        print("❌ No agent bridge found")
        return

    # Test streaming message
    test_message = "Can you tell me a short story about a robot learning to code?"
    print(f"💬 Sending streaming message: '{test_message}'")

    # Simulate user typing and sending message
    chat_widget.input_text.setText(test_message)
    chat_widget.send_message()

    print("✅ Streaming message sent - watch for chunked response!")


if __name__ == "__main__":
    exit_code = test_streaming_chat()
    sys.exit(exit_code)
