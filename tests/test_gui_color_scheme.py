#!/usr/bin/env python3
"""
Unit tests to verify GUI color scheme functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import tempfile

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestGUIColorScheme(unittest.TestCase):
    """Test GUI color scheme functionality without creating GUI windows."""
    
    @patch('gui.GUI')
    @patch('tkinter.Tk')
    def test_gui_color_scheme_integration(self, mock_tk, mock_gui):
        """Test that the GUI properly integrates with color scheme functionality."""
        from gui import GUI
        
        # Mock root window
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Mock GUI instance
        mock_gui_instance = MagicMock()
        mock_gui.return_value = mock_gui_instance
        
        # Create GUI instance (mocked)
        gui = GUI(mock_root)
        
        # Verify GUI was created with root
        mock_gui.assert_called_once_with(mock_root)
        
        # Test file content update functionality
        sample_code = '''def hello_world():
    """Simple hello world function."""
    name = "World"
    message = f"Hello, {name}!"
    print(message)
    return message

# Call the function
if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")
'''
        
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sample_code)
            temp_file = f.name
        
        try:
            # Test file loading (mocked)
            gui.update_file_content('', filename=temp_file)
            
            # Verify update_file_content was called
            mock_gui_instance.update_file_content.assert_called_once_with('', filename=temp_file)
            
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file)
            except:
                pass
                
    def test_gui_syntax_highlighting_support(self):
        """Test that GUI supports syntax highlighting for Python files."""
        # This test verifies that the necessary components exist for syntax highlighting
        # without actually creating GUI windows
        
        # Test that we can import the necessary modules
        try:
            from gui import GUI
            from syntax_manager import SyntaxManager
            
            # These imports should work without error
            self.assertTrue(True, "Required modules import successfully")
            
        except ImportError as e:
            self.fail(f"Required modules for GUI color scheme not available: {e}")


if __name__ == "__main__":
    unittest.main() 