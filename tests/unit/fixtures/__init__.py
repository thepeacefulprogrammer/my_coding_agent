"""Test fixtures package for My Coding Agent.

This package contains pytest fixtures for testing various components
of the application, including GUI components, file system mocks,
and sample data.
"""

from __future__ import annotations

# Import commonly used fixtures for easy access
try:
    from .gui_fixtures import (
        process_qt_events,
        qapp_instance,
        qmainwindow,
        qsplitter,
        qtextedit,
        qtreeview,
        qwidget,
        wait_for_signal,
    )

    __all__ = [
        "qapp_instance",
        "qwidget",
        "qtreeview",
        "qtextedit",
        "qmainwindow",
        "qsplitter",
        "process_qt_events",
        "wait_for_signal",
    ]

except ImportError:
    # GUI fixtures not available (e.g., PyQt6 not installed)
    __all__ = []
