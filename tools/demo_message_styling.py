#!/usr/bin/env python3
"""Demo script to show message styling changes."""

import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

# Add src to path
sys.path.insert(0, "../src")

from my_coding_agent.gui.chat_widget import ChatWidget


class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Message Styling Demo")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)

        # Create chat widget
        self.chat_widget = ChatWidget()
        layout.addWidget(self.chat_widget)

        # Apply dark theme
        self.chat_widget.apply_theme("dark")

        # Add demo messages
        self.add_demo_messages()

    def add_demo_messages(self):
        """Add demo messages to show styling."""
        # User messages - should have borders and be left-aligned
        self.chat_widget.add_user_message(
            "Hello! This is a user message that should have a border around it to distinguish it from AI messages."
        )

        # AI messages - should be transparent with natural flow
        self.chat_widget.add_assistant_message(
            "Hi there! This is an AI assistant message that should have a transparent background and natural text flow without any borders or visual barriers."
        )

        # User message
        self.chat_widget.add_user_message("Can you help me with my code?")

        # AI message
        self.chat_widget.add_assistant_message(
            "Of course! I'd be happy to help you with your code. What specific issue are you working on? Please share the code you're having trouble with and I'll take a look."
        )

        # System message
        self.chat_widget.add_system_message(
            "System: Connection established successfully."
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DemoWindow()
    window.show()
    sys.exit(app.exec())
