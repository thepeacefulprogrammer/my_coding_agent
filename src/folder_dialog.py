"""
Custom folder selection dialog that properly handles folder selection
"""
import tkinter as tk
from tkinter import ttk
import os


class FolderSelectDialog:
    """Custom folder selection dialog that returns the selected folder, not the navigated one"""
    
    def __init__(self, parent=None, title="Select Folder", initialdir=None):
        self.result = None
        self.selected_folder = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x400")
        self.dialog.resizable(True, True)
        
        # Make it modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"600x400+{x}+{y}")
        
        # Initialize starting directory
        self.current_dir = initialdir or os.path.expanduser("~")
        
        self.create_widgets()
        self.populate_tree()
        
    def create_widgets(self):
        """Create the dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Path label
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(path_frame, text="Current Path:").pack(side=tk.LEFT)
        self.path_var = tk.StringVar(value=self.current_dir)
        self.path_label = ttk.Label(path_frame, textvariable=self.path_var, relief=tk.SUNKEN)
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Tree frame
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview with scrollbar
        self.tree = ttk.Treeview(tree_frame, selectmode='browse')
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # Selection info
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text="Selected:").pack(side=tk.LEFT)
        self.selection_var = tk.StringVar(value="(None)")
        ttk.Label(info_frame, textvariable=self.selection_var, relief=tk.SUNKEN).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        self.ok_button = ttk.Button(button_frame, text="OK", command=self.ok, state=tk.DISABLED)
        self.ok_button.pack(side=tk.RIGHT)
        
        # Up button
        ttk.Button(button_frame, text="Up", command=self.go_up).pack(side=tk.LEFT)
        
    def populate_tree(self):
        """Populate the tree with directories"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Update path label
        self.path_var.set(self.current_dir)
        
        try:
            # Get directories in current path
            items = []
            for item in os.listdir(self.current_dir):
                item_path = os.path.join(self.current_dir, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    items.append((item, item_path))
            
            # Sort directories
            items.sort(key=lambda x: x[0].lower())
            
            # Insert directories
            for name, path in items:
                self.tree.insert('', 'end', text=name, values=(path,))
                
        except (OSError, PermissionError):
            # Handle permission errors gracefully
            self.tree.insert('', 'end', text="[Permission Denied]", values=('',))
    
    def on_select(self, event):
        """Handle tree selection"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            if values and values[0]:
                self.selected_folder = values[0]
                self.selection_var.set(os.path.basename(self.selected_folder))
                self.ok_button.config(state=tk.NORMAL)
            else:
                self.selected_folder = None
                self.selection_var.set("(None)")
                self.ok_button.config(state=tk.DISABLED)
        else:
            self.selected_folder = None
            self.selection_var.set("(None)")
            self.ok_button.config(state=tk.DISABLED)
    
    def on_double_click(self, event):
        """Handle double-click to navigate into folder"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            if values and values[0]:
                self.current_dir = values[0]
                self.populate_tree()
                # Clear selection after navigation
                self.selected_folder = None
                self.selection_var.set("(None)")
                self.ok_button.config(state=tk.DISABLED)
    
    def go_up(self):
        """Navigate to parent directory"""
        parent = os.path.dirname(self.current_dir)
        if parent != self.current_dir:  # Avoid infinite loop at root
            self.current_dir = parent
            self.populate_tree()
            # Clear selection after navigation
            self.selected_folder = None
            self.selection_var.set("(None)")
            self.ok_button.config(state=tk.DISABLED)
    
    def ok(self):
        """Handle OK button"""
        if self.selected_folder:
            self.result = self.selected_folder
        self.dialog.destroy()
    
    def cancel(self):
        """Handle Cancel button"""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the selected folder"""
        # Focus on the dialog
        self.dialog.focus_set()
        
        # Wait for dialog to close
        self.dialog.wait_window()
        
        return self.result


def askdirectory_custom(parent=None, title="Select Folder", initialdir=None):
    """Custom askdirectory that properly returns the selected folder"""
    dialog = FolderSelectDialog(parent, title, initialdir)
    return dialog.show()


if __name__ == "__main__":
    # Test the custom dialog
    root = tk.Tk()
    root.withdraw()
    
    result = askdirectory_custom(title="Test Custom Folder Dialog")
    print(f"Selected folder: {result}")
    
    root.destroy() 