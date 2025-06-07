#!/usr/bin/env python3
"""Debug script to identify recursion issues."""

import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print('🔍 Debugging recursion issues...')

try:
    # Test just basic imports first
    print('Step 1: Testing imports...')
    from code_editor import CodeEditor
    from syntax_manager import SyntaxManager
    print('✅ Imports successful')

    # Test basic tkinter
    print('Step 2: Testing basic tkinter...')
    root = tk.Tk()
    root.withdraw()
    frame = tk.Frame(root)
    print('✅ Basic tkinter successful')

    # Test syntax manager
    print('Step 3: Testing syntax manager...')
    syntax_manager = SyntaxManager()
    print('✅ SyntaxManager successful')

    # Test CodeEditor creation (without line numbers first)
    print('Step 4: Testing CodeEditor creation (no line numbers)...')
    code_editor_no_lines = CodeEditor(frame, syntax_manager, show_line_numbers=False)
    print('✅ CodeEditor (no line numbers) successful')

    # Test CodeEditor creation (with line numbers)
    print('Step 5: Testing CodeEditor creation (with line numbers)...')
    code_editor = CodeEditor(frame, syntax_manager, show_line_numbers=True)
    print('✅ CodeEditor (with line numbers) successful')

    # Test content update (simple)
    print('Step 6: Testing simple content update...')
    widget = code_editor.update_file_content('print("hello")', filename='test.py')
    print('✅ Simple content update successful')

    # Test widget properties
    print('Step 7: Testing widget properties...')
    if widget:
        print(f'  - Widget type: {type(widget)}')
        print(f'  - Has _line_numbers: {hasattr(widget, "_line_numbers")}')
        if hasattr(widget, '_line_numbers') and widget._line_numbers:
            print(f'  - Line numbers type: {type(widget._line_numbers)}')
            print(f'  - Has redraw: {hasattr(widget._line_numbers, "redraw")}')
    print('✅ Widget properties check successful')

    # Test cleanup
    print('Step 8: Testing cleanup...')
    root.destroy()
    print('✅ Cleanup successful')

    print('🎉 All steps completed successfully - no recursion detected!')

except RecursionError as e:
    print(f'❌ RECURSION ERROR detected at step: {e}')
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f'❌ Other error: {e}')
    import traceback
    traceback.print_exc()

print('🏁 Debug completed') 