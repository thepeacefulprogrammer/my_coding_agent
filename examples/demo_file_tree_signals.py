#!/usr/bin/env python3
"""
Demo script showing file tree selection and click-to-open functionality.

This script demonstrates the file tree widget with signal handling for:
- File selection (single click)
- File opening (double click or Enter key)
- Directory expansion/collapse (double click)

Run this script to see the file tree in action.
"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from my_coding_agent.core.file_tree import FileTreeWidget


class FileTreeDemo(QMainWindow):
    """Demo window showing file tree functionality."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Tree Demo - Selection and Click-to-Open")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add info label
        info_label = QLabel(
            "File Tree Demo:\n"
            "• Single-click a file to select it\n"
            "• Double-click a file to open it\n"
            "• Double-click a directory to expand/collapse\n"
            "• Press Enter on a selected file to open it\n"
            "• Watch the status messages below"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_label.setStyleSheet(
            "padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc;"
        )
        layout.addWidget(info_label)

        # Create file tree
        self.file_tree = FileTreeWidget()

        # Set root to current directory
        current_dir = Path.cwd()
        self.file_tree.set_root_directory(current_dir)

        layout.addWidget(self.file_tree)

        # Create status label
        self.status_label = QLabel(
            "Ready - Select or open a file to see signals in action"
        )
        self.status_label.setStyleSheet(
            "padding: 5px; background-color: #e8e8e8; border: 1px solid #ccc;"
        )
        layout.addWidget(self.status_label)

        # Connect signals
        self.file_tree.file_selected.connect(self.on_file_selected)
        self.file_tree.file_opened.connect(self.on_file_opened)

        print(f"Demo started. Showing files from: {current_dir}")
        print("Interact with the file tree to see signal handling in action.")

    def on_file_selected(self, file_path: Path) -> None:
        """Handle file selection signal."""
        message = f"📄 File SELECTED: {file_path.name} ({file_path})"
        self.status_label.setText(message)
        print(message)

    def on_file_opened(self, file_path: Path) -> None:
        """Handle file opening signal."""
        message = f"🚀 File OPENED: {file_path.name} ({file_path})"
        self.status_label.setText(message)
        print(message)


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)

    demo = FileTreeDemo()
    demo.show()

    print("\nDemo Instructions:")
    print("1. Single-click any file to see the 'file_selected' signal")
    print("2. Double-click any file to see the 'file_opened' signal")
    print("3. Double-click directories to expand/collapse them")
    print("4. Use keyboard navigation (arrow keys + Enter)")
    print("5. Close the window or press Ctrl+C to exit")

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nDemo terminated by user.")


if __name__ == "__main__":
    main()
