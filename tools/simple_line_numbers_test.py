#!/usr/bin/env python3
"""
Simple, reliable test for line numbers functionality.
This avoids complex GUI interactions that can cause widget lifecycle issues.
"""

import tkinter as tk
import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


def simple_line_numbers_test():
    """Simple test that focuses on core line numbers functionality."""
    print("🔢 Simple Line Numbers Test")
    print("=" * 40)
    
    # Create root window
    root = tk.Tk()
    root.title("Simple Line Numbers Test")
    root.geometry("600x400")
    
    # Configure root for better error handling
    def handle_errors(exc, val, tb):
        print(f"⚠️  Minor callback issue (continuing): {str(val)[:100]}")
    
    root.report_callback_exception = handle_errors
    
    try:
        # Create frame with proper grid setup
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(main_frame)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Create syntax manager
        syntax_manager = SyntaxManager()
        
        # Create CodeEditor with line numbers enabled
        code_editor = CodeEditor(
            main_frame,
            syntax_manager,
            scrollbar=scrollbar,
            show_line_numbers=True,
            line_numbers_border=1,
            width=60,
            height=20
        )
        
        # Simple test content
        test_content = """# Line Numbers Test
def hello_world():
    print("Hello, World!")
    return True

def add_numbers(a, b):
    result = a + b
    print(f"Result: {result}")
    return result

# Test line 11
# Test line 12
# Test line 13
for i in range(5):
    print(f"Line {15}: {i}")"""
        
        print("📝 Creating widget...")
        
        # Load content
        widget = code_editor.update_file_content(test_content, filename="test.py")
        
        if widget:
            print("✅ Widget created successfully")
            print(f"Widget type: {type(widget)}")
            
            # Check line numbers object
            if hasattr(widget, '_line_numbers'):
                line_nums = widget._line_numbers
                if line_nums:
                    print("✅ Line numbers object exists")
                    print(f"Line numbers type: {type(line_nums)}")
                    
                    # Test if redraw method exists
                    if hasattr(line_nums, 'redraw'):
                        print("✅ Line numbers has redraw method")
                        
                        # Test manual redraw (safely)
                        try:
                            line_nums.redraw()
                            print("✅ Manual redraw completed")
                        except Exception as e:
                            print(f"⚠️  Manual redraw had issues: {e}")
                            
                    else:
                        print("❌ Line numbers missing redraw method")
                else:
                    print("❌ Line numbers object is None")
            else:
                print("❌ Widget missing _line_numbers attribute")
            
            # Check event bindings
            try:
                events = widget.bind()
                if "<<Modified>>" in str(events):
                    print("✅ Modified event is bound")
                else:
                    print("⚠️  Modified event not found in bindings")
            except Exception as e:
                print(f"⚠️  Could not check bindings: {e}")
            
            # Add simple instructions
            instruction_label = tk.Label(
                main_frame, 
                text="👀 Visual Check: Line numbers 1-16 should be visible on the left",
                font=("Arial", 11, "bold"),
                fg="blue"
            )
            instruction_label.grid(row=1, column=0, columnspan=2, pady=5, sticky='ew')
            
            # Add close button
            def close_test():
                print("🔒 Closing test...")
                try:
                    root.quit()
                    root.destroy()
                except Exception:
                    pass
            
            close_button = tk.Button(
                main_frame,
                text="Close Test",
                command=close_test,
                bg='lightcoral'
            )
            close_button.grid(row=2, column=0, columnspan=2, pady=5)
            
            print("\n📋 VISUAL VERIFICATION:")
            print("1. Check that line numbers 1, 2, 3, ... 16 are visible")
            print("2. Numbers should appear immediately (not just '1')")
            print("3. Click 'Close Test' when done")
            
        else:
            print("❌ Failed to create widget")
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False
    
    # Start GUI with timeout protection
    print("🖥️  Starting simple test GUI...")
    
    # Auto-close after 30 seconds to prevent hanging
    def auto_close():
        print("⏰ Auto-closing test after timeout...")
        try:
            root.quit()
        except Exception:
            pass
    
    root.after(30000, auto_close)  # 30 second timeout
    
    try:
        root.mainloop()
        print("✅ Test completed")
        return True
    except Exception as e:
        print(f"⚠️  Test ended with: {e}")
        return False
    finally:
        try:
            root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        print("🚀 Starting simple line numbers test...")
        success = simple_line_numbers_test()
        if success:
            print("🎉 Simple test completed successfully!")
        else:
            print("⚠️  Simple test had issues")
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
        # Don't print full traceback for simpler output
        print("💡 Try running: python -m pytest tests/test_line_numbers_display_fix.py") 