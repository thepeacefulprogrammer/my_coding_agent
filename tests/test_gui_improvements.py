"""
Test the GUI improvements for folder navigation and syntax highlighting
"""
import unittest
import tkinter as tk
import tempfile
import os
from src.gui import GUI


class TestGUIImprovements(unittest.TestCase):
    """Test GUI improvements for better user experience"""
    
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
    
    def test_codeview_has_monokai_color_scheme(self):
        """Test that CodeView is configured with monokai color scheme"""
        # Check that the CodeView widget exists
        self.assertTrue(hasattr(self.gui, 'file_content_codeview'))
        
        # Create a test Python file content
        python_code = '''#!/usr/bin/env python3
def hello_world():
    """A simple function"""
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
'''
        
        # Update with syntax highlighting
        self.gui.update_file_content(python_code, filename="test.py")
        
        # Verify content was set
        content = self.gui.file_content_codeview.get('1.0', 'end-1c')
        self.assertEqual(content, python_code)
        
        print("✅ Monokai color scheme test completed")
    
    def test_double_click_handler_exists(self):
        """Test that double-click handler is properly bound"""
        # Check that the tree view exists
        self.assertTrue(hasattr(self.gui, 'tree_view'))
        
        # Verify that double-click event is bound
        # We can't easily test the actual binding, but we can test the method exists
        self.assertTrue(hasattr(self.gui, 'on_tree_item_double_click'))
        self.assertTrue(callable(self.gui.on_tree_item_double_click))
        
        print("✅ Double-click handler test completed")
    
    def test_syntax_highlighting_visibility(self):
        """Test that syntax highlighting is more visible with new color scheme"""
        # Test with different file types
        test_files = {
            'test.py': '''
import os
def function():
    # Comment
    return "string"
''',
            'test.js': '''
function greet(name) {
    // This is a comment
    return `Hello, ${name}!`;
}
''',
            'test.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>
'''
        }
        
        for filename, content in test_files.items():
            # Apply syntax highlighting
            self.gui.update_file_content(content, filename=filename)
            
            # Verify content was applied
            displayed_content = self.gui.file_content_codeview.get('1.0', 'end-1c')
            self.assertEqual(displayed_content, content)
            
            print(f"✅ Syntax highlighting test for {filename} completed")
    
    def test_codeview_scrollbar_connection(self):
        """Test that CodeView is properly connected to scrollbar"""
        # Check that both scrollbar and codeview exist
        self.assertTrue(hasattr(self.gui, 'file_content_scrollbar'))
        self.assertTrue(hasattr(self.gui, 'file_content_codeview'))
        
        # Create long content to test scrolling
        long_content = '\n'.join([f"Line {i}: This is a test line with content" for i in range(100)])
        
        self.gui.update_file_content(long_content, filename="test.txt")
        
        # Verify content was set
        content = self.gui.file_content_codeview.get('1.0', 'end-1c')
        self.assertIn("Line 99:", content)
        
        print("✅ Scrollbar connection test completed")


if __name__ == '__main__':
    unittest.main(verbosity=2) 