import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
import tkinter as tk
from src.gui import GUI


class TestDialogBehavior(unittest.TestCase):
    """Test dialog behavior for GUI components"""
    
    def setUp(self):
        """Set up test environment with real tkinter root"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.gui = GUI(self.root)
    
    def tearDown(self):
        """Clean up test environment"""
        self.root.destroy()
    
    def test_open_folder_handler_calls_dialog(self):
        """Test that open_folder_handler calls open_folder_dialog and handles result"""
        # Mock the open_folder_dialog method
        with patch.object(self.gui, 'open_folder_dialog', return_value="/selected/folder") as mock_dialog:
            # Test that open_folder_handler should call open_folder_dialog
            result = self.gui.open_folder_handler()
            
            # Verify open_folder_dialog was called
            mock_dialog.assert_called_once()
            
            # Verify it returns the selected folder
            self.assertEqual(result, "/selected/folder", "Expected handler to return selected folder path")

    def test_new_folder_handler_calls_dialog(self):
        """Test that new_folder_handler calls new_folder_dialog with current directory"""
        # Set a current directory for the GUI
        self.gui.current_directory = "/current/working/dir"
        
        # Mock the new_folder_dialog method
        with patch.object(self.gui, 'new_folder_dialog', return_value="/current/working/dir/new_folder") as mock_dialog:
            # Test that new_folder_handler should call new_folder_dialog
            result = self.gui.new_folder_handler()
            
            # Verify new_folder_dialog was called with current directory
            mock_dialog.assert_called_once_with("/current/working/dir")
            
            # Verify it returns the created folder
            self.assertEqual(result, "/current/working/dir/new_folder", "Expected handler to return created folder path")

    def test_dialog_error_handling(self):
        """Test that dialogs handle OS errors gracefully"""
        # Test new_folder_dialog with permission error
        with patch('tkinter.simpledialog.askstring', return_value="test_folder"), \
             patch('os.mkdir', side_effect=PermissionError("Permission denied")) as mock_mkdir:
            
            # Should handle the error gracefully and return None
            result = self.gui.new_folder_dialog("/readonly/path")
            
            # Verify mkdir was called
            mock_mkdir.assert_called_once()
            
            # Should return None when creation fails
            self.assertIsNone(result, "Expected method to return None when folder creation fails")

    def test_dialog_with_empty_folder_name(self):
        """Test that new_folder_dialog handles empty/invalid folder names"""
        # Test with empty string
        with patch('tkinter.simpledialog.askstring', return_value=""), \
             patch('os.mkdir') as mock_mkdir:
            
            result = self.gui.new_folder_dialog("/test/path")
            
            # Should not call mkdir with empty name
            mock_mkdir.assert_not_called()
            self.assertIsNone(result, "Expected method to return None for empty folder name")
        
        # Test with whitespace-only string
        with patch('tkinter.simpledialog.askstring', return_value="   "), \
             patch('os.mkdir') as mock_mkdir:
            
            result = self.gui.new_folder_dialog("/test/path")
            
            # Should not call mkdir with whitespace-only name
            mock_mkdir.assert_not_called()
            self.assertIsNone(result, "Expected method to return None for whitespace-only folder name")

    def test_gui_has_current_directory_attribute(self):
        """Test that GUI maintains a current_directory attribute"""
        # Should have a current_directory attribute (initially None or home directory)
        self.assertTrue(hasattr(self.gui, 'current_directory'), "Expected GUI to have current_directory attribute")


if __name__ == '__main__':
    unittest.main() 