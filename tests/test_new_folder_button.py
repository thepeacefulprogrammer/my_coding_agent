import unittest
import tkinter as tk
from src.gui import GUI


class TestNewFolderButton(unittest.TestCase):
    """Test new folder button functionality"""
    
    def setUp(self):
        """Set up test environment with real tkinter root"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.gui = GUI(self.root)
    
    def tearDown(self):
        """Clean up test environment"""
        self.root.destroy()

    def test_gui_module_has_new_folder_handler(self):
        """Test that GUI class has a new_folder_handler method"""
        # Should have a new_folder_handler method
        self.assertTrue(hasattr(self.gui, 'new_folder_handler'), "Expected GUI to have new_folder_handler method")
        self.assertTrue(callable(self.gui.new_folder_handler), "Expected new_folder_handler to be callable")

    def test_new_folder_handler_is_stub(self):
        """Test that new_folder_handler method exists and is implemented"""
        # Method should exist and be callable
        self.assertTrue(hasattr(self.gui, 'new_folder_handler'), "Expected GUI to have new_folder_handler method")
        
        # Method should be implementable and callable without errors when no directory is set
        result = self.gui.new_folder_handler()
        
        # When no current directory is set, it should return None
        self.assertIsNone(result, "Expected new_folder_handler to return None when no current directory is set")


if __name__ == '__main__':
    unittest.main() 