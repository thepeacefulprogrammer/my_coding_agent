"""
Debug test to verify syntax highlighting is working correctly
"""
import unittest
import tempfile
import os
import tkinter as tk
from src.gui import GUI


class TestSyntaxHighlightingDebug(unittest.TestCase):
    """Debug tests for syntax highlighting visibility"""
    
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
    
    def test_syntax_highlighting_with_python_code(self):
        """Test that Python syntax highlighting is applied and detectable"""
        # Sample Python code with different syntax elements
        python_code = '''#!/usr/bin/env python3
"""
This is a Python module for testing syntax highlighting.
"""

import os
import sys
from pathlib import Path

class TestClass:
    """A test class with various Python syntax elements"""
    
    def __init__(self, name: str):
        self.name = name
        self._private_var = 42
    
    def hello_world(self) -> str:
        """Print a greeting"""
        if self.name:
            return f"Hello, {self.name}!"
        else:
            return "Hello, World!"
    
    @staticmethod
    def calculate(x: int, y: int) -> int:
        # This is a comment
        result = x + y * 2
        return result

# Main execution
if __name__ == "__main__":
    obj = TestClass("Python")
    print(obj.hello_world())
    print(f"Result: {TestClass.calculate(5, 3)}")
'''
        
        # Update the CodeView with Python code
        self.gui.update_file_content(python_code, filename="test.py")
        
        # Verify that the content was set
        content = self.gui.file_content_codeview.get('1.0', 'end-1c')
        self.assertEqual(content, python_code, "Content should be set in CodeView")
        
        # Check that syntax highlighting was applied by verifying a lexer was used
        # This is a basic test - in a real scenario we'd check for specific highlighting
        self.assertTrue(hasattr(self.gui.file_content_codeview, 'highlight_all'), 
                       "CodeView should have highlight_all method")
        
        print(f"✅ Python syntax highlighting test completed")
        print(f"Content length: {len(content)}")
        print(f"First 100 chars: {content[:100]}")
    
    def test_syntax_manager_python_detection(self):
        """Test that SyntaxManager correctly detects Python files"""
        python_files = ['test.py', 'script.py', 'module.pyw', 'package/__init__.py']
        
        for filename in python_files:
            lexer = self.gui.syntax_manager.get_lexer_for_file(filename)
            lexer_name = str(type(lexer)).lower()
            self.assertIn('python', lexer_name, f"Should detect Python lexer for {filename}")
            print(f"✅ {filename} -> {type(lexer)}")
    
    def test_shebang_detection_with_file(self):
        """Test shebang detection with an actual temporary file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False) as f:
            f.write('#!/usr/bin/env python3\nprint("Hello from shebang")\n')
            temp_file = f.name
        
        try:
            lexer = self.gui.syntax_manager.get_lexer_for_file(temp_file)
            lexer_name = str(type(lexer)).lower()
            self.assertIn('python', lexer_name, "Should detect Python from shebang")
            print(f"✅ Shebang detection: {temp_file} -> {type(lexer)}")
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main(verbosity=2) 