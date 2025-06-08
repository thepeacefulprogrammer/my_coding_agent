#!/usr/bin/env python3
"""Debug script to check the main window menu structure."""

import sys

sys.path.append("src")

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication

from my_coding_agent.core.main_window import MainWindow


def check_menu(window):
    """Check menu structure after window is shown."""
    print("=== Main Window Menu Debug (After Show) ===")

    # Check if exit action exists
    exit_action = window.findChild(QAction, "exit_action")
    print(f"Exit action found: {exit_action is not None}")
    if exit_action:
        print(f"  Text: '{exit_action.text()}'")
        print(f"  Shortcut: '{exit_action.shortcut().toString()}'")
        print(f"  Enabled: {exit_action.isEnabled()}")
        print(f"  Visible: {exit_action.isVisible()}")
        print(f"  Parent: {exit_action.parent()}")

    # Check open action too
    open_action = window.findChild(QAction, "open_action")
    print(f"Open action found: {open_action is not None}")
    if open_action:
        print(f"  Text: '{open_action.text()}'")
        print(f"  Shortcut: '{open_action.shortcut().toString()}'")

    # Check the file menu structure
    menu_bar = window.menuBar()
    print(f"Menu bar found: {menu_bar is not None}")

    if menu_bar:
        print("Menu bar actions:")
        for i, action in enumerate(menu_bar.actions()):
            print(f"  {i}: '{action.text()}'")
            if action.menu():
                menu = action.menu()
                print(f"    Menu actions ({len(menu.actions())} total):")
                for j, menu_action in enumerate(menu.actions()):
                    if menu_action.isSeparator():
                        print(f"      {j}: [SEPARATOR]")
                    else:
                        print(
                            f"      {j}: '{menu_action.text()}' (visible: {menu_action.isVisible()}, enabled: {menu_action.isEnabled()})"
                        )

    # Exit after checking
    QApplication.quit()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    # Show the window first
    window.show()

    # Use a timer to check the menu after the window is fully initialized
    QTimer.singleShot(500, lambda: check_menu(window))  # Check after 500ms

    # Run the event loop briefly
    app.exec()


if __name__ == "__main__":
    main()
