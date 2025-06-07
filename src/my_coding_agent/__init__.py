"""My Coding Agent - An epic code viewer with AI agent integration.

This package provides a modern, feature-rich code viewing application that combines
intuitive GUI design with powerful AI agent capabilities. Built with Python and
following the latest development best practices.

Key Features:
    * Modern GUI with syntax highlighting and line numbers
    * AI agent integration for enhanced productivity
    * Extensible plugin architecture
    * Type-safe codebase with comprehensive documentation
    * Performance optimized for large codebases

Example:
    Basic usage of the code viewer:

    >>> from my_coding_agent import CodeViewer
    >>> viewer = CodeViewer()
    >>> viewer.load_file("example.py")
    >>> viewer.show()

    With AI agent integration:

    >>> from my_coding_agent import CodeViewer, AIAgent
    >>> viewer = CodeViewer()
    >>> agent = AIAgent(api_key="your-api-key")
    >>> viewer.set_agent(agent)
    >>> viewer.load_file("complex_code.py")
    >>> agent.analyze_code()  # Get AI insights

Note:
    This package requires Python 3.8+ and PyQt6 for the GUI components.
    Optional AI features require valid API credentials.

Attributes:
    __version__ (str): The current version of the package.
    __author__ (str): Package author information.
    __email__ (str): Contact email for support.
"""

from typing import TYPE_CHECKING

try:
    from ._version import __version__
except ImportError:
    # Version not available during development
    __version__ = "0.0.0+unknown"

__author__ = "Randy Herritt"
__email__ = "randy.herritt@gmail.com"
__license__ = "Proprietary"

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from .core.viewer import CodeViewer
    from .agents.base import AIAgent

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    # Main components will be added as they're implemented
    # "CodeViewer", 
    # "AIAgent",
]


def get_version() -> str:
    """Get the current version of My Coding Agent.
    
    Returns:
        The version string in semantic versioning format.
        
    Example:
        >>> from my_coding_agent import get_version
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
        >>> from my_coding_agent import get_info
        >>> info = get_info()
        >>> print(f"Author: {info['author']}")
        Author: Randy Herritt
    """
    return {
        "name": "my-coding-agent",
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "license": __license__,
        "description": "An epic code viewer with AI agent integration",
        "python_requires": ">=3.8",
    } 