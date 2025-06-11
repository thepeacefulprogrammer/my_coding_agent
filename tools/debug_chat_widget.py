#!/usr/bin/env python3
"""Debug script to test the chat widget functionality."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from my_coding_agent.gui.chat_widget_v2 import SimplifiedChatWidget


class DebugWindow(QMainWindow):
    """Debug window to test chat widget."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Widget Debug")
        self.setGeometry(100, 100, 600, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create chat widget
        self.chat_widget = SimplifiedChatWidget()
        layout.addWidget(self.chat_widget)

        # Test some messages
        self.add_test_messages()

        # Print widget info
        self.print_widget_info()

    def add_test_messages(self):
        """Add test messages to see styling."""
        print("Adding test messages...")

        # Add user message
        user_id = self.chat_widget.add_user_message(
            "Hello! This is a user message to test styling."
        )
        print(f"Added user message: {user_id}")

        # Add AI message
        ai_id = self.chat_widget.add_assistant_message(
            "Hello! This is an AI response message to test styling and see the difference."
        )
        print(f"Added AI message: {ai_id}")

        # Add system message
        sys_id = self.chat_widget.add_system_message(
            "This is a system message for testing."
        )
        print(f"Added system message: {sys_id}")

    def print_widget_info(self):
        """Print information about the widget structure."""
        print("\n=== Widget Debug Info ===")
        print(f"Chat widget type: {type(self.chat_widget)}")
        print(f"Input text type: {type(self.chat_widget.input_text)}")
        print(f"Send button size: {self.chat_widget.send_button.size()}")
        print(f"Send button fixed size: {self.chat_widget.send_button.maximumSize()}")

        # Check message bubbles
        bubbles = self.chat_widget.display_area._message_bubbles
        print(f"Number of message bubbles: {len(bubbles)}")

        for msg_id, bubble in bubbles.items():
            print(
                f"Bubble {msg_id}: role={bubble.role}, style_length={len(bubble.styleSheet())}"
            )
            style = bubble.styleSheet()
            if len(style) > 0:
                print(f"  Style preview: {style[:100]}...")
            else:
                print("  No style applied!")


def main():
    """Run the debug application."""
    app = QApplication(sys.argv)

    window = DebugWindow()
    window.show()

    print("Debug window opened. Check the chat widget...")
    print("Press Ctrl+C to exit")

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
