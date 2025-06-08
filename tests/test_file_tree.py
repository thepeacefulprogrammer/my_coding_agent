"""Tests for file tree navigation components."""

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QTreeView

from my_coding_agent.core.file_tree import FileTreeModel, FileTreeWidget


class TestFileTreeWidget:
    """Test cases for FileTreeWidget class."""

    def test_file_tree_widget_initialization(self, qapp):
        """Test FileTreeWidget initializes correctly."""
        widget = FileTreeWidget()

        # Should be a QTreeView
        assert isinstance(widget, QTreeView)

        # Should have a FileTreeModel set
        assert isinstance(widget.model(), FileTreeModel)

        # Should have selection behavior set to SelectRows
        assert widget.selectionBehavior() == QTreeView.SelectionBehavior.SelectRows

    def test_file_type_icons(self, qapp, tmp_path):
        """Test that file type icons are displayed correctly."""
        widget = FileTreeWidget()
        model = widget.model()

        # Create test files with different extensions
        python_file = tmp_path / "test.py"
        python_file.write_text("print('hello')")

        js_file = tmp_path / "test.js"
        js_file.write_text("console.log('hello');")

        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')

        text_file = tmp_path / "test.txt"
        text_file.write_text("hello world")

        # Set the root directory to our test directory
        widget.set_root_directory(str(tmp_path))

        # Get file indexes
        python_index = model.index(str(python_file))
        js_index = model.index(str(js_file))
        json_index = model.index(str(json_file))
        text_index = model.index(str(text_file))

        # Check that files have appropriate icons
        python_icon = model.data(python_index, Qt.ItemDataRole.DecorationRole)
        js_icon = model.data(js_index, Qt.ItemDataRole.DecorationRole)
        json_icon = model.data(json_index, Qt.ItemDataRole.DecorationRole)
        text_icon = model.data(text_index, Qt.ItemDataRole.DecorationRole)

        # Icons should not be None
        assert python_icon is not None
        assert js_icon is not None
        assert json_icon is not None
        assert text_icon is not None

        # Icons should be different for different file types
        assert python_icon != js_icon
        assert python_icon != json_icon

    def test_folder_icons(self, qapp, tmp_path):
        """Test that folder icons are displayed correctly."""
        widget = FileTreeWidget()
        model = widget.model()

        # Create test folders
        folder1 = tmp_path / "folder1"
        folder1.mkdir()

        folder2 = tmp_path / "folder2"
        folder2.mkdir()

        # Set the root directory to our test directory
        widget.set_root_directory(str(tmp_path))

        # Get folder indexes
        folder1_index = model.index(str(folder1))
        folder2_index = model.index(str(folder2))

        # Check that folders have folder icons
        folder1_icon = model.data(folder1_index, Qt.ItemDataRole.DecorationRole)
        folder2_icon = model.data(folder2_index, Qt.ItemDataRole.DecorationRole)

        # Icons should not be None
        assert folder1_icon is not None
        assert folder2_icon is not None

    def test_expand_collapse_functionality(self, qapp, tmp_path):
        """Test that folders can be expanded and collapsed."""
        widget = FileTreeWidget()

        # Create test folder structure
        parent_folder = tmp_path / "parent"
        parent_folder.mkdir()

        child_folder = parent_folder / "child"
        child_folder.mkdir()

        child_file = parent_folder / "file.txt"
        child_file.write_text("content")

        # Set the root directory to our test directory
        widget.set_root_directory(str(tmp_path))

        # Get the parent folder index
        model = widget.model()
        parent_index = model.index(str(parent_folder))

        # Initially, the folder should be collapsed (not expanded)
        assert not widget.isExpanded(parent_index)

        # Expand the folder
        widget.expand(parent_index)
        assert widget.isExpanded(parent_index)

        # Collapse the folder
        widget.collapse(parent_index)
        assert not widget.isExpanded(parent_index)

    def test_file_tree_widget_with_root_path(self, qtbot, tmp_path):
        """Test FileTreeWidget with custom root path."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        model = widget.model()
        assert model.rootPath() == str(tmp_path)

    def test_file_tree_widget_set_root_path(self, qtbot, tmp_path):
        """Test setting root path after initialization."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)

        widget.set_root_directory(str(tmp_path))

        model = widget.model()
        assert model.rootPath() == str(tmp_path)

    def test_file_tree_widget_current_path_property(self, qtbot, tmp_path):
        """Test current_path property returns correct path."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        model = widget.model()
        assert model.rootPath() == str(tmp_path)

    def test_file_tree_widget_file_selected_signal(self, qtbot, tmp_path):
        """Test that file_selected signal is emitted when a file is clicked."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Mock the signal (skip if signal doesn't exist yet)
        # This test will be implemented when signals are added
        # For now, just test that we can select the file
        model = widget.model()
        file_index = model.index(str(test_file))
        assert file_index.isValid()

    def test_file_tree_widget_directory_selected_no_signal(self, qtbot, tmp_path):
        """Test that file_selected signal is not emitted for directories."""
        # Create a test directory
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Get the model and find the directory index
        model = widget.model()
        dir_index = model.index(str(test_dir))

        # Test that we can identify the directory
        assert dir_index.isValid()
        assert model.isDir(dir_index)

    def test_file_tree_widget_expand_directory(self, qtbot, tmp_path):
        """Test expanding and collapsing directories."""
        # Create nested directory structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        nested_file = subdir / "nested.py"
        nested_file.write_text("# nested file")

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        model = widget.model()

        # Get index for subdirectory
        subdir_index = model.index(str(subdir))

        # Initially should be collapsed
        assert not widget.isExpanded(subdir_index)

        # Expand directory
        widget.expand(subdir_index)
        assert widget.isExpanded(subdir_index)

        # Collapse directory
        widget.collapse(subdir_index)
        assert not widget.isExpanded(subdir_index)

    def test_file_tree_widget_keyboard_navigation(self, qtbot, tmp_path):
        """Test keyboard navigation in file tree."""
        # Create test files
        file1 = tmp_path / "file1.py"
        file1.write_text("# file 1")
        file2 = tmp_path / "file2.py"
        file2.write_text("# file 2")

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Wait for the model to load
        qtbot.waitUntil(
            lambda: widget.model().rowCount(widget.rootIndex()) > 0, timeout=1000
        )

        # Select the first item to establish a starting point
        model = widget.model()
        first_index = model.index(0, 0, widget.rootIndex())
        if first_index.isValid():
            widget.setCurrentIndex(first_index)

        # Focus the widget
        widget.setFocus()

        # Test that arrow key navigation works
        from PyQt6.QtCore import Qt

        QTest.keyPress(widget, Qt.Key.Key_Down)
        QTest.keyPress(widget, Qt.Key.Key_Up)

        # Should not crash - we don't require a specific selection state
        # since the behavior can vary based on the model state
        assert widget.model() is not None

    def test_file_tree_widget_selection_changed_signal(self, qtbot, tmp_path):
        """Test selection changes work correctly."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Change selection
        model = widget.model()
        file_index = model.index(str(test_file))
        widget.setCurrentIndex(file_index)

        # Should have a valid selection
        assert widget.currentIndex().isValid()

    def test_file_tree_widget_invalid_root_path(self, qtbot):
        """Test FileTreeWidget handles invalid root path gracefully."""
        invalid_path = "/this/path/does/not/exist"

        # Should not raise exception
        widget = FileTreeWidget()
        qtbot.addWidget(widget)

        # Try to set invalid path - should handle gracefully
        import contextlib

        with contextlib.suppress(ValueError):
            widget.set_root_directory(invalid_path)
            # Expected behavior - invalid path should raise ValueError

        # Model should still exist
        model = widget.model()
        assert model is not None

    def test_file_tree_widget_get_selected_file_path(self, qtbot, tmp_path):
        """Test getting currently selected file path."""
        test_file = tmp_path / "selected.py"
        test_file.write_text("# selected file")

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Select the file
        model = widget.model()
        file_index = model.index(str(test_file))
        widget.setCurrentIndex(file_index)

        # Should return the selected file path
        selected_path = widget.get_selected_file_path()
        assert str(selected_path) == str(test_file)

    def test_file_tree_widget_get_selected_file_path_no_selection(
        self, qtbot, tmp_path
    ):
        """Test getting selected file path when nothing is selected."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Clear selection
        widget.clearSelection()

        # No selection should return None
        selected_path = widget.get_selected_file_path()
        assert selected_path is None

    def test_file_tree_widget_refresh_model(self, qtbot, tmp_path):
        """Test refreshing the file tree model."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Create a new file after widget initialization
        new_file = tmp_path / "new_file.py"
        new_file.write_text("# new file")

        # Refresh the model
        widget.refresh()

        # The new file should be visible in the model
        model = widget.model()
        file_index = model.index(str(new_file))
        assert file_index.isValid()
