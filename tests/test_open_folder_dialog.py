import unittest
from unittest.mock import patch
import tkinter as tk
from src.gui import GUI


class TestOpenFolderDialog(unittest.TestCase):
    """Test open folder dialog functionality"""
    
    def setUp(self):
        """Set up test environment with real tkinter root"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.gui = GUI(self.root)
    
    def tearDown(self):
        """Clean up test environment"""
        self.root.destroy()
        
    def test_open_folder_dialog_calls_askdirectory(self):
        """Test that open_folder_dialog calls our custom askdirectory_custom"""
        # Test that open_folder_dialog method exists
        self.assertTrue(hasattr(self.gui, 'open_folder_dialog'), "Expected GUI to have open_folder_dialog method")
        self.assertTrue(callable(self.gui.open_folder_dialog), "Expected open_folder_dialog to be callable")
        
        # Mock our custom askdirectory_custom to avoid showing actual dialog
        with patch('src.gui.askdirectory_custom', return_value="/selected/folder") as mock_askdir:
            result = self.gui.open_folder_dialog()
            
            # Verify askdirectory_custom was called
            mock_askdir.assert_called_once()
            # Verify it returns the selected folder
            self.assertEqual(result, "/selected/folder")
    
    def test_open_folder_dialog_with_title(self):
        """Test that open_folder_dialog passes correct parameters to askdirectory_custom"""
        # Mock our custom askdirectory_custom to capture arguments
        with patch('src.gui.askdirectory_custom', return_value="/another/folder") as mock_askdir:
            self.gui.open_folder_dialog()
            
            # Verify askdirectory_custom was called with expected parameters
            mock_askdir.assert_called_once()
            # Check that it was called with the right arguments
            call_args = mock_askdir.call_args
            self.assertEqual(call_args[1]['title'], "Select Project Folder")
            self.assertEqual(call_args[1]['parent'], self.gui.root)


if __name__ == '__main__':
    unittest.main() 