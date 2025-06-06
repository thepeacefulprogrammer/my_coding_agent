#!/usr/bin/env python3
"""
Test script to verify the live application
"""

import tkinter as tk
from src.gui import GUI
import os

def test_app():
    """Launch the app and test it"""
    print("🚀 Launching test app...")
    
    root = tk.Tk()
    root.title("Vibe Coding IDE - Test")
    root.geometry("800x600")
    
    # Create GUI
    gui = GUI(root)
    
    # Set up initial directory to current directory
    current_dir = os.getcwd()
    gui.current_directory = current_dir
    gui.file_explorer.current_directory = current_dir
    
    # Scan and populate
    try:
        scan_result = gui.file_explorer.scan_directory(current_dir)
        gui.populate_tree(gui.tree_view, scan_result)
        print(f"✅ Loaded directory: {current_dir}")
        print(f"✅ Found {len(scan_result.get('files', []))} files and {len(scan_result.get('directories', []))} directories")
    except Exception as e:
        print(f"❌ Error loading directory: {e}")
    
    # Test syntax highlighting with demo file
    if os.path.exists("demo_test_fixes.py"):
        with open("demo_test_fixes.py", 'r') as f:
            content = f.read()
        gui.update_file_content(content, "demo_test_fixes.py")
        print("✅ Loaded demo_test_fixes.py for syntax highlighting test")
    
    print("\n📝 Instructions:")
    print("1. Check if the editor background is dark (not white)")
    print("2. Check if Python code has colorful syntax highlighting")
    print("3. Select a folder in the tree and click 'Open Folder'")
    print("4. It should navigate to that folder without showing a dialog")
    print("\nClose the window when done testing.")
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    test_app() 