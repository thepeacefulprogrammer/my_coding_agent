#!/usr/bin/env python3
"""
Demo script showcasing the chat widget with dark theme functionality.

This script demonstrates the enhanced dark theme styling that's consistent
with the main application's dark theme.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from my_coding_agent.gui.chat_widget import ChatWidget


class DarkThemeChatDemo(QMainWindow):
    """Demo window showcasing dark theme chat widget."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Widget Dark Theme Demo")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout(central_widget)

        # Theme toggle buttons
        button_layout = QHBoxLayout()

        self.light_button = QPushButton("Light Theme")
        self.light_button.clicked.connect(lambda: self.apply_theme("light"))
        button_layout.addWidget(self.light_button)

        self.dark_button = QPushButton("Dark Theme")
        self.dark_button.clicked.connect(lambda: self.apply_theme("dark"))
        button_layout.addWidget(self.dark_button)

        layout.addLayout(button_layout)

        # Chat widget
        self.chat_widget = ChatWidget()
        layout.addWidget(self.chat_widget)

        # Add some demo messages
        self.setup_demo_messages()

        # Start with dark theme
        self.apply_theme("dark")

        # Connect chat widget signal
        self.chat_widget.message_sent.connect(self.handle_message)

    def setup_demo_messages(self):
        """Add some demo messages to showcase the styling."""
        self.chat_widget.add_system_message("Welcome to the dark theme chat demo!")
        self.chat_widget.add_user_message("Hello! This is a user message.")
        self.chat_widget.add_assistant_message(
            "Hi there! This is an assistant response. The dark theme provides excellent contrast and readability."
        )
        self.chat_widget.add_user_message(
            "The dark theme looks great! It's consistent with the main application styling."
        )
        self.chat_widget.add_assistant_message(
            "Absolutely! The dark theme uses colors from the main application's dark.qss theme file, ensuring visual consistency across the entire interface."
        )

    def apply_theme(self, theme: str):
        """Apply theme to the chat widget and update window styling."""
        self.chat_widget.apply_theme(theme)

        # Update window styling to match
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #4a4a4a;
                    color: #ffffff;
                    border: 1px solid #666666;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #555555;
                }
                QPushButton:pressed {
                    background-color: #333333;
                }
            """)
        else:
            self.setStyleSheet("")

    def handle_message(self, message: str):
        """Handle new messages from the chat widget."""
        # Echo the message as an assistant response
        self.chat_widget.add_assistant_message(f"You said: {message}")


def main():
    """Run the dark theme chat demo."""
    app = QApplication(sys.argv)

    # Set application-wide dark theme
    app.setStyleSheet("""
        QApplication {
            background-color: #2d2d2d;
            color: #ffffff;
        }
    """)

    demo = DarkThemeChatDemo()
    demo.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
