"""
File tree navigation components for the Simple Code Viewer.

This module provides the file tree model and widget for directory navigation
using PyQt6's QFileSystemModel as the foundation.
"""

from pathlib import Path
from typing import Any, Optional, Union

from PyQt6.QtCore import QDir, QModelIndex, Qt
from PyQt6.QtGui import QFileSystemModel, QIcon
from PyQt6.QtWidgets import QTreeView


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
        """
        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")

        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")

        # Set the root path and return the index
        root_index = self.setRootPath(str(directory_path))
        return root_index

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

        file_path = self.filePath(index)
        return Path(file_path) if file_path else None

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
            ".yml",  # Data formats
            ".md",
            ".txt",
            ".cfg",
            ".ini",  # Text files
        }

        return file_path.suffix.lower() in code_extensions

    def get_file_info(self, index: QModelIndex) -> "dict[str, Any]":
        """
        Get detailed information about a file or directory.

        Args:
            index: QModelIndex to get info for

        Returns:
            Dictionary containing file information
        """
        if not index.isValid():
            return {}

        file_path = self.get_file_path(index)
        if not file_path:
            return {}

        info = {
            "name": self.fileName(index),
            "path": file_path,
            "is_directory": self.is_directory(index),
            "is_code_file": self.is_code_file(index),
            "size": self.size(index),
            "last_modified": self.lastModified(index),
            "type": self.type(index),
        }

        # Add file size in human-readable format for files
        if not info["is_directory"]:
            size_bytes = info["size"]
            if size_bytes < 1024:
                info["size_human"] = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                info["size_human"] = f"{size_bytes / 1024:.1f} KB"
            else:
                info["size_human"] = f"{size_bytes / (1024 * 1024):.1f} MB"
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

    def __init__(self, parent: Optional[Any] = None) -> None:
        """
        Initialize the FileTreeWidget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_widget()

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

    def set_root_directory(self, directory_path: Union[str, Path]) -> None:
        """
        Set the root directory for the file tree view.

        Args:
            directory_path: Path to the directory to display
        """
        # Convert to Path object for validation
        path = (
            Path(directory_path) if isinstance(directory_path, str) else directory_path
        )

        if self._model:
            root_index = self._model.set_root_directory(path)
            self.setRootIndex(root_index)

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

    def get_selected_file_info(self) -> "dict[str, Any]":
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
        if not file_path.exists():
            return

        # Get the model index for this path
        index = self._model.index(str(file_path))
        if index.isValid():
            # Expand all parent directories
            parent = index.parent()
            while parent.isValid():
                self.expand(parent)
                parent = parent.parent()

            # Select and scroll to the item
            self.setCurrentIndex(index)
            self.scrollTo(index)
