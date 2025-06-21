"""Code Viewer Library.

A Qt-based code viewer application with integrated chat interface for
external agent integration. This library provides a clean interface for
viewing and navigating code files while maintaining a chat interface
that can connect to external agent architectures.

## Features

- **File Tree Navigation**: Browse and navigate through project files
- **Code Viewer**: Syntax-highlighted code display with line numbers
- **Chat Interface**: Integrated chat for agent communication
- **Theme Support**: Light and dark themes
- **External Agent Integration**: Connect to external agent architectures

## Quick Start

>>> from code_viewer import CodeViewer
    >>> viewer = CodeViewer()
    >>> viewer.show()

## Agent Integration

>>> from code_viewer.core.agent_integration import AgentBridge
    >>> bridge = AgentBridge()
>>> await bridge.initialize_connection()

## Configuration

The library supports configuration through environment variables
and configuration files. See the configuration module for details.

## Architecture

The code viewer is designed to work with external agent architectures:

```
┌─────────────────┐    ┌──────────────────┐
│   Code Viewer   │    │ Agent Architecture│
│   Library       │    │   Library         │
│                 │    │                   │
│ ┌─────────────┐ │    │ ┌───────────────┐ │
│ │ Chat Widget │◄┼────┼►│ Orchestrator  │ │
│ └─────────────┘ │    │ └───────────────┘ │
│ ┌─────────────┐ │    │ ┌───────────────┐ │
│ │ File Tree   │◄┼────┼►│ File Monitor  │ │
│ └─────────────┘ │    │ └───────────────┘ │
│ ┌─────────────┐ │    │ ┌───────────────┐ │
│ │ Code Viewer │◄┼────┼►│ Code Analysis │ │
│ └─────────────┘ │    │ └───────────────┘ │
└─────────────────┘    └──────────────────┘
```

## Version Information

>>> from code_viewer import get_version
>>> print(get_version())

## Package Information

>>> from code_viewer import get_info
>>> info = get_info()
>>> print(f"Code Viewer v{info['version']}")
"""

from __future__ import annotations

try:
    from ._version import __version__
except ImportError:
    # Version not available during development
    __version__ = "0.0.0+unknown"

__author__ = "Randy Herritt"
__email__ = "randy.herritt@gmail.com"
__license__ = "Proprietary"

# Import submodules
from . import core, gui

# Type checking imports removed - using external agent architecture

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "core",
    "gui",
    # Main components will be added as they're implemented
    # "CodeViewer",
    # "AIAgent",
]


def get_version() -> str:
    """Get the current version of My Coding Agent.

    Returns:
        The version string in semantic versioning format.

    Example:
        >>> from code_viewer import get_version
        >>> print(f"Version: {get_version()}")
        Version: 0.1.0
    """
    return __version__


def get_info() -> dict[str, str]:
    """Get comprehensive package information.

    Returns:
        A dictionary containing package metadata including version,
        author, license, and other relevant information.

    Example:
        >>> from code_viewer import get_info
        >>> info = get_info()
        >>> print(f"Author: {info['author']}")
        Author: Randy Herritt
    """
    return {
        "name": "code-viewer",
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "license": __license__,
        "description": "A modern code viewer with external agent integration",
        "python_requires": ">=3.8",
    }
