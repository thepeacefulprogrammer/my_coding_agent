#!/usr/bin/env python3
"""
Simple visual test for line numbers - no complex error handling.
Just shows the basic functionality.
"""

import tkinter as tk
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def simple_visual_test():
    """Simple visual test with minimal complexity."""
    print("🔢 Simple Line Numbers Visual Test")
    print("=" * 40)
    
    # Import here to avoid early failures
    from code_editor import CodeEditor
    from syntax_manager import SyntaxManager
    
    # Create window
    window = tk.Tk()
    window.title("Line Numbers Test")
    window.geometry("700x500")
    
    # Main container
    container = tk.Frame(window)
    container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    # Instructions at top
    instructions = tk.Label(
        container,
        text="📋 CHECK: Are line numbers 1-15 visible immediately on the left?",
        font=('Arial', 12, 'bold'),
        bg='lightblue',
        pady=10
    )
    instructions.pack(fill=tk.X, pady=(0, 10))
    
    # Editor container (use grid for proper layout)
    editor_frame = tk.Frame(container)
    editor_frame.pack(fill=tk.BOTH, expand=True)
    editor_frame.grid_rowconfigure(0, weight=1)
    editor_frame.grid_columnconfigure(0, weight=1)
    
    print("📝 Creating syntax manager...")
    syntax_manager = SyntaxManager()
    
    print("📝 Creating code editor...")
    code_editor = CodeEditor(
        editor_frame,
        syntax_manager,
        show_line_numbers=True,
        line_numbers_border=2,
        width=70,
        height=25
    )
    
    # Test content
    test_code = """# Line Numbers Test
import tkinter as tk
from typing import Optional

def example_function():
    '''Example function with multiple lines'''
    numbers = [1, 2, 3, 4, 5]
    for num in numbers:
        print(f"Number: {num}")
        if num > 3:
            break
    return numbers

class ExampleClass:
    def __init__(self, value: str):
        self.value = value"""
    
    print("📝 Loading test content...")
    widget = code_editor.update_file_content(test_code, filename="test.py")
    
    if widget:
        print("✅ Code editor created successfully")
        print(f"Widget type: {type(widget)}")
        
        # Check line numbers
        if hasattr(widget, '_line_numbers') and widget._line_numbers:
            print("✅ Line numbers widget found")
            # Try to redraw once more to ensure visibility
            try:
                widget._line_numbers.redraw()
                print("✅ Line numbers redraw completed")
            except Exception as e:
                print(f"⚠️  Redraw issue: {e}")
        else:
            print("❌ No line numbers widget found")
    else:
        print("❌ Failed to create code editor")
        window.destroy()
        return False
    
    # Close button
    close_btn = tk.Button(
        container,
        text="✅ CLOSE - Line numbers should be visible 1-15",
        command=window.quit,  # Use quit() to avoid destroy issues
        font=('Arial', 12, 'bold'),
        bg='lightgreen',
        pady=10
    )
    close_btn.pack(fill=tk.X, pady=(10, 0))
    
    print("\n🎯 LOOK FOR:")
    print("→ Line numbers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15")
    print("→ Numbers should appear immediately (no clicking needed)")
    print("→ Numbers should be on the LEFT side of the code")
    
    # Start GUI - no exception handling to keep it simple
    try:
        window.mainloop()
        print("✅ Visual test completed")
        return True
    except Exception as e:
        print(f"❌ GUI error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting simple visual test...")
    
    try:
        success = simple_visual_test()
        
        if success:
            print("\n🎉 Test completed!")
            print("\n📊 PLEASE REPORT:")
            print("✓ Were line numbers 1-15 visible immediately?")
            print("✓ Were they on the left side?")
            print("✓ Did you need to click anywhere first?")
        else:
            print("\n❌ Test failed")
            
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
    
    # Clean exit
    print("\n🏁 Exiting...")
    sys.exit(0) 