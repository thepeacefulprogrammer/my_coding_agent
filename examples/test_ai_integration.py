#!/usr/bin/env python3
"""
Test script for AI integration in the main window.
This script creates a main window and tests sending a message to verify AI integration.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from my_coding_agent.core.main_window import MainWindow


def test_ai_integration():
    """Test AI integration by creating a main window and sending a test message."""
    app = QApplication(sys.argv)

    # Create main window
    window = MainWindow()
    window.show()

    # Get the chat widget
    chat_widget = window.chat_widget

    # Add a welcome message to show chat is working
    chat_widget.add_system_message("AI Integration Test Started")

    # Simulate sending a message after a short delay
    def send_test_message():
        print("Sending test message...")
        chat_widget.add_user_message("Hello, can you help me?")

        # The message should trigger AI response if integration is working
        # You can manually type messages in the chat to test further

    # Send test message after 2 seconds
    QTimer.singleShot(2000, send_test_message)

    print("Main window created with AI integration.")
    print("Check the chat widget to see if AI responses work.")
    print("You can type messages in the chat to test AI integration.")

    sys.exit(app.exec())


if __name__ == "__main__":
    test_ai_integration()
