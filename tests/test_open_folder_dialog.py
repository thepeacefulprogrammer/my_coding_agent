from unittest.mock import patch, MagicMock

def test_open_folder_dialog_calls_askdirectory():
    """Test that open_folder_dialog calls filedialog.askdirectory"""
    # Mock tkinter to avoid display issues
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Test that open_folder_dialog method exists
        assert hasattr(gui, 'open_folder_dialog'), "Expected GUI to have open_folder_dialog method"
        
        # Mock the filedialog after import
        with patch('src.gui.filedialog.askdirectory', return_value="/test/folder/path") as mock_ask:
            # Call the method and verify it calls askdirectory
            result = gui.open_folder_dialog()
            
            # Verify askdirectory was called
            mock_ask.assert_called_once()
            assert result == "/test/folder/path", "Expected method to return selected folder path"

def test_open_folder_dialog_with_title():
    """Test that open_folder_dialog passes title to askdirectory"""
    # Mock tkinter to avoid display issues  
    with patch.dict('sys.modules', {'tkinter': MagicMock(), 'tkinter.filedialog': MagicMock()}):
        from src.gui import GUI
        
        # Create GUI instance with mocked root
        mock_root = MagicMock()
        gui = GUI(mock_root)
        
        # Mock the filedialog after import
        with patch('src.gui.filedialog.askdirectory', return_value="/test/folder") as mock_ask:
            # Call the method
            gui.open_folder_dialog()
            
            # Verify askdirectory was called with title
            mock_ask.assert_called_once_with(title="Select Project Folder") 