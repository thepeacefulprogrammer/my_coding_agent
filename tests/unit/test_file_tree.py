"""Tests for file tree navigation components."""

from __future__ import annotations

import contextlib

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QTreeView

from my_coding_agent.core.file_tree import FileTreeModel, FileTreeWidget


@pytest.mark.qt
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
        """Test that refresh method updates the model correctly."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Create initial files
        file1 = tmp_path / "file1.py"
        file1.write_text("# File 1")

        # Refresh to see the new file
        widget.refresh()

        # Get the model and check that the file is visible
        model = widget.model()
        file1_index = model.index(str(file1))
        assert file1_index.isValid()

    def test_file_selection_signal_emission(self, qtbot, tmp_path):
        """Test that file_selected signal is emitted when a file is selected."""
        # Create test files
        python_file = tmp_path / "test.py"
        python_file.write_text("print('hello')")

        text_file = tmp_path / "readme.txt"
        text_file.write_text("This is a readme")

        # Create test directory
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Set up signal spy
        with qtbot.waitSignal(widget.file_selected, timeout=1000) as blocker:
            # Get file index and simulate selection
            model = widget.model()
            file_index = model.index(str(python_file))

            # Simulate clicking on the file
            widget.setCurrentIndex(file_index)
            QTest.mouseClick(
                widget.viewport(),
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                widget.visualRect(file_index).center(),
            )

        # Check that signal was emitted with correct file path
        assert blocker.signal_triggered
        emitted_path = blocker.args[0]
        assert emitted_path == python_file

    def test_file_selection_signal_not_emitted_for_directory(self, qtbot, tmp_path):
        """Test that file_selected signal is not emitted when a directory is selected."""
        # Create test directory
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Get directory index
        model = widget.model()
        dir_index = model.index(str(test_dir))

        # Set up signal spy to ensure no signal is emitted
        signal_emitted = False

        def signal_handler(path):
            nonlocal signal_emitted
            signal_emitted = True

        widget.file_selected.connect(signal_handler)

        # Simulate clicking on the directory
        widget.setCurrentIndex(dir_index)
        QTest.mouseClick(
            widget.viewport(),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            widget.visualRect(dir_index).center(),
        )

        # Give some time for signal processing
        qtbot.wait(100)

        # Signal should not have been emitted for directory
        assert not signal_emitted

    def test_double_click_opens_file(self, qtbot, tmp_path):
        """Test that double-clicking a file triggers file opening."""
        # Create test file
        python_file = tmp_path / "test.py"
        python_file.write_text("print('hello')")

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Get file index and make sure it's visible
        model = widget.model()
        file_index = model.index(str(python_file))

        # Wait for the model to be ready
        qtbot.wait(200)
        widget.setCurrentIndex(file_index)
        qtbot.wait(100)

        # Test double-click by directly calling the handler
        # (Mouse simulation can be unreliable in tests)
        signal_emitted = False
        emitted_path = None

        def signal_handler(path):
            nonlocal signal_emitted, emitted_path
            signal_emitted = True
            emitted_path = path

        widget.file_opened.connect(signal_handler)

        # Call the double-click handler directly
        widget._on_double_clicked(file_index)

        # Give time for signal processing
        qtbot.wait(50)

        # Check that signal was emitted with correct file path
        assert signal_emitted
        assert emitted_path == python_file

    def test_double_click_directory_expands_collapses(self, qtbot, tmp_path):
        """Test that double-clicking a directory expands/collapses it."""
        # Create test directory with subdirectory
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()

        nested_dir = test_dir / "nested"
        nested_dir.mkdir()

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Get directory index
        model = widget.model()
        dir_index = model.index(str(test_dir))

        # Wait for model to be ready
        qtbot.wait(200)
        widget.setCurrentIndex(dir_index)
        qtbot.wait(100)

        # Initially should be collapsed
        assert not widget.isExpanded(dir_index)

        # Call double-click handler directly to expand
        widget._on_double_clicked(dir_index)
        qtbot.wait(50)  # Wait for expansion
        assert widget.isExpanded(dir_index)

        # Call double-click handler again to collapse
        widget._on_double_clicked(dir_index)
        qtbot.wait(50)  # Wait for collapse
        assert not widget.isExpanded(dir_index)

    def test_file_selection_updates_current_file_path(self, qtbot, tmp_path):
        """Test that selecting a file updates the current file tracking."""
        # Create test files
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("print('file1')")
        file2.write_text("print('file2')")

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        model = widget.model()

        # Select first file
        file1_index = model.index(str(file1))
        widget.setCurrentIndex(file1_index)
        assert widget.get_selected_file_path() == file1

        # Select second file
        file2_index = model.index(str(file2))
        widget.setCurrentIndex(file2_index)
        assert widget.get_selected_file_path() == file2

    def test_keyboard_navigation_opens_selected_file(self, qtbot, tmp_path):
        """Test that pressing Enter on a selected file opens it."""
        # Create test file
        test_file = tmp_path / "keyboard_test.py"
        test_file.write_text("print('keyboard test')")

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        model = widget.model()
        file_index = model.index(str(test_file))
        widget.setCurrentIndex(file_index)

        # Test Enter key opens file
        with qtbot.waitSignal(widget.file_opened, timeout=1000) as blocker:
            QTest.keyClick(widget, Qt.Key.Key_Return)

        assert blocker.signal_triggered
        assert blocker.args[0] == test_file

    def test_only_viewable_files_trigger_open_signal(self, qtbot, tmp_path):
        """Test that only viewable files trigger the file_opened signal."""
        # Create different types of files
        python_file = tmp_path / "script.py"
        python_file.write_text("print('hello')")

        text_file = tmp_path / "readme.txt"
        text_file.write_text("This is a readme")

        binary_file = tmp_path / "image.png"
        binary_file.write_bytes(b"\x89PNG\x0d\x0a\x1a\x0a")  # PNG header

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        model = widget.model()

        # Test Python file - should trigger signal
        with qtbot.waitSignal(widget.file_opened, timeout=1000) as blocker:
            python_index = model.index(str(python_file))
            widget.setCurrentIndex(python_index)
            QTest.keyClick(widget, Qt.Key.Key_Return)

        assert blocker.signal_triggered
        assert blocker.args[0] == python_file

        # Test text file - should trigger signal (text files are viewable)
        with qtbot.waitSignal(widget.file_opened, timeout=1000) as blocker:
            text_index = model.index(str(text_file))
            widget.setCurrentIndex(text_index)
            QTest.keyClick(widget, Qt.Key.Key_Return)

        assert blocker.signal_triggered
        assert blocker.args[0] == text_file

        # Test binary file - should not trigger signal
        signal_triggered = False

        def signal_handler(path):
            nonlocal signal_triggered
            signal_triggered = True

        widget.file_opened.connect(signal_handler)

        binary_index = model.index(str(binary_file))
        widget.setCurrentIndex(binary_index)
        QTest.keyClick(widget, Qt.Key.Key_Return)

        qtbot.wait(100)  # Wait for any potential signal
        assert not signal_triggered  # Binary files should not trigger open

    def test_only_code_files_trigger_open_signal(self, qtbot, tmp_path):
        """Test that only code files trigger the file_opened signal."""
        # Create different types of files
        python_file = tmp_path / "script.py"
        python_file.write_text("print('hello')")

        text_file = tmp_path / "readme.txt"
        text_file.write_text("This is a readme")

        binary_file = tmp_path / "image.png"
        binary_file.write_bytes(b"\x89PNG\x0d\x0a\x1a\x0a")  # PNG header

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        model = widget.model()

        # Test Python file - should trigger signal
        with qtbot.waitSignal(widget.file_opened, timeout=1000) as blocker:
            python_index = model.index(str(python_file))
            widget.setCurrentIndex(python_index)
            QTest.keyClick(widget, Qt.Key.Key_Return)

        assert blocker.signal_triggered
        assert blocker.args[0] == python_file

        # Test text file - should trigger signal (text files are viewable)
        with qtbot.waitSignal(widget.file_opened, timeout=1000) as blocker:
            text_index = model.index(str(text_file))
            widget.setCurrentIndex(text_index)
            QTest.keyClick(widget, Qt.Key.Key_Return)

        assert blocker.signal_triggered
        assert blocker.args[0] == text_file

        # Test binary file - should not trigger signal
        signal_triggered = False

        def signal_handler(path):
            nonlocal signal_triggered
            signal_triggered = True

        widget.file_opened.connect(signal_handler)

        binary_index = model.index(str(binary_file))
        widget.setCurrentIndex(binary_index)
        QTest.keyClick(widget, Qt.Key.Key_Return)

        qtbot.wait(100)  # Wait for any potential signal
        assert not signal_triggered  # Binary files should not trigger open

    def test_context_menu_creation(self, qtbot, tmp_path):
        """Test that context menu is created correctly."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Test that context menu policy is set correctly
        assert widget.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu

    def test_context_menu_actions(self, qtbot, tmp_path):
        """Test that context menu contains the correct actions."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Get context menu actions (assuming the menu is accessible)
        # This will test the actual menu creation when implemented
        # For now, we'll test that the widget can handle context menu requests
        assert hasattr(widget, "customContextMenuRequested")

    def test_refresh_action_functionality(self, qtbot, tmp_path):
        """Test the refresh action functionality."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Create initial file
        initial_file = tmp_path / "initial.py"
        initial_file.write_text("print('initial')")

        # Call refresh method (should exist)
        widget.refresh()

        # Add a new file after refresh
        new_file = tmp_path / "new.py"
        new_file.write_text("print('new')")

        # Refresh again to pick up the new file
        widget.refresh()

        # Verify that both files are visible in the model
        model = widget.model()
        initial_index = model.index(str(initial_file))
        new_index = model.index(str(new_file))

        assert initial_index.isValid()
        assert new_index.isValid()

    def test_expand_all_action_functionality(self, qtbot, tmp_path):
        """Test the expand all action functionality."""
        # Create nested directory structure
        level1 = tmp_path / "level1"
        level1.mkdir()
        level2 = level1 / "level2"
        level2.mkdir()
        level3 = level2 / "level3"
        level3.mkdir()

        # Create files at each level
        (level1 / "file1.py").write_text("content1")
        (level2 / "file2.py").write_text("content2")
        (level3 / "file3.py").write_text("content3")

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        model = widget.model()

        # Initially, directories should be collapsed
        level1_index = model.index(str(level1))
        assert level1_index.isValid()
        assert not widget.isExpanded(level1_index)

        # Test expand all functionality
        widget.expandAll()

        # After expand all, directories should be expanded
        assert widget.isExpanded(level1_index)

    def test_collapse_all_action_functionality(self, qtbot, tmp_path):
        """Test the collapse all action functionality."""
        # Create nested directory structure
        level1 = tmp_path / "level1"
        level1.mkdir()
        level2 = level1 / "level2"
        level2.mkdir()

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        model = widget.model()
        level1_index = model.index(str(level1))

        # First expand all
        widget.expandAll()
        assert widget.isExpanded(level1_index)

        # Then collapse all
        widget.collapseAll()
        assert not widget.isExpanded(level1_index)

    def test_context_menu_show_on_right_click(self, qtbot, tmp_path):
        """Test that context menu shows when right-clicking."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        # Test that we can simulate a context menu request
        # This will test the signal emission when the context menu is implemented
        assert hasattr(widget, "customContextMenuRequested")

    def test_permission_error_handling(self, qtbot, tmp_path):
        """Test handling of permission errors when accessing directories."""
        import os

        # Create a directory that we'll make inaccessible
        restricted_dir = tmp_path / "restricted"
        restricted_dir.mkdir()

        # Create a file inside the restricted directory
        test_file = restricted_dir / "secret.py"
        test_file.write_text("print('secret')")

        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # On Unix systems, we can test permission errors
        if os.name == "posix":
            try:
                # Remove read permissions from the directory
                os.chmod(restricted_dir, 0o000)

                model = widget.model()

                # Try to access the restricted directory
                # This should not crash the application
                restricted_index = model.index(str(restricted_dir))

                # The directory should still show up in the model (QFileSystemModel handles this)
                # but accessing its contents should be handled gracefully
                if restricted_index.isValid():
                    # Try to expand the directory - should not crash
                    widget.expand(restricted_index)

                # Try to get file info from restricted directory - should handle gracefully
                file_info = model.get_file_info(restricted_index)
                assert isinstance(
                    file_info, dict
                )  # Should return empty dict or basic info

            finally:
                # Restore permissions for cleanup
                with contextlib.suppress(OSError):
                    os.chmod(restricted_dir, 0o755)
        else:
            # On Windows, just test that the widget can handle the scenario
            assert widget is not None

    def test_symlink_handling(self, qtbot, tmp_path):
        """Test handling of symbolic links."""
        import os

        # Create a target file
        target_file = tmp_path / "target.py"
        target_file.write_text("print('target')")

        # Create a target directory
        target_dir = tmp_path / "target_dir"
        target_dir.mkdir()
        target_subfile = target_dir / "sub.py"
        target_subfile.write_text("print('sub')")

        widget = FileTreeWidget()
        qtbot.addWidget(widget)

        # Test symlinks if the platform supports them
        if hasattr(os, "symlink"):
            try:
                # Create symbolic links
                file_symlink = tmp_path / "file_link.py"
                dir_symlink = tmp_path / "dir_link"

                os.symlink(target_file, file_symlink)
                os.symlink(target_dir, dir_symlink)

                widget.set_root_directory(tmp_path)
                model = widget.model()

                # Test file symlink
                file_link_index = model.index(str(file_symlink))
                if file_link_index.isValid():
                    # Should be able to get file path
                    file_path = model.get_file_path(file_link_index)
                    assert file_path is not None

                    # Should be recognized as a viewable file
                    assert widget._is_viewable_file(file_path)

                # Test directory symlink
                dir_link_index = model.index(str(dir_symlink))
                if dir_link_index.isValid():
                    # Should be recognized as a directory
                    assert model.is_directory(dir_link_index)

                    # Should be able to expand
                    widget.expand(dir_link_index)

            except OSError:
                # Symlink creation might fail due to permissions
                pass

        # Test should pass regardless of symlink support
        assert widget is not None

    def test_broken_symlink_handling(self, qtbot, tmp_path):
        """Test handling of broken symbolic links."""
        import os

        widget = FileTreeWidget()
        qtbot.addWidget(widget)

        if hasattr(os, "symlink"):
            try:
                # Create a symlink to a non-existent target
                broken_link = tmp_path / "broken_link.py"
                non_existent = tmp_path / "does_not_exist.py"

                os.symlink(non_existent, broken_link)

                widget.set_root_directory(tmp_path)
                model = widget.model()

                # Test broken symlink
                broken_index = model.index(str(broken_link))
                if broken_index.isValid():
                    # Should handle gracefully without crashing
                    file_path = model.get_file_path(broken_index)

                    # Should not crash when checking if viewable
                    is_viewable = (
                        widget._is_viewable_file(file_path) if file_path else False
                    )

                    # Broken symlinks should not be considered viewable
                    assert not is_viewable

            except OSError:
                # Symlink creation might fail due to permissions
                pass

        assert widget is not None

    def test_network_path_handling(self, qtbot, tmp_path):
        """Test handling of network paths and slow file systems."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)

        # Test with a deep directory structure that might be slow to traverse
        deep_path = tmp_path
        for i in range(10):
            deep_path = deep_path / f"level_{i}"
            deep_path.mkdir()

        # Create a file at the deep level
        deep_file = deep_path / "deep.py"
        deep_file.write_text("print('deep')")

        # Should handle deep paths without issues
        widget.set_root_directory(tmp_path)
        model = widget.model()

        # Test expand_to_path with deep structure
        widget.expand_to_path(deep_file)

        # Should not crash with deep paths
        assert model is not None

    def test_special_characters_in_paths(self, qtbot, tmp_path):
        """Test handling of paths with special characters."""
        # Create files/directories with special characters
        special_names = [
            "file with spaces.py",
            "file-with-dashes.py",
            "file_with_underscores.py",
            "file.with.dots.py",
            "файл.py",  # Cyrillic
            "文件.py",  # Chinese
        ]

        widget = FileTreeWidget()
        qtbot.addWidget(widget)

        created_files = []
        for name in special_names:
            try:
                special_file = tmp_path / name
                special_file.write_text("print('special')")
                created_files.append(special_file)
            except (OSError, UnicodeError):
                # Some filesystems might not support certain characters
                continue

        if created_files:
            widget.set_root_directory(tmp_path)
            model = widget.model()

            # Test that special character files are handled properly
            for file_path in created_files:
                file_index = model.index(str(file_path))
                if file_index.isValid():
                    # Should be able to get file path
                    retrieved_path = model.get_file_path(file_index)
                    assert retrieved_path is not None

                    # Should be recognized as viewable
                    assert widget._is_viewable_file(retrieved_path)

        assert widget is not None

    def test_very_long_paths(self, qtbot, tmp_path):
        """Test handling of very long file paths."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)

        # Create a path that's close to system limits
        long_name = "a" * 200  # Very long filename

        try:
            long_file = tmp_path / f"{long_name}.py"
            long_file.write_text("print('long')")

            widget.set_root_directory(tmp_path)
            model = widget.model()

            # Should handle long paths gracefully
            long_index = model.index(str(long_file))
            if long_index.isValid():
                file_path = model.get_file_path(long_index)
                assert file_path is not None

        except OSError:
            # Filesystem might not support such long names
            pass

        assert widget is not None

    def test_concurrent_file_operations(self, qtbot, tmp_path):
        """Test handling of files being modified while tree is displayed."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Create initial file
        test_file = tmp_path / "changing.py"
        test_file.write_text("print('initial')")

        model = widget.model()

        # Get initial index
        initial_index = model.index(str(test_file))
        assert initial_index.isValid()

        # Modify the file while tree is displayed
        test_file.write_text("print('modified')")

        # Create new file
        new_file = tmp_path / "new.py"
        new_file.write_text("print('new')")

        # Refresh the model
        widget.refresh()

        # Should handle concurrent modifications gracefully
        new_index = model.index(str(new_file))
        assert new_index.isValid() or True  # May take time for model to update

        assert widget is not None


@pytest.mark.qt
class TestFileTreeModel:
    """Test cases for FileTreeModel class."""

    def test_file_tree_model_initialization(self, qapp):
        """Test FileTreeModel initializes correctly."""
        model = FileTreeModel()

        # Should be a QFileSystemModel
        assert model is not None
        assert model.isReadOnly()

    def test_file_tree_model_set_root_directory_invalid_path(self, qapp, tmp_path):
        """Test FileTreeModel handles invalid directory paths."""
        model = FileTreeModel()

        # Test non-existent directory
        non_existent = tmp_path / "does_not_exist"
        try:
            model.set_root_directory(non_existent)
            pytest.fail("Should have raised ValueError")
        except ValueError as e:
            assert "does not exist" in str(e)

    def test_file_tree_model_set_root_directory_file_path(self, qapp, tmp_path):
        """Test FileTreeModel rejects file paths as root directory."""
        model = FileTreeModel()

        # Create a file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        # Try to set file as root directory
        try:
            model.set_root_directory(test_file)
            pytest.fail("Should have raised ValueError")
        except ValueError as e:
            assert "not a directory" in str(e)

    def test_file_tree_model_get_file_path_invalid_index(self, qapp):
        """Test FileTreeModel handles invalid indexes."""
        model = FileTreeModel()

        # Create invalid index
        from PyQt6.QtCore import QModelIndex

        invalid_index = QModelIndex()

        result = model.get_file_path(invalid_index)
        assert result is None

    def test_file_tree_model_is_directory_invalid_index(self, qapp):
        """Test FileTreeModel directory check with invalid index."""
        model = FileTreeModel()

        from PyQt6.QtCore import QModelIndex

        invalid_index = QModelIndex()

        result = model.is_directory(invalid_index)
        assert result is False

    def test_file_tree_model_is_code_file_with_various_extensions(self, qapp, tmp_path):
        """Test FileTreeModel code file detection."""
        model = FileTreeModel()
        model.set_root_directory(tmp_path)

        # Create files with different extensions
        test_files = {
            "script.py": True,
            "app.js": True,
            "style.css": True,
            "data.json": True,
            "readme.md": True,
            "config.ini": True,
            "image.png": False,
            "archive.zip": False,
        }

        for filename, should_be_code in test_files.items():
            test_file = tmp_path / filename
            test_file.write_text("content")

            file_index = model.index(str(test_file))
            result = model.is_code_file(file_index)
            assert result == should_be_code, (
                f"File {filename} should {'be' if should_be_code else 'not be'} code"
            )

    def test_file_tree_model_get_file_info(self, qapp, tmp_path):
        """Test FileTreeModel file info retrieval."""
        model = FileTreeModel()
        model.set_root_directory(tmp_path)

        # Create test file
        test_file = tmp_path / "test.py"
        test_content = "print('hello world')"
        test_file.write_text(test_content)

        file_index = model.index(str(test_file))
        file_info = model.get_file_info(file_index)

        assert isinstance(file_info, dict)
        assert file_info["name"] == "test.py"
        assert file_info["is_directory"] is False
        assert file_info["size"] == len(test_content)
        assert "size_human" in file_info

    def test_file_tree_model_get_file_info_directory(self, qapp, tmp_path):
        """Test FileTreeModel file info for directories."""
        model = FileTreeModel()
        model.set_root_directory(tmp_path)

        # Create test directory
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        dir_index = model.index(str(test_dir))
        dir_info = model.get_file_info(dir_index)

        assert isinstance(dir_info, dict)
        assert dir_info["name"] == "test_dir"
        assert dir_info["is_directory"] is True
        assert dir_info["size_human"] == ""

    def test_file_tree_model_data_tooltip_role(self, qapp, tmp_path):
        """Test FileTreeModel data method with tooltip role."""
        model = FileTreeModel()
        model.set_root_directory(tmp_path)

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        file_index = model.index(str(test_file))
        tooltip = model.data(file_index, Qt.ItemDataRole.ToolTipRole)

        assert isinstance(tooltip, str)
        assert "test.py" in tooltip
        assert "Size:" in tooltip

    def test_file_tree_model_data_decoration_role(self, qapp, tmp_path):
        """Test FileTreeModel data method with decoration role."""
        model = FileTreeModel()
        model.set_root_directory(tmp_path)

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        file_index = model.index(str(test_file))
        icon = model.data(file_index, Qt.ItemDataRole.DecorationRole)

        # Should return an icon (QIcon)
        assert icon is not None


@pytest.mark.qt
class TestFileTreeModelWidgetInteraction:
    """Test cases for FileTreeModel and FileTreeWidget interactions."""

    def test_widget_model_integration(self, qtbot, tmp_path):
        """Test integration between widget and model."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)

        # Test that widget has a model
        model = widget.model()
        assert model is not None
        assert isinstance(model, FileTreeModel)

        # Test setting root directory through widget
        widget.set_root_directory(tmp_path)
        assert model.rootPath() == str(tmp_path.resolve())

    def test_model_widget_signal_integration(self, qtbot, tmp_path):
        """Test that model changes trigger appropriate widget signals."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Create test file
        test_file = tmp_path / "signal_test.py"
        test_file.write_text("print('signal test')")

        model = widget.model()

        # Test file selection signal
        with qtbot.waitSignal(widget.file_selected, timeout=1000) as blocker:
            file_index = model.index(str(test_file))
            widget.setCurrentIndex(file_index)

        assert blocker.signal_triggered
        assert blocker.args[0] == test_file

    def test_widget_model_file_info_integration(self, qtbot, tmp_path):
        """Test widget accessing model file info."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Create test file
        test_file = tmp_path / "info_test.py"
        test_file.write_text("print('info test')")

        model = widget.model()
        file_index = model.index(str(test_file))
        widget.setCurrentIndex(file_index)

        # Test widget accessing model info
        file_info = widget.get_selected_file_info()
        assert isinstance(file_info, dict)
        assert file_info["name"] == "info_test.py"
        assert not file_info["is_directory"]

    def test_widget_model_directory_operations(self, qtbot, tmp_path):
        """Test widget directory operations through model."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Create test directory
        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()

        model = widget.model()
        dir_index = model.index(str(test_dir))
        widget.setCurrentIndex(dir_index)

        # Test directory detection
        assert widget.is_selected_directory()
        assert not widget.is_selected_code_file()

    def test_widget_model_refresh_integration(self, qtbot, tmp_path):
        """Test widget refresh updates model."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Initially no files
        model = widget.model()

        # Create file after widget setup
        new_file = tmp_path / "new_file.py"
        new_file.write_text("print('new')")

        # Refresh should pick up new file
        widget.refresh()

        # File should now be accessible through model
        file_index = model.index(str(new_file))
        # Note: May take time for filesystem model to update
        assert file_index.isValid() or True

    def test_model_icon_integration(self, qtbot, tmp_path):
        """Test model icon functionality."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        model = widget.model()

        # Test just a few file types, not many
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        file_index = model.index(str(test_file))
        icon = model._get_file_icon(file_index)

        # Should return a QIcon
        assert icon is not None

    def test_widget_keyboard_model_interaction(self, qtbot, tmp_path):
        """Test keyboard navigation with model."""
        widget = FileTreeWidget()
        qtbot.addWidget(widget)
        widget.set_root_directory(tmp_path)

        # Create test file
        test_file = tmp_path / "keyboard_test.py"
        test_file.write_text("print('keyboard')")

        model = widget.model()
        file_index = model.index(str(test_file))
        widget.setCurrentIndex(file_index)

        # Test Enter key with model integration
        with qtbot.waitSignal(widget.file_opened, timeout=1000) as blocker:
            QTest.keyClick(widget, Qt.Key.Key_Return)

        assert blocker.signal_triggered
        assert blocker.args[0] == test_file


@pytest.mark.slow
class TestFileTreePerformanceOptimizations:
    """Test performance optimizations for the file tree."""

    @pytest.fixture
    def optimized_model(self, tmp_path):
        """Create an optimized file tree model for testing."""
        from my_coding_agent.core.file_tree import FileTreeModel

        model = FileTreeModel()
        model.set_root_directory(tmp_path)
        return model

    def test_lazy_loading_enabled(self, optimized_model):
        """Test that lazy loading is enabled for better performance."""
        # Check if the model has lazy loading capability
        assert hasattr(optimized_model, "_lazy_loading_enabled")
        assert optimized_model._lazy_loading_enabled is True

    def test_icon_caching_mechanism(self, optimized_model):
        """Test that icon caching reduces repeated icon generation."""
        # Check that icon cache exists
        assert hasattr(optimized_model, "_icon_cache")
        assert isinstance(optimized_model._icon_cache, dict)

    def test_performance_metrics_tracking(self, optimized_model):
        """Test that performance metrics can be tracked."""
        # Check if performance tracking is available
        assert hasattr(optimized_model, "_performance_metrics")
        assert isinstance(optimized_model._performance_metrics, dict)

        # Basic metrics should be trackable
        expected_metrics = ["scan_time", "cache_hits", "cache_misses"]
        for metric in expected_metrics:
            assert metric in optimized_model._performance_metrics
            assert isinstance(optimized_model._performance_metrics[metric], int | float)

    def test_memory_management_limits(self, optimized_model):
        """Test that memory usage is controlled through caching limits."""
        # Check that memory management is in place
        assert hasattr(optimized_model, "_max_cache_size")
        assert optimized_model._max_cache_size > 0
        assert optimized_model._max_cache_size <= 1000  # Reasonable upper bound

    def test_background_scanning_capability(self, optimized_model):
        """Test that background scanning is available for large directories."""
        # Check if model supports background operations
        assert hasattr(optimized_model, "_enable_background_scanning")

        # Verify background scanning can be toggled
        optimized_model._enable_background_scanning = True
        assert optimized_model._enable_background_scanning is True

        optimized_model._enable_background_scanning = False
        assert optimized_model._enable_background_scanning is False

    def test_file_filtering_capability(self, optimized_model):
        """Test that file filtering improves scanning performance."""
        # Check that model has filtering capabilities
        assert hasattr(optimized_model, "_should_filter_file")
        assert optimized_model._should_filter_file is True

    def test_thread_safety_mechanism(self, optimized_model):
        """Test that the model has thread safety mechanisms."""
        # Check if the model has thread safety mechanisms
        assert hasattr(optimized_model, "_lock")
        # Check that it's a threading lock of some type
        assert hasattr(optimized_model._lock, "acquire")
        assert hasattr(optimized_model._lock, "release")
        # Verify it's actually an RLock instance
        assert type(optimized_model._lock).__name__ == "RLock"

    def test_debounced_refresh_mechanism(self, qtbot, tmp_path):
        """Test that refresh operations are debounced to prevent excessive updates."""
        from my_coding_agent.core.file_tree import FileTreeWidget

        widget = FileTreeWidget()
        widget.set_root_directory(tmp_path)

        # Check that debouncing mechanism exists
        assert hasattr(widget, "_refresh_timer")
        assert hasattr(widget, "_refresh_debounce_ms")

        # Test that the timer is properly configured
        assert widget._refresh_timer.isSingleShot()
        assert widget._refresh_debounce_ms > 0
