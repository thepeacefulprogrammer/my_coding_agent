"""
Main application window for the Simple Code Viewer.

This module contains the MainWindow class which serves as the primary
application window using PyQt6. It provides the main layout structure
and will later host the file tree and code viewer components.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from .code_viewer import CodeViewerWidget
    from .file_tree import FileTreeWidget

from PyQt6.QtCore import (
    QSettings,
    QSize,
    QThread,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout

from ..gui.chat_widget_v2 import SimplifiedChatWidget
from .ai_agent import AIAgent, AIAgentConfig
from .mcp_client_coordinator import MCPClientCoordinator, MCPCoordinatorConfig
from .theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class MCPWorkerThread(QThread):
    """Worker thread for handling MCP requests asynchronously."""

    response_ready = pyqtSignal(str, bool, str)  # content, success, error

    def __init__(self, coordinator: MCPClientCoordinator, message: str) -> None:
        super().__init__()
        self.coordinator = coordinator
        self.message = message

    def run(self) -> None:
        """Execute the MCP request in the background thread."""
        loop = None
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Send message and get response
            response = loop.run_until_complete(
                self.coordinator.send_message(self.message)
            )

            # Emit success signal
            self.response_ready.emit(response.content, True, "")

        except Exception as e:
            # Emit error signal
            self.response_ready.emit("", False, str(e))
        finally:
            if loop:
                loop.close()

    def _initialize_mcp_connection(self) -> None:
        """Initialize MCP connection asynchronously after GUI startup."""
        if not self._mcp_coordinator:
            return

        def run_mcp_initialization():
            """Run MCP connection initialization in a separate thread with event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                print("🔗 Connecting to MCP server...")
                # Connect to MCP server
                loop.run_until_complete(self._mcp_coordinator.connect())
                print("✅ MCP server connected successfully")

                # Update chat widget with connection status
                if hasattr(self, "_chat_widget") and self._chat_widget:
                    QTimer.singleShot(
                        0,
                        lambda: self._chat_widget.add_system_message(
                            "Connected to MCP server successfully"
                        ),
                    )

            except Exception as e:
                error_msg = f"❌ Failed to connect to MCP server: {e}"
                print(error_msg)
                if hasattr(self, "_chat_widget") and self._chat_widget:
                    # Capture the error message in the lambda to avoid variable scope issues
                    error_message = f"MCP server connection failed: {str(e)}"
                    QTimer.singleShot(
                        0,
                        lambda msg=error_message: self._chat_widget.add_system_message(
                            msg
                        ),
                    )
            finally:
                loop.close()

        # Start initialization in background thread
        thread = threading.Thread(target=run_mcp_initialization, daemon=True)
        thread.start()

    def _handle_chat_message(self, message: str) -> None:
        """Handle messages from the chat widget and generate MCP responses with streaming."""
        if not self._mcp_coordinator:
            # If no MCP coordinator, show a simple message
            self._chat_widget.add_assistant_message(
                "MCP client is not available. Please check configuration."
            )
            return

        # Show thinking indicator
        self._chat_widget.show_ai_thinking(animated=True)

        # Start streaming MCP response asynchronously
        QTimer.singleShot(10, lambda: self._start_streaming_response(message))

    def _start_streaming_response(self, message: str) -> None:
        """Start the streaming MCP response."""

        # Create a new thread for the async operation
        def run_async_response():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Run the streaming response
                loop.run_until_complete(self._stream_mcp_response(message))
            except Exception as error:
                # Handle any errors - capture exception variable properly
                self.streaming_error_signal.emit(error)
            finally:
                loop.close()

        # Start the thread
        thread = threading.Thread(target=run_async_response, daemon=True)
        thread.start()

    async def _stream_mcp_response(self, message: str) -> None:
        """Generate streaming MCP response."""
        print(f"🚀 Starting MCP stream for message: '{message}'")

        # Add None check for MCP coordinator
        if not self._mcp_coordinator:
            print("❌ No MCP coordinator available")
            self.streaming_error_signal.emit(Exception("MCP coordinator not available"))
            return

        try:
            print("🔄 Hiding typing indicator and starting stream")
            # Hide thinking indicator and start streaming response
            QTimer.singleShot(0, lambda: self._chat_widget.hide_typing_indicator())

            # Generate a unique stream ID
            stream_id = str(uuid.uuid4())
            print(f"📝 Stream ID: {stream_id}")

            # Track response content
            response_content = ""
            message_started = False

            # Start streaming response
            self.start_streaming_signal.emit(stream_id)
            _message_started = True

            # Send message with streaming support
            print(f"📡 Sending message to MCP server. Message length: {len(message)}")

            async for chunk in self._mcp_coordinator.send_message_streaming(message):
                print(
                    f"🔍 Received chunk: content='{chunk.content}', complete={chunk.is_complete}"
                )

                # Accumulate response content
                if chunk.content:
                    response_content += chunk.content
                    self.append_chunk_signal.emit(chunk.content)

                # Check if streaming is complete
                if chunk.is_complete:
                    print("🏁 Streaming response complete")
                    self.complete_streaming_signal.emit()
                    break

            print(
                f"✅ MCP response completed. Total content length: {len(response_content)}"
            )

        except Exception as error:
            # Handle any unexpected errors
            print(f"❌ MCP streaming error: {error}")
            self.streaming_error_signal.emit(error)

    def _connect_streaming_signals(self) -> None:
        """Connect streaming signals between main window and chat widget."""
        if not self._chat_widget:
            return

        # Connect streaming signals
        self.start_streaming_signal.connect(self._chat_widget.start_streaming_response)
        self.append_chunk_signal.connect(self._chat_widget.append_streaming_chunk)
        self.complete_streaming_signal.connect(
            self._chat_widget.complete_streaming_response
        )
        self.streaming_error_signal.connect(self._chat_widget.handle_streaming_error)

        # Connect MCP tool call signals
        self.tool_call_started_signal.connect(self._chat_widget.start_tool_call)
        self.tool_call_completed_signal.connect(self._chat_widget.complete_tool_call)
        self.tool_call_failed_signal.connect(self._chat_widget.fail_tool_call)

        print("✅ MainWindow: All streaming signals connected")

    def _handle_streaming_error(self, error: Exception) -> None:
        """Handle streaming errors in the main thread."""
        # Hide any indicators and show error
        self._chat_widget.hide_typing_indicator()

        # If there's an active stream, handle the error through the streaming system
        if self._chat_widget.is_streaming():
            self._chat_widget.handle_streaming_error(error)
        else:
            # Fallback: add error message directly
            self._chat_widget.add_assistant_message(f"MCP Error: {str(error)}")

    def _new_chat(self) -> None:
        """Start a new chat conversation by clearing the current conversation."""
        if hasattr(self, "_chat_widget") and self._chat_widget is not None:
            # Reset streaming state if widget supports it
            if hasattr(self._chat_widget, "_is_streaming"):
                self._chat_widget._is_streaming = False

            # Clear the conversation
            self._chat_widget.clear_conversation()

            # Provide status feedback
            if hasattr(self, "_file_info_label"):
                self._file_info_label.setText("New chat started")

            # Also update the status bar with a temporary message
            status_bar = self.statusBar()
            if status_bar is not None:
                status_bar.showMessage(
                    "New chat conversation started", 3000
                )  # Show for 3 seconds


class MainWindow(QMainWindow):
    """
    Main application window for the Simple Code Viewer.

    This class inherits from QMainWindow and provides the main window
    structure including status bar, central widget, and proper sizing.
    """

    # Add custom signals for thread-safe communication
    start_streaming_signal = pyqtSignal(str)  # stream_id
    append_chunk_signal = pyqtSignal(str)  # chunk
    complete_streaming_signal = pyqtSignal()  # no args
    streaming_error_signal = pyqtSignal(Exception)  # error

    # MCP tool call signals for chat visualization
    tool_call_started_signal = pyqtSignal(dict)  # tool_call_data
    tool_call_completed_signal = pyqtSignal(dict)  # result_data
    tool_call_failed_signal = pyqtSignal(dict)  # error_data

    def __init__(self, directory_path: str) -> None:
        """Initialize the main window.

        Args:
            directory_path: Path to the directory to open
        """
        super().__init__()
        self.directory_path = directory_path

        # Initialize memory handler - moved to lazy initialization in _handle_chat_message
        # self._memory_handler will be created when first needed

        # Generate or restore session ID for conversation persistence
        self.current_session_id = self._get_or_create_session_id()

        # Initialize components
        app = QApplication.instance()
        if app is not None and isinstance(app, QApplication):
            self._theme_manager = ThemeManager(app)
        else:
            self._theme_manager = None

        self._ai_agent: AIAgent | None = None
        self._chat_widget: SimplifiedChatWidget | None = None

        # Initialize MCP coordinator
        self._mcp_coordinator: MCPClientCoordinator | None = None
        self._mcp_worker_thread: MCPWorkerThread | None = None

        # Set up the user interface
        self._setup_ui()

        # Set up persistent settings
        self._setup_settings()

        # Apply initial theme and window settings
        self._setup_window()

        # Set up AI integration
        self._setup_ai_integration()

        # Load conversation history if available
        self._load_conversation_history()

    def get_theme_manager(self) -> ThemeManager | None:
        """Get the theme manager instance.

        Returns:
            ThemeManager instance if available, None otherwise
        """
        return getattr(self, "_theme_manager", None)

    @property
    def file_tree(self) -> FileTreeWidget:
        """Get the file tree widget."""
        return self._file_tree

    @property
    def code_viewer(self) -> CodeViewerWidget:
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
        from ..gui.chat_widget_v2 import SimplifiedChatWidget as ChatWidget

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)  # Small margins

        self._chat_widget = ChatWidget()
        right_layout.addWidget(self._chat_widget)

        # Apply current theme to chat widget
        if hasattr(self, "_theme_manager"):
            current_theme = self._theme_manager.get_current_theme()
            self._chat_widget.apply_theme(current_theme)

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

        # Create New Chat action
        new_chat_action = QAction("&New Chat", self)
        new_chat_action.setObjectName("new_chat_action")
        new_chat_action.setShortcut(QKeySequence.StandardKey.New)  # Ctrl+N
        new_chat_action.setStatusTip("Start a new chat conversation")
        new_chat_action.setToolTip("Start a new chat conversation (Ctrl+N)")
        new_chat_action.triggered.connect(self._new_chat)
        file_menu.addAction(new_chat_action)

        # Add separator after New Chat
        file_menu.addSeparator()

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
        self._new_chat_action = new_chat_action
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

            # Set up MCP configuration for filesystem tools
            from pathlib import Path

            from .mcp_file_server import MCPFileConfig

            # Configure MCP for current workspace
            workspace_path = Path.cwd()
            mcp_config = MCPFileConfig(
                base_directory=workspace_path,
                allowed_extensions=[
                    ".py",
                    ".md",
                    ".txt",
                    ".json",
                    ".yaml",
                    ".yml",
                    ".toml",
                    ".cfg",
                    ".ini",
                ],
                enable_write_operations=True,
                enable_delete_operations=False,  # Safer to keep disabled
                max_file_size=5 * 1024 * 1024,  # 5MB limit
            )

            # Initialize AI agent with MCP support and memory awareness
            self._ai_agent = AIAgent(
                config=self._ai_config,
                mcp_config=mcp_config,
                enable_filesystem_tools=True,
                enable_memory_awareness=True,
                enable_mcp_tools=True,
                auto_discover_mcp_servers=True,
                signal_handler=self,  # Pass MainWindow as signal handler for MCP tool visualization
            )

            # Connect chat widget message_sent signal to our handler
            self._chat_widget.message_sent.connect(self._handle_chat_message)

            # Initialize worker thread as None
            self._ai_worker_thread = None

            # Show success message in chat
            available_tools = self._ai_agent.get_available_tools()
            if available_tools:
                tools_list = ", ".join(available_tools)
                self._chat_widget.add_system_message(
                    f"AI initialized with filesystem tools: {tools_list}"
                )
            else:
                self._chat_widget.add_system_message("AI initialized successfully")

            # Connect streaming signals now that chat widget is available
            self._connect_streaming_signals()

            # Schedule MCP server connections to happen after GUI initialization
            if self._ai_agent and self._ai_agent.mcp_tools_enabled:
                QTimer.singleShot(1000, self._initialize_mcp_servers)  # 1 second delay

        except Exception as e:
            # If AI initialization fails, show error in chat
            self._chat_widget.add_system_message(
                f"AI initialization failed: {str(e)}. Chat will work without AI responses."
            )
            self._ai_agent = None

    def _initialize_mcp_servers(self) -> None:
        """Initialize MCP servers asynchronously after GUI startup."""
        if not self._ai_agent or not self._ai_agent.mcp_tools_enabled:
            return

        def run_mcp_initialization():
            """Run MCP server initialization in a separate thread with event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                print("🔗 Initializing MCP servers...")
                # Connect to MCP servers using the startup method
                loop.run_until_complete(
                    self._ai_agent._connect_mcp_servers_on_startup()
                )
                print("✅ MCP servers initialized successfully")

                # Update chat widget with MCP tool availability
                if hasattr(self, "_chat_widget") and self._chat_widget:
                    available_tools = self._ai_agent.get_available_tools()
                    mcp_tools = [
                        tool
                        for tool in available_tools
                        if not tool.startswith(
                            (
                                "read_file",
                                "write_file",
                                "list_directory",
                                "create_directory",
                                "get_file_info",
                                "search_files",
                            )
                        )
                    ]
                    if mcp_tools:
                        QTimer.singleShot(
                            0,
                            lambda: self._chat_widget.add_system_message(
                                f"MCP tools are now available: {', '.join(mcp_tools)}"
                            ),
                        )

            except Exception as e:
                error_msg = f"❌ Failed to initialize MCP servers: {e}"
                print(error_msg)
                if hasattr(self, "_chat_widget") and self._chat_widget:
                    # Capture the error message in the lambda to avoid variable scope issues
                    error_message = f"MCP server initialization failed: {str(e)}"
                    QTimer.singleShot(
                        0,
                        lambda msg=error_message: self._chat_widget.add_system_message(
                            msg
                        ),
                    )
            finally:
                loop.close()

        # Start initialization in background thread
        thread = threading.Thread(target=run_mcp_initialization, daemon=True)
        thread.start()

    def _handle_chat_message(self, message: str) -> None:
        """Handle messages from the chat widget and generate AI responses with streaming."""
        if not self._ai_agent:
            # If no AI agent, show a simple echo response
            self._chat_widget.add_assistant_message(
                "AI is not available. Configuration required for responses."
            )
            return

        # Memory handling is now done by the AI agent's built-in memory system
        print(
            f"💾 Using AI agent's built-in memory system for message: '{message[:50]}...'"
        )

        # Show thinking indicator
        self._chat_widget.show_ai_thinking(animated=True)

        # Start streaming AI response asynchronously with conversation context
        QTimer.singleShot(
            10, lambda: self._start_streaming_response_with_context(message)
        )

    def _start_streaming_response_with_context(self, message: str) -> None:
        """Start the streaming AI response with conversation context."""

        # Create a new thread for the async operation
        def run_async_response():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Run the streaming response with context
                loop.run_until_complete(self._stream_ai_response_with_context(message))
            except Exception as error:
                # Handle any errors - capture exception variable properly
                self.streaming_error_signal.emit(error)
            finally:
                loop.close()

        # Start the thread
        thread = threading.Thread(target=run_async_response, daemon=True)
        thread.start()

    async def _stream_ai_response_with_context(self, message: str) -> None:
        """Generate streaming AI response with conversation context."""
        print(f"🚀 Starting stream with context for message: '{message}'")

        # Add None check for AI agent
        if not self._ai_agent:
            print("❌ No AI agent available")
            self.streaming_error_signal.emit(Exception("AI agent not available"))
            return

        try:
            print("🔄 Hiding typing indicator and starting stream")
            # Hide thinking indicator and start streaming response
            QTimer.singleShot(0, lambda: self._chat_widget.hide_typing_indicator())

            # Generate a unique stream ID
            stream_id = str(uuid.uuid4())
            print(f"📝 Stream ID: {stream_id}")

            # Note: We'll start the streaming response later, after reasoning appears
            # This ensures reasoning shows first, then assistant response follows

            # Track assistant response content for memory storage
            assistant_response_content = ""

            # Track streaming state
            assistant_message_started = False

            # Define streaming callbacks
            def on_chunk(chunk: str, is_final: bool) -> None:
                """Handle streaming chunks from AI response."""
                nonlocal assistant_response_content, assistant_message_started
                print(f"🔍 MainWindow callback: chunk='{chunk}', is_final={is_final}")

                # Accumulate assistant response content
                if chunk:
                    assistant_response_content += chunk

                # Start streaming response if not already started
                if chunk and not assistant_message_started:
                    assistant_message_started = True
                    print("🎯 MainWindow: Starting assistant streaming response now")
                    self.start_streaming_signal.emit(stream_id)
                    print("🎯 MainWindow: Emitted start_streaming_signal")

                # Emit chunks for the assistant response
                if chunk:
                    print("🎯 MainWindow: About to emit append_chunk_signal")
                    self.append_chunk_signal.emit(chunk)
                    print("🎯 MainWindow: Emitted append_chunk_signal")

                if is_final:
                    print("🏁 MainWindow: Completing streaming response")

                    # Memory storage is handled by the AI agent's memory system
                    print(
                        "💾 AI agent's memory system handles response storage automatically"
                    )

                    # Complete the streaming response
                    print("🎯 MainWindow: About to emit complete_streaming_signal")
                    self.complete_streaming_signal.emit()
                    print("🎯 MainWindow: Emitted complete_streaming_signal")

            def on_error(error: Exception) -> None:
                """Handle streaming errors."""
                print(f"❌ MainWindow callback: error={error}")
                self.streaming_error_signal.emit(error)

            # Send message with streaming support and reasoning callbacks
            print(
                f"📡 Calling AI agent memory-aware streaming. Message length: {len(message)}"
            )

            # Import QTimer for main thread signal emission
            # Start a timer to ensure assistant response starts even if no reasoning chunks come
            # This prevents the UI from hanging if there's no reasoning
            import asyncio

            async def ensure_response_starts():
                nonlocal assistant_message_started
                try:
                    await asyncio.sleep(
                        1.0
                    )  # Reduced to 1 second to prevent long hangs
                    if not assistant_message_started:
                        print(
                            "⏰ No response detected after 1s, starting assistant response"
                        )
                        self.start_streaming_signal.emit(stream_id)
                        assistant_message_started = True
                    else:
                        print("⏰ Assistant response already started, timer not needed")
                except asyncio.CancelledError:
                    print("⏰ Fallback timer was cancelled")

            # Start the fallback timer
            asyncio.create_task(ensure_response_starts())

            response = await self._ai_agent.send_memory_aware_message_stream(
                message=message,  # Use original message, not manually constructed context
                on_chunk=on_chunk,
                on_error=on_error,
                enable_filesystem=False,  # Disable filesystem tools to prevent fallback from MCP
            )
            print(
                f"✅ AI agent response: success={response.success}, content='{response.content}'"
            )

            # Check if response failed without calling callbacks
            if not response.success and response.error:
                print(f"❌ AI agent failed: {response.error}")
                self.streaming_error_signal.emit(Exception(response.error))

        except Exception as error:
            # Handle any unexpected errors - capture exception variable properly
            self.streaming_error_signal.emit(error)

    def _handle_streaming_error(self, error: Exception) -> None:
        """Handle streaming errors in the main thread."""
        # Hide any indicators and show error
        self._chat_widget.hide_typing_indicator()

        # If there's an active stream, handle the error through the streaming system
        if self._chat_widget.is_streaming():
            self._chat_widget.handle_streaming_error(error)
        else:
            # Fallback: add error message directly
            self._chat_widget.add_assistant_message(f"AI Error: {str(error)}")

    def _handle_ai_response(self, content: str, success: bool, error: str) -> None:
        """Handle AI response from worker thread - DEPRECATED: Now using streaming."""
        # This method is kept for compatibility but should not be used
        # with the new streaming implementation
        pass

    def _new_chat(self) -> None:
        """Start a new chat conversation by clearing the current conversation."""
        if hasattr(self, "_chat_widget") and self._chat_widget is not None:
            # Reset streaming state if widget supports it
            if hasattr(self._chat_widget, "_is_streaming"):
                self._chat_widget._is_streaming = False

            # Start a new memory session to properly separate conversations
            if (
                hasattr(self, "_ai_agent")
                and self._ai_agent
                and hasattr(self._ai_agent, "_memory_system")
                and self._ai_agent._memory_system
            ):
                try:
                    self._ai_agent._memory_system.start_new_session()
                    # Memory session started successfully
                except Exception as e:
                    print(f"Failed to start new memory session: {e}")
            else:
                print(
                    "💾 AI agent's memory system will handle new conversation context"
                )

            # Clear the conversation
            self._chat_widget.clear_conversation()

            # Provide status feedback
            if hasattr(self, "_file_info_label"):
                self._file_info_label.setText("New chat started")

            # Also update the status bar with a temporary message
            status_bar = self.statusBar()
            if status_bar is not None:
                status_bar.showMessage(
                    "New chat conversation started", 3000
                )  # Show for 3 seconds

    def _get_or_create_session_id(self) -> str:
        """Generate or restore session ID for conversation persistence."""
        # Implement logic to get or create a session ID
        # This is a placeholder and should be replaced with actual implementation
        return str(uuid.uuid4())

    def _load_conversation_history(self) -> None:
        """Load conversation history if available."""
        # Implement logic to load conversation history
        # This is a placeholder and should be replaced with actual implementation
        pass

    def _setup_mcp_integration(self) -> None:
        """Setup MCP (Model Context Protocol) integration."""
        try:
            # Create MCP coordinator configuration
            # Get server URL from environment or use default
            server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080")

            config = MCPCoordinatorConfig(
                server_url=server_url,
                timeout=30.0,
                enable_streaming=True,
                max_retries=3,
            )

            # Initialize MCP coordinator
            self._mcp_coordinator = MCPClientCoordinator(config)

            # Connect chat widget message_sent signal to our handler
            self._chat_widget.message_sent.connect(self._handle_chat_message)

            # Connect streaming signals
            self._connect_streaming_signals()

            # Show success message in chat
            self._chat_widget.add_system_message("MCP Client initialized successfully")

            # Schedule MCP server connection to happen after GUI initialization
            QTimer.singleShot(1000, self._initialize_mcp_connection)  # 1 second delay

        except Exception as e:
            # If MCP initialization fails, show error in chat
            self._chat_widget.add_system_message(
                f"MCP initialization failed: {str(e)}. Chat will work with limited functionality."
            )
            self._mcp_coordinator = None

    def _initialize_mcp_connection(self) -> None:
        """Initialize MCP connection after GUI startup."""
        if not self._mcp_coordinator:
            return

        # Create MCP worker thread
        self._mcp_worker_thread = MCPWorkerThread(
            self._mcp_coordinator, "Initial connection"
        )
        self._mcp_worker_thread.response_ready.connect(self._handle_mcp_response)
        self._mcp_worker_thread.start()

    def _handle_mcp_response(self, content: str, success: bool, error: str) -> None:
        """Handle MCP response from worker thread."""
        if success:
            self.update_file_info_display(f"MCP connection successful: {content}")
        else:
            self.update_file_info_display(f"MCP connection failed: {error}")
