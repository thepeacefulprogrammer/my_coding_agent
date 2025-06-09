"""
File tree navigation components for the Simple Code Viewer.

This module provides the file tree model and widget for directory navigation
using PyQt6's QFileSystemModel as the foundation.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

import qtawesome as qta
from PyQt6.QtCore import QDir, QModelIndex, QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFileSystemModel, QIcon, QPainter
from PyQt6.QtWidgets import QMenu, QTreeView


class FileTreeModel(QFileSystemModel):
    """
    Custom file tree model based on QFileSystemModel.

    This model provides file system navigation with filtering for code files
    and directories. It extends QFileSystemModel to add custom behavior
    for code viewing applications.
    """

    def __init__(self, parent: Optional[Any] = None) -> None:
        """
        Initialize the FileTreeModel.

        Args:
            parent: Parent object for the model
        """
        super().__init__(parent)
        self._setup_model()
        self._load_icons()

    def _setup_model(self) -> None:
        """Set up the file system model with appropriate filters and settings."""
        # Set filters to show directories and files
        self.setFilter(
            QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.Hidden
        )

        # Note: Sorting is handled by the view, not the model directly

        # Make the model read-only (for safety)
        self.setReadOnly(True)

        # Set the root path to the current directory by default
        self.setRootPath(str(Path.cwd()))

    def _load_icons(self) -> None:
        """Load file type icons from the assets directory."""
        self._icons = {}

        # Base path for icons
        base_path = Path(__file__).parent.parent / "assets" / "icons" / "file_types"

        # Load icons for different file types
        icon_mapping = {
            "folder": "folder.png",
            "folder_open": "folder_open.png",
            "python": "python.png",
            "javascript": "javascript.png",
            "json": "json.png",
            "text": "text.png",
            "file": "file.png",  # Default file icon
        }

        for icon_type, filename in icon_mapping.items():
            icon_path = base_path / filename
            if icon_path.exists():
                self._icons[icon_type] = QIcon(str(icon_path))
            else:
                # Create empty icon as fallback
                self._icons[icon_type] = QIcon()

    def _get_file_icon(self, index: QModelIndex) -> QIcon:
        """Get the appropriate icon for a file or directory."""
        if not index.isValid():
            return QIcon()

        if self.is_directory(index):
            return self._icons.get("folder", QIcon())

        # Get file extension to determine icon
        file_path = self.get_file_path(index)
        if not file_path:
            return self._icons.get("file", QIcon())

        ext = file_path.suffix.lower()

        # Map extensions to icon types
        if ext in [".py", ".pyw"]:
            return self._icons.get("python", QIcon())
        elif ext in [".js", ".jsx", ".ts", ".tsx"]:
            return self._icons.get("javascript", QIcon())
        elif ext == ".json":
            return self._icons.get("json", QIcon())
        elif ext in [".txt", ".md", ".cfg", ".ini"]:
            return self._icons.get("text", QIcon())
        else:
            return self._icons.get("file", QIcon())

    def set_root_directory(self, directory_path: Path) -> QModelIndex:
        """
        Set the root directory for the file tree.

        Args:
            directory_path: Path to the directory to use as root

        Returns:
            QModelIndex for the root directory

        Raises:
            ValueError: If the path doesn't exist or isn't a directory
            PermissionError: If the directory is not accessible
        """
        try:
            # Resolve the path to handle symlinks and relative paths
            resolved_path = directory_path.resolve()

            # Check if path exists (this will fail for broken symlinks)
            if not resolved_path.exists():
                raise ValueError(f"Directory does not exist: {directory_path}")

            # Check if it's a directory
            if not resolved_path.is_dir():
                raise ValueError(f"Path is not a directory: {directory_path}")

            # Test if directory is readable
            try:
                # Try to list directory contents to check read permissions
                list(resolved_path.iterdir())
            except PermissionError as e:
                raise PermissionError(
                    f"Permission denied accessing directory: {directory_path}"
                ) from e

            # Set the root path and return the index
            root_index = self.setRootPath(str(resolved_path))
            return root_index

        except OSError as e:
            # Handle other OS-level errors (network issues, etc.)
            raise ValueError(f"Cannot access directory {directory_path}: {e}") from e

    def get_file_path(self, index: QModelIndex) -> Optional[Path]:
        """
        Get the file path for a given model index.

        Args:
            index: QModelIndex to get the path for

        Returns:
            Path object for the file/directory, or None if invalid
        """
        if not index.isValid():
            return None

        try:
            file_path = self.filePath(index)
            if not file_path:
                return None

            # Create Path object and handle potential encoding issues
            path_obj = Path(file_path)

            # Validate the path exists (this may fail for broken symlinks or permission issues)
            # We don't raise exceptions here to allow the UI to show broken symlinks
            return path_obj

        except (OSError, UnicodeDecodeError, ValueError):
            # Handle file path encoding issues or OS errors
            # Return None to indicate the path is invalid
            return None

    def is_directory(self, index: QModelIndex) -> bool:
        """
        Check if the given index represents a directory.

        Args:
            index: QModelIndex to check

        Returns:
            True if the index represents a directory, False otherwise
        """
        if not index.isValid():
            return False

        return self.isDir(index)

    def is_code_file(self, index: QModelIndex) -> bool:
        """
        Check if the given index represents a code file.

        Args:
            index: QModelIndex to check

        Returns:
            True if the index represents a code file, False otherwise
        """
        if not index.isValid() or self.is_directory(index):
            return False

        file_path = self.get_file_path(index)
        if not file_path:
            return False

        # Define supported code file extensions
        code_extensions = {
            ".py",
            ".pyw",  # Python
            ".js",
            ".jsx",
            ".ts",
            ".tsx",  # JavaScript/TypeScript
            ".html",
            ".htm",
            ".css",  # Web
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".hpp",  # Other languages
            ".cs",
            ".php",
            ".rb",
            ".go",  # More languages
            ".rs",
            ".swift",
            ".kt",  # Modern languages
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",  # Config files
            ".md",
            ".txt",
            ".log",  # Text files
        }

        ext = file_path.suffix.lower()
        return ext in code_extensions

    def get_file_info(self, index: QModelIndex) -> "Dict[str, Any]":
        """
        Get detailed information about a file or directory.

        Args:
            index: QModelIndex for the item

        Returns:
            Dictionary containing file information
        """
        if not index.isValid():
            return {}

        info = {
            "name": self.fileName(index),
            "path": self.get_file_path(index),
            "is_directory": self.is_directory(index),
            "size": self.size(index),
            "last_modified": self.lastModified(index),
            "type": self.type(index),
        }

        # Add file size in human-readable format for files
        if not info["is_directory"]:
            size_bytes = info["size"]
            if isinstance(size_bytes, int):
                if size_bytes < 1024:
                    info["size_human"] = f"{size_bytes} B"
                else:
                    info["size_human"] = f"{size_bytes / 1024:.1f} KB"
            else:
                info["size_human"] = "Unknown"
        else:
            info["size_human"] = ""

        return info

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Override data method to customize display behavior.

        Args:
            index: QModelIndex for the item
            role: Item data role

        Returns:
            Data for the specified role
        """
        # For display role, we might want to customize the display text
        if role == Qt.ItemDataRole.DisplayRole:
            return super().data(index, role)

        # For tooltip role, provide file information
        elif role == Qt.ItemDataRole.ToolTipRole:
            file_info = self.get_file_info(index)
            if file_info:
                if file_info["is_directory"]:
                    return f"Directory: {file_info['name']}"
                else:
                    return (
                        f"File: {file_info['name']}\n"
                        f"Size: {file_info['size_human']}\n"
                        f"Modified: {file_info['last_modified'].toString()}"
                    )

        # For decoration role, provide file type icons
        elif role == Qt.ItemDataRole.DecorationRole:
            return self._get_file_icon(index)

        # For all other roles, use parent implementation
        return super().data(index, role)


class FileTreeWidget(QTreeView):
    """
    Custom file tree widget based on QTreeView.

    This widget provides a user interface for the FileTreeModel,
    allowing users to navigate directories and select files.
    """

    # Define signals for file operations
    file_selected = pyqtSignal(Path)  # Emitted when a file is selected
    file_opened = pyqtSignal(Path)  # Emitted when a file should be opened

    def __init__(self, parent: Optional[Any] = None) -> None:
        """
        Initialize the FileTreeWidget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_widget()
        self._connect_signals()

    def _setup_widget(self) -> None:
        """Set up the tree view with appropriate settings."""
        # Create and set the model
        self._model = FileTreeModel(self)
        self.setModel(self._model)

        # Configure the view
        self.setRootIndex(self._model.index(str(Path.cwd())))
        self.setHeaderHidden(False)  # Show column headers
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)  # Sort by name

        # Set selection behavior
        self.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)

        # Enable drag and drop (for future enhancements)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)

        # Hide some columns by default (can be shown via context menu later)
        self.hideColumn(1)  # Size column
        self.hideColumn(2)  # Type column
        self.hideColumn(3)  # Date modified column

        # Enable custom context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Set up Font Awesome expansion icons
        self._setup_expansion_icons()

    def _setup_expansion_icons(self) -> None:
        """Set up Font Awesome icons for folder expansion indicators."""
        try:
            # Get theme-appropriate color for icons
            # Use a mid-gray that works well in both light and dark themes
            icon_color = "#666666"  # Neutral gray that works in both themes

            # Create Font Awesome icons for expansion indicators
            self._collapsed_icon = qta.icon("fa6s.chevron-right", color=icon_color)
            self._expanded_icon = qta.icon("fa6s.chevron-down", color=icon_color)

        except Exception as e:
            # Fallback if Font Awesome fails to load
            print(f"Warning: Could not load Font Awesome icons: {e}")
            self._collapsed_icon = None
            self._expanded_icon = None

    def _connect_signals(self) -> None:
        """Connect internal signals to handle file selection and opening."""
        # Connect selection changed signal
        selection_model = self.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)

        # Connect double-click signal
        self.doubleClicked.connect(self._on_double_clicked)

        # Connect context menu signal
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _on_selection_changed(self, selected, deselected) -> None:
        """
        Handle selection changes in the tree view.

        Args:
            selected: Newly selected items
            deselected: Previously selected items
        """
        current_index = self.currentIndex()
        if not current_index.isValid():
            return

        # Only emit signal for files, not directories
        if not self._model.is_directory(current_index):
            file_path = self._model.get_file_path(current_index)
            if file_path:
                self.file_selected.emit(file_path)

    def _on_double_clicked(self, index: QModelIndex) -> None:
        """
        Handle double-click events on tree items.

        Args:
            index: The model index that was double-clicked
        """
        if not index.isValid():
            return

        # For directories, toggle expansion
        if self._model.is_directory(index):
            if self.isExpanded(index):
                self.collapse(index)
            else:
                self.expand(index)
        else:
            # For files, emit file_opened signal if it's a viewable file
            file_path = self._model.get_file_path(index)
            if file_path and self._is_viewable_file(file_path):
                self.file_opened.emit(file_path)

    def _is_viewable_file(self, file_path: Path) -> bool:
        """
        Check if a file is viewable (text-based, not binary).

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file can be viewed in a text editor
        """
        try:
            # First, check if the file exists (handles broken symlinks)
            if not file_path.exists():
                return False

            # Check if it's actually a file (not a directory)
            if not file_path.is_file():
                return False

            # Check file size - don't try to open very large files
            try:
                file_size = file_path.stat().st_size
                # Skip files larger than 10MB for performance
                if file_size > 10 * 1024 * 1024:
                    return False
            except (OSError, PermissionError):
                # If we can't get file stats, assume it's not viewable
                return False

            # Define viewable file extensions
            viewable_extensions = {
                # Code files
                ".py",
                ".pyw",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".html",
                ".htm",
                ".css",
                ".scss",
                ".sass",
                ".less",
                ".java",
                ".c",
                ".cpp",
                ".cxx",
                ".cc",
                ".h",
                ".hpp",
                ".hxx",
                ".cs",
                ".php",
                ".rb",
                ".go",
                ".rs",
                ".swift",
                ".kt",
                ".scala",
                ".clj",
                ".hs",
                ".ml",
                ".elm",
                ".dart",
                # Configuration and data files
                ".json",
                ".xml",
                ".yaml",
                ".yml",
                ".toml",
                ".ini",
                ".cfg",
                ".conf",
                ".properties",
                ".env",
                # Documentation and text files
                ".txt",
                ".md",
                ".rst",
                ".tex",
                ".rtf",
                # Shell and script files
                ".sh",
                ".bash",
                ".zsh",
                ".fish",
                ".ps1",
                ".bat",
                ".cmd",
                # Logs and other text files
                ".log",
                ".out",
                ".err",
            }

            # Check by file extension first
            ext = file_path.suffix.lower()
            if ext in viewable_extensions:
                return True

            # Files without extensions that are commonly viewable
            viewable_names = {
                "makefile",
                "dockerfile",
                "readme",
                "changelog",
                "license",
                "authors",
                "contributors",
                "copying",
                "install",
                "news",
            }

            if file_path.name.lower() in viewable_names:
                return True

            # Simple binary file detection by checking for null bytes and common binary signatures
            try:
                with file_path.open("rb") as f:
                    # Read first 1024 bytes to check for binary content
                    chunk = f.read(1024)
                    if not chunk:
                        return True  # Empty file is viewable

                    # Check for common binary file signatures
                    binary_signatures = [
                        b"\x89PNG",  # PNG
                        b"\xff\xd8\xff",  # JPEG
                        b"GIF8",  # GIF
                        b"PK\x03\x04",  # ZIP
                        b"PK\x05\x06",  # ZIP empty
                        b"\x7fELF",  # ELF executable
                        b"MZ",  # Windows executable
                        b"\xca\xfe\xba\xbe",  # Java class file
                        b"\xfe\xed\xfa\xce",  # Mach-O binary (macOS)
                        b"\xfe\xed\xfa\xcf",  # Mach-O binary (macOS)
                    ]

                    for signature in binary_signatures:
                        if chunk.startswith(signature):
                            return False

                    # Check for null bytes (strong indicator of binary content)
                    if b"\x00" in chunk:
                        return False

                    # Try to decode as UTF-8 for final check
                    try:
                        chunk.decode("utf-8")
                        return True
                    except UnicodeDecodeError:
                        # If UTF-8 fails, assume binary for simplicity
                        return False

            except (OSError, PermissionError, IsADirectoryError):
                # If we can't read the file, assume it's not viewable
                return False

        except (OSError, ValueError):
            # Handle any other OS-level errors or path issues
            return False

    def keyPressEvent(self, event) -> None:
        """
        Handle key press events.

        Args:
            event: The key press event
        """
        # Handle Enter/Return key to open files
        if event and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current_index = self.currentIndex()
            if current_index.isValid():
                if not self._model.is_directory(current_index):
                    # For files, emit file_opened signal
                    file_path = self._model.get_file_path(current_index)
                    if file_path and self._is_viewable_file(file_path):
                        self.file_opened.emit(file_path)
                        return
                else:
                    # For directories, toggle expansion
                    if self.isExpanded(current_index):
                        self.collapse(current_index)
                    else:
                        self.expand(current_index)
                    return

        # Call parent implementation for other keys
        super().keyPressEvent(event)

    def set_root_directory(self, directory_path: Union[str, Path]) -> None:
        """
        Set the root directory for the file tree view.

        Args:
            directory_path: Path to the directory to display

        Raises:
            ValueError: If the path is invalid or inaccessible
            PermissionError: If access is denied to the directory
        """
        # Convert to Path object for validation
        path = (
            Path(directory_path) if isinstance(directory_path, str) else directory_path
        )

        if self._model:
            try:
                root_index = self._model.set_root_directory(path)
                self.setRootIndex(root_index)
            except (ValueError, PermissionError, OSError):
                # Re-raise the exception to let the caller handle it
                # The UI layer should catch and display appropriate error messages
                raise

    def get_selected_file_path(self) -> Optional[Path]:
        """
        Get the file path of the currently selected item.

        Returns:
            Path object for the selected file/directory, or None if nothing selected
        """
        current_index = self.currentIndex()
        if not current_index.isValid():
            return None

        return self._model.get_file_path(current_index)

    def get_selected_file_info(self) -> "Dict[str, Any]":
        """
        Get file information for the currently selected item.

        Returns:
            Dictionary containing file information, empty if nothing selected
        """
        current_index = self.currentIndex()
        if not current_index.isValid():
            return {}

        return self._model.get_file_info(current_index)

    def is_selected_directory(self) -> bool:
        """
        Check if the currently selected item is a directory.

        Returns:
            True if selected item is a directory, False otherwise
        """
        current_index = self.currentIndex()
        if not current_index.isValid():
            return False

        return self._model.is_directory(current_index)

    def is_selected_code_file(self) -> bool:
        """
        Check if the currently selected item is a code file.

        Returns:
            True if selected item is a code file, False otherwise
        """
        current_index = self.currentIndex()
        if not current_index.isValid():
            return False

        return self._model.is_code_file(current_index)

    def refresh(self) -> None:
        """
        Refresh the file tree by updating the model.
        """
        if self._model:
            # Get current root path and reset it to trigger refresh
            current_root = self._model.rootPath()
            if current_root:
                self._model.setRootPath("")  # Clear first
                self._model.setRootPath(current_root)  # Reset to refresh

    def expand_to_path(self, file_path: Path) -> None:
        """
        Expand the tree view to show the given file path.

        Args:
            file_path: Path to expand to and select
        """
        try:
            # Resolve the path to handle symlinks
            resolved_path = file_path.resolve()

            # Check if the path exists
            if not resolved_path.exists():
                return

            # Get the model index for this path
            index = self._model.index(str(resolved_path))
            if index.isValid():
                # Expand all parent directories, but be careful about deep hierarchies
                parent = index.parent()
                expanded_count = 0
                max_expansions = 100  # Prevent infinite loops or excessive expansion

                while parent.isValid() and expanded_count < max_expansions:
                    self.expand(parent)
                    parent = parent.parent()
                    expanded_count += 1

                # Select and scroll to the item
                self.setCurrentIndex(index)
                self.scrollTo(index)

        except (OSError, RuntimeError):
            # Handle path resolution errors, deep recursion, or other issues
            # Silently fail to avoid disrupting the UI
            pass

    def _show_context_menu(self, position: QPoint) -> None:
        """
        Show the context menu at the given position.

        Args:
            position: The position where the menu should be shown
        """
        # Create the context menu
        menu = QMenu(self)

        # Add refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh)
        menu.addAction(refresh_action)

        menu.addSeparator()

        # Add expand/collapse actions
        expand_all_action = QAction("Expand All", self)
        expand_all_action.triggered.connect(self.expandAll)
        menu.addAction(expand_all_action)

        collapse_all_action = QAction("Collapse All", self)
        collapse_all_action.triggered.connect(self.collapseAll)
        menu.addAction(collapse_all_action)

        # Show the menu at the requested position
        global_pos = self.mapToGlobal(position)
        menu.exec(global_pos)

    def drawBranches(
        self, painter: Optional[QPainter], rect: QRect, index: QModelIndex
    ) -> None:
        """
        Override drawBranches method to paint Font Awesome icons at correct tree positions

        Args:
            painter: QPainter object for drawing
            rect: QRect object for the branch area
            index: QModelIndex for the item
        """
        if not painter or not index.isValid():
            return

        if self._model.is_directory(index):
            if (
                hasattr(self, "_expanded_icon")
                and hasattr(self, "_collapsed_icon")
                and self._expanded_icon
                and self._collapsed_icon
            ):
                # Use Qt's provided rect which is already positioned correctly for the branch area
                # The rect parameter represents where the branch indicator should be drawn
                icon_size = 12  # Slightly smaller to fit better in the branch area

                # Center the icon within the provided branch rect
                icon_x = rect.left() + (rect.width() - icon_size) // 2
                icon_y = rect.top() + (rect.height() - icon_size) // 2

                # Choose and draw the appropriate icon
                if self.isExpanded(index):
                    pixmap = self._expanded_icon.pixmap(icon_size, icon_size)
                else:
                    pixmap = self._collapsed_icon.pixmap(icon_size, icon_size)

                painter.drawPixmap(icon_x, icon_y, pixmap)
        else:
            # For non-directories, call parent implementation to maintain tree lines
            super().drawBranches(painter, rect, index)

    def mousePressEvent(self, e) -> None:
        """
        Override mouse press event to handle clicks on our custom chevron icons.

        Args:
            e: QMouseEvent object
        """
        if e and e.button() == Qt.MouseButton.LeftButton:
            index = self.indexAt(e.pos())
            if index.isValid() and self._model.is_directory(index):
                # Calculate the branch area using Qt's standard approach
                branch_rect = self.visualRect(index)
                depth = 0
                parent = index.parent()
                while parent.isValid():
                    depth += 1
                    parent = parent.parent()

                # Standard Qt indentation
                indent_size = self.indentation()
                branch_x = depth * indent_size

                # Create the clickable area for the chevron
                click_rect = QRect(
                    branch_x, branch_rect.y(), indent_size, branch_rect.height()
                )

                if click_rect.contains(e.pos()):
                    # Toggle expanded state
                    if self.isExpanded(index):
                        self.collapse(index)
                    else:
                        self.expand(index)
                    return  # Don't call parent to avoid selection

        # Call parent implementation for all other clicks (file selection, etc.)
        super().mousePressEvent(e)
