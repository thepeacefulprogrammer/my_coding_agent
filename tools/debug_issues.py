#!/usr/bin/env python3
"""Debug script to test the issues"""

import tkinter as tk
import tempfile
import os
from src.gui import GUI

def test_color_scheme():
    """Test the color scheme"""
    print("=== Testing Color Scheme ===")
    root = tk.Tk()
    root.withdraw()
    gui = GUI(root)
    
    print(f"CodeView background: {gui.file_content_codeview.cget('bg')}")
    print(f"CodeView foreground: {gui.file_content_codeview.cget('fg')}")
    
    # Test with Python code
    test_code = '''def hello():
    """Test function"""
    print("Hello World")  # Comment
    return True'''
    
    gui.update_file_content(test_code, "test.py")
    print(f"Content set successfully: {len(gui.file_content_codeview.get('1.0', 'end-1c'))} chars")
    
    root.destroy()

def test_folder_selection():
    """Test folder selection behavior"""
    print("\n=== Testing Folder Selection ===")
    root = tk.Tk()
    root.withdraw()
    gui = GUI(root)
    
    # Create test structure
    with tempfile.TemporaryDirectory() as temp_dir:
        sub_dir = os.path.join(temp_dir, "test_folder")
        os.makedirs(sub_dir)
        
        # Populate tree
        scan_result = gui.file_explorer.scan_directory(temp_dir)
        gui.populate_tree(gui.tree_view, scan_result)
        
        items = gui.tree_view.get_children()
        print(f"Tree items found: {len(items)}")
        
        if items:
            # Check item data
            item_data = gui.tree_view.item(items[0])
            print(f"Item data: {item_data}")
            
            # Select the item
            gui.tree_view.selection_set(items[0])
            selected = gui.tree_view.selection()
            print(f"Selected: {selected}")
            
            # Test handler
            print("Testing open_folder_handler...")
            result = gui.open_folder_handler()
            print(f"Result: {result}")
    
    root.destroy()

if __name__ == "__main__":
    test_color_scheme()
    test_folder_selection() 