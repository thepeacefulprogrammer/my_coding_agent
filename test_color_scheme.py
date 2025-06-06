#!/usr/bin/env python3
"""
Simple test script to verify color scheme functionality in CodeEditor.
"""

import tkinter as tk
from src.syntax_manager import SyntaxManager
from src.code_editor import CodeEditor

def test_color_scheme():
    """Test that color schemes are applied to CodeView widgets."""
    
    # Create test window
    root = tk.Tk()
    root.title("Color Scheme Test")
    root.geometry("800x600")
    
    # Create syntax manager
    syntax_manager = SyntaxManager()
    
    # Create code editor with monokai color scheme
    editor = CodeEditor(root, syntax_manager, color_scheme="monokai")
    
    # Create widget for Python file
    lexer = syntax_manager.get_lexer_for_file("test.py")
    widget = editor.create_widget(lexer=lexer)
    
    # Add some sample Python code
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
    
    # Insert the code
    widget.insert("1.0", sample_code)
    
    # Pack the widget
    widget.pack(fill="both", expand=True)
    
    # Set as current widget
    editor.current_widget = widget
    
    print("Color scheme test created. You should see syntax-highlighted Python code.")
    print("If all text appears white, there may be a color scheme configuration issue.")
    
    # Run the GUI
    root.mainloop()

if __name__ == "__main__":
    test_color_scheme() 