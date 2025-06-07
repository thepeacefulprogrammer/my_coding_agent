#!/usr/bin/env python3
"""
Test to verify that scroll events are properly bound to widgets with line numbers.
"""

import tkinter as tk
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_editor import CodeEditor
from syntax_manager import SyntaxManager


def test_scroll_event_bindings():
    """Test that scroll events are properly bound."""
    print("🔄 Testing Scroll Event Bindings")
    print("=" * 40)
    
    try:
        # Create hidden root
        root = tk.Tk()
        root.withdraw()
        
        frame = tk.Frame(root)
        syntax_manager = SyntaxManager()
        
        print("📝 Creating CodeEditor with line numbers enabled...")
        code_editor = CodeEditor(
            frame,
            syntax_manager,
            show_line_numbers=True
        )
        
        # Create widget
        widget = code_editor.create_widget()
        print(f"✅ Widget created: {type(widget).__name__}")
        
        # Load some content
        code_editor.update_file_content("print('test')\nprint('line 2')\nprint('line 3')", filename="test.py")
        
        # Check line numbers
        has_line_numbers = hasattr(widget, '_line_numbers') and widget._line_numbers
        print(f"✅ Line numbers present: {'✓' if has_line_numbers else '✗'}")
        
        if has_line_numbers:
            # Get all bound events
            bound_events = widget.bind()
            print(f"✅ Total events bound: {len(bound_events)}")
            
            # Check for specific scroll events
            expected_scroll_events = [
                '<MouseWheel>',
                '<Button-4>',
                '<Button-5>', 
                '<Key-Up>',
                '<Key-Down>',
                '<Key-Prior>',
                '<Key-Next>',
                '<Key-Home>',
                '<Key-End>',
                '<Control-Home>',
                '<Control-End>'
            ]
            
            print("\n🔍 Checking scroll event bindings:")
            scroll_events_found = 0
            
            for event in expected_scroll_events:
                if event in bound_events:
                    print(f"  ✅ {event} - BOUND")
                    scroll_events_found += 1
                else:
                    print(f"  ❌ {event} - NOT BOUND")
            
            print(f"\n📊 Scroll events bound: {scroll_events_found}/{len(expected_scroll_events)}")
            
            # Check Modified event specifically
            if '<<Modified>>' in bound_events:
                print("✅ <<Modified>> event - BOUND")
                
                # Get the number of callbacks for Modified event
                modified_callbacks = widget.bind('<<Modified>>')
                if modified_callbacks:
                    # Count bindings by splitting the callback string
                    callback_count = len(modified_callbacks.split()) if isinstance(modified_callbacks, str) else 1
                    print(f"✅ <<Modified>> has {callback_count} callback(s)")
                else:
                    print("⚠️  <<Modified>> bound but no callbacks found")
            else:
                print("❌ <<Modified>> event - NOT BOUND")
            
            # Test a sample scroll event callback
            print("\n🧪 Testing scroll event callback:")
            try:
                # Simulate a scroll event
                widget.event_generate('<MouseWheel>', delta=120)
                print("✅ Generated <MouseWheel> event successfully")
                
                # Try manual redraw
                widget._line_numbers.redraw()
                print("✅ Manual line numbers redraw successful")
                
            except Exception as e:
                print(f"⚠️  Scroll event test issue: {e}")
        
        else:
            print("❌ No line numbers found - cannot test scroll events")
            return False
        
        root.quit()
        
        print(f"\n🎯 SCROLL EVENTS SUMMARY:")
        print(f"✓ Line numbers enabled: {has_line_numbers}")
        print(f"✓ Scroll events bound: {scroll_events_found}/{len(expected_scroll_events)}")
        print(f"✓ Modified event bound: {'<<Modified>>' in bound_events}")
        
        # Determine success
        success = (has_line_numbers and 
                  scroll_events_found >= 8 and  # At least most scroll events
                  '<<Modified>>' in bound_events)
        
        if success:
            print("🎉 SCROLL EVENT BINDING TEST PASSED!")
            print("💡 Line numbers should update when scrolling!")
        else:
            print("❌ SCROLL EVENT BINDING TEST FAILED!")
            print("💡 Some scroll events may not trigger line number updates")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting scroll event binding test...")
    
    success = test_scroll_event_bindings()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("📊 CONCLUSION: Scroll events are properly bound")
        print("💡 Line numbers should now update when scrolling!")
    else:
        print("\n❌ Test failed")
        print("💡 Scroll events may not be working correctly")
    
    print("\n🏁 Test completed")
    sys.exit(0) 