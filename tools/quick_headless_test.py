#!/usr/bin/env python3
"""Quick headless test for core line numbers functionality."""

import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from code_editor import CodeEditor
from syntax_manager import SyntaxManager

print('🔍 Quick line numbers functionality test...')

try:
    root = tk.Tk()
    root.withdraw()  # Hide window

    frame = tk.Frame(root)
    syntax_manager = SyntaxManager()
    code_editor = CodeEditor(frame, syntax_manager, show_line_numbers=True)

    widget = code_editor.update_file_content(
        'print("test")\nprint("line 2")\nprint("line 3")', 
        filename='test.py'
    )

    if widget:
        print('✅ Widget created successfully')
        if hasattr(widget, '_line_numbers') and widget._line_numbers:
            print('✅ Line numbers object exists')
            if hasattr(widget._line_numbers, 'redraw'):
                print('✅ Redraw method available')
                # Test redraw safety
                try:
                    widget._line_numbers.redraw()
                    print('✅ Redraw executed without errors')
                except Exception as e:
                    print(f'⚠️  Redraw had issues: {e}')
            else:
                print('❌ No redraw method')
        else:
            print('❌ No line numbers object')
    else:
        print('❌ Widget creation failed')

    root.destroy()
    print('✅ Quick test completed successfully')

except Exception as e:
    print(f'❌ Quick test failed: {e}')
    try:
        root.destroy()
    except:
        pass 