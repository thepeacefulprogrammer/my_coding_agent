"""
Main application window for the Simple Code Viewer.

This module contains the MainWindow class which serves as the primary
application window using PyQt6. It provides the main layout structure
and will later host the file tree and code viewer components.
"""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from .code_viewer import CodeViewerWidget
    from .file_tree import FileTreeWidget

from PyQt6.QtCore import QSize, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import QLabel, QMainWindow, QWidget

from .ai_agent import AIAgent, AIAgentConfig
from .theme_manager import ThemeManager


class AIWorkerThread(QThread):
    """Worker thread for handling AI requests asynchronously."""

    response_ready = pyqtSignal(str, bool, str)  # content, success, error

    def __init__(self, ai_agent: AIAgent, message: str) -> None:
        super().__init__()
        self.ai_agent = ai_agent
        self.message = message

    def run(self) -> None:
        """Run the AI request in a separate thread."""
        loop = None
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run the AI request
            response = loop.run_until_complete(self.ai_agent.send_message(self.message))

            # Emit the response
            self.response_ready.emit(
                response.content, response.success, response.error or ""
            )

        except Exception as e:
            self.response_ready.emit("", False, str(e))
        finally:
            if loop is not None:
                loop.close()


class MainWindow(QMainWindow):
    """
    Main application window for the Simple Code Viewer.

    This class inherits from QMainWindow and provides the main window
    structure including status bar, central widget, and proper sizing.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the MainWindow.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)

        # Initialize theme manager
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None and isinstance(app, QApplication):
            self._theme_manager = ThemeManager(app)

        self._setup_window()
        self._setup_ui()
        self._setup_settings()

        # Restore window state from previous session
        self.restore_window_state()

    def get_theme_manager(self) -> ThemeManager | None:
        """Get the theme manager instance.

        Returns:
            ThemeManager instance if available, None otherwise
        """
        return getattr(self, "_theme_manager", None)

    @property
    def file_tree(self) -> "FileTreeWidget":
        """Get the file tree widget."""
        return self._file_tree

    @property
    def code_viewer(self) -> "CodeViewerWidget":
        """Get the code viewer widget."""
        return self._code_viewer

    @property
    def chat_widget(self):
        """Get the chat widget."""
        return self._chat_widget

    @property
    def theme_manager(self) -> ThemeManager | None:
        """Get the theme manager instance."""
        return getattr(self, "_theme_manager", None)

    @property
    def status_bar(self):
        """Get the status bar."""
        return super().statusBar()

    @property
    def splitter(self):
        """Get the main splitter widget."""
        return getattr(self, "_splitter", None)

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

        # Create horizontal splitter for main layout (25% left, 45% center, 30% right)
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

        # Create center panel (code viewer)
        center_panel = QFrame()
        center_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        center_panel.setLineWidth(1)

        # Add code viewer widget to center panel
        from .code_viewer import CodeViewerWidget

        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(5, 5, 5, 5)  # Small margins

        self._code_viewer = CodeViewerWidget()
        center_layout.addWidget(self._code_viewer)

        # Apply current theme to code viewer if theme manager is available
        if hasattr(self, "_theme_manager"):
            self._theme_manager.apply_theme_to_widget(self._code_viewer)

        # Create right panel (chat widget)
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        right_panel.setLineWidth(1)

        # Add chat widget to right panel
        from ..gui.chat_widget import ChatWidget

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)  # Small margins

        self._chat_widget = ChatWidget()
        right_layout.addWidget(self._chat_widget)

        # Apply current theme to chat widget
        if hasattr(self, "_theme_manager"):
            current_theme = self._theme_manager.get_current_theme()
            self._chat_widget.apply_theme(current_theme)

        # Initialize AI agent and connect chat widget
        self._setup_ai_integration()

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)

        # Set initial sizes for 25%/45%/30% split
        # Calculate based on default window width (1200px)
        left_width = int(1200 * 0.25)  # 300px
        center_width = int(1200 * 0.45)  # 540px
        right_width = int(1200 * 0.30)  # 360px
        splitter.setSizes([left_width, center_width, right_width])

        # Set minimum sizes to prevent panels from being too small
        left_panel.setMinimumWidth(120)  # Minimum for file tree
        center_panel.setMinimumWidth(250)  # Minimum for code viewer
        right_panel.setMinimumWidth(200)  # Minimum for chat widget

        # Make splitter handle visible and responsive
        splitter.setChildrenCollapsible(False)  # Prevent complete collapse
        splitter.setHandleWidth(3)  # 3px handle width

        # Store references for future use
        self._splitter = splitter
        self._left_panel = left_panel
        self._center_panel = center_panel
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

        # Create View menu for theme switching
        view_menu = menu_bar.addMenu("&View")
        if view_menu is not None:
            # Add theme toggle action
            toggle_theme_action = QAction("Toggle &Dark Mode", self)
            toggle_theme_action.setObjectName("toggle_theme_action")
            toggle_theme_action.setShortcut(QKeySequence("Ctrl+D"))
            toggle_theme_action.setStatusTip("Toggle between light and dark themes")
            toggle_theme_action.setToolTip(
                "Toggle between light and dark themes (Ctrl+D)"
            )
            toggle_theme_action.triggered.connect(self._toggle_theme)
            view_menu.addAction(toggle_theme_action)

            self._toggle_theme_action = toggle_theme_action

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

    def _toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        if hasattr(self, "_theme_manager"):
            new_theme = self._theme_manager.toggle_theme()

            # Apply theme to code viewer if it exists
            if hasattr(self, "_code_viewer"):
                self._theme_manager.apply_theme_to_widget(self._code_viewer)

            # Apply theme to chat widget if it exists
            if hasattr(self, "_chat_widget"):
                self._chat_widget.apply_theme(new_theme)

            # Update status bar to show theme change
            if hasattr(self, "_file_info_label"):
                self._file_info_label.setText(f"Theme: {new_theme.title()}")

            # Update toggle action text based on current theme
            if hasattr(self, "_toggle_theme_action"):
                if new_theme == "dark":
                    self._toggle_theme_action.setText("Toggle &Light Mode")
                    self._toggle_theme_action.setStatusTip("Switch to light theme")
                else:
                    self._toggle_theme_action.setText("Toggle &Dark Mode")
                    self._toggle_theme_action.setStatusTip("Switch to dark theme")

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
        # Load the file into the code viewer
        if hasattr(self, "_code_viewer"):
            success = self._code_viewer.load_file(file_path)
            if success:
                self.update_file_info_display(f"Loaded: {file_path.name}")

                # Get and display additional file info
                try:
                    content = self._code_viewer.toPlainText()
                    line_count = content.count("\n") + 1 if content else 0

                    file_size = file_path.stat().st_size
                    if file_size < 1024:
                        size_str = f"{file_size} B"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.1f} KB"
                    else:
                        size_str = f"{file_size / (1024 * 1024):.1f} MB"

                    file_type = (
                        file_path.suffix.upper()[1:] if file_path.suffix else "File"
                    )
                    language = self._code_viewer.get_current_language().title()
                    info_text = (
                        f"{file_type} | {language} | {line_count} lines | {size_str}"
                    )
                    self.update_file_info_display(info_text)
                except Exception:
                    self.update_file_info_display(f"Loaded: {file_path.name}")
            else:
                self.update_file_info_display(f"Failed to load: {file_path.name}")
        else:
            # Fallback if code viewer not available
            self.update_file_info_display(f"Opening: {file_path.name}")

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
                    and len(splitter_sizes) == 3
                ):
                    try:
                        # Convert to integers if they're strings
                        splitter_list = cast("list[Any]", splitter_sizes)
                        sizes: list[int] = [int(size) for size in splitter_list]
                        if all(size > 0 for size in sizes):
                            self._splitter.setSizes(sizes)
                    except (ValueError, TypeError):
                        # If conversion fails, keep default sizes
                        pass

        except Exception:
            # If any restoration fails, use defaults (no action needed)
            pass

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Handle window close event by saving state."""
        # Save current window state before closing
        self.save_window_state()

        # Accept the close event
        if a0 is not None:
            a0.accept()

    def _setup_ai_integration(self) -> None:
        """Set up AI integration and connect chat widget."""
        try:
            # Initialize AI agent with configuration
            self._ai_config = AIAgentConfig.from_env()
            self._ai_agent = AIAgent(self._ai_config)

            # Connect chat widget message_sent signal to our handler
            self._chat_widget.message_sent.connect(self._handle_chat_message)

            # Initialize worker thread as None
            self._ai_worker_thread = None

        except Exception as e:
            # If AI initialization fails, show error in chat
            self._chat_widget.add_system_message(
                f"AI initialization failed: {str(e)}. Chat will work without AI responses."
            )
            self._ai_agent = None

    def _handle_chat_message(self, message: str) -> None:
        """Handle messages from the chat widget and generate AI responses."""
        if not self._ai_agent:
            # If no AI agent, show a simple echo response
            self._chat_widget.add_assistant_message(
                "AI is not available. Configuration required for responses."
            )
            return

        # Show thinking indicator
        self._chat_widget.show_ai_thinking(animated=True)

        # Create and start worker thread for AI request
        self._ai_worker_thread = AIWorkerThread(self._ai_agent, message)
        self._ai_worker_thread.response_ready.connect(self._handle_ai_response)
        self._ai_worker_thread.start()

    def _handle_ai_response(self, content: str, success: bool, error: str) -> None:
        """Handle AI response from worker thread."""
        # Hide typing indicator
        self._chat_widget.hide_typing_indicator()

        if success and content:
            # Add successful AI response
            self._chat_widget.add_assistant_message(content)
        else:
            # Add error message
            error_msg = (
                f"AI Error: {error}" if error else "AI failed to generate response"
            )
            self._chat_widget.add_assistant_message(error_msg)

        # Clean up worker thread
        if self._ai_worker_thread:
            self._ai_worker_thread.deleteLater()
            self._ai_worker_thread = None
