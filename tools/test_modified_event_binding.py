#!/usr/bin/env python3
"""
Test script to verify that the <<Modified>> event binding for line numbers is working.
This follows the TkLineNums documentation pattern exactly.
"""

import tkinter as tk
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


def test_modified_event_binding():
    """Test that the Modified event binding properly triggers line numbers redraw."""
    print("🔄 Testing <<Modified>> event binding for line numbers...")
    
    # Create root window
    root = tk.Tk()
    root.title("Test Modified Event Binding")
    root.geometry("700x500")
    
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
        width=70,
        height=20
    )
    
    # Test content with multiple lines
    test_content = """# Testing Modified Event
def test_function():
    print("Line 3")
    for i in range(5):
        print(f"Line {5+i}: {i}")
    
class TestClass:
    def __init__(self):
        self.value = "Line 9"
        
    def method(self):
        return "Line 12"

# More lines to test scrolling
for x in range(10):
    print(f"Generated line {16+x}")"""
    
    print("📝 Loading test content...")
    
    # Load content and get widget
    widget = code_editor.update_file_content(test_content, filename="test.py")
    
    if widget:
        print("✅ Widget created successfully")
        
        # Check event bindings
        def check_event_bindings():
            """Check what events are bound to the widget."""
            print("\n🔍 CHECKING EVENT BINDINGS:")
            print("=" * 40)
            
            try:
                # Get all bound events
                all_events = widget.bind()
                if all_events:
                    print(f"   Bound events: {all_events}")
                    
                    # Check specifically for Modified event
                    if "<<Modified>>" in str(all_events):
                        print("   ✅ <<Modified>> event is bound")
                    else:
                        print("   ❌ <<Modified>> event is NOT bound")
                else:
                    print("   ❌ No events bound to widget")
                    
                # Try to get the specific Modified binding
                try:
                    modified_binding = widget.bind("<<Modified>>")
                    if modified_binding:
                        print(f"   <<Modified>> binding: {modified_binding}")
                    else:
                        print("   ❌ No <<Modified>> binding found")
                except Exception as e:
                    print(f"   ❌ Error checking <<Modified>> binding: {e}")
                
            except Exception as e:
                print(f"   ❌ Error checking bindings: {e}")
            
            # Check line numbers object
            print("\n🔢 CHECKING LINE NUMBERS OBJECT:")
            print("=" * 40)
            
            if hasattr(widget, '_line_numbers'):
                line_nums = widget._line_numbers
                if line_nums:
                    print("   ✅ Line numbers object exists")
                    print(f"   Line numbers type: {type(line_nums)}")
                    
                    # Check for redraw method
                    if hasattr(line_nums, 'redraw'):
                        print("   ✅ Line numbers has redraw method")
                        
                        # Test manual redraw
                        try:
                            line_nums.redraw()
                            print("   ✅ Manual redraw successful")
                        except Exception as e:
                            print(f"   ❌ Manual redraw failed: {e}")
                    else:
                        print("   ❌ Line numbers missing redraw method")
                else:
                    print("   ❌ Line numbers object is None")
            else:
                print("   ❌ Widget missing _line_numbers attribute")
        
        # Test manual content modification to trigger Modified event
        def test_manual_modification():
            """Test manual content modification to see if Modified event triggers."""
            print("\n🖋️  TESTING MANUAL MODIFICATION:")
            print("=" * 40)
            
            try:
                # Enable widget for editing
                widget.config(state='normal')
                
                # Insert a new line at the end
                widget.insert(tk.END, "\n# New line added manually")
                
                # Set back to disabled
                widget.config(state='disabled')
                
                print("   ✅ Manual modification completed")
                print("   → This should trigger <<Modified>> event and redraw line numbers")
                
            except Exception as e:
                print(f"   ❌ Manual modification failed: {e}")
        
        # Test forced Modified event generation
        def test_force_modified_event():
            """Test forcing a Modified event generation."""
            print("\n⚡ TESTING FORCED MODIFIED EVENT:")
            print("=" * 40)
            
            try:
                # Generate Modified event manually
                widget.event_generate("<<Modified>>")
                print("   ✅ Generated <<Modified>> event manually")
                
            except Exception as e:
                print(f"   ❌ Failed to generate <<Modified>> event: {e}")
        
        # Schedule tests after widget is displayed
        def run_all_tests():
            check_event_bindings()
            test_manual_modification()
            test_force_modified_event()
            
            print("\n" + "=" * 40)
            print("📋 VISUAL VERIFICATION:")
            print("1. Check that ALL line numbers (1-25+) are visible on the left")
            print("2. If you only see '1', the fix didn't work")
            print("3. Try scrolling to see if line numbers update correctly")
            print("4. Look for any changes after the tests above")
            print("5. Close window when done testing")
        
        # Schedule tests to run after widget is displayed
        root.after(1000, run_all_tests)
        
        # Add control buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=5)
        
        def force_redraw():
            """Force line numbers redraw."""
            try:
                if hasattr(widget, '_line_numbers') and widget._line_numbers:
                    widget.after_idle(widget._line_numbers.redraw)
                    print("🔄 Forced line numbers redraw")
            except Exception as e:
                print(f"❌ Force redraw failed: {e}")
        
        tk.Button(button_frame, text="Force Redraw", command=force_redraw).pack(side=tk.LEFT, padx=5)
        
        def trigger_modified():
            """Trigger Modified event."""
            try:
                widget.event_generate("<<Modified>>")
                print("⚡ Triggered <<Modified>> event")
            except Exception as e:
                print(f"❌ Trigger Modified failed: {e}")
        
        tk.Button(button_frame, text="Trigger Modified", command=trigger_modified).pack(side=tk.LEFT, padx=5)
        
    else:
        print("❌ Failed to create widget")
    
    # Start the GUI
    print("🖥️  Starting GUI - check line numbers and console output...")
    root.mainloop()


if __name__ == "__main__":
    test_modified_event_binding() 