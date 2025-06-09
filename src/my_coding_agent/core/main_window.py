"""
Main application window for the Simple Code Viewer.

This module contains the MainWindow class which serves as the primary
application window using PyQt6. It provides the main layout structure
and will later host the file tree and code viewer components.
"""

from pathlib import Path
from typing import Any, List, Optional, cast

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import QLabel, QMainWindow, QWidget


class MainWindow(QMainWindow):
    """
    Main application window for the Simple Code Viewer.

    This class inherits from QMainWindow and provides the main window
    structure including status bar, central widget, and proper sizing.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the MainWindow.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self._setup_window()
        self._setup_ui()
        self._setup_settings()

        # Restore window state from previous session
        self.restore_window_state()

    def _setup_window(self) -> None:
        """Set up basic window properties."""
        # Set window title
        self.setWindowTitle("Simple Code Viewer")

        # Set minimum size
        self.setMinimumSize(QSize(800, 600))

        # Set default size - ensure we meet minimum expectations
        self.resize(QSize(1200, 800))

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Set up menu bar first
        self._setup_menu_bar()

        # Create horizontal splitter for main layout (30% left, 70% right)
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QFrame, QSplitter

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        # Create left panel with file tree
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        left_panel.setLineWidth(1)

        # Add file tree widget to left panel
        from PyQt6.QtWidgets import QVBoxLayout

        from .file_tree import FileTreeWidget

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)  # Small margins

        self._file_tree = FileTreeWidget()
        # Set the file tree to show the current working directory
        import os

        self._file_tree.set_root_directory(os.getcwd())

        # Connect file tree signals to update status bar
        self._file_tree.file_selected.connect(self._on_file_selected)
        self._file_tree.file_opened.connect(self._on_file_opened)

        left_layout.addWidget(self._file_tree)

        # Create right panel (will hold code viewer)
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        right_panel.setLineWidth(1)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # Set initial sizes for 30%/70% split
        # Calculate based on default window width (1000px)
        left_width = int(1000 * 0.3)  # 300px
        right_width = int(1000 * 0.7)  # 700px
        splitter.setSizes([left_width, right_width])

        # Set minimum sizes to prevent panels from being too small
        left_panel.setMinimumWidth(150)  # Minimum 150px for file tree
        right_panel.setMinimumWidth(300)  # Minimum 300px for code viewer

        # Make splitter handle visible and responsive
        splitter.setChildrenCollapsible(False)  # Prevent complete collapse
        splitter.setHandleWidth(3)  # 3px handle width

        # Store references for future use
        self._splitter = splitter
        self._left_panel = left_panel
        self._right_panel = right_panel

        # Set up enhanced status bar
        self._setup_status_bar()

    def _setup_menu_bar(self) -> None:
        """Set up the menu bar with File menu and actions."""
        menu_bar = self.menuBar()
        if menu_bar is None:
            return

        # Create File menu
        file_menu = menu_bar.addMenu("&File")
        if file_menu is None:
            return

        # Create Open action
        open_action = QAction("&Open", self)
        open_action.setObjectName("open_action")
        open_action.setShortcut(QKeySequence.StandardKey.Open)  # Ctrl+O
        open_action.setStatusTip("Open a file")
        open_action.setToolTip("Open a file (Ctrl+O)")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        # Add separator
        file_menu.addSeparator()

        # Create Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setObjectName("exit_action")
        # Set shortcut explicitly to ensure it works in all environments
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.setStatusTip("Exit the application")
        exit_action.setToolTip("Exit the application (Ctrl+Q)")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Store references for testing
        self._open_action = open_action
        self._exit_action = exit_action

    def _open_file(self) -> None:
        """Handle Open File action. This is a placeholder for now."""
        # TODO: Implement file opening functionality in a future task
        # For now, just show a status message
        if hasattr(self, "_file_path_label"):
            self._file_path_label.setText("Open file functionality not yet implemented")

        # This method will be expanded when implementing file tree and code viewer

    def _setup_status_bar(self) -> None:
        """Set up the status bar with file path and info displays."""
        status_bar = self.statusBar()
        assert status_bar is not None  # QMainWindow always provides a status bar

        # Create file path label (left side, permanent)
        self._file_path_label = QLabel("No file selected")
        self._file_path_label.setObjectName("file_path_label")
        status_bar.addPermanentWidget(self._file_path_label, 1)  # Stretch factor 1

        # Create file info label (right side, permanent)
        self._file_info_label = QLabel("Ready")
        self._file_info_label.setObjectName("file_info_label")
        status_bar.addPermanentWidget(self._file_info_label, 0)  # No stretch

    def update_file_path_display(self, file_path: Path) -> None:
        """Update the file path display in the status bar.

        Args:
            file_path: Path to the currently selected file
        """
        if hasattr(self, "_file_path_label"):
            self._file_path_label.setText(f"File: {file_path}")

    def update_file_info_display(self, file_info: str) -> None:
        """Update the file info display in the status bar.

        Args:
            file_info: Information about the file (type, size, lines, etc.)
        """
        if hasattr(self, "_file_info_label"):
            self._file_info_label.setText(file_info)

    def clear_file_display(self) -> None:
        """Clear the file displays and return to initial state."""
        if hasattr(self, "_file_path_label"):
            self._file_path_label.setText("No file selected")
        if hasattr(self, "_file_info_label"):
            self._file_info_label.setText("Ready")

    def _on_file_selected(self, file_path: Path) -> None:
        """
        Handle file selection from the file tree.

        Args:
            file_path: Path to the selected file
        """
        # Update status bar with selected file
        self.update_file_path_display(file_path)

        # Get file info and display it
        try:
            file_size = file_path.stat().st_size
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"

            file_type = file_path.suffix.upper()[1:] if file_path.suffix else "File"
            info_text = f"{file_type} | {size_str}"
            self.update_file_info_display(info_text)
        except OSError:
            self.update_file_info_display("File info unavailable")

    def _on_file_opened(self, file_path: Path) -> None:
        """
        Handle file opening from the file tree.

        Args:
            file_path: Path to the file to open
        """
        # For now, just update the status bar to indicate the file would be opened
        # This will be expanded when the code viewer is implemented in task 4.0
        self.update_file_info_display(f"Opening: {file_path.name}")

        # TODO: In task 4.0, this will load the file content into the code viewer

    def _setup_settings(self) -> None:
        """Set up QSettings for persistent application state."""
        from PyQt6.QtCore import QSettings

        # Create settings object for persistent storage
        self._settings = QSettings("MyCodeViewerApp", "SimpleCodeViewer")

    def save_window_state(self) -> None:
        """Save the current window state (geometry, splitter positions) to settings."""
        if not hasattr(self, "_settings"):
            return

        # Save window geometry (size and position)
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("window_state", self.saveState())

        # Save splitter sizes
        if hasattr(self, "_splitter"):
            splitter_sizes = self._splitter.sizes()
            self._settings.setValue("splitter_sizes", splitter_sizes)

    def restore_window_state(self) -> None:
        """Restore window state from settings, using defaults if none exist."""
        if not hasattr(self, "_settings"):
            return

        try:
            # Restore window geometry
            geometry = self._settings.value("geometry")
            if geometry is not None:
                self.restoreGeometry(geometry)

            # Restore window state (toolbars, docks, etc.)
            window_state = self._settings.value("window_state")
            if window_state is not None:
                self.restoreState(window_state)

            # Restore splitter sizes
            if hasattr(self, "_splitter"):
                splitter_sizes = self._settings.value("splitter_sizes")
                if (
                    splitter_sizes is not None
                    and isinstance(splitter_sizes, list)
                    and len(splitter_sizes) == 2
                ):
                    try:
                        # Convert to integers if they're strings
                        splitter_list = cast(List[Any], splitter_sizes)
                        sizes: List[int] = [int(size) for size in splitter_list]
                        if all(size > 0 for size in sizes):
                            self._splitter.setSizes(sizes)
                    except (ValueError, TypeError):
                        # If conversion fails, keep default sizes
                        pass

        except Exception:
            # If any restoration fails, use defaults (no action needed)
            pass

    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:
        """Handle window close event by saving state."""
        # Save current window state before closing
        self.save_window_state()

        # Accept the close event
        if a0 is not None:
            a0.accept()
