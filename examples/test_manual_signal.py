#!/usr/bin/env python3
"""
Test script to manually trigger the chat message signal and debug the flow.
"""

import sys
from pathlib import Path

# Add the source directories to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "code_viewer" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "agent_arch" / "src"))

from code_viewer.core.main_window import MainWindow
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication


def test_manual_signal():
    """Test manual signal triggering."""
    print("🔍 Testing manual signal triggering...")

    app = QApplication(sys.argv)

    # Create main window
    workspace_path = Path(__file__).parent.parent
    main_window = MainWindow(str(workspace_path))
    main_window.show()

    # Wait for initialization, then trigger signal manually
    QTimer.singleShot(3000, lambda: trigger_manual_signal(main_window))

    # Exit after testing
    QTimer.singleShot(10000, app.quit)

    print("🎬 Starting application...")
    return app.exec()


def trigger_manual_signal(main_window):
    """Manually trigger the chat message signal."""
    print("\n🎯 Manually triggering chat message signal...")

    # Check components
    chat_widget = main_window.chat_widget
    if not chat_widget:
        print("❌ No chat widget")
        return

    print(f"💬 Chat widget: {chat_widget}")
    print(f"🔗 Has message_sent signal: {hasattr(chat_widget, 'message_sent')}")

    # Check agent bridge
    if hasattr(main_window, '_agent_bridge'):
        bridge = main_window._agent_bridge
        print(f"🌉 Agent bridge: {bridge}")
        if bridge:
            print(f"   - Connected: {bridge.is_connected}")
            print(f"   - Available: {bridge.agent_available}")
        else:
            print("   - Bridge is None")

    # Check if chat widget has agent bridge
    if hasattr(chat_widget, '_agent_bridge'):
        widget_bridge = chat_widget._agent_bridge
        print(f"💬 Chat widget bridge: {widget_bridge}")
        if widget_bridge:
            print(f"   - Connected: {widget_bridge.is_connected}")

    # Manually trigger the signal
    test_message = "Manual test message"
    print(f"\n📡 Manually emitting message_sent signal with: '{test_message}'")

    try:
        # Emit the signal directly
        chat_widget.message_sent.emit(test_message)
        print("✅ Signal emitted successfully")
    except Exception as e:
        print(f"❌ Error emitting signal: {e}")

    # Also try calling the handler directly
    print("\n🎯 Directly calling _handle_chat_message...")
    try:
        main_window._handle_chat_message(test_message)
        print("✅ Handler called successfully")
    except Exception as e:
        print(f"❌ Error calling handler: {e}")


if __name__ == "__main__":
    exit_code = test_manual_signal()
    sys.exit(exit_code)
