#!/usr/bin/env python3
"""Debug script to check keyboard shortcuts."""

import sys

sys.path.append("src")

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication

from my_coding_agent.core.main_window import MainWindow


def main():
    app = QApplication(sys.argv)  # noqa: F841
    window = MainWindow()

    print("=== Keyboard Shortcuts Debug ===")

    # Check exit action
    exit_action = window.findChild(QAction, "exit_action")
    print(f"Exit action found: {exit_action is not None}")
    if exit_action:
        print(f"  Text: '{exit_action.text()}'")
        shortcut = exit_action.shortcut()
        print(f"  Shortcut: '{shortcut.toString()}'")
        print(f"  Shortcut empty: {shortcut.isEmpty()}")

    # Check open action
    open_action = window.findChild(QAction, "open_action")
    print(f"Open action found: {open_action is not None}")
    if open_action:
        print(f"  Text: '{open_action.text()}'")
        shortcut = open_action.shortcut()
        print(f"  Shortcut: '{shortcut.toString()}'")
        print(f"  Shortcut empty: {shortcut.isEmpty()}")


if __name__ == "__main__":
    main()
