#!/usr/bin/env python3
"""
Demo to test that line numbers display immediately after loading content.
This will help us verify that the fix actually works in practice.
"""

import tkinter as tk
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


def test_immediate_line_numbers():
    """Test immediate line numbers display."""
    print("🔢 Testing immediate line numbers display...")
    
    # Create root window
    root = tk.Tk()
    root.title("Line Numbers Immediate Display Test")
    root.geometry("600x400")
    
    # Create main frame
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create editor frame (separate frame for grid layout)
    editor_frame = tk.Frame(main_frame)
    editor_frame.pack(fill=tk.BOTH, expand=True)
    
    # Configure grid weights for editor frame
    editor_frame.grid_rowconfigure(0, weight=1)
    editor_frame.grid_columnconfigure(0, weight=1)
    
    # Create scrollbar
    scrollbar = tk.Scrollbar(editor_frame)
    scrollbar.grid(row=0, column=1, sticky='ns')
    
    # Create syntax manager
    syntax_manager = SyntaxManager()
    
    # Create CodeEditor with line numbers enabled (use editor_frame for grid layout)
    code_editor = CodeEditor(
        editor_frame,
        syntax_manager,
        scrollbar=scrollbar,
        show_line_numbers=True,
        line_numbers_border=1,
        width=60,
        height=20
    )
    
    # Test content with 10 lines
    test_content = """# Test file for line numbers
def function_one():
    print("Line 3")
    return True

def function_two():
    print("Line 7")
    for i in range(3):
        print(f"Line {9}: {i}")
    return False"""
    
    print("📝 Loading test content...")
    
    # Load content and check if widget is created
    widget = code_editor.update_file_content(test_content, filename="test.py")
    
    if widget:
        print("✅ Widget created successfully")
        
        # Check if line numbers are visible immediately
        def check_line_numbers():
            try:
                if hasattr(widget, '_line_numbers'):
                    print("✅ Widget has line numbers attribute")
                    return True
                else:
                    print("❌ Widget missing line numbers attribute")
                    return False
            except Exception as e:
                print(f"❌ Error checking line numbers: {e}")
                return False
        
        # Check immediately
        immediate_result = check_line_numbers()
        
        # Check after a short delay to see if refresh helps
        def delayed_check():
            delayed_result = check_line_numbers()
            print(f"🕐 Delayed check result: {delayed_result}")
            
            # Show instructions
            instruction_text = """
📋 VISUAL TEST INSTRUCTIONS:
1. Look at the left side of the editor
2. You should see line numbers 1, 2, 3, ... 10
3. If you only see "1", the fix didn't work
4. Close this window when done testing
"""
            print(instruction_text)
            
            # Add a label with instructions
            instruction_label = tk.Label(
                main_frame, 
                text="👀 Check if ALL line numbers (1-10) are visible on the left",
                font=("Arial", 12, "bold"),
                fg="blue"
            )
            instruction_label.pack(pady=5)
            
        # Schedule delayed check
        root.after(100, delayed_check)
        
    else:
        print("❌ Failed to create widget")
    
    # Start the GUI
    print("🖥️  Starting GUI - check line numbers visually...")
    root.mainloop()


if __name__ == "__main__":
    test_immediate_line_numbers() 