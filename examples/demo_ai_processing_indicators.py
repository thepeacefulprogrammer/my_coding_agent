#!/usr/bin/env python3
"""
Demo script for AI Processing Indicators

This script demonstrates the enhanced AI processing indicators in the chat widget,
showing different states like thinking, processing, generating, and error states,
with support for animations and theme consistency.

Usage:
    python examples/demo_ai_processing_indicators.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from my_coding_agent.gui.chat_widget import ChatWidget


class ProcessingIndicatorDemo(QWidget):
    """Demo widget showcasing AI processing indicators."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Processing Indicators Demo")
        self.setGeometry(200, 200, 800, 600)

        # Initialize chat widget
        self.chat_widget = ChatWidget()

        # Setup UI
        self._setup_ui()
        self._setup_demo_messages()

    def _setup_ui(self):
        """Setup the demo UI."""
        layout = QVBoxLayout(self)

        # Control buttons
        controls = QHBoxLayout()

        # Basic state buttons
        thinking_btn = QPushButton("Show Thinking")
        thinking_btn.clicked.connect(lambda: self.chat_widget.show_ai_thinking())
        controls.addWidget(thinking_btn)

        processing_btn = QPushButton("Show Processing")
        processing_btn.clicked.connect(
            lambda: self.chat_widget.show_ai_processing("Analyzing your request...")
        )
        controls.addWidget(processing_btn)

        generating_btn = QPushButton("Show Generating")
        generating_btn.clicked.connect(
            lambda: self.chat_widget.show_ai_generating("Writing response...")
        )
        controls.addWidget(generating_btn)

        error_btn = QPushButton("Show Error")
        error_btn.clicked.connect(
            lambda: self.chat_widget.show_ai_error("Failed to process request")
        )
        controls.addWidget(error_btn)

        # Animated indicators
        controls.addWidget(QPushButton("  "))  # Spacer

        animated_thinking_btn = QPushButton("Animated Thinking")
        animated_thinking_btn.clicked.connect(
            lambda: self.chat_widget.show_ai_thinking(animated=True)
        )
        controls.addWidget(animated_thinking_btn)

        animated_processing_btn = QPushButton("Animated Processing")
        animated_processing_btn.clicked.connect(
            lambda: self.chat_widget.show_ai_processing("Loading", animated=True)
        )
        controls.addWidget(animated_processing_btn)

        # Simulation button
        simulate_btn = QPushButton("Simulate AI Workflow")
        simulate_btn.clicked.connect(self.simulate_ai_workflow)
        controls.addWidget(simulate_btn)

        # Hide button
        hide_btn = QPushButton("Hide Indicators")
        hide_btn.clicked.connect(self.chat_widget.hide_typing_indicator)
        controls.addWidget(hide_btn)

        # Theme toggle
        theme_btn = QPushButton("Toggle Theme")
        theme_btn.clicked.connect(self.toggle_theme)
        controls.addWidget(theme_btn)

        layout.addLayout(controls)
        layout.addWidget(self.chat_widget)

    def _setup_demo_messages(self):
        """Add some demo messages to the chat."""
        self.chat_widget.add_system_message(
            "Welcome to the AI Processing Indicators demo!"
        )
        self.chat_widget.add_user_message(
            "Hello! Can you show me some processing indicators?"
        )
        self.chat_widget.add_assistant_message(
            "Of course! I can show you different processing states:\n"
            "• Thinking - when I'm analyzing your request\n"
            "• Processing - when I'm working on your task\n"
            "• Generating - when I'm writing a response\n"
            "• Error - when something goes wrong\n\n"
            "Each state has its own distinct styling and can be animated!"
        )

    def simulate_ai_workflow(self):
        """Simulate a complete AI workflow with different processing states."""
        # Start with thinking
        self.chat_widget.show_ai_thinking(animated=True)

        # After 2 seconds, switch to processing
        QTimer.singleShot(
            2000,
            lambda: self.chat_widget.show_ai_processing(
                "Reading files...", animated=True
            ),
        )

        # After 4 seconds, update the processing message
        QTimer.singleShot(
            4000,
            lambda: self.chat_widget.update_processing_message(
                "Analyzing code structure..."
            ),
        )

        # After 6 seconds, switch to generating
        QTimer.singleShot(
            6000,
            lambda: self.chat_widget.show_ai_generating(
                "Writing response...", animated=True
            ),
        )

        # After 8 seconds, hide indicator and add response
        QTimer.singleShot(8000, self._complete_simulation)

    def _complete_simulation(self):
        """Complete the AI workflow simulation."""
        self.chat_widget.hide_typing_indicator()
        self.chat_widget.add_assistant_message(
            "Simulation complete! I went through the following states:\n"
            "1. 🤔 Thinking (animated)\n"
            "2. 📖 Reading files (animated)\n"
            "3. 🔍 Analyzing code structure\n"
            "4. ✍️ Writing response (animated)\n"
            "5. ✅ Complete!\n\n"
            "Each state has distinct visual styling that adapts to the current theme."
        )

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        # This is a simple theme toggle for demo purposes
        # In a real application, this would integrate with the ThemeManager
        current_palette = self.palette()
        is_dark = current_palette.window().color().lightness() < 128

        if is_dark:
            self.chat_widget.apply_theme("light")
        else:
            self.chat_widget.apply_theme("dark")


def main():
    """Run the AI processing indicators demo."""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("AI Processing Indicators Demo")
    app.setApplicationVersion("1.0.0")

    # Create and show demo
    demo = ProcessingIndicatorDemo()
    demo.show()

    # Instructions
    print("AI Processing Indicators Demo")
    print("=" * 40)
    print("Use the buttons to test different processing states:")
    print("• Basic states: Thinking, Processing, Generating, Error")
    print("• Animated versions with moving dots")
    print("• Simulate AI Workflow: shows a complete processing sequence")
    print("• Theme toggle: see how indicators adapt to different themes")
    print()
    print("The indicators feature:")
    print("• State-specific color coding")
    print("• Theme-aware styling")
    print("• Smooth animations")
    print("• Message updates during processing")
    print()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
