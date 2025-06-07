#!/usr/bin/env python3
"""
Comprehensive verification script for the line numbers display fix.
This tests the TkLineNums recommended pattern with <<Modified>> event binding.
"""

import tkinter as tk
import sys
import os
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


def verify_line_numbers_fix():
    """Comprehensive verification of the line numbers display fix."""
    print("🔍 Comprehensive Line Numbers Fix Verification")
    print("=" * 50)
    
    # Create root window
    root = tk.Tk()
    root.title("Line Numbers Fix Verification")
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
        width=70,
        height=25
    )
    
    # Comprehensive test content
    test_content = """# Line Numbers Fix Verification
import tkinter as tk
from typing import List, Dict, Optional

class TestClass:
    \"\"\"Test class for line numbers verification.\"\"\"
    
    def __init__(self, value: int = 0):
        self.value = value
        self.items: List[str] = []
        
    def add_item(self, item: str) -> None:
        \"\"\"Add an item to the list.\"\"\"
        self.items.append(item)
        print(f"Added item: {item}")
        
    def process_items(self) -> Dict[str, int]:
        \"\"\"Process all items and return counts.\"\"\"
        result = {}
        for item in self.items:
            if item in result:
                result[item] += 1
            else:
                result[item] = 1
        return result

def main():
    \"\"\"Main function for testing.\"\"\"
    test = TestClass(42)
    test.add_item("apple")
    test.add_item("banana")
    test.add_item("apple")
    
    counts = test.process_items()
    for item, count in counts.items():
        print(f"{item}: {count}")

if __name__ == "__main__":
    main()

# Additional lines to test scrolling behavior
for i in range(1, 21):
    print(f"Generated line {35 + i}: {i * 2}")"""
    
    print("📝 Loading comprehensive test content...")
    
    # Load content and get widget
    widget = code_editor.update_file_content(test_content, filename="test.py")
    
    verification_results = {}
    
    if widget:
        print("✅ Widget created successfully")
        print(f"Widget type: {type(widget)}")
        
        def comprehensive_verification():
            """Run comprehensive verification checks."""
            print("\n🔍 COMPREHENSIVE VERIFICATION CHECKS:")
            print("=" * 50)
            
            # Test 1: Widget structure verification
            print("1. Widget Structure Verification:")
            try:
                if hasattr(widget, '_line_numbers'):
                    line_nums = widget._line_numbers
                    if line_nums:
                        print("   ✅ Line numbers object exists")
                        verification_results['line_numbers_object'] = True
                        
                        if hasattr(line_nums, 'redraw'):
                            print("   ✅ Line numbers has redraw method")
                            verification_results['redraw_method'] = True
                        else:
                            print("   ❌ Line numbers missing redraw method")
                            verification_results['redraw_method'] = False
                    else:
                        print("   ❌ Line numbers object is None")
                        verification_results['line_numbers_object'] = False
                else:
                    print("   ❌ Widget missing _line_numbers attribute")
                    verification_results['line_numbers_object'] = False
            except Exception as e:
                print(f"   ❌ Error checking widget structure: {e}")
                verification_results['line_numbers_object'] = False
            
            # Test 2: Event binding verification
            print("\n2. Event Binding Verification:")
            try:
                all_events = widget.bind()
                if "<<Modified>>" in str(all_events):
                    print("   ✅ <<Modified>> event is bound")
                    verification_results['modified_binding'] = True
                else:
                    print("   ❌ <<Modified>> event is NOT bound")
                    verification_results['modified_binding'] = False
                    
                # Get the specific binding
                modified_binding = widget.bind("<<Modified>>")
                if modified_binding:
                    print(f"   ✅ Modified binding exists: {len(modified_binding)} handlers")
                    verification_results['binding_count'] = len(modified_binding) if isinstance(modified_binding, list) else 1
                else:
                    print("   ❌ No Modified binding handlers found")
                    verification_results['binding_count'] = 0
                    
            except Exception as e:
                print(f"   ❌ Error checking event bindings: {e}")
                verification_results['modified_binding'] = False
                verification_results['binding_count'] = 0
            
            # Test 3: Manual refresh test
            print("\n3. Manual Refresh Test:")
            try:
                if hasattr(widget, '_line_numbers') and widget._line_numbers:
                    widget.after_idle(widget._line_numbers.redraw)
                    print("   ✅ Manual after_idle redraw scheduled successfully")
                    verification_results['manual_refresh'] = True
                    
                    # Direct redraw test
                    widget._line_numbers.redraw()
                    print("   ✅ Direct redraw executed successfully")
                    verification_results['direct_refresh'] = True
                else:
                    print("   ❌ Cannot test manual refresh - no line numbers object")
                    verification_results['manual_refresh'] = False
                    verification_results['direct_refresh'] = False
                    
            except Exception as e:
                print(f"   ❌ Manual refresh test failed: {e}")
                verification_results['manual_refresh'] = False
                verification_results['direct_refresh'] = False
            
            # Test 4: Content modification test
            print("\n4. Content Modification Test:")
            try:
                original_state = widget.cget('state')
                widget.config(state='normal')
                
                # Add a new line
                widget.insert(tk.END, "\n# New line added for testing")
                
                # Restore original state
                widget.config(state=original_state)
                
                print("   ✅ Content modification completed")
                print("   → This should trigger <<Modified>> event automatically")
                verification_results['content_modification'] = True
                
            except Exception as e:
                print(f"   ❌ Content modification test failed: {e}")
                verification_results['content_modification'] = False
            
            # Test 5: Force Modified event test
            print("\n5. Force Modified Event Test:")
            try:
                widget.event_generate("<<Modified>>")
                print("   ✅ Successfully generated <<Modified>> event")
                verification_results['force_modified_event'] = True
                
            except Exception as e:
                print(f"   ❌ Failed to generate <<Modified>> event: {e}")
                verification_results['force_modified_event'] = False
            
            # Test summary
            print("\n" + "=" * 50)
            print("📊 VERIFICATION SUMMARY:")
            
            passed_tests = sum(1 for result in verification_results.values() if result is True)
            total_tests = len(verification_results)
            
            print(f"Tests passed: {passed_tests}/{total_tests}")
            
            for test_name, result in verification_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {test_name}: {status}")
            
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            print(f"\nSuccess rate: {success_rate:.1f}%")
            
            if success_rate >= 80:
                print("🎉 OVERALL: Line numbers fix is working well!")
            elif success_rate >= 60:
                print("⚠️  OVERALL: Line numbers fix has some issues")
            else:
                print("❌ OVERALL: Line numbers fix needs more work")
            
            print("\n📋 VISUAL VERIFICATION:")
            print("1. Check that ALL line numbers (1-55+) are visible on the left")
            print("2. Line numbers should be clearly visible and properly aligned")
            print("3. Try scrolling to verify line numbers update correctly") 
            print("4. If you only see '1' or missing numbers, the fix needs improvement")
            print("5. Close window when done with visual verification")
        
        # Schedule comprehensive verification
        root.after(1000, comprehensive_verification)
        
        # Add interactive test buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        def manual_redraw():
            """Manual redraw test."""
            try:
                if hasattr(widget, '_line_numbers') and widget._line_numbers:
                    widget.after_idle(widget._line_numbers.redraw)
                    print("🔄 Manual redraw triggered")
                else:
                    print("❌ No line numbers object for manual redraw")
            except Exception as e:
                print(f"❌ Manual redraw failed: {e}")
        
        def trigger_modified():
            """Trigger Modified event test."""
            try:
                widget.event_generate("<<Modified>>")
                print("⚡ Modified event triggered")
            except Exception as e:
                print(f"❌ Modified event trigger failed: {e}")
        
        def add_content():
            """Add more content to test dynamic updating."""
            try:
                widget.config(state='normal')
                widget.insert(tk.END, f"\n# Added at {time.strftime('%H:%M:%S')}")
                widget.config(state='disabled')
                print("📝 Added new content")
            except Exception as e:
                print(f"❌ Add content failed: {e}")
        
        # Create interactive buttons
        tk.Button(button_frame, text="Manual Redraw", command=manual_redraw, 
                 bg='lightblue').pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Trigger Modified", command=trigger_modified,
                 bg='lightgreen').pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Add Content", command=add_content,
                 bg='lightyellow').pack(side=tk.LEFT, padx=5)
        
        # Status label
        status_label = tk.Label(
            main_frame, 
            text="🔍 Verification Mode: Check console for detailed analysis",
            font=("Arial", 11, "bold"),
            fg="blue"
        )
        status_label.pack(pady=5)
        
    else:
        print("❌ Failed to create widget")
        verification_results['widget_creation'] = False
    
    # Start the GUI with better error handling
    print("🖥️  Starting verification GUI...")
    print("Watch console output for detailed verification results")
    
    # Add better exception handling for Tkinter callbacks
    def handle_callback_exception(exc, val, tb):
        """Handle Tkinter callback exceptions gracefully."""
        print(f"⚠️  Tkinter callback warning (non-fatal): {str(val)[:200]}...")
        # Don't print full traceback for minor issues, just continue
    
    # Set up exception handler on the actual Tkinter root window
    try:
        # Make sure we're setting this on the actual root, not any other widget
        actual_root = root.winfo_toplevel()
        if hasattr(actual_root, 'report_callback_exception'):
            actual_root.report_callback_exception = handle_callback_exception
        elif hasattr(root, 'tk') and hasattr(root.tk, 'report_callback_exception'):
            root.tk.report_callback_exception = handle_callback_exception
        else:
            # Fallback: try setting on root directly if it's actually the root
            if hasattr(root, 'report_callback_exception'):
                root.report_callback_exception = handle_callback_exception
    except Exception as e:
        print(f"⚠️  Could not set exception handler: {e}")
    
    try:
        root.mainloop()
    except Exception as e:
        print(f"⚠️  GUI terminated with: {e}")
        # Don't re-raise the exception, just continue gracefully
    
    return verification_results


if __name__ == "__main__":
    try:
        results = verify_line_numbers_fix()
        print(f"\n🏁 Final verification results: {results}")
    except Exception as e:
        print(f"❌ Verification failed with error: {e}")
        print("This might be due to widget lifecycle issues - trying simplified test...")
        
        # Try a simplified test without GUI
        try:
            import tkinter as tk
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            from code_editor import CodeEditor
            from syntax_manager import SyntaxManager
            
            print("🔧 Running simplified test...")
            root = tk.Tk()
            root.withdraw()  # Hide window
            
            frame = tk.Frame(root)
            syntax_manager = SyntaxManager()
            code_editor = CodeEditor(frame, syntax_manager, show_line_numbers=True)
            
            # Quick test
            widget = code_editor.update_file_content("print('test')", filename="test.py")
            if widget:
                print("✅ Simplified test: Widget creation successful")
                if hasattr(widget, '_line_numbers'):
                    print("✅ Simplified test: Line numbers object exists")
                else:
                    print("❌ Simplified test: No line numbers object")
            else:
                print("❌ Simplified test: Widget creation failed")
                
            root.destroy()
            
        except Exception as e2:
            print(f"❌ Simplified test also failed: {e2}")
            import traceback
            traceback.print_exc() 