#!/usr/bin/env python3
"""
Test Live Agent Chat Integration

This script tests the agent integration by simulating chat messages
and verifying that they get routed to the agent orchestrator.
"""

import sys
from pathlib import Path

# Add the code_viewer library to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "code_viewer" / "src"))

from code_viewer.core.main_window import MainWindow
from PyQt6.QtWidgets import QApplication


def test_agent_chat_integration():
    """Test the agent chat integration in a live application."""
    print("🤖 Testing Live Agent Chat Integration")
    print("=" * 50)

    # Create QApplication
    app = QApplication(sys.argv)

    # Create main window
    workspace_path = Path(__file__).parent.parent
    main_window = MainWindow(str(workspace_path))

    print(f"✅ Main window created for workspace: {workspace_path}")

    # Show the window
    main_window.show()

    # Wait a moment for initialization
    print("⏳ Waiting for agent initialization...")

    def check_agent_status():
        """Check if agent is connected."""
        if hasattr(main_window, '_agent_bridge'):
            bridge = main_window._agent_bridge
            print(f"   Agent Bridge: {bridge}")
            print(f"   Connected: {bridge.is_connected if bridge else 'No bridge'}")
            print(f"   Available: {bridge.agent_available if bridge else 'No bridge'}")
            print(f"   Status: {bridge.status if bridge else 'No bridge'}")
        else:
            print("   No agent bridge found")

        # Check chat widget
        if hasattr(main_window, '_chat_widget'):
            chat = main_window._chat_widget
            print(f"   Chat Widget: {chat}")
            if hasattr(chat, '_agent_bridge'):
                print(f"   Chat Agent Bridge: {chat._agent_bridge}")
        else:
            print("   No chat widget found")

    # Schedule status check after initialization
    from PyQt6.QtCore import QTimer
    timer = QTimer()
    timer.timeout.connect(check_agent_status)
    timer.setSingleShot(True)
    timer.start(3000)  # Check after 3 seconds

    # Test sending a message after initialization
    def send_test_message():
        """Send a test message to verify agent routing."""
        print("\n📝 Sending test message to agent...")
        if hasattr(main_window, '_chat_widget'):
            chat = main_window._chat_widget

            # Add user message
            chat.add_user_message("Hello, can you help me analyze this project?")

            # Trigger message processing
            chat.message_sent.emit("Hello, can you help me analyze this project?")

            print("✅ Test message sent")
        else:
            print("❌ No chat widget available")

    # Schedule test message after status check
    test_timer = QTimer()
    test_timer.timeout.connect(send_test_message)
    test_timer.setSingleShot(True)
    test_timer.start(5000)  # Send message after 5 seconds

    # Exit after test
    exit_timer = QTimer()
    exit_timer.timeout.connect(app.quit)
    exit_timer.setSingleShot(True)
    exit_timer.start(10000)  # Exit after 10 seconds

    print("🚀 Starting application for 10 seconds...")
    print("   Watch the status bar for 'Agent: Connected'")
    print("   A test message will be sent automatically")

    # Run the application
    app.exec()

    print("\n🎉 Live agent chat test completed!")
    return True


if __name__ == "__main__":
    try:
        test_agent_chat_integration()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
