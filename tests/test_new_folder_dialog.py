from unittest.mock import patch, MagicMock
import tempfile
import os

def test_new_folder_dialog_calls_askstring():
    """Test that new_folder_dialog calls simpledialog.askstring"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Test that new_folder_dialog method exists
        assert hasattr(gui, 'new_folder_dialog'), "Expected GUI to have new_folder_dialog method"
        
        # Mock the simpledialog and os after import
        with patch('src.gui.simpledialog.askstring', return_value="test_folder") as mock_ask, \
             patch('src.gui.os.mkdir') as mock_mkdir, \
             patch('src.gui.os.path.join', return_value="/test/parent/path/test_folder") as mock_join:
            
            # Call the method
            result = gui.new_folder_dialog("/test/parent/path")
            
            # Verify askstring was called
            mock_ask.assert_called_once_with("New Folder", "Enter folder name:")
            
            # Verify os.path.join was called
            mock_join.assert_called_once_with("/test/parent/path", "test_folder")
            
            # Verify mkdir was called with correct path
            mock_mkdir.assert_called_once_with("/test/parent/path/test_folder")
            
            # Verify it returns the created path
            assert result == "/test/parent/path/test_folder", "Expected method to return created folder path"

def test_new_folder_dialog_with_canceled_input():
    """Test that new_folder_dialog handles user canceling the dialog"""
    # Mock tkinter to avoid display issues  
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock the simpledialog and os after import
        with patch('src.gui.simpledialog.askstring', return_value=None) as mock_ask, \
             patch('src.gui.os.mkdir') as mock_mkdir:
            
            # Call the method
            result = gui.new_folder_dialog("/test/parent/path")
            
            # Verify askstring was called
            mock_ask.assert_called_once_with("New Folder", "Enter folder name:")
            
            # Verify mkdir was NOT called
            mock_mkdir.assert_not_called()
            
            # Verify it returns None when canceled
            assert result is None, "Expected method to return None when user cancels"

def test_new_folder_dialog_creates_actual_folder():
    """Test that new_folder_dialog actually creates a folder when given valid input"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock(), 'tkinter.simpledialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Use a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the simpledialog to return a test folder name
            with patch('src.gui.simpledialog.askstring', return_value="test_new_folder") as mock_ask:
                # Call the method
                result = gui.new_folder_dialog(temp_dir)
                
                # Verify the folder was actually created
                expected_path = os.path.join(temp_dir, "test_new_folder")
                assert os.path.exists(expected_path), "Expected folder to be created"
                assert os.path.isdir(expected_path), "Expected created path to be a directory"
                assert result == expected_path, "Expected method to return created folder path" 