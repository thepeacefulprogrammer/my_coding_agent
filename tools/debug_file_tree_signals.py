#!/usr/bin/env python3
"""
Debug script to test file tree signals manually.
"""

import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from my_coding_agent.core.file_tree import FileTreeWidget


def main():
    app = QApplication(sys.argv)

    # Create temporary test files
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create test files
        python_file = tmp_path / "test.py"
        python_file.write_text("print('hello world')")

        text_file = tmp_path / "readme.txt"
        text_file.write_text("This is a readme file")

        # Create test directory
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()

        # Create widget
        widget = FileTreeWidget()
        widget.set_root_directory(tmp_path)
        widget.show()

        # Connect signals for debugging
        def on_file_selected(path):
            print(f"File selected: {path}")

        def on_file_opened(path):
            print(f"File opened: {path}")

        widget.file_selected.connect(on_file_selected)
        widget.file_opened.connect(on_file_opened)

        print("Widget created and signals connected.")
        print("Try selecting and double-clicking files.")
        print("Press Ctrl+C to exit.")

        # Set up a timer to keep the app running
        timer = QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(100)

        try:
            app.exec()
        except KeyboardInterrupt:
            print("\nExiting...")


if __name__ == "__main__":
    main()
