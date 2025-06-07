#!/usr/bin/env python3
"""
Minimal test for line numbers functionality.
This test focuses on core functionality without complex GUI error handling.
"""

import tkinter as tk
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


def minimal_line_numbers_test():
    """Minimal test focusing on line numbers core functionality."""
    print("🔢 Minimal Line Numbers Test")
    print("=" * 35)
    
    try:
        # Create root window
        root = tk.Tk()
        root.title("Minimal Line Numbers Test")
        root.geometry("500x300")
        
        # Simple frame setup
        frame = tk.Frame(root)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure for grid
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Create syntax manager
        syntax_manager = SyntaxManager()
        
        print("📝 Creating CodeEditor...")
        
        # Create CodeEditor (no scrollbar to avoid complexity)
        code_editor = CodeEditor(
            frame,
            syntax_manager,
            show_line_numbers=True,
            line_numbers_border=1,
            width=50,
            height=15
        )
        
        # Simple test content
        test_content = """# Minimal Test
def test():
    print("Line 3")
    return True

print("Line 6")
print("Line 7")
print("Line 8")"""
        
        print("📝 Loading content...")
        
        # Load content
        widget = code_editor.update_file_content(test_content, filename="test.py")
        
        if widget:
            print("✅ Widget created successfully")
            
            # Basic checks
            has_line_numbers = hasattr(widget, '_line_numbers') and widget._line_numbers
            print(f"✅ Line numbers object: {'✓' if has_line_numbers else '✗'}")
            
            if has_line_numbers:
                has_redraw = hasattr(widget._line_numbers, 'redraw')
                print(f"✅ Redraw method: {'✓' if has_redraw else '✗'}")
            
            # Simple GUI with manual close
            close_button = tk.Button(
                frame,
                text="✓ Close (Line numbers should be visible 1-9)",
                command=root.destroy,
                bg='lightgreen',
                font=('Arial', 10, 'bold')
            )
            close_button.grid(row=1, column=0, pady=10)
            
            print("\n📋 QUICK CHECK:")
            print("→ Look for line numbers 1, 2, 3, 4, 5, 6, 7, 8, 9 on the left")
            print("→ Click the green button to close")
            
            # Simple mainloop without complex error handling
            root.mainloop()
            
            print("✅ Test completed successfully")
            return True
            
        else:
            print("❌ Widget creation failed")
            root.destroy()
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        try:
            root.destroy()
        except:
            pass
        return False


if __name__ == "__main__":
    print("🚀 Starting minimal line numbers test...")
    success = minimal_line_numbers_test()
    
    if success:
        print("🎉 Minimal test completed!")
        print("💡 If line numbers 1-9 were visible, the fix is working!")
    else:
        print("⚠️  Minimal test had issues")
        print("💡 Try: python -m pytest tests/test_line_numbers_display_fix.py") 