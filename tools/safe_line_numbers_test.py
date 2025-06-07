#!/usr/bin/env python3
"""
Safe line numbers test that avoids the chlorophyll destroy bug.
"""

import tkinter as tk
import sys
import os
import signal

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


def safe_line_numbers_test():
    """Safe test that avoids the chlorophyll destroy() recursion bug."""
    print("🔢 Safe Line Numbers Test")
    print("=" * 35)
    
    root = None
    
    try:
        # Create root window
        root = tk.Tk()
        root.title("Safe Line Numbers Test")
        root.geometry("600x400")
        
        # Simple frame setup
        frame = tk.Frame(root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure for grid
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Create syntax manager
        syntax_manager = SyntaxManager()
        
        print("📝 Creating CodeEditor...")
        
        # Create CodeEditor
        code_editor = CodeEditor(
            frame,
            syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1,
            width=60,
            height=20
        )
        
        # Test content with multiple lines
        test_content = """# Safe Line Numbers Test
def function_example():
    '''This is a function example'''
    for i in range(10):
        print(f"Line {i+5}: Hello World")
        if i > 5:
            break
    return True

# More lines to test scrolling
class TestClass:
    def __init__(self):
        self.value = "test"
        
    def method(self):
        return self.value

# End of test content
print("All done!")"""
        
        print("📝 Loading content...")
        
        # Load content
        widget = code_editor.update_file_content(test_content, filename="test.py")
        
        if widget:
            print("✅ Widget created successfully")
            
            # Check line numbers functionality
            has_line_numbers = hasattr(widget, '_line_numbers') and widget._line_numbers
            print(f"✅ Line numbers object: {'✓' if has_line_numbers else '✗'}")
            
            if has_line_numbers:
                has_redraw = hasattr(widget._line_numbers, 'redraw')
                print(f"✅ Redraw method: {'✓' if has_redraw else '✗'}")
                
                # Test initial redraw (this should work)
                try:
                    widget._line_numbers.redraw()
                    print("✅ Initial redraw successful")
                except Exception as e:
                    print(f"⚠️  Initial redraw issue: {e}")
            
            # Add control buttons
            button_frame = tk.Frame(frame)
            button_frame.grid(row=1, column=0, pady=10, sticky='ew')
            
            def close_safely():
                """Close without triggering chlorophyll destroy bug."""
                print("🔄 Closing safely (avoiding chlorophyll bug)...")
                # Don't call destroy on widgets with chlorophyll - just quit
                root.quit()  # Use quit() instead of destroy()
            
            def refresh_line_numbers():
                """Manual line numbers refresh test."""
                if has_line_numbers:
                    try:
                        widget._line_numbers.redraw()
                        print("✅ Manual refresh successful")
                    except Exception as e:
                        print(f"⚠️  Manual refresh issue: {e}")
            
            # Control buttons
            close_button = tk.Button(
                button_frame,
                text="✓ Close Test",
                command=close_safely,
                bg='lightgreen',
                font=('Arial', 10, 'bold')
            )
            close_button.pack(side=tk.LEFT, padx=5)
            
            refresh_button = tk.Button(
                button_frame,
                text="🔄 Refresh Line Numbers",
                command=refresh_line_numbers,
                bg='lightblue'
            )
            refresh_button.pack(side=tk.LEFT, padx=5)
            
            print("\n📋 TEST INSTRUCTIONS:")
            print("→ Look for line numbers 1-19 on the left side")
            print("→ All line numbers should be visible immediately")
            print("→ Try the 'Refresh Line Numbers' button")
            print("→ Click 'Close Test' when done")
            print("\n🎯 SUCCESS CRITERIA:")
            print("→ Line numbers 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19")
            print("→ Numbers appear immediately without clicking in editor")
            
            # Start the event loop (use mainloop which handles quit properly)
            root.mainloop()
            
            print("✅ Test completed successfully - line numbers should have been visible!")
            return True
            
        else:
            print("❌ Widget creation failed")
            if root:
                root.quit()
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if root:
            try:
                root.quit()  # Use quit instead of destroy
            except:
                pass
        return False


if __name__ == "__main__":
    print("🚀 Starting safe line numbers test...")
    print("💡 This test avoids the chlorophyll destroy() recursion bug")
    
    success = safe_line_numbers_test()
    
    if success:
        print("\n🎉 Safe test completed!")
        print("💡 If line numbers 1-19 were immediately visible, the fix is working!")
    else:
        print("\n⚠️  Safe test had issues")
    
    print("\n🔍 WHAT TO REPORT:")
    print("→ Were line numbers visible immediately when content loaded?")
    print("→ Did you need to click in the editor to see numbers?")
    print("→ Did the refresh button work?")
    
    # Force exit to avoid any lingering tkinter issues
    try:
        sys.exit(0)
    except:
        os._exit(0) 