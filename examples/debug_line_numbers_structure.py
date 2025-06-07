#!/usr/bin/env python3
"""
Debug script to understand the chlorophyll CodeView structure and line numbers.
"""

import tkinter as tk
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


def debug_codeview_structure():
    """Debug the CodeView structure and methods."""
    print("🔍 Debugging CodeView structure and line numbers...")
    
    # Create root window
    root = tk.Tk()
    root.title("Debug CodeView Structure")
    root.geometry("800x600")
    
    # Create main frame
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create scrollbar
    scrollbar = tk.Scrollbar(main_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Create syntax manager
    syntax_manager = SyntaxManager()
    
    # Create CodeEditor with line numbers enabled
    code_editor = CodeEditor(
        main_frame,
        syntax_manager,
        scrollbar=scrollbar,
        show_line_numbers=True,
        line_numbers_border=1,
        width=80,
        height=25
    )
    
    # Test content with multiple lines
    test_content = """Line 1
Line 2
Line 3
Line 4
Line 5
Line 6
Line 7
Line 8
Line 9
Line 10"""
    
    print("📝 Creating widget and loading content...")
    
    # Load content
    widget = code_editor.update_file_content(test_content, filename="test.txt")
    
    if widget:
        print("✅ Widget created successfully")
        
        # Explore the widget structure
        def explore_widget():
            print("\n🔍 Widget exploration:")
            print(f"Widget type: {type(widget)}")
            print(f"Widget attributes: {dir(widget)}")
            
            # Look for line numbers related attributes
            line_num_attrs = [attr for attr in dir(widget) if 'line' in attr.lower() or 'num' in attr.lower()]
            print(f"Line number related attributes: {line_num_attrs}")
            
            # Check for internal attributes
            internal_attrs = [attr for attr in dir(widget) if attr.startswith('_')]
            print(f"Internal attributes: {internal_attrs[:10]}...")  # Show first 10
            
            # Check specifically for _line_numbers
            if hasattr(widget, '_line_numbers'):
                line_nums = widget._line_numbers
                print(f"✅ Found _line_numbers: {type(line_nums)}")
                print(f"Line numbers attributes: {dir(line_nums)}")
                
                # Look for redraw/refresh methods
                refresh_methods = [attr for attr in dir(line_nums) if 'draw' in attr.lower() or 'refresh' in attr.lower() or 'update' in attr.lower()]
                print(f"Refresh methods on line numbers: {refresh_methods}")
                
                # Try different refresh methods
                def try_refresh_methods():
                    for method_name in refresh_methods:
                        try:
                            method = getattr(line_nums, method_name)
                            if callable(method):
                                print(f"🔧 Trying {method_name}()...")
                                method()
                                print(f"✅ {method_name}() succeeded")
                        except Exception as e:
                            print(f"❌ {method_name}() failed: {e}")
                
                root.after(1000, try_refresh_methods)
            else:
                print("❌ No _line_numbers attribute found")
            
            # Check for highlight_all method
            if hasattr(widget, 'highlight_all'):
                print("✅ Found highlight_all method")
                try:
                    widget.highlight_all()
                    print("✅ highlight_all() succeeded")
                except Exception as e:
                    print(f"❌ highlight_all() failed: {e}")
            else:
                print("❌ No highlight_all method found")
        
        # Schedule exploration after widget is displayed
        root.after(500, explore_widget)
        
        # Add debugging label
        debug_label = tk.Label(
            main_frame, 
            text="🔍 Debug mode - check console for widget structure info",
            font=("Arial", 10),
            fg="red"
        )
        debug_label.pack(pady=5)
        
    else:
        print("❌ Failed to create widget")
    
    # Start the GUI
    print("🖥️  Starting debug GUI...")
    root.mainloop()


if __name__ == "__main__":
    debug_codeview_structure() 