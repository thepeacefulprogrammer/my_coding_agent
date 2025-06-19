#!/usr/bin/env python3
"""Debug script to test visual styling differences."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

from my_coding_agent.gui.chat_widget_v2 import SimplifiedChatWidget


class StylingDebugWindow(QMainWindow):
    """Debug window to test visual styling."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Styling Debug - Look for Visual Differences")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add test button
        test_button = QPushButton("Add Test Messages")
        test_button.clicked.connect(self.add_test_messages)
        layout.addWidget(test_button)

        # Create chat widget
        self.chat_widget = SimplifiedChatWidget()
        layout.addWidget(self.chat_widget)

        # Automatically add test messages after a short delay
        QTimer.singleShot(100, self.add_test_messages)

    def add_test_messages(self):
        """Add test messages with detailed debugging."""
        print("\n=== Adding Test Messages for Visual Comparison ===")

        # Clear existing messages first
        self.chat_widget.clear_conversation()

        # Add user message
        print("Adding USER message...")
        self.chat_widget.add_user_message(
            "👤 USER: This should have a BLUE BORDER and BACKGROUND COLOR. Do you see a blue border around this message?"
        )

        # Add AI message
        print("Adding AI message...")
        self.chat_widget.add_assistant_message(
            "🤖 AI: This should be TRANSPARENT with NO BORDER. This message should look different from the user message above - no border, no background."
        )

        # Add system message
        print("Adding SYSTEM message...")
        self.chat_widget.add_system_message(
            "⚙️ SYSTEM: This should have a GRAY BACKGROUND. This is a system message with different styling."
        )

        # Debug the actual styling
        QTimer.singleShot(200, self.debug_visual_styling)

    def debug_visual_styling(self):
        """Debug the visual styling after widgets are rendered."""
        print("\n=== Visual Styling Debug ===")

        bubbles = self.chat_widget.display_area._message_bubbles
        print(f"Found {len(bubbles)} message bubbles")

        for _msg_id, bubble in bubbles.items():
            print(f"\n--- Bubble {bubble.role.value.upper()} ---")
            print(f"Widget type: {type(bubble)}")
            print(f"Role: {bubble.role.value}")

            # Get the actual rendered style
            style = bubble.styleSheet()
            print(f"StyleSheet length: {len(style)}")

            if style:
                print("StyleSheet content:")
                print(style)

                # Check for key styling elements
                has_border = "border:" in style and "border: none" not in style
                has_background = (
                    "background-color:" in style and "transparent" not in style
                )
                has_border_radius = "border-radius:" in style

                print(f"Has border: {has_border}")
                print(f"Has background: {has_background}")
                print(f"Has border-radius: {has_border_radius}")

                # Check if widget is actually visible
                print(f"Visible: {bubble.isVisible()}")
                print(f"Size: {bubble.size()}")
                print(f"Geometry: {bubble.geometry()}")
            else:
                print("❌ NO STYLESHEET APPLIED!")

        # Also check the input area
        print("\n--- Input Area Debug ---")
        print(f"Send icon size: {self.chat_widget.send_icon.size()}")
        print(f"Send icon position: {self.chat_widget.send_icon.pos()}")
        print(f"Input text type: {type(self.chat_widget.input_text)}")

        # Check input styling
        input_style = self.chat_widget.input_text.styleSheet()
        icon_style = self.chat_widget.send_icon.styleSheet()

        print(f"Input has styling: {len(input_style) > 0}")
        print(f"Icon has styling: {len(icon_style) > 0}")

        if icon_style:
            print(f"Icon style preview: {icon_style[:100]}...")


def main():
    """Run the styling debug application."""
    app = QApplication(sys.argv)

    print("=== STYLING DEBUG TEST ===")
    print("This test will show you if the message styling is working.")
    print("Look for:")
    print("1. USER messages should have BLUE BORDERS")
    print("2. AI messages should be TRANSPARENT (no border)")
    print("3. SYSTEM messages should have GRAY background")
    print("4. Send button should be smaller (60x28 instead of 80x32)")
    print("\nOpening debug window...")

    window = StylingDebugWindow()
    window.show()

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
