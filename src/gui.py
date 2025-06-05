import tkinter as tk
from tkinter import filedialog, simpledialog
import os

class GUI:
    """Main GUI class for the file explorer application"""
    
    def __init__(self, root):
        """Initialize the GUI"""
        self.root = root
        self.current_directory = None  # Track current working directory
        
        # Set window title and size
        self.root.title("Vibe Coding - File Explorer")
        self.root.geometry("800x600")
        
        # Create main menu
        self.create_menu()
        
        # Create main layout
        self.create_layout()
    
    def create_menu(self):
        """Create the main menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Folder", command=self.open_folder_handler)
        file_menu.add_command(label="New Folder", command=self.new_folder_handler)
    
    def create_layout(self):
        """Create the main application layout"""
        # Main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top buttons frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Open Folder button
        open_btn = tk.Button(button_frame, text="Open Folder", command=self.open_folder_handler)
        open_btn.pack(side="left", padx=(0, 10))
        
        # New Folder button
        new_btn = tk.Button(button_frame, text="New Folder", command=self.new_folder_handler)
        new_btn.pack(side="left")
        
        # Placeholder content area
        content_frame = tk.Frame(main_frame, bg="lightgray", relief="sunken", bd=2)
        content_frame.pack(fill="both", expand=True)
        
        # Add placeholder label
        placeholder_label = tk.Label(content_frame, text="File explorer content will appear here", 
                                      bg="lightgray", fg="gray")
        placeholder_label.pack(expand=True)
    
    def open_folder_handler(self):
        """Handle opening a folder"""
        selected_folder = self.open_folder_dialog()
        if selected_folder:
            self.current_directory = selected_folder
        return selected_folder
    
    def new_folder_handler(self):
        """Handle creating a new folder"""
        if self.current_directory:
            return self.new_folder_dialog(self.current_directory)
        return None
    
    def open_folder_dialog(self):
        """Show dialog to select a folder"""
        folder_path = filedialog.askdirectory(title="Select Project Folder")
        return folder_path if folder_path else None
    
    def new_folder_dialog(self, parent_path):
        """Show dialog to create a new folder"""
        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        
        # Handle empty or invalid names
        if not folder_name or not folder_name.strip():
            return None
        
        # Clean the folder name
        folder_name = folder_name.strip()
        
        # Create the full path
        new_folder_path = os.path.join(parent_path, folder_name)
        
        try:
            os.mkdir(new_folder_path)
            return new_folder_path
        except (OSError, PermissionError):
            # Handle errors gracefully - in a real app we'd show an error dialog
            return None