#!/usr/bin/env python3
"""
Demo to test that line numbers display properly after loading content.

This demo creates a simple GUI that loads content into a CodeEditor widget
and verifies that all line numbers display immediately, not just "1".
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


def main():
    """Main demo function."""
    print("🔢 Testing line numbers display after content loading...")
    
    # Create root window
    root = tk.Tk()
    root.title("Line Numbers Display Test")
    root.geometry("800x600")
    
    # Create main frame
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create status label
    status_label = tk.Label(main_frame, text="Initializing...", font=("Arial", 10))
    status_label.pack(pady=(0, 10))
    
    # Create editor frame
    editor_frame = tk.Frame(main_frame)
    editor_frame.pack(fill=tk.BOTH, expand=True)
    
    # Create scrollbar
    scrollbar = tk.Scrollbar(editor_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Create syntax manager
    syntax_manager = SyntaxManager()
    
    # Create CodeEditor with line numbers enabled
    code_editor = CodeEditor(
        editor_frame,
        syntax_manager,
        scrollbar=scrollbar,
        show_line_numbers=True,
        line_numbers_border=1,
        width=80,
        height=25
    )
    
    # Create sample Python content with multiple lines
    sample_content = '''def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return "success"

def fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

def main():
    """Main function."""
    hello_world()
    for i in range(10):
        fib = fibonacci(i)
        print(f"Fibonacci({i}) = {fib}")

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, value):
        """Add a value to the result."""
        self.result += value
        return self.result
    
    def subtract(self, value):
        """Subtract a value from the result."""
        self.result -= value
        return self.result

if __name__ == "__main__":
    main()
'''
    
    def load_content():
        """Load content into the editor."""
        status_label.config(text="Loading content...")
        root.update()
        
        # Update file content with Python syntax highlighting
        widget = code_editor.update_file_content(sample_content, filename="demo.py")
        
        if widget:
            status_label.config(text="✅ Content loaded! Check that ALL line numbers are visible (1-34)")
            print("✅ Content loaded successfully")
            print("📝 Check the editor - all line numbers (1-34) should be visible immediately")
            print("🔍 If you only see line number '1', the fix didn't work")
        else:
            status_label.config(text="❌ Failed to load content")
            print("❌ Failed to load content")
    
    # Create button to load content
    load_button = tk.Button(
        main_frame, 
        text="Load Sample Python File", 
        command=load_content,
        font=("Arial", 12),
        bg="#4CAF50",
        fg="white",
        padx=20,
        pady=10
    )
    load_button.pack(pady=10)
    
    # Load content after a short delay to ensure GUI is ready
    root.after(500, load_content)
    
    print("🖥️  GUI started. The content will load automatically.")
    print("📋 Expected behavior: All line numbers (1-34) should be visible immediately")
    print("🐛 Bug behavior: Only line number '1' visible until widget is clicked")
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main() 