#!/usr/bin/env python3
"""
Main entry point for the Vibe Coding IDE
"""
import tkinter as tk
import sys
import os

# Add the src directory to Python path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import GUI

def main():
    """Launch the Vibe Coding IDE"""
    try:
        root = tk.Tk()
        root.geometry("800x600")  # Set a reasonable default size
        app = GUI(root)
        
        print("Vibe Coding IDE launched successfully!")
        print("- Open Folder button/menu available")
        print("- New Folder button/menu available")
        print("Close the window to exit.")
        
        root.mainloop()
        
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 