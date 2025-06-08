"""Main entry point for My Coding Agent.

This module provides the main entry point for running the application
using 'python -m my_coding_agent' command. It handles command-line
arguments, initializes the application, and starts the GUI.

Example:
    Run the application:
        $ python -m my_coding_agent

    Show help:
        $ python -m my_coding_agent --help

    Open with specific directory:
        $ python -m my_coding_agent /path/to/code
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from .config.settings import Settings, get_settings


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser.

    Returns:
        Configured ArgumentParser instance with all supported options
    """
    parser = argparse.ArgumentParser(
        prog="my_coding_agent",
        description="A modern Python-based simple code viewer with syntax highlighting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Start with current directory
  %(prog)s /path/to/project         # Start with specific directory
  %(prog)s --theme light            # Start with light theme
  %(prog)s --font-size 14           # Start with larger font
        """,
    )

    # Positional arguments
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="Directory to open (default: current directory)",
    )

    # Theme options
    parser.add_argument(
        "--theme",
        choices=["dark", "light"],
        help="UI theme to use (default: from settings)",
    )

    # Font options
    parser.add_argument(
        "--font-family", help="Font family for code display (default: from settings)"
    )

    parser.add_argument(
        "--font-size",
        type=int,
        help="Font size for code display (default: from settings)",
    )

    # Window options
    parser.add_argument(
        "--window-size",
        metavar="WIDTHxHEIGHT",
        help="Initial window size, e.g., 1200x800",
    )

    # Debug options
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with verbose logging"
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {_get_version()}"
    )

    return parser


def _get_version() -> str:
    """Get the application version.

    Returns:
        Version string from package metadata or fallback
    """
    try:
        from importlib.metadata import version

        return version("my_coding_agent")
    except Exception:
        return "0.1.0-dev"


def _parse_window_size(size_str: str) -> Tuple[int, int]:
    """Parse window size string into width and height.

    Args:
        size_str: Size string in format "WIDTHxHEIGHT"

    Returns:
        Tuple of (width, height) in pixels

    Raises:
        ValueError: If size string format is invalid
    """
    try:
        width_str, height_str = size_str.lower().split("x")
        width = int(width_str)
        height = int(height_str)

        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")

        return width, height
    except ValueError as e:
        raise ValueError(
            f"Invalid window size format '{size_str}'. Use format like '1200x800'"
        ) from e


def configure_settings_from_args(args: argparse.Namespace) -> Settings:
    """Configure application settings based on command-line arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        Settings instance with argument overrides applied
    """
    settings = get_settings()

    # Apply theme override
    if args.theme:
        settings.theme = args.theme

    # Apply font overrides
    if args.font_family:
        settings.font_family = args.font_family

    if args.font_size:
        settings.font_size = args.font_size

    # Apply window size override
    if args.window_size:
        try:
            width, height = _parse_window_size(args.window_size)
            settings.window_width = width
            settings.window_height = height
        except ValueError as e:
            print(f"Warning: {e}", file=sys.stderr)

    return settings


def validate_directory(directory: Path) -> Path:
    """Validate that the specified directory exists and is accessible.

    Args:
        directory: Directory path to validate

    Returns:
        Resolved absolute path to the directory

    Raises:
        SystemExit: If directory is invalid or inaccessible
    """
    try:
        resolved_dir = directory.resolve()

        if not resolved_dir.exists():
            print(f"Error: Directory does not exist: {directory}", file=sys.stderr)
            sys.exit(1)

        if not resolved_dir.is_dir():
            print(f"Error: Path is not a directory: {directory}", file=sys.stderr)
            sys.exit(1)

        # Test if directory is readable
        try:
            list(resolved_dir.iterdir())
        except PermissionError:
            print(
                f"Error: Permission denied accessing directory: {directory}",
                file=sys.stderr,
            )
            sys.exit(1)

        return resolved_dir

    except Exception as e:
        print(f"Error: Cannot access directory {directory}: {e}", file=sys.stderr)
        sys.exit(1)


def setup_debug_logging(debug: bool) -> None:
    """Set up debug logging if requested.

    Args:
        debug: Whether to enable debug logging
    """
    if debug:
        import logging

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logging.getLogger("my_coding_agent").debug("Debug mode enabled")


def main(argv: Optional[List[str]] = None) -> None:
    """Main entry point for the application.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    This function:
    1. Parses command-line arguments
    2. Validates input directory
    3. Configures application settings
    4. Initializes and starts the GUI application
    """
    # Parse command-line arguments
    parser = create_argument_parser()
    args = parser.parse_args(argv)

    # Set up debug logging if requested
    setup_debug_logging(args.debug)

    # Validate directory
    directory = validate_directory(args.directory)

    # Configure settings from arguments
    settings = configure_settings_from_args(args)

    # Import GUI components
    from PyQt6.QtWidgets import QApplication

    from .core.main_window import MainWindow

    # Create QApplication
    app = QApplication(sys.argv)

    # Print configuration info
    print("My Coding Agent - Simple Code Viewer")
    print(f"Opening directory: {directory}")
    print(f"Theme: {settings.theme}")
    print(f"Font: {settings.font_family} {settings.font_size}pt")
    print(f"Window size: {settings.window_width}x{settings.window_height}")
    print(f"Configuration: {settings.config_dir}")
    print("Starting GUI...")

    # Create and show the main window
    main_window = MainWindow()

    # Apply settings to window
    if hasattr(settings, "window_width") and hasattr(settings, "window_height"):
        main_window.resize(settings.window_width, settings.window_height)

    main_window.show()

    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
