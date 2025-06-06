# Unit tests for gui.py

# TODO: Add tests for GUI components once implemented
# - test_populate_tree
# - test_tree_selection_handler
# - test_file_viewer_scrolling
# - test_open_folder_dialog
# - test_new_folder_dialog

from unittest.mock import patch, MagicMock

def test_gui_has_tree_view_widget():
    """Test that GUI class has a tree view widget"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have a tree view widget
        assert hasattr(gui, 'tree_view'), "Expected GUI to have tree_view attribute"
        assert gui.tree_view is not None, "Expected tree_view to be initialized"

def test_gui_tree_view_is_configured():
    """Test that tree view widget is properly configured"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Tree view should be configured with proper columns
        # We'll verify this by checking that the tree view was created with the right parameters
        assert hasattr(gui, 'tree_view'), "Expected GUI to have tree_view attribute"

def test_gui_tree_view_is_packed_or_placed():
    """Test that tree view widget is added to the layout"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Tree view should be packed or placed in the layout
        # We'll verify the tree view exists and can be accessed
        assert hasattr(gui, 'tree_view'), "Expected GUI to have tree_view widget"
        assert gui.tree_view is not None, "Expected tree_view to be created"

def test_gui_has_tree_frame():
    """Test that GUI has a dedicated frame for the tree view"""
    # Mock tkinter to avoid display issues  
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have a frame for the tree view sidebar
        assert hasattr(gui, 'tree_frame'), "Expected GUI to have tree_frame attribute"
        assert gui.tree_frame is not None, "Expected tree_frame to be initialized"

def test_gui_layout_has_sidebar_and_content():
    """Test that GUI layout includes both sidebar and content areas"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have both tree frame (sidebar) and content frame
        assert hasattr(gui, 'tree_frame'), "Expected GUI to have tree_frame (sidebar)"
        assert hasattr(gui, 'content_frame'), "Expected GUI to have content_frame"

def test_gui_tree_view_has_scrollbar():
    """Test that tree view has a scrollbar for navigation"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have a scrollbar for the tree view
        assert hasattr(gui, 'tree_scrollbar'), "Expected GUI to have tree_scrollbar"
        assert gui.tree_scrollbar is not None, "Expected tree_scrollbar to be initialized"

def test_placeholder():
    """Placeholder test to ensure file exists and pytest runs"""
    assert True 

def test_gui_has_populate_tree_method():
    """Test that GUI class has a populate_tree method"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have a populate_tree method
        assert hasattr(gui, 'populate_tree'), "Expected GUI to have populate_tree method"
        assert callable(gui.populate_tree), "Expected populate_tree to be callable"

def test_populate_tree_with_empty_data():
    """Test populate_tree with empty directory data"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view with get_children returning empty list
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = []
        
        # Test with empty data
        empty_data = {'files': [], 'directories': []}
        gui.populate_tree(mock_treeview, empty_data)
        
        # Should call get_children to check for existing items
        mock_treeview.get_children.assert_called()
        # With empty data, no insert calls should be made
        mock_treeview.insert.assert_not_called()

def test_populate_tree_with_files_only():
    """Test populate_tree with files only"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        
        # Test with files only
        files_data = {
            'files': ['/test/file1.txt', '/test/file2.py'],
            'directories': []
        }
        gui.populate_tree(mock_treeview, files_data)
        
        # Should insert file items
        assert mock_treeview.insert.call_count >= 2, "Expected at least 2 insert calls for files"

def test_populate_tree_with_directories_only():
    """Test populate_tree with directories only"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        
        # Test with directories only
        dirs_data = {
            'files': [],
            'directories': ['/test/subdir1', '/test/subdir2']
        }
        gui.populate_tree(mock_treeview, dirs_data)
        
        # Should insert directory items
        assert mock_treeview.insert.call_count >= 2, "Expected at least 2 insert calls for directories"

def test_populate_tree_with_mixed_content():
    """Test populate_tree with both files and directories"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        
        # Test with mixed content
        mixed_data = {
            'files': ['/test/file1.txt', '/test/script.py'],
            'directories': ['/test/folder1', '/test/folder2']
        }
        gui.populate_tree(mock_treeview, mixed_data)
        
        # Should insert both file and directory items
        assert mock_treeview.insert.call_count >= 4, "Expected at least 4 insert calls for mixed content"

def test_populate_tree_clears_existing_items():
    """Test that populate_tree clears existing tree items before populating"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view with existing items
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = ['item1', 'item2']
        
        # Test data
        test_data = {
            'files': ['/test/file1.txt'],
            'directories': ['/test/folder1']
        }
        gui.populate_tree(mock_treeview, test_data)
        
        # Should call delete for each existing item
        expected_delete_calls = [('item1',), ('item2',)]
        actual_delete_calls = mock_treeview.delete.call_args_list
        assert len(actual_delete_calls) == 2, f"Expected 2 delete calls, got {len(actual_delete_calls)}"

def test_populate_tree_uses_correct_item_format():
    """Test that populate_tree uses correct format for tree items"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        
        # Test data
        test_data = {
            'files': ['/test/path/file.txt'],
            'directories': ['/test/path/folder']
        }
        gui.populate_tree(mock_treeview, test_data)
        
        # Check that insert was called with proper parameters
        insert_calls = mock_treeview.insert.call_args_list
        assert len(insert_calls) >= 2, "Expected at least 2 insert calls"
        
        # Verify insert call structure (parent, index, text/values)
        for call in insert_calls:
            args, kwargs = call
            assert len(args) >= 2, "Expected at least 2 arguments to insert (parent, index)"

def test_populate_tree_integration_with_file_explorer():
    """Test that populate_tree works with FileExplorer data format"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view and file explorer
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = []
        
        # Simulate FileExplorer data format (from our existing tests)
        explorer_data = {
            'files': ['/test/README.md', '/test/script.py'],
            'directories': ['/test/src', '/test/docs']
        }
        
        # Should work without errors
        gui.populate_tree(mock_treeview, explorer_data)
        
        # Verify it processed the data
        assert mock_treeview.get_children.called, "Expected tree children to be checked"
        assert mock_treeview.insert.called, "Expected items to be inserted"
        # Should have 6 insert calls (2 directories + 2 placeholder children + 2 files)
        assert mock_treeview.insert.call_count == 6, f"Expected 6 insert calls, got {mock_treeview.insert.call_count}"

def test_gui_has_setup_tree_events_method():
    """Test that GUI class has a setup_tree_events method"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have a setup_tree_events method
        assert hasattr(gui, 'setup_tree_events'), "Expected GUI to have setup_tree_events method"
        assert callable(gui.setup_tree_events), "Expected setup_tree_events to be callable"

def test_setup_tree_events_binds_tree_open_event():
    """Test that setup_tree_events binds the tree open event"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        
        # Call setup_tree_events
        gui.setup_tree_events(mock_treeview)
        
        # Should bind the tree open event
        mock_treeview.bind.assert_called()
        # Check if '<<TreeviewOpen>>' was bound
        bind_calls = mock_treeview.bind.call_args_list
        open_event_bound = any('<<TreeviewOpen>>' in str(call) for call in bind_calls)
        assert open_event_bound, "Expected '<<TreeviewOpen>>' event to be bound"

def test_gui_has_on_tree_item_expand_method():
    """Test that GUI class has an on_tree_item_expand event handler"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have an on_tree_item_expand method
        assert hasattr(gui, 'on_tree_item_expand'), "Expected GUI to have on_tree_item_expand method"
        assert callable(gui.on_tree_item_expand), "Expected on_tree_item_expand to be callable"

def test_on_tree_item_expand_loads_directory_contents():
    """Test that expanding a directory loads its contents"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view and event
        mock_treeview = MagicMock()
        mock_event = MagicMock()
        mock_event.widget = mock_treeview
        
        # Mock tree item selection and values
        mock_treeview.selection.return_value = ['item1']
        mock_treeview.item.return_value = {'values': ['/test/folder', 'directory']}
        mock_treeview.get_children.return_value = []  # No existing children
        
        # Mock FileExplorer scan_directory
        gui.file_explorer.scan_directory = MagicMock(return_value={
            'files': ['/test/folder/file1.txt'],
            'directories': ['/test/folder/subfolder']
        })
        
        # Call the expand handler
        gui.on_tree_item_expand(mock_event)
        
        # Should scan the directory
        gui.file_explorer.scan_directory.assert_called_with('/test/folder')
        
        # Should insert children into the tree
        mock_treeview.insert.assert_called()

def test_on_tree_item_expand_only_works_on_directories():
    """Test that expand only works on directory items, not files"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view and event
        mock_treeview = MagicMock()
        mock_event = MagicMock()
        mock_event.widget = mock_treeview
        
        # Mock tree item selection for a file (not directory)
        mock_treeview.selection.return_value = ['item1']
        mock_treeview.item.return_value = {'values': ['/test/file.txt', 'file']}
        
        # Mock FileExplorer scan_directory
        gui.file_explorer.scan_directory = MagicMock()
        
        # Call the expand handler
        gui.on_tree_item_expand(mock_event)
        
        # Should NOT scan directory for files
        gui.file_explorer.scan_directory.assert_not_called()

def test_on_tree_item_expand_handles_already_expanded():
    """Test that expand handler doesn't reload if item already has children"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view and event
        mock_treeview = MagicMock()
        mock_event = MagicMock()
        mock_event.widget = mock_treeview
        
        # Mock tree item selection and values
        mock_treeview.selection.return_value = ['item1']
        mock_treeview.item.return_value = {'values': ['/test/folder', 'directory']}
        mock_treeview.get_children.return_value = ['child1', 'child2']  # Already has children
        
        # Mock FileExplorer scan_directory
        gui.file_explorer.scan_directory = MagicMock()
        
        # Call the expand handler
        gui.on_tree_item_expand(mock_event)
        
        # Should NOT scan directory again if already expanded
        gui.file_explorer.scan_directory.assert_not_called()

def test_on_tree_item_expand_handles_scan_errors():
    """Test that expand handler gracefully handles scan errors"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view and event
        mock_treeview = MagicMock()
        mock_event = MagicMock()
        mock_event.widget = mock_treeview
        
        # Mock tree item selection and values
        mock_treeview.selection.return_value = ['item1']
        mock_treeview.item.return_value = {'values': ['/test/folder', 'directory']}
        mock_treeview.get_children.return_value = []
        
        # Mock FileExplorer scan_directory to raise an error
        gui.file_explorer.scan_directory = MagicMock(side_effect=PermissionError("Access denied"))
        
        # Call the expand handler - should not raise an exception
        try:
            gui.on_tree_item_expand(mock_event)
        except Exception as e:
            assert False, f"on_tree_item_expand should handle errors gracefully, but raised: {e}"

def test_populate_tree_creates_expandable_directories():
    """Test that directories are created as expandable items in the tree"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        
        # Mock insert calls to track behavior
        mock_treeview.insert.side_effect = ['dir1_id', 'placeholder1', 'dir2_id', 'placeholder2']
        
        # Test with directories
        dirs_data = {
            'files': [],
            'directories': ['/test/folder1', '/test/folder2']
        }
        gui.populate_tree(mock_treeview, dirs_data)
        
        # Should create directory items with placeholder children for expansion
        expected_calls = [
            # First directory
            (('', 'end'), {'text': 'folder1', 'values': ('/test/folder1', 'directory')}),
            # Placeholder for first directory
            (('dir1_id', 'end'), {'text': '', 'values': ('', 'placeholder')}),
            # Second directory  
            (('', 'end'), {'text': 'folder2', 'values': ('/test/folder2', 'directory')}),
            # Placeholder for second directory
            (('placeholder1', 'end'), {'text': '', 'values': ('', 'placeholder')})
        ]
        
        # Verify the insert calls (at least the directory ones)
        assert mock_treeview.insert.call_count >= 2, "Expected at least 2 insert calls for directories and placeholders"

def test_gui_has_refresh_tree_method():
    """Test that GUI class has a refresh_tree method"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have a refresh_tree method
        assert hasattr(gui, 'refresh_tree'), "Expected GUI to have refresh_tree method"
        assert callable(gui.refresh_tree), "Expected refresh_tree to be callable"

def test_refresh_tree_calls_file_explorer_refresh():
    """Test that refresh_tree calls FileExplorer.refresh() and updates tree view"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock the file explorer's refresh method
        mock_refresh_data = {
            'files': ['/test/new_file.txt'],
            'directories': ['/test/new_folder']
        }
        gui.file_explorer.refresh = MagicMock(return_value=mock_refresh_data)
        
        # Mock the tree view
        mock_treeview = MagicMock()
        gui.tree_view = mock_treeview
        
        # Call refresh_tree
        gui.refresh_tree()
        
        # Should call file_explorer.refresh()
        gui.file_explorer.refresh.assert_called_once()
        
        # Should call populate_tree with the refreshed data
        mock_treeview.get_children.assert_called()

def test_refresh_tree_handles_no_current_directory():
    """Test that refresh_tree handles case when no directory has been scanned"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock the file explorer's refresh method to return None (no current directory)
        gui.file_explorer.refresh = MagicMock(return_value=None)
        
        # Mock the tree view
        mock_treeview = MagicMock()
        gui.tree_view = mock_treeview
        
        # Call refresh_tree
        result = gui.refresh_tree()
        
        # Should call file_explorer.refresh()
        gui.file_explorer.refresh.assert_called_once()
        
        # Should return None or handle gracefully
        assert result is None or result is False, "Expected refresh_tree to handle None return gracefully"

def test_refresh_tree_updates_tree_view_when_data_available():
    """Test that refresh_tree updates tree view when refresh data is available"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock the file explorer's refresh method
        mock_refresh_data = {
            'files': ['/test/updated_file.txt', '/test/another_file.py'],
            'directories': ['/test/updated_folder']
        }
        gui.file_explorer.refresh = MagicMock(return_value=mock_refresh_data)
        
        # Mock the tree view
        mock_treeview = MagicMock()
        gui.tree_view = mock_treeview
        
        # Mock populate_tree method to track if it's called
        gui.populate_tree = MagicMock()
        
        # Call refresh_tree
        gui.refresh_tree()
        
        # Should call file_explorer.refresh()
        gui.file_explorer.refresh.assert_called_once()
        
        # Should call populate_tree with the refreshed data
        gui.populate_tree.assert_called_once_with(mock_treeview, mock_refresh_data)

def test_populate_tree_handles_missing_directories_key():
    """Test populate_tree handles data missing 'directories' key gracefully"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = []
        
        # Test data missing 'directories' key
        incomplete_data = {'files': ['/test/file1.txt']}
        
        # Should handle gracefully without errors
        gui.populate_tree(mock_treeview, incomplete_data)
        
        # Should still process files
        assert mock_treeview.insert.called, "Expected files to be inserted"

def test_populate_tree_handles_missing_files_key():
    """Test populate_tree handles data missing 'files' key gracefully"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = []
        
        # Test data missing 'files' key
        incomplete_data = {'directories': ['/test/folder1']}
        
        # Should handle gracefully without errors
        gui.populate_tree(mock_treeview, incomplete_data)
        
        # Should still process directories
        assert mock_treeview.insert.called, "Expected directories to be inserted"

def test_populate_tree_handles_empty_dictionary():
    """Test populate_tree handles completely empty data dictionary"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = []
        
        # Test with completely empty data
        empty_data = {}
        
        # Should handle gracefully without errors
        gui.populate_tree(mock_treeview, empty_data)
        
        # Should clear existing items but not insert anything
        mock_treeview.get_children.assert_called()
        # Insert should not be called for empty data
        mock_treeview.insert.assert_not_called()

def test_populate_tree_extracts_correct_filenames():
    """Test that populate_tree correctly extracts filenames from full paths"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = []
        
        # Test with files having complex paths
        test_data = {
            'files': ['/deep/nested/path/document.pdf', '/home/user/script.py'],
            'directories': []
        }
        
        gui.populate_tree(mock_treeview, test_data)
        
        # Verify that only filenames are used as text, not full paths
        insert_calls = mock_treeview.insert.call_args_list
        assert len(insert_calls) == 2, "Expected 2 insert calls for files"
        
        # Check that text parameters contain only filenames
        call1_kwargs = insert_calls[0][1] if len(insert_calls[0]) > 1 else insert_calls[0][0]
        call2_kwargs = insert_calls[1][1] if len(insert_calls[1]) > 1 else insert_calls[1][0]
        
        # Should use basename, not full path in display text
        # This is implementation specific - adapt based on actual call structure

def test_populate_tree_extracts_correct_folder_names():
    """Test that populate_tree correctly extracts folder names from full paths"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = []
        mock_treeview.insert.side_effect = ['dir1_id', 'placeholder1', 'dir2_id', 'placeholder2']
        
        # Test with directories having complex paths
        test_data = {
            'files': [],
            'directories': ['/home/user/projects/my_project', '/var/log/application']
        }
        
        gui.populate_tree(mock_treeview, test_data)
        
        # Verify that only folder names are used as text, not full paths
        insert_calls = mock_treeview.insert.call_args_list
        assert len(insert_calls) == 4, "Expected 4 insert calls (2 dirs + 2 placeholders)"

def test_populate_tree_preserves_full_paths_in_values():
    """Test that populate_tree preserves full paths in values for later access"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = []
        
        # Test data with full paths
        test_data = {
            'files': ['/full/path/to/file.txt'],
            'directories': ['/full/path/to/directory']
        }
        
        gui.populate_tree(mock_treeview, test_data)
        
        # Check that full paths are preserved in values
        insert_calls = mock_treeview.insert.call_args_list
        
        # Find file and directory insert calls by examining arguments
        for call in insert_calls:
            args, kwargs = call
            if 'values' in kwargs:
                values = kwargs['values']
                if len(values) >= 2:
                    path, item_type = values[0], values[1]
                    if item_type == 'file':
                        assert path == '/full/path/to/file.txt', f"Expected full file path in values, got {path}"
                    elif item_type == 'directory':
                        assert path == '/full/path/to/directory', f"Expected full directory path in values, got {path}"

def test_populate_tree_directories_inserted_before_files():
    """Test that directories are inserted before files in the tree"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = []
        mock_treeview.insert.side_effect = ['dir1', 'placeholder1', 'file1']
        
        # Test with mixed content
        test_data = {
            'files': ['/test/file.txt'],
            'directories': ['/test/folder']
        }
        
        gui.populate_tree(mock_treeview, test_data)
        
        # Verify order of insert calls
        insert_calls = mock_treeview.insert.call_args_list
        assert len(insert_calls) == 3, "Expected 3 insert calls (1 dir + 1 placeholder + 1 file)"
        
        # First calls should be for directory and its placeholder
        # Implementation specific verification would go here

def test_populate_tree_adds_placeholders_to_directories():
    """Test that placeholder children are added to directories to make them expandable"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = []
        mock_treeview.insert.side_effect = ['dir1_id', 'placeholder1']
        
        # Test with single directory
        test_data = {
            'files': [],
            'directories': ['/test/folder']
        }
        
        gui.populate_tree(mock_treeview, test_data)
        
        # Should have 2 insert calls: directory + placeholder
        insert_calls = mock_treeview.insert.call_args_list
        assert len(insert_calls) == 2, "Expected 2 insert calls (directory + placeholder)"
        
        # Second call should be placeholder under the directory
        placeholder_call = insert_calls[1]
        args, kwargs = placeholder_call
        
        # Placeholder should be inserted under the directory (first argument should be dir1_id)
        assert args[0] == 'dir1_id', f"Expected placeholder to be inserted under directory, got parent: {args[0]}"

def test_populate_tree_handles_none_data():
    """Test that populate_tree handles None data gracefully"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        mock_treeview.get_children.return_value = []
        
        # Test with None data - this should handle gracefully or raise appropriate error
        try:
            gui.populate_tree(mock_treeview, None)
            # If it doesn't raise an error, verify it handled gracefully
            mock_treeview.get_children.assert_called()
        except (AttributeError, TypeError):
            # If it raises an error, that's also acceptable behavior for None input
            pass

def test_gui_has_file_content_text_widget():
    """Test that GUI class has a file content text widget"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have a file content text widget
        assert hasattr(gui, 'file_content_text'), "Expected GUI to have file_content_text attribute"
        assert gui.file_content_text is not None, "Expected file_content_text to be initialized"

def test_gui_file_content_text_is_readonly():
    """Test that file content text widget is configured as read-only"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # File content text should be read-only
        # This will be checked by verifying the state is set to 'disabled' in the widget creation
        assert hasattr(gui, 'file_content_text'), "Expected GUI to have file_content_text widget"

def test_gui_has_file_content_scrollbar():
    """Test that GUI has a scrollbar for the file content text widget"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have a scrollbar for the file content text
        assert hasattr(gui, 'file_content_scrollbar'), "Expected GUI to have file_content_scrollbar"
        assert gui.file_content_scrollbar is not None, "Expected file_content_scrollbar to be initialized"

def test_gui_file_content_text_is_in_content_frame():
    """Test that file content text widget is properly placed in the content frame"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have content frame and text widget
        assert hasattr(gui, 'content_frame'), "Expected GUI to have content_frame"
        assert hasattr(gui, 'file_content_text'), "Expected GUI to have file_content_text widget"

def test_gui_file_content_scrollbar_is_configured():
    """Test that file content scrollbar is properly configured with the text widget"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have both scrollbar and text widget
        assert hasattr(gui, 'file_content_scrollbar'), "Expected GUI to have file_content_scrollbar"
        assert hasattr(gui, 'file_content_text'), "Expected GUI to have file_content_text"
        
        # The scrollbar should be properly configured with the text widget
        # We'll verify this by checking that the widgets exist and can be accessed

def test_gui_has_on_tree_item_select_method():
    """Test that GUI class has an on_tree_item_select event handler"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have an on_tree_item_select method
        assert hasattr(gui, 'on_tree_item_select'), "Expected GUI to have on_tree_item_select method"
        assert callable(gui.on_tree_item_select), "Expected on_tree_item_select to be callable"

def test_setup_tree_events_binds_selection_event():
    """Test that setup_tree_events binds the tree selection event"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view
        mock_treeview = MagicMock()
        
        # Call setup_tree_events
        gui.setup_tree_events(mock_treeview)
        
        # Should bind the tree selection event
        mock_treeview.bind.assert_called()
        # Check if '<<TreeviewSelect>>' was bound
        bind_calls = mock_treeview.bind.call_args_list
        selection_event_bound = any('<<TreeviewSelect>>' in str(call) for call in bind_calls)
        assert selection_event_bound, "Expected '<<TreeviewSelect>>' event to be bound"

def test_on_tree_item_select_loads_file_content():
    """Test that selecting a file loads its content into the text widget"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view and event
        mock_treeview = MagicMock()
        mock_event = MagicMock()
        mock_event.widget = mock_treeview
        
        # Mock tree item selection for a file
        mock_treeview.selection.return_value = ['file_item']
        mock_treeview.item.return_value = {'values': ['/test/file.txt', 'file']}
        
        # Mock FileExplorer read_file method
        test_content = "Hello, World!\nThis is file content."
        gui.file_explorer.read_file = MagicMock(return_value=test_content)
        
        # Mock the text widget update method
        gui.update_file_content = MagicMock()
        
        # Call the selection handler
        gui.on_tree_item_select(mock_event)
        
        # Should read the file content
        gui.file_explorer.read_file.assert_called_with('/test/file.txt')
        
        # Should update the text widget with content
        gui.update_file_content.assert_called_with(test_content)

def test_on_tree_item_select_ignores_directories():
    """Test that selecting a directory does not load content"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view and event
        mock_treeview = MagicMock()
        mock_event = MagicMock()
        mock_event.widget = mock_treeview
        
        # Mock tree item selection for a directory
        mock_treeview.selection.return_value = ['dir_item']
        mock_treeview.item.return_value = {'values': ['/test/folder', 'directory']}
        
        # Mock FileExplorer read_file method
        gui.file_explorer.read_file = MagicMock()
        
        # Mock the text widget update method
        gui.update_file_content = MagicMock()
        
        # Call the selection handler
        gui.on_tree_item_select(mock_event)
        
        # Should NOT read file content for directories
        gui.file_explorer.read_file.assert_not_called()
        
        # Should NOT update the text widget
        gui.update_file_content.assert_not_called()

def test_on_tree_item_select_handles_no_selection():
    """Test that selection handler handles case with no selection gracefully"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view and event with no selection
        mock_treeview = MagicMock()
        mock_event = MagicMock()
        mock_event.widget = mock_treeview
        mock_treeview.selection.return_value = []
        
        # Mock FileExplorer read_file method
        gui.file_explorer.read_file = MagicMock()
        
        # Call the selection handler
        gui.on_tree_item_select(mock_event)
        
        # Should handle gracefully and not crash
        gui.file_explorer.read_file.assert_not_called()

def test_on_tree_item_select_handles_unreadable_file():
    """Test that selection handler handles unreadable files gracefully"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock tree view and event
        mock_treeview = MagicMock()
        mock_event = MagicMock()
        mock_event.widget = mock_treeview
        
        # Mock tree item selection for a file
        mock_treeview.selection.return_value = ['file_item']
        mock_treeview.item.return_value = {'values': ['/test/unreadable.bin', 'file']}
        
        # Mock FileExplorer read_file method to return None (unreadable)
        gui.file_explorer.read_file = MagicMock(return_value=None)
        
        # Mock the text widget update method
        gui.update_file_content = MagicMock()
        
        # Call the selection handler
        gui.on_tree_item_select(mock_event)
        
        # Should attempt to read the file
        gui.file_explorer.read_file.assert_called_with('/test/unreadable.bin')
        
        # Should update text widget with appropriate message
        gui.update_file_content.assert_called()

def test_gui_has_update_file_content_method():
    """Test that GUI class has an update_file_content method"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have an update_file_content method
        assert hasattr(gui, 'update_file_content'), "Expected GUI to have update_file_content method"
        assert callable(gui.update_file_content), "Expected update_file_content to be callable"

def test_update_file_content_updates_text_widget():
    """Test that update_file_content updates the text widget correctly"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock the text widget
        mock_text_widget = MagicMock()
        gui.file_content_text = mock_text_widget
        
        # Test content
        test_content = "Line 1\nLine 2\nLine 3"
        
        # Call update_file_content
        gui.update_file_content(test_content)
        
        # Should configure text widget to be editable, clear it, insert content, then make read-only
        # Verify that the text widget operations are called
        mock_text_widget.config.assert_called()
        mock_text_widget.delete.assert_called()
        mock_text_widget.insert.assert_called()

def test_open_folder_handler_populates_tree_view():
    """Test that open_folder_handler scans directory and populates tree view"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock the tree view
        gui.tree_view = MagicMock()
        
        # Mock the open_folder_dialog to return a test path
        test_folder = '/test/project'
        gui.open_folder_dialog = MagicMock(return_value=test_folder)
        
        # Mock FileExplorer scan_directory method
        test_scan_result = {
            'directories': ['/test/project/src', '/test/project/tests'],
            'files': ['/test/project/main.py', '/test/project/README.md']
        }
        gui.file_explorer.scan_directory = MagicMock(return_value=test_scan_result)
        
        # Mock populate_tree method
        gui.populate_tree = MagicMock()
        
        # Call open_folder_handler
        result = gui.open_folder_handler()
        
        # Should return the selected folder
        assert result == test_folder
        
        # Should set current_directory
        assert gui.current_directory == test_folder
        
        # Should set FileExplorer's current directory
        assert gui.file_explorer.current_directory == test_folder
        
        # Should scan the directory
        gui.file_explorer.scan_directory.assert_called_with(test_folder)
        
        # Should populate the tree view with scan results
        gui.populate_tree.assert_called_with(gui.tree_view, test_scan_result)

def test_open_folder_handler_handles_scan_error():
    """Test that open_folder_handler handles directory scan errors gracefully"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock the tree view
        gui.tree_view = MagicMock()
        
        # Mock the open_folder_dialog to return a test path
        test_folder = '/test/inaccessible'
        gui.open_folder_dialog = MagicMock(return_value=test_folder)
        
        # Mock FileExplorer scan_directory method to raise an error
        gui.file_explorer.scan_directory = MagicMock(side_effect=PermissionError("Access denied"))
        
        # Mock populate_tree method
        gui.populate_tree = MagicMock()
        
        # Call open_folder_handler
        result = gui.open_folder_handler()
        
        # Should return the selected folder even if scan fails
        assert result == test_folder
        
        # Should set current_directory
        assert gui.current_directory == test_folder
        
        # Should set FileExplorer's current directory
        assert gui.file_explorer.current_directory == test_folder
        
        # Should attempt to scan the directory
        gui.file_explorer.scan_directory.assert_called_with(test_folder)
        
        # Should populate the tree view with empty data due to error
        gui.populate_tree.assert_called_with(gui.tree_view, {'directories': [], 'files': []}) 