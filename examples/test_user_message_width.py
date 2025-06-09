#!/usr/bin/env python3
"""
Test script specifically for user message display width and text wrapping.
This verifies that user messages display properly with the same fix as AI messages.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from my_coding_agent.gui.chat_widget import ChatWidget


def test_user_message_width():
    """Test user message width and text wrapping."""
    app = QApplication(sys.argv)

    # Create a window with chat widget
    window = QMainWindow()
    window.setWindowTitle("User Message Width Test")
    window.setGeometry(100, 100, 800, 600)

    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    # Create chat widget
    chat_widget = ChatWidget()
    layout.addWidget(chat_widget)

    # Test user messages specifically
    chat_widget.add_system_message("Testing user message width and wrapping")

    def add_user_messages():
        # Short user message
        print("Adding short user message...")
        chat_widget.add_user_message("Hi")

        # Medium user message (the problematic case)
        print("Adding medium user message...")
        chat_widget.add_user_message("Hello, can you help me with something?")

        # Longer user message
        print("Adding long user message...")
        chat_widget.add_user_message(
            "I need help with a programming problem that requires detailed explanation and support."
        )

        # Very long user message to test wrapping
        print("Adding very long user message...")
        chat_widget.add_user_message(
            "This is a very long user message to test text wrapping and ensure that all content is visible "
            "even when the user message spans multiple lines and contains quite a bit of text that should wrap "
            "properly within the message bubble without being cut off or truncated."
        )

        # Add AI responses for comparison
        QTimer.singleShot(1000, add_ai_responses)

    def add_ai_responses():
        print("Adding AI responses for comparison...")
        chat_widget.add_assistant_message("Hello! How can I assist you today?")
        chat_widget.add_assistant_message(
            "I'd be happy to help you with your programming problem. Please provide more details about "
            "what you're working on, and I'll do my best to give you a comprehensive solution."
        )

    # Start adding messages after window is shown
    QTimer.singleShot(500, add_user_messages)

    window.show()

    print("User message width test started.")
    print(
        "Compare user messages (blue, right-aligned) with AI responses (gray, left-aligned)."
    )
    print("Check that:")
    print("1. User messages are not too narrow")
    print("2. User message text is not cut off")
    print("3. User messages wrap properly")
    print("4. User messages have similar width behavior to AI responses")

    sys.exit(app.exec())


if __name__ == "__main__":
    test_user_message_width()
