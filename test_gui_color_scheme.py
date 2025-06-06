#!/usr/bin/env python3
"""
Test script to verify GUI color scheme functionality.
"""

import tkinter as tk
from src.gui import GUI
import tempfile
import os

def test_gui_color_scheme():
    """Test that the GUI properly displays syntax highlighting colors."""
    
    # Create test window
    root = tk.Tk()
    root.title("GUI Color Scheme Test")
    root.geometry("1000x700")
    
    # Create GUI
    gui = GUI(root)
    
    # Create a temporary Python file with sample code
    sample_code = '''def hello_world():
    """Simple hello world function."""
    name = "World"
    message = f"Hello, {name}!"
    print(message)
    return message

# Call the function
if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sample_code)
        temp_file = f.name
    
    print(f'Created test file: {temp_file}')
    
    # Load the file content using the GUI
    try:
        gui.update_file_content('', filename=temp_file)
        print('✅ File loaded successfully with syntax highlighting!')
        print('Check the GUI window - you should see colored Python syntax highlighting.')
    except Exception as e:
        print(f'❌ Error loading file: {e}')
    
    # Clean up the temporary file
    try:
        os.unlink(temp_file)
        print('✅ Temporary file cleaned up')
    except:
        pass
    
    print('\n🎨 GUI Color Scheme Test Results:')
    print('- If you see colored syntax highlighting (keywords, strings, comments), the color scheme is working!')
    print('- If all text appears white/monochrome, there may be a color scheme issue.')
    print('- Close the window when done testing.')
    
    # Run the GUI
    root.mainloop()

if __name__ == "__main__":
    test_gui_color_scheme() 