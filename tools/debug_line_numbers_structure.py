#!/usr/bin/env python3
"""
Debug script to understand chlorophyll CodeView structure and line numbers behavior.
This will help us identify why line numbers aren't displaying immediately.
"""

import tkinter as tk
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


def debug_chlorophyll_structure():
    """Debug the chlorophyll CodeView structure and line numbers."""
    print("🔍 Debugging chlorophyll CodeView structure...")
    
    # Create root window
    root = tk.Tk()
    root.title("Debug Chlorophyll Structure")
    root.geometry("800x600")
    
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
        width=80,
        height=25
    )
    
    # Test content with multiple lines
    test_content = """Line 1: First line
Line 2: Second line  
Line 3: Third line
Line 4: Fourth line
Line 5: Fifth line
Line 6: Sixth line
Line 7: Seventh line
Line 8: Eighth line
Line 9: Ninth line
Line 10: Tenth line"""
    
    print("📝 Creating widget and loading content...")
    
    # Load content
    widget = code_editor.update_file_content(test_content, filename="test.txt")
    
    if widget:
        print("✅ Widget created successfully")
        print(f"Widget type: {type(widget)}")
        
        def deep_analysis():
            print("\n🔍 DEEP WIDGET ANALYSIS:")
            print("=" * 50)
            
            # 1. Check basic widget structure
            print("1. Basic widget information:")
            print(f"   - Class: {widget.__class__}")
            print(f"   - Module: {widget.__class__.__module__}")
            print(f"   - MRO: {[cls.__name__ for cls in widget.__class__.__mro__]}")
            
            # 2. Look for line number attributes
            print("\n2. Line number related attributes:")
            all_attrs = dir(widget)
            line_attrs = [attr for attr in all_attrs if 'line' in attr.lower() or 'num' in attr.lower()]
            for attr in line_attrs:
                try:
                    value = getattr(widget, attr)
                    print(f"   - {attr}: {type(value)} = {value}")
                except Exception as e:
                    print(f"   - {attr}: Error accessing - {e}")
            
            # 3. Check internal attributes
            print("\n3. Internal attributes (starting with _):")
            internal_attrs = [attr for attr in all_attrs if attr.startswith('_') and not attr.startswith('__')]
            for attr in internal_attrs[:15]:  # Show first 15
                try:
                    value = getattr(widget, attr)
                    print(f"   - {attr}: {type(value)}")
                    if attr == '_line_numbers' and value is not None:
                        print(f"      Line numbers object: {value}")
                        print(f"      Line numbers dir: {dir(value)}")
                except Exception as e:
                    print(f"   - {attr}: Error - {e}")
            
            # 4. Check for specific line numbers object
            print("\n4. Line numbers object analysis:")
            if hasattr(widget, '_line_numbers'):
                line_nums = widget._line_numbers
                if line_nums is not None:
                    print(f"   ✅ Found _line_numbers: {type(line_nums)}")
                    
                    # Look for methods
                    methods = [attr for attr in dir(line_nums) if not attr.startswith('_')]
                    print(f"   Methods: {methods}")
                    
                    # Look for refresh/redraw methods
                    refresh_methods = [attr for attr in dir(line_nums) 
                                     if any(keyword in attr.lower() 
                                           for keyword in ['draw', 'refresh', 'update', 'render'])]
                    print(f"   Refresh methods: {refresh_methods}")
                    
                    # Try to get current state
                    try:
                        if hasattr(line_nums, 'winfo_exists'):
                            print(f"   Line numbers widget exists: {line_nums.winfo_exists()}")
                        if hasattr(line_nums, 'winfo_viewable'):
                            print(f"   Line numbers widget viewable: {line_nums.winfo_viewable()}")
                        if hasattr(line_nums, 'winfo_mapped'):
                            print(f"   Line numbers widget mapped: {line_nums.winfo_mapped()}")
                    except Exception as e:
                        print(f"   Error checking line numbers state: {e}")
                else:
                    print("   ❌ _line_numbers is None")
            else:
                print("   ❌ No _line_numbers attribute found")
            
            # 5. Check highlight_all method
            print("\n5. Syntax highlighting methods:")
            if hasattr(widget, 'highlight_all'):
                print("   ✅ Found highlight_all method")
                try:
                    widget.highlight_all()
                    print("   ✅ highlight_all() executed successfully")
                except Exception as e:
                    print(f"   ❌ highlight_all() failed: {e}")
            else:
                print("   ❌ No highlight_all method found")
            
            # 6. Try different refresh approaches
            print("\n6. Testing refresh approaches:")
            
            # Approach 1: Force update_idletasks
            try:
                widget.update_idletasks()
                print("   ✅ update_idletasks() succeeded")
            except Exception as e:
                print(f"   ❌ update_idletasks() failed: {e}")
            
            # Approach 2: Force update
            try:
                widget.update()
                print("   ✅ update() succeeded")
            except Exception as e:
                print(f"   ❌ update() failed: {e}")
            
            # Approach 3: Try manual line number redraw
            if hasattr(widget, '_line_numbers') and widget._line_numbers:
                line_nums = widget._line_numbers
                for method_name in ['redraw', 'refresh', 'update', 'draw']:
                    if hasattr(line_nums, method_name):
                        try:
                            method = getattr(line_nums, method_name)
                            if callable(method):
                                method()
                                print(f"   ✅ Line numbers {method_name}() succeeded")
                        except Exception as e:
                            print(f"   ❌ Line numbers {method_name}() failed: {e}")
            
            print("\n" + "=" * 50)
            print("📋 VISUAL CHECK:")
            print("Look at the editor and count visible line numbers on the left side.")
            print("Expected: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10")
            print("If you only see '1', the line numbers aren't refreshing properly.")
        
        # Schedule deep analysis after widget is displayed
        root.after(500, deep_analysis)
        
        # Add status label
        status_label = tk.Label(
            main_frame, 
            text="🔍 Debug mode - check console output for detailed analysis",
            font=("Arial", 10),
            fg="red"
        )
        status_label.pack(pady=5)
        
    else:
        print("❌ Failed to create widget")
    
    # Start the GUI
    print("🖥️  Starting debug GUI...")
    root.mainloop()


if __name__ == "__main__":
    debug_chlorophyll_structure() 