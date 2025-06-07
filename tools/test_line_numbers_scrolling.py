#!/usr/bin/env python3
"""
Visual test for line numbers scrolling functionality.
This test verifies that line numbers update properly when scrolling through content.
"""

import tkinter as tk
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


def test_line_numbers_scrolling():
    """Visual test for line numbers scrolling functionality."""
    print("🔄 Line Numbers Scrolling Test")
    print("=" * 35)
    
    # Create window
    window = tk.Tk()
    window.title("Line Numbers Scrolling Test")
    window.geometry("800x600")
    
    # Main container
    container = tk.Frame(window)
    container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    # Instructions at top
    instructions = tk.Label(
        container,
        text="📋 TEST: Scroll with mouse wheel, arrow keys, page up/down. Line numbers should update!",
        font=('Arial', 12, 'bold'),
        bg='lightgreen',
        pady=10,
        wraplength=750
    )
    instructions.pack(fill=tk.X, pady=(0, 10))
    
    # Editor frame with scrollbar
    editor_frame = tk.Frame(container)
    editor_frame.pack(fill=tk.BOTH, expand=True)
    
    # Create scrollbar
    scrollbar = tk.Scrollbar(editor_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Configure grid for proper layout
    content_frame = tk.Frame(editor_frame)
    content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    content_frame.grid_rowconfigure(0, weight=1)
    content_frame.grid_columnconfigure(0, weight=1)
    
    print("📝 Creating syntax manager...")
    syntax_manager = SyntaxManager()
    
    print("📝 Creating code editor with line numbers...")
    code_editor = CodeEditor(
        content_frame,
        syntax_manager,
        scrollbar=scrollbar,
        show_line_numbers=True,
        line_numbers_border=2,
        width=70,
        height=25
    )
    
    # Create long test content to enable scrolling
    long_content = """# Line Numbers Scrolling Test File
# This file has many lines to test scrolling functionality
import tkinter as tk
from typing import Optional, List, Dict, Any

class ScrollTestClass:
    '''A test class with many lines for scrolling'''
    
    def __init__(self, param1: str, param2: int = 0):
        self.param1 = param1
        self.param2 = param2
        self.data = []
        self.config = {}
        
    def method_one(self):
        '''First test method'''
        for i in range(10):
            self.data.append(f"Item {i}")
            if i % 2 == 0:
                print(f"Even number: {i}")
            else:
                print(f"Odd number: {i}")
        return len(self.data)
    
    def method_two(self, values: List[str]):
        '''Second test method'''
        result = []
        for value in values:
            processed = value.strip().upper()
            if processed:
                result.append(processed)
        return result
    
    def method_three(self, config: Dict[str, Any]):
        '''Third test method'''
        self.config.update(config)
        if 'debug' in self.config:
            print("Debug mode enabled")
        if 'verbose' in self.config:
            print("Verbose mode enabled")
        return self.config

def function_one():
    '''Standalone function one'''
    items = ["apple", "banana", "cherry", "date"]
    for item in items:
        print(f"Processing: {item}")
    return items

def function_two(x: int, y: int) -> int:
    '''Standalone function two'''
    result = x + y
    if result > 100:
        print("Large result!")
    elif result < 0:
        print("Negative result!")
    else:
        print(f"Result: {result}")
    return result

def function_three():
    '''Standalone function three'''
    data = {
        'numbers': [1, 2, 3, 4, 5],
        'letters': ['a', 'b', 'c', 'd', 'e'],
        'mixed': [1, 'a', 2, 'b', 3, 'c']
    }
    
    for key, value in data.items():
        print(f"{key}: {value}")
    
    return data

# More lines for testing
if __name__ == "__main__":
    # Create test instance
    test_obj = ScrollTestClass("test", 42)
    
    # Test methods
    test_obj.method_one()
    test_obj.method_two(["  hello  ", "  world  ", ""])
    test_obj.method_three({"debug": True, "verbose": False})
    
    # Test functions
    function_one()
    function_two(25, 75)
    function_three()
    
    print("Scroll test complete!")
    print("Line numbers should update when scrolling!")
    print("Try using:")
    print("- Mouse wheel")
    print("- Arrow keys (up/down)")
    print("- Page Up/Page Down keys")
    print("- Home/End keys")
    print("- Ctrl+Home/Ctrl+End")
    print("- Scrollbar dragging")
    
# End of file - you should see line numbers up to around 100!"""
    
    print("📝 Loading long test content...")
    widget = code_editor.update_file_content(long_content, filename="scroll_test.py")
    
    if widget:
        print("✅ Code editor created successfully")
        print(f"Widget type: {type(widget)}")
        
        # Configure scrollbar
        code_editor.configure_scrollbar(widget)
        
        # Check line numbers
        if hasattr(widget, '_line_numbers') and widget._line_numbers:
            print("✅ Line numbers widget found")
            try:
                widget._line_numbers.redraw()
                print("✅ Initial line numbers redraw completed")
            except Exception as e:
                print(f"⚠️  Initial redraw issue: {e}")
        else:
            print("❌ No line numbers widget found")
    else:
        print("❌ Failed to create code editor")
        window.destroy()
        return False
    
    # Test instructions
    test_info = tk.Label(
        container,
        text="""
🧪 SCROLL TESTS TO TRY:
• Mouse wheel up/down
• Arrow keys ↑ ↓
• Page Up / Page Down
• Home / End keys
• Ctrl+Home / Ctrl+End
• Drag the scrollbar
        """,
        justify=tk.LEFT,
        bg='lightyellow',
        font=('Arial', 10),
        pady=10
    )
    test_info.pack(pady=5)
    
    # Action buttons
    button_frame = tk.Frame(container)
    button_frame.pack(pady=10)
    
    def force_redraw():
        """Force line numbers redraw."""
        try:
            if hasattr(widget, '_line_numbers') and widget._line_numbers:
                widget._line_numbers.redraw()
                print("🔄 Forced line numbers redraw")
        except Exception as e:
            print(f"❌ Force redraw failed: {e}")
    
    def scroll_to_middle():
        """Scroll to middle of document."""
        try:
            widget.yview_moveto(0.5)
            print("📍 Scrolled to middle")
        except Exception as e:
            print(f"❌ Scroll to middle failed: {e}")
    
    def scroll_to_end():
        """Scroll to end of document."""
        try:
            widget.yview_moveto(1.0)
            print("📍 Scrolled to end")
        except Exception as e:
            print(f"❌ Scroll to end failed: {e}")
    
    tk.Button(button_frame, text="Force Redraw", command=force_redraw, bg='lightblue').pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Scroll to Middle", command=scroll_to_middle, bg='lightcoral').pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Scroll to End", command=scroll_to_end, bg='lightcoral').pack(side=tk.LEFT, padx=5)
    
    # Close button
    close_btn = tk.Button(
        container,
        text="✅ CLOSE - Line numbers should update during ALL scroll actions!",
        command=window.quit,
        font=('Arial', 12, 'bold'),
        bg='lightgreen',
        pady=10
    )
    close_btn.pack(fill=tk.X, pady=(10, 0))
    
    print("\n🎯 TESTING CHECKLIST:")
    print("1. ✓ Line numbers 1-100+ should be visible on the left")
    print("2. ✓ Mouse wheel scrolling should update line numbers")
    print("3. ✓ Arrow key scrolling should update line numbers")
    print("4. ✓ Page Up/Down should update line numbers")
    print("5. ✓ Home/End keys should update line numbers")
    print("6. ✓ Scrollbar dragging should update line numbers")
    print("7. ✓ All scroll actions should be IMMEDIATE (no clicking needed)")
    
    # Start GUI
    try:
        window.mainloop()
        print("✅ Scrolling test completed")
        return True
    except Exception as e:
        print(f"❌ GUI error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting line numbers scrolling test...")
    
    try:
        success = test_line_numbers_scrolling()
        
        if success:
            print("\n🎉 Scrolling test completed!")
            print("\n📊 REPORT YOUR RESULTS:")
            print("✓ Did line numbers update immediately when scrolling?")
            print("✓ Did ALL scroll methods work (wheel, keys, scrollbar)?")
            print("✓ Were there any scroll actions that didn't update line numbers?")
        else:
            print("\n❌ Scrolling test failed")
            
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
    
    print("\n🏁 Exiting...")
    sys.exit(0) 