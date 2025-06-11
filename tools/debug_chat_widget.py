#!/usr/bin/env python3
"""Debug script to test the chat widget functionality."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from my_coding_agent.gui.chat_widget import ChatWidget


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
        self.chat_widget = ChatWidget()
        layout.addWidget(self.chat_widget)

        # Test some messages
        self.add_test_messages()

        # Print widget info
        self.print_widget_info()

        # Test bubble height fix
        self.test_bubble_height_fix()

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

        # Handle different widget types for input field
        if hasattr(self.chat_widget, 'input_text'):
            print(f"Input text type: {type(self.chat_widget.input_text)}")  # type: ignore
        elif hasattr(self.chat_widget, 'input_field'):
            print(f"Input field type: {type(self.chat_widget.input_field)}")  # type: ignore
        else:
            print("Input field: Not found")

        # Handle different widget types for send button
        if hasattr(self.chat_widget, 'send_button'):
            print(f"Send button size: {self.chat_widget.send_button.size()}")  # type: ignore
            print(f"Send button fixed size: {self.chat_widget.send_button.maximumSize()}")  # type: ignore
        else:
            print("Send button: Not found (simplified widget)")

        # Check message bubbles - handle different display area types
        if hasattr(self.chat_widget, 'display_area'):
            bubbles = self.chat_widget.display_area._message_bubbles
        else:
            print("No display area found")
            return

        print(f"Number of message bubbles: {len(bubbles)}")

        for msg_id, bubble in bubbles.items():
            print(
                f"Bubble {msg_id}: role={bubble.role}, style_length={len(bubble.styleSheet())}"
            )

            # NEW: Print size policy and size information
            size_policy = bubble.sizePolicy()
            print(f"  Size policy: H={size_policy.horizontalPolicy()}, V={size_policy.verticalPolicy()}")
            print(f"  Current size: {bubble.size()}")
            print(f"  Size hint: {bubble.sizeHint()}")
            print(f"  Minimum size hint: {bubble.minimumSizeHint()}")

            # Check content label size policy - handle different attribute names
            content_widget = None
            if hasattr(bubble, 'content_text'):
                content_widget = bubble.content_text  # type: ignore
            elif hasattr(bubble, 'content_display'):
                content_widget = bubble.content_display  # type: ignore

            if content_widget:
                content_policy = content_widget.sizePolicy()
                print(f"  Content label size policy: H={content_policy.horizontalPolicy()}, V={content_policy.verticalPolicy()}")
                print(f"  Content label size: {content_widget.size()}")
                print(f"  Content label size hint: {content_widget.sizeHint()}")

            style = bubble.styleSheet()
            if len(style) > 0:
                print(f"  Style preview: {style[:100]}...")
            else:
                print("  No style applied!")

    def test_bubble_height_fix(self):
        """Test that message bubbles properly size to content height."""
        print("\n=== Testing Bubble Height Fix ===")

        # Add messages with different lengths to test sizing
        short_msg = self.chat_widget.add_user_message("Short message")
        long_msg = self.chat_widget.add_assistant_message(
            "This is a much longer message that should wrap to multiple lines and demonstrate "
            "that the bubble height adjusts properly to the content height without stretching "
            "to fill the entire available space in the chat area. The bubble should only be "
            "as tall as needed to display this text content properly."
        )

        # Force layout update
        self.chat_widget.repaint()
        QApplication.processEvents()

        # Check bubble sizes
        if hasattr(self.chat_widget, 'display_area'):
            bubbles = self.chat_widget.display_area._message_bubbles
        else:
            print("No display area found")
            return

        print(f"Added {len(bubbles)} test messages")

        for msg_id, bubble in bubbles.items():
            # Get content widget - handle different attribute names
            content_widget = None
            if hasattr(bubble, 'content_text'):
                content_widget = bubble.content_text  # type: ignore
            elif hasattr(bubble, 'content_display'):
                content_widget = bubble.content_display  # type: ignore

            if content_widget:
                content_height = content_widget.heightForWidth(content_widget.width())
                actual_height = bubble.height()
                print(f"Message {msg_id[:8]}... - Content height needed: {content_height}, Actual height: {actual_height}")

                # Check if height is reasonable (not stretched to fill screen)
                if actual_height > content_height * 3:  # Allow some padding but not excessive
                    print("  WARNING: Bubble may be stretching too much!")
                else:
                    print("  ✓ Bubble height looks appropriate")
            else:
                print(f"Message {msg_id[:8]}... - No content widget found")


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
