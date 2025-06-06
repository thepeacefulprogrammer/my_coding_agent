import unittest
import tempfile
import os
from unittest.mock import patch
import tkinter as tk
from src.gui import GUI


class TestNewFolderDialog(unittest.TestCase):
    """Test new folder dialog functionality"""
    
    def setUp(self):
        """Set up test environment with real tkinter root"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.gui = GUI(self.root)
    
    def tearDown(self):
        """Clean up test environment"""
        self.root.destroy()

    def test_new_folder_dialog_calls_askstring(self):
        """Test that new_folder_dialog calls simpledialog.askstring"""
        # Test that new_folder_dialog method exists
        self.assertTrue(hasattr(self.gui, 'new_folder_dialog'), "Expected GUI to have new_folder_dialog method")
        self.assertTrue(callable(self.gui.new_folder_dialog), "Expected new_folder_dialog to be callable")
        
        # Mock simpledialog.askstring and os.mkdir to avoid side effects
        with patch('tkinter.simpledialog.askstring', return_value="test_folder") as mock_ask, \
             patch('os.mkdir') as mock_mkdir:
            
            # Call the method with a test parent path
            result = self.gui.new_folder_dialog("/test/parent/path")
            
            # Verify askstring was called with proper prompt
            mock_ask.assert_called_once_with("New Folder", "Enter folder name:")
            
            # Verify mkdir was called with the constructed path
            mock_mkdir.assert_called_once_with("/test/parent/path/test_folder")
            
            # Verify it returns the created folder path
            self.assertEqual(result, "/test/parent/path/test_folder")

    def test_new_folder_dialog_with_canceled_input(self):
        """Test that new_folder_dialog handles user canceling the dialog"""
        # Mock user canceling the dialog (returns None)
        with patch('tkinter.simpledialog.askstring', return_value=None) as mock_ask, \
             patch('os.mkdir') as mock_mkdir:
            
            result = self.gui.new_folder_dialog("/test/parent/path")
            
            # Verify askstring was called
            mock_ask.assert_called_once()
            
            # Should not call mkdir when user cancels
            mock_mkdir.assert_not_called()
            
            # Should return None
            self.assertIsNone(result)

    def test_new_folder_dialog_creates_actual_folder(self):
        """Test that new_folder_dialog actually creates a folder when given valid input"""
        # Use a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the askstring to return a folder name
            with patch('tkinter.simpledialog.askstring', return_value="test_folder"):
                result = self.gui.new_folder_dialog(temp_dir)
                
                # Verify the folder was created
                expected_path = os.path.join(temp_dir, "test_folder")
                self.assertTrue(os.path.exists(expected_path), "Expected folder to be created")
                self.assertTrue(os.path.isdir(expected_path), "Expected created path to be a directory")
                
                # Verify it returns the correct path
                self.assertEqual(result, expected_path)


if __name__ == '__main__':
    unittest.main() 