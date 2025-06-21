#!/usr/bin/env python3
"""
Simple test to verify signal connections work properly.
"""

import sys
from pathlib import Path

# Add the source directories to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "code_viewer" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "agent_arch" / "src"))

from code_viewer.core.main_window import MainWindow
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication


def test_simple_signal():
    """Test signal connections."""
    print("🧪 Testing signal connections...")

    app = QApplication(sys.argv)

    # Create main window but don't show it
    workspace_path = Path(__file__).parent.parent
    main_window = MainWindow(str(workspace_path))

    # Give it time to initialize
    QTimer.singleShot(2000, lambda: check_connections(main_window, app))

    print("🎬 Starting app...")
    return app.exec()


def check_connections(main_window, app):
    """Check the connections."""
    print("\n🔍 Checking connections...")

    # Check main window components
    chat_widget = main_window.chat_widget
    print(f"💬 Chat widget: {chat_widget is not None}")

    # Check agent bridge
    if hasattr(main_window, '_agent_bridge'):
        bridge = main_window._agent_bridge
        print(f"🌉 Agent bridge exists: {bridge is not None}")
        if bridge:
            print(f"   - Connected: {bridge.is_connected}")
            print(f"   - Available: {bridge.agent_available}")
            print(f"   - Status: {bridge.status}")
    else:
        print("❌ No _agent_bridge attribute")

    # Check chat widget agent bridge
    if chat_widget and hasattr(chat_widget, '_agent_bridge'):
        widget_bridge = chat_widget._agent_bridge
        print(f"💬 Chat widget has bridge: {widget_bridge is not None}")
        if widget_bridge:
            print(f"   - Same as main bridge: {widget_bridge is main_window._agent_bridge}")
            print(f"   - Connected: {widget_bridge.is_connected}")

    # Check streaming methods
    if chat_widget:
        has_streaming = hasattr(chat_widget, 'send_streaming_query_to_agent')
        has_regular = hasattr(chat_widget, 'send_query_to_agent')
        print("🔧 Chat widget methods:")
        print(f"   - send_streaming_query_to_agent: {has_streaming}")
        print(f"   - send_query_to_agent: {has_regular}")

    # Test signal emission
    print("\n📡 Testing signal emission...")
    test_message = "Test signal message"

    # Add a simple signal handler to verify it works
    def signal_received(message):
        print(f"✅ Signal received: '{message}'")
        app.quit()

    if chat_widget and hasattr(chat_widget, 'message_sent'):
        chat_widget.message_sent.connect(signal_received)
        print(f"🎯 Emitting signal with: '{test_message}'")
        chat_widget.message_sent.emit(test_message)
    else:
        print("❌ No message_sent signal found")
        app.quit()


if __name__ == "__main__":
    exit_code = test_simple_signal()
    print(f"🏁 Test completed with exit code: {exit_code}")
    sys.exit(exit_code)
