#!/usr/bin/env python3
"""
Test script for message height consistency.
This script specifically tests the issue where message boxes were initially too large
and then became too small after subsequent messages.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from my_coding_agent.gui.chat_widget import ChatWidget


def test_height_consistency():
    """Test message height consistency behavior."""
    app = QApplication(sys.argv)

    # Create a window with chat widget
    window = QMainWindow()
    window.setWindowTitle("Message Height Consistency Test")
    window.setGeometry(100, 100, 800, 600)

    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    # Create chat widget
    chat_widget = ChatWidget()
    layout.addWidget(chat_widget)

    # Test the specific scenario: user message followed by AI response
    chat_widget.add_system_message("Testing height consistency issue")

    def add_messages_sequence():
        # Add user message (this should have consistent height)
        print("Adding user message...")
        chat_widget.add_user_message("Hello, can you help me?")

        # Add AI response after a short delay (this should also have consistent height)
        QTimer.singleShot(1000, lambda: add_ai_response())

    def add_ai_response():
        print("Adding AI response...")
        chat_widget.add_assistant_message("Hello! How can I assist you today?")

        # Add another exchange to test consistency
        QTimer.singleShot(1000, lambda: add_second_exchange())

    def add_second_exchange():
        print("Adding second exchange...")
        chat_widget.add_user_message("I need help with my code.")
        QTimer.singleShot(
            500,
            lambda: chat_widget.add_assistant_message(
                "I'd be happy to help you with your code! Please share the code you're working on and describe the issue you're facing."
            ),
        )

    # Start the message sequence after window is shown
    QTimer.singleShot(500, add_messages_sequence)

    window.show()

    print("Height consistency test started.")
    print("Watch the message bubbles as they appear:")
    print("1. User message should have appropriate height")
    print("2. AI response should have consistent height (not too large, not too small)")
    print("3. Subsequent messages should maintain consistent sizing")

    sys.exit(app.exec())


if __name__ == "__main__":
    test_height_consistency()
