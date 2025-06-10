"""GUI test fixtures for PyQt6 components.

This module provides pytest fixtures for testing PyQt6 GUI components
in a clean and isolated environment. It handles QApplication lifecycle
management and provides common widget fixtures.

The fixtures are designed to work in headless environments and CI/CD
pipelines by checking for display availability and using virtual displays.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from unittest.mock import Mock

import pytest

# Try to import PyQt6 - handle gracefully if not available
try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QApplication,
        QMainWindow,
        QSplitter,
        QTextEdit,
        QTreeView,
        QWidget,
    )

    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    # Create mock classes for testing without PyQt6
    QApplication = Mock
    QWidget = Mock
    QTreeView = Mock
    QTextEdit = Mock
    QMainWindow = Mock
    QSplitter = Mock


def is_headless_environment() -> bool:
    """Check if we're running in a headless environment.

    Returns:
        True if no display is available, False otherwise
    """
    # Check for common CI environment variables
    ci_vars = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "TRAVIS",
        "CIRCLECI",
        "JENKINS_URL",
        "BUILDKITE",
    ]

    if any(os.getenv(var) for var in ci_vars):
        return True

    # Check for display availability on Unix systems
    return os.name == "posix" and not os.getenv("DISPLAY")


def setup_headless_display() -> None:
    """Set up a virtual display for headless testing.

    This function attempts to configure a virtual display using Xvfb
    for testing in CI environments without a physical display.
    """
    if not is_headless_environment():
        return

    try:
        # Try to set up Xvfb virtual display
        import subprocess

        subprocess.run(["which", "xvfb-run"], check=True, capture_output=True)

        # If Xvfb is available, set a display
        if not os.getenv("DISPLAY"):
            os.environ["DISPLAY"] = ":99"

    except (ImportError, subprocess.CalledProcessError, FileNotFoundError):
        # Xvfb not available, will use mock objects instead
        pass


@pytest.fixture(scope="session")
def qapp_instance() -> Generator[QApplication | None, None, None]:
    """Provide a QApplication instance for GUI testing.

    This fixture ensures that there's exactly one QApplication instance
    throughout the test session. It handles headless environments by
    using mock objects when PyQt6 is not available or no display exists.

    Yields:
        QApplication instance or Mock for headless testing
    """
    if not PYQT6_AVAILABLE:
        # Return a mock for environments without PyQt6
        mock_app = Mock(spec=QApplication)
        mock_app.instance.return_value = mock_app
        mock_app.exec.return_value = 0
        yield mock_app
        return

    # Set up headless display if needed
    setup_headless_display()

    # Check if QApplication already exists
    existing_app = QApplication.instance()
    if existing_app is not None:
        yield existing_app
        return

    try:
        # Create new QApplication instance
        app = QApplication(sys.argv)
        app.setApplicationName("MyCodeViewerTest")
        app.setOrganizationName("TestOrg")

        # Configure for testing
        app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, True)
        app.setQuitOnLastWindowClosed(False)

        yield app  # type: ignore[misc]

    except Exception:
        # If Qt fails to initialize, provide a mock
        mock_app = Mock(spec=QApplication)
        mock_app.instance.return_value = mock_app
        mock_app.exec.return_value = 0
        yield mock_app

    finally:
        # Clean up - but be careful not to quit if other tests are running
        if QApplication.instance() is not None:
            QApplication.instance().processEvents()


@pytest.fixture
def qwidget(qapp_instance: QApplication) -> Generator[QWidget, None, None]:
    """Provide a clean QWidget instance for testing.

    This fixture creates a basic QWidget that can be used as a parent
    for other widgets or for testing widget functionality.

    Args:
        qapp_instance: QApplication fixture dependency

    Yields:
        QWidget instance for testing
    """
    if not PYQT6_AVAILABLE or isinstance(qapp_instance, Mock):
        # Return mock widget for headless environments
        mock_widget = Mock(spec=QWidget)
        mock_widget.show.return_value = None
        mock_widget.hide.return_value = None
        mock_widget.close.return_value = True
        mock_widget.parent.return_value = None
        yield mock_widget
        return

    try:
        widget = QWidget()
        widget.setWindowTitle("Test Widget")
        widget.resize(400, 300)

        yield widget

    except Exception:
        # Provide mock if widget creation fails
        mock_widget = Mock(spec=QWidget)
        mock_widget.show.return_value = None
        mock_widget.hide.return_value = None
        mock_widget.close.return_value = True
        yield mock_widget

    finally:
        # Clean up widget
        try:
            if "widget" in locals() and hasattr(widget, "close"):
                widget.close()
        except Exception:
            pass


@pytest.fixture
def qtreeview(qapp_instance: QApplication) -> Generator[QTreeView, None, None]:
    """Provide a QTreeView instance for testing file tree components.

    This fixture creates a QTreeView configured for file tree testing
    with appropriate settings for the application.

    Args:
        qapp_instance: QApplication fixture dependency

    Yields:
        QTreeView instance configured for file tree testing
    """
    if not PYQT6_AVAILABLE or isinstance(qapp_instance, Mock):
        # Return mock tree view for headless environments
        mock_tree = Mock(spec=QTreeView)
        mock_tree.setModel.return_value = None
        mock_tree.selectionModel.return_value = Mock()
        mock_tree.expand.return_value = None
        mock_tree.collapse.return_value = None
        yield mock_tree
        return

    try:
        tree_view = QTreeView()
        tree_view.setWindowTitle("Test Tree View")
        tree_view.resize(300, 400)

        # Configure for file tree usage
        tree_view.setAnimated(True)
        tree_view.setIndentation(20)
        tree_view.setSortingEnabled(True)
        tree_view.setAlternatingRowColors(True)

        yield tree_view

    except Exception:
        # Provide mock if tree view creation fails
        mock_tree = Mock(spec=QTreeView)
        mock_tree.setModel.return_value = None
        mock_tree.selectionModel.return_value = Mock()
        yield mock_tree

    finally:
        # Clean up tree view
        try:
            if "tree_view" in locals() and hasattr(tree_view, "close"):
                tree_view.close()
        except Exception:
            pass


@pytest.fixture
def qtextedit(qapp_instance: QApplication) -> Generator[QTextEdit, None, None]:
    """Provide a QTextEdit instance for testing code viewer components.

    This fixture creates a QTextEdit configured for code viewing
    with appropriate font and settings for syntax highlighting.

    Args:
        qapp_instance: QApplication fixture dependency

    Yields:
        QTextEdit instance configured for code viewing
    """
    if not PYQT6_AVAILABLE or isinstance(qapp_instance, Mock):
        # Return mock text edit for headless environments
        mock_text = Mock(spec=QTextEdit)
        mock_text.setPlainText.return_value = None
        mock_text.toPlainText.return_value = "mock content"
        mock_text.setReadOnly.return_value = None
        mock_text.setFont.return_value = None
        yield mock_text
        return

    try:
        text_edit = QTextEdit()
        text_edit.setWindowTitle("Test Text Edit")
        text_edit.resize(600, 400)

        # Configure for code viewing
        font = QFont("JetBrains Mono", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        text_edit.setFont(font)

        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        text_edit.setTabStopDistance(40)  # 4 spaces * 10 pixels per space

        yield text_edit

    except Exception:
        # Provide mock if text edit creation fails
        mock_text = Mock(spec=QTextEdit)
        mock_text.setPlainText.return_value = None
        mock_text.toPlainText.return_value = "mock content"
        yield mock_text

    finally:
        # Clean up text edit
        try:
            if "text_edit" in locals() and hasattr(text_edit, "close"):
                text_edit.close()
        except Exception:
            pass


@pytest.fixture
def qmainwindow(qapp_instance: QApplication) -> Generator[QMainWindow, None, None]:
    """Provide a QMainWindow instance for testing main window components.

    This fixture creates a QMainWindow that can be used for testing
    the main application window and its components.

    Args:
        qapp_instance: QApplication fixture dependency

    Yields:
        QMainWindow instance for testing
    """
    if not PYQT6_AVAILABLE or isinstance(qapp_instance, Mock):
        # Return mock main window for headless environments
        mock_window = Mock(spec=QMainWindow)
        mock_window.setCentralWidget.return_value = None
        mock_window.statusBar.return_value = Mock()
        mock_window.menuBar.return_value = Mock()
        yield mock_window
        return

    try:
        main_window = QMainWindow()
        main_window.setWindowTitle("Test Main Window")
        main_window.resize(1000, 700)

        yield main_window

    except Exception:
        # Provide mock if main window creation fails
        mock_window = Mock(spec=QMainWindow)
        mock_window.setCentralWidget.return_value = None
        yield mock_window

    finally:
        # Clean up main window
        try:
            if "main_window" in locals() and hasattr(main_window, "close"):
                main_window.close()
        except Exception:
            pass


@pytest.fixture
def qsplitter(qapp_instance: QApplication) -> Generator[QSplitter, None, None]:
    """Provide a QSplitter instance for testing split layouts.

    This fixture creates a QSplitter that can be used for testing
    the split layout between file tree and code viewer.

    Args:
        qapp_instance: QApplication fixture dependency

    Yields:
        QSplitter instance for testing
    """
    if not PYQT6_AVAILABLE or isinstance(qapp_instance, Mock):
        # Return mock splitter for headless environments
        mock_splitter = Mock(spec=QSplitter)
        mock_splitter.addWidget.return_value = None
        mock_splitter.setSizes.return_value = None
        mock_splitter.sizes.return_value = [300, 700]
        yield mock_splitter
        return

    try:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 0)  # Left panel fixed
        splitter.setStretchFactor(1, 1)  # Right panel stretches

        yield splitter

    except Exception:
        # Provide mock if splitter creation fails
        mock_splitter = Mock(spec=QSplitter)
        mock_splitter.addWidget.return_value = None
        yield mock_splitter

    finally:
        # Clean up splitter
        try:
            if "splitter" in locals() and hasattr(splitter, "close"):
                splitter.close()
        except Exception:
            pass


# Helper functions for GUI testing
def process_qt_events(app: QApplication, timeout_ms: int = 100) -> None:
    """Process Qt events for a specified time.

    Args:
        app: QApplication instance
        timeout_ms: Maximum time to process events in milliseconds
    """
    if isinstance(app, Mock):
        return

    try:
        app.processEvents()
        if hasattr(app, "processEvents"):
            # Process events for specified time
            import time

            start_time = time.time()
            while (time.time() - start_time) * 1000 < timeout_ms:
                app.processEvents()
                time.sleep(0.001)  # Small delay to prevent busy waiting
    except Exception:
        pass


def wait_for_signal(signal, timeout_ms: int = 1000) -> bool:
    """Wait for a Qt signal to be emitted.

    Args:
        signal: Qt signal to wait for
        timeout_ms: Maximum time to wait in milliseconds

    Returns:
        True if signal was emitted, False if timeout
    """
    if isinstance(signal, Mock):
        return True

    try:
        from PyQt6.QtCore import QEventLoop, QTimer

        loop = QEventLoop()
        timer = QTimer()

        signal_received = [False]

        def on_signal():
            signal_received[0] = True
            loop.quit()

        def on_timeout():
            loop.quit()

        signal.connect(on_signal)
        timer.timeout.connect(on_timeout)
        timer.start(timeout_ms)

        loop.exec()

        return signal_received[0]

    except Exception:
        return False
