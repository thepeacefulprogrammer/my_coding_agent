#!/usr/bin/env python3
"""Demo script for the simplified chat widget."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from my_coding_agent.gui.chat_widget_v2 import SimplifiedChatWidget


class ChatDemo(QMainWindow):
    """Demo application for the simplified chat widget."""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_demo_data()

    def setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle("Simplified Chat Widget Demo")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create chat widget
        self.chat_widget = SimplifiedChatWidget()
        self.chat_widget.message_sent.connect(self.handle_user_message)
        layout.addWidget(self.chat_widget)

        # Add demo controls
        controls_layout = QHBoxLayout()

        add_user_btn = QPushButton("Add Demo User Message")
        add_user_btn.clicked.connect(self.add_demo_user_message)
        controls_layout.addWidget(add_user_btn)

        add_ai_btn = QPushButton("Add Demo AI Message")
        add_ai_btn.clicked.connect(self.add_demo_ai_message)
        controls_layout.addWidget(add_ai_btn)

        add_system_btn = QPushButton("Add Demo System Message")
        add_system_btn.clicked.connect(self.add_demo_system_message)
        controls_layout.addWidget(add_system_btn)

        clear_btn = QPushButton("Clear Chat")
        clear_btn.clicked.connect(self.chat_widget.clear_conversation)
        controls_layout.addWidget(clear_btn)

        toggle_theme_btn = QPushButton("Toggle Theme")
        toggle_theme_btn.clicked.connect(self.toggle_theme)
        controls_layout.addWidget(toggle_theme_btn)

        layout.addLayout(controls_layout)

        # Set dark theme by default
        self.current_theme = "dark"
        self.chat_widget.apply_theme(self.current_theme)

        # Apply dark theme to main window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QPushButton {
                background-color: #4285F4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A9BFF;
            }
            QPushButton:pressed {
                background-color: #2D5AA0;
            }
        """)

    def setup_demo_data(self):
        """Add some initial demo messages."""
        self.chat_widget.add_system_message(
            "Welcome to the simplified chat widget demo!"
        )
        self.chat_widget.add_user_message("Hello! This is a user message with borders.")
        self.chat_widget.add_assistant_message(
            "Hi there! This is an AI assistant message with no borders. "
            "It flows naturally across the full width and can contain "
            "much longer text to demonstrate the layout behavior."
        )
        self.chat_widget.add_user_message(
            "This is another user message to show the consistent styling."
        )

    def handle_user_message(self, message: str):
        """Handle user messages from the input field."""
        # Simulate AI response after a short delay
        QTimer.singleShot(1000, lambda: self.add_ai_response(message))

    def add_ai_response(self, user_message: str):
        """Add an AI response to the user message."""
        responses = [
            f"I understand you said: '{user_message}'. That's interesting!",
            "Thanks for your message! I'm a demo AI assistant.",
            "This is an example of how the chat widget handles responses.",
            f"Echo: {user_message}",
            "I'm just a demo, but your message is noted!",
        ]
        import random

        response = random.choice(responses)
        self.chat_widget.add_assistant_message(response)

    def add_demo_user_message(self):
        """Add a demo user message."""
        messages = [
            "This is a demo user message with a border.",
            "User messages are left-aligned with blue borders.",
            "They have a contained width for better readability.",
            "Perfect for questions and user input!",
        ]
        import random

        message = random.choice(messages)
        self.chat_widget.add_user_message(message)

    def add_demo_ai_message(self):
        """Add a demo AI message."""
        messages = [
            "This is a demo AI assistant message that flows naturally across the full width without borders.",
            "AI messages are transparent and blend with the background for a clean, conversational flow.",
            "They can contain longer explanations and detailed responses without visual barriers.",
            "The design emphasizes readability and natural conversation flow.",
        ]
        import random

        message = random.choice(messages)
        self.chat_widget.add_assistant_message(message)

    def add_demo_system_message(self):
        """Add a demo system message."""
        messages = [
            "System: Connection established",
            "System: Theme changed successfully",
            "System: Demo mode activated",
            "System: All features working correctly",
        ]
        import random

        message = random.choice(messages)
        self.chat_widget.add_system_message(message)

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.chat_widget.apply_theme(self.current_theme)

        # Update main window theme
        if self.current_theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                }
                QPushButton {
                    background-color: #4285F4;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5A9BFF;
                }
                QPushButton:pressed {
                    background-color: #2D5AA0;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #ffffff;
                }
                QPushButton {
                    background-color: #4285F4;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5A9BFF;
                }
                QPushButton:pressed {
                    background-color: #2D5AA0;
                }
            """)


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    demo = ChatDemo()
    demo.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
