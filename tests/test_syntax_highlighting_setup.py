import unittest
import inspect
from unittest.mock import patch, MagicMock
import sys


class TestSyntaxHighlightingSetup(unittest.TestCase):
    """Test syntax highlighting setup and dependencies"""
    
    def test_chlorophyll_import_available(self):
        """Test that chlorophyll library can be imported successfully"""
        try:
            import chlorophyll
            # Should have CodeView class available
            self.assertTrue(hasattr(chlorophyll, 'CodeView'), 
                          "chlorophyll should have CodeView class")
        except ImportError as e:
            self.fail(f"chlorophyll library not available: {e}")
    
    def test_pygments_import_available(self):
        """Test that pygments library (chlorophyll dependency) can be imported"""
        try:
            import pygments
            import pygments.lexers
            # Should have basic lexers available
            self.assertTrue(hasattr(pygments.lexers, 'PythonLexer'),
                          "pygments should have PythonLexer available")
        except ImportError as e:
            self.fail(f"pygments library not available: {e}")
    
    def test_chlorophyll_codeview_class_available(self):
        """Test that CodeView class is available and has expected text widget methods"""
        try:
            from chlorophyll import CodeView
            # Should be a class
            self.assertTrue(inspect.isclass(CodeView), "CodeView should be a class")
            
            # Should have text widget methods (since it extends tkinter.Text)
            expected_methods = ['get', 'insert', 'delete', 'highlight_all', 'highlight_line']
            for method_name in expected_methods:
                self.assertTrue(hasattr(CodeView, method_name), 
                              f"CodeView should have {method_name} method")
                
        except Exception as e:
            self.fail(f"CodeView class access failed: {e}")


if __name__ == '__main__':
    unittest.main() 