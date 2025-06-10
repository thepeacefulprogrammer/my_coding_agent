#!/usr/bin/env python3
"""
Manual test script for message display to verify text truncation fix.
This script creates a chat widget and tests long messages to ensure full text is visible.

NOTE: This is a MANUAL test script - run it separately, not as part of automated test suite.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from my_coding_agent.gui.chat_widget import ChatWidget


def test_message_display():
    """Test message display with various text lengths."""
    app = QApplication(sys.argv)

    # Create a window with chat widget
    window = QMainWindow()
    window.setWindowTitle("Message Display Test")
    window.setGeometry(100, 100, 800, 600)

    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    # Create chat widget
    chat_widget = ChatWidget()
    layout.addWidget(chat_widget)

    # Test various message lengths
    chat_widget.add_system_message("Testing message display with various lengths")

    # Short message
    chat_widget.add_user_message("Hello!")
    chat_widget.add_assistant_message("Hi there!")

    # Medium message (this is the one that was being cut off)
    chat_widget.add_user_message("Can you help me with something?")
    chat_widget.add_assistant_message("Hello! How can I assist you today?")

    # Longer message
    chat_widget.add_user_message(
        "I need help with a more complex problem that requires a detailed explanation."
    )
    chat_widget.add_assistant_message(
        "Of course! I'd be happy to help you with complex problems. "
        "Please provide more details about what you're working on, and I'll do my best to give you a comprehensive solution. "
        "Whether it's coding, problem-solving, or anything else, I'm here to assist."
    )

    # Very long message
    chat_widget.add_user_message(
        "This is a very long message to test text wrapping and ensure that all content is visible even when the message spans multiple lines and contains quite a bit of text that should wrap properly within the message bubble."
    )
    chat_widget.add_assistant_message(
        "This is a comprehensive response that should demonstrate proper text wrapping and display behavior. "
        "The message bubble should expand to accommodate all of this text without cutting off any content. "
        "Each line should be properly visible, and the user should be able to read the entire message from start to finish. "
        "This includes ensuring that word wrapping works correctly and that the message bubble resizes appropriately to fit all content. "
        "The text should be fully readable without any truncation issues."
    )

    window.show()

    print("Message display test window created.")
    print("Check that all messages are fully visible without truncation.")
    print(
        "Especially verify that 'Hello! How can I assist you today?' is completely visible."
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    test_message_display()
