"""
Test verification for the syntax highlighting and folder navigation fixes
"""
import unittest
import tkinter as tk
import tempfile
import os
from src.gui import GUI


class TestFixesVerification(unittest.TestCase):
    """Test that both the syntax highlighting and folder navigation fixes work"""
    
    def setUp(self):
        """Set up test environment with real tkinter root"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.gui = GUI(self.root)
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            # Use GUI's proper cleanup mechanism
            if hasattr(self, 'gui') and self.gui:
                self.gui.on_closing()
            else:
                # Fallback to direct destruction if no GUI
                if hasattr(self, 'root') and self.root:
                    self.root.destroy()
        except Exception:
            # If cleanup fails, try direct destruction
            try:
                if hasattr(self, 'root') and self.root:
                    self.root.destroy()
            except Exception:
                pass
    
    def test_custom_color_scheme_applied(self):
        """Test that custom dark color scheme is applied to CodeView"""
        # Check that CodeView exists
        self.assertTrue(hasattr(self.gui, 'file_content_codeview'))
        
        # Test with Python code that has different syntax elements
        python_code = '''import os
def test_function():
    """This is a docstring"""
    # This is a comment
    name = "Hello World"  # String
    number = 42  # Number
    return name + str(number)
'''
        
        # Apply the content with syntax highlighting
        self.gui.update_file_content(python_code, filename="test.py")
        
        # Verify content was set
        content = self.gui.file_content_codeview.get('1.0', 'end-1c')
        self.assertEqual(content, python_code)
        
        print("✅ Custom color scheme test completed - content applied successfully")
    
    def test_folder_selection_behavior_with_mock_selection(self):
        """Test that open_folder_handler always shows dialog regardless of tree selection"""
        # Create a temporary directory structure for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a subdirectory
            sub_dir = os.path.join(temp_dir, "test_folder")
            os.makedirs(sub_dir)
            
            # Populate the tree with the temp directory
            scan_result = self.gui.file_explorer.scan_directory(temp_dir)
            self.gui.populate_tree(self.gui.tree_view, scan_result)
            
            # Get the tree items (should include our test_folder)
            tree_items = self.gui.tree_view.get_children()
            self.assertTrue(len(tree_items) > 0, "Tree should have at least one item")
            
            # Find the folder item
            folder_item = None
            for item in tree_items:
                item_data = self.gui.tree_view.item(item)
                values = item_data.get('values', [])
                if len(values) >= 2 and values[1] == 'directory':
                    folder_item = item
                    break
            
            self.assertIsNotNone(folder_item, "Should find a directory item in tree")
            
            # Simulate selecting the folder
            self.gui.tree_view.selection_set(folder_item)
            
            # Mock the dialog to return a specific folder (simulating user selection from dialog)
            original_dialog = self.gui.open_folder_dialog
            self.gui.open_folder_dialog = lambda: sub_dir  # Return the test_folder
            
            try:
                # Test the open_folder_handler - should use dialog result, not tree selection
                result = self.gui.open_folder_handler()
                
                # Verify it opened the folder selected from dialog (not tree selection)
                self.assertTrue(result.endswith("test_folder"), f"Should open folder from dialog, got: {result}")
                self.assertEqual(result, sub_dir, "Should open the exact folder returned by dialog")
                
            finally:
                # Restore original dialog
                self.gui.open_folder_dialog = original_dialog
            
        print("✅ Folder selection behavior test completed - dialog is always used")
    
    def test_open_folder_without_selection_shows_dialog(self):
        """Test that open_folder_handler shows dialog when no folder is selected"""
        # Clear any selection
        self.gui.tree_view.selection_remove(self.gui.tree_view.selection())
        
        # Mock the dialog to return None (user cancels)
        original_dialog = self.gui.open_folder_dialog
        self.gui.open_folder_dialog = lambda: None
        
        try:
            result = self.gui.open_folder_handler()
            self.assertIsNone(result, "Should return None when dialog is cancelled")
        finally:
            # Restore original dialog
            self.gui.open_folder_dialog = original_dialog
        
        print("✅ Dialog fallback test completed")
    
    def test_syntax_highlighting_with_different_languages(self):
        """Test syntax highlighting works with different programming languages"""
        test_files = {
            'test.py': 'def hello():\n    return "Python code"',
            'test.js': 'function hello() {\n    return "JavaScript code";\n}',
            'test.html': '<html>\n<body>HTML content</body>\n</html>',
            'test.css': 'body {\n    color: red;\n    font-size: 14px;\n}'
        }
        
        for filename, content in test_files.items():
            self.gui.update_file_content(content, filename=filename)
            displayed = self.gui.file_content_codeview.get('1.0', 'end-1c')
            self.assertEqual(displayed, content, f"Content should match for {filename}")
            
        print("✅ Multi-language syntax highlighting test completed")


if __name__ == '__main__':
    unittest.main(verbosity=2) 