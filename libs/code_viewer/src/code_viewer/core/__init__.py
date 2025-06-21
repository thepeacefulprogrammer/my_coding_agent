"""Core functionality for the Code Viewer application.

This module contains the core components that power the code viewer:
- File tree navigation
- Code viewing and syntax highlighting
- Theme management
- MCP client integration
- Agent integration bridge

## Main Components

- **MainWindow**: Primary application window
- **CodeViewerWidget**: Code display with syntax highlighting
- **FileTreeWidget**: File navigation tree
- **ThemeManager**: Theme switching and management

## Usage

>>> from code_viewer.core import MainWindow
>>> window = MainWindow()
>>> window.show()

## Code Viewer

For standalone code viewing:

```python
from code_viewer.core.code_viewer import CodeViewerWidget

viewer = CodeViewerWidget()
viewer.load_file("example.py")
viewer.show()
```

## File Tree

For file navigation:

```python
from code_viewer.core.file_tree import FileTreeWidget

tree = FileTreeWidget()
tree.set_root_path("/path/to/project")
tree.show()
```
"""

from __future__ import annotations

from .code_viewer import CodeViewerWidget
from .file_tree import FileTreeModel, FileTreeWidget

# Import core components
from .main_window import MainWindow
from .theme_manager import ThemeManager

__all__ = [
    "MainWindow",
    "CodeViewerWidget",
    "FileTreeWidget",
    "FileTreeModel",
    "ThemeManager",
]
