from unittest.mock import patch, MagicMock
import tempfile
import os

def test_open_folder_handler_calls_dialog():
    """Test that open_folder_handler calls open_folder_dialog and handles result"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock the open_folder_dialog method
        with patch.object(gui, 'open_folder_dialog', return_value="/selected/folder") as mock_dialog:
            # Test that open_folder_handler should call open_folder_dialog
            # Currently it's a stub, so this test will fail until we implement it
            result = gui.open_folder_handler()
            
            # Verify open_folder_dialog was called
            mock_dialog.assert_called_once()
            
            # Verify it returns the selected folder
            assert result == "/selected/folder", "Expected handler to return selected folder path"

def test_new_folder_handler_calls_dialog():
    """Test that new_folder_handler calls new_folder_dialog with current directory"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Set a current directory for the GUI
        gui.current_directory = "/current/working/dir"
        
        # Mock the new_folder_dialog method
        with patch.object(gui, 'new_folder_dialog', return_value="/current/working/dir/new_folder") as mock_dialog:
            # Test that new_folder_handler should call new_folder_dialog
            # Currently it's a stub, so this test will fail until we implement it
            result = gui.new_folder_handler()
            
            # Verify new_folder_dialog was called with current directory
            mock_dialog.assert_called_once_with("/current/working/dir")
            
            # Verify it returns the created folder
            assert result == "/current/working/dir/new_folder", "Expected handler to return created folder path"

def test_dialog_error_handling():
    """Test that dialogs handle OS errors gracefully"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Test new_folder_dialog with permission error
        with patch('src.gui.simpledialog.askstring', return_value="test_folder"), \
             patch('src.gui.os.mkdir', side_effect=PermissionError("Permission denied")) as mock_mkdir:
            
            # Should handle the error gracefully and return None
            result = gui.new_folder_dialog("/readonly/path")
            
            # Verify mkdir was called
            mock_mkdir.assert_called_once()
            
            # Should return None when creation fails
            assert result is None, "Expected method to return None when folder creation fails"

def test_dialog_with_empty_folder_name():
    """Test that new_folder_dialog handles empty/invalid folder names"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Test with empty string
        with patch('src.gui.simpledialog.askstring', return_value=""), \
             patch('src.gui.os.mkdir') as mock_mkdir:
            
            result = gui.new_folder_dialog("/test/path")
            
            # Should not call mkdir with empty name
            mock_mkdir.assert_not_called()
            assert result is None, "Expected method to return None for empty folder name"
        
        # Test with whitespace-only string
        with patch('src.gui.simpledialog.askstring', return_value="   "), \
             patch('src.gui.os.mkdir') as mock_mkdir:
            
            result = gui.new_folder_dialog("/test/path")
            
            # Should not call mkdir with whitespace-only name
            mock_mkdir.assert_not_called()
            assert result is None, "Expected method to return None for whitespace-only folder name"

def test_gui_has_current_directory_attribute():
    """Test that GUI maintains a current_directory attribute"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Should have a current_directory attribute (initially None or home directory)
        assert hasattr(gui, 'current_directory'), "Expected GUI to have current_directory attribute" 