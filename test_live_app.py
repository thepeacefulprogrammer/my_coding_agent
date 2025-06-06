#!/usr/bin/env python3
"""
Test script to verify the live application
"""

import tkinter as tk
from src.gui import GUI
import os
import sys

def check_app_can_launch():
    """Test that the app can launch without errors (for automated testing)"""
    print("🧪 Testing app launch without GUI...")
    
    root = tk.Tk()
    root.withdraw()  # Hide the window during automated testing
    
    try:
        # Create GUI
        gui = GUI(root)
        
        # Set up initial directory to current directory
        current_dir = os.getcwd()
        gui.current_directory = current_dir
        gui.file_explorer.current_directory = current_dir
        
        # Test basic functionality without showing GUI
        scan_result = gui.file_explorer.scan_directory(current_dir)
        
        print(f"✅ App can launch successfully")
        print(f"✅ Directory scanning works: {len(scan_result.get('files', []))} files found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during app test: {e}")
        return False
    finally:
        root.destroy()

def launch_app_interactive():
    """Launch the app interactively for manual testing"""
    print("🚀 Launching interactive test app...")
    
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

# When run by pytest, use the non-interactive test
# When run directly, use the interactive version
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        launch_app_interactive()
    else:
        # Default to interactive when run directly
        launch_app_interactive()

# For pytest discovery - this will run the non-interactive version
def test_live_app():
    """Pytest-compatible test function"""
    assert check_app_can_launch(), "App should launch successfully" 