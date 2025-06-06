import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from tkinter import ttk
import os
from chlorophyll import CodeView

try:
    from .file_explorer import FileExplorer
    from .syntax_manager import SyntaxManager
    from .folder_dialog import askdirectory_custom
    from .code_editor import CodeEditor
except ImportError:
    from file_explorer import FileExplorer
    from syntax_manager import SyntaxManager
    from folder_dialog import askdirectory_custom
    from code_editor import CodeEditor

class GUI:
    """Main GUI class for the file explorer application"""
    
    def __init__(self, root):
        """Initialize the GUI"""
        self.root = root
        self.current_directory = None  # Track current working directory
        self.file_explorer = FileExplorer()
        self.syntax_manager = SyntaxManager()  # Initialize syntax manager
        
        # Set window title and size
        self.root.title("Vibe Coding - File Explorer")
        self.root.geometry("800x600")
        
        # Bind cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
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
        """Create the main layout with sidebar and content areas"""
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
        
        # Create paned window for sidebar and content
        paned_window = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Create tree frame (sidebar)
        self.tree_frame = tk.Frame(paned_window, width=250)
        paned_window.add(self.tree_frame, minsize=200)
        
        # Create tree view with scrollbar
        tree_container = tk.Frame(self.tree_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        self.tree_scrollbar = tk.Scrollbar(tree_container)
        self.tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create tree view widget
        self.tree_view = ttk.Treeview(tree_container, yscrollcommand=self.tree_scrollbar.set)
        self.tree_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        self.tree_scrollbar.config(command=self.tree_view.yview)
        
        # Setup tree events for expand/collapse functionality
        self.setup_tree_events(self.tree_view)
        
        # Create content frame
        self.content_frame = tk.Frame(paned_window, bg='white')
        paned_window.add(self.content_frame, minsize=300)
        
        # Create text widget container with scrollbar
        text_container = tk.Frame(self.content_frame)
        text_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollbar for file content
        self.file_content_scrollbar = tk.Scrollbar(text_container)
        self.file_content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create CodeEditor for syntax highlighting with color scheme support
        self.code_editor = CodeEditor(
            text_container, 
            self.syntax_manager, 
            scrollbar=self.file_content_scrollbar,
            color_scheme="monokai"
        )
        
        # Create initial widget without automatic grid layout
        widget = self.code_editor.create_widget()
        self.code_editor.configure_scrollbar(widget)
        self.code_editor.current_widget = widget
        
        # Use pack geometry manager instead of grid
        widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Get the current widget for compatibility
        self.file_content_codeview = self.code_editor.current_widget
    
    def open_folder_handler(self):
        """Handle opening a folder"""
        # Always show folder selection dialog regardless of tree selection
        print("Showing folder selection dialog...")
        selected_folder = self.open_folder_dialog()
        
        if selected_folder:
            print(f"✅ Opening folder from dialog: {selected_folder}")
            self.current_directory = selected_folder
            
            # Set FileExplorer's current directory
            self.file_explorer.current_directory = selected_folder
            
            # Scan the directory and populate tree view
            try:
                scan_result = self.file_explorer.scan_directory(selected_folder)
                self.populate_tree(self.tree_view, scan_result)
                print(f"✅ Tree populated with {len(scan_result.get('files', []))} files, {len(scan_result.get('directories', []))} dirs")
            except Exception as e:
                print(f"❌ Error scanning directory: {e}")
                # Handle errors gracefully - clear tree view if scan fails
                self.populate_tree(self.tree_view, {'directories': [], 'files': []})
                
        return selected_folder
    
    def new_folder_handler(self):
        """Handle creating a new folder"""
        if self.current_directory:
            return self.new_folder_dialog(self.current_directory)
        return None
    
    def open_folder_dialog(self):
        """Show dialog to select a folder"""
        # Set initial directory to current directory if available, otherwise use home directory
        initial_dir = self.current_directory if self.current_directory else os.path.expanduser("~")
        
        # Use our custom folder dialog that properly handles folder selection
        folder_path = askdirectory_custom(
            parent=self.root,
            title="Select Project Folder",
            initialdir=initial_dir
        )
        return folder_path if folder_path else None
            
    def new_folder_dialog(self, parent_path=None):
        """Show dialog to create a new folder"""
        # Use provided parent_path or current_directory
        if parent_path is None:
            if not self.current_directory:
                messagebox.showwarning("No Directory", "Please select a directory first.")
                return
            parent_path = self.current_directory
            
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
            if hasattr(self, 'current_directory') and self.current_directory:
                messagebox.showinfo("Success", f"Folder '{folder_name}' created successfully.")
            return new_folder_path
        except (OSError, PermissionError):
            # Handle errors gracefully - in a real app we'd show an error dialog
            return None
    
    def populate_tree(self, treeview, data):
        """Populate tree view with file and directory data
        
        Args:
            treeview: The ttk.Treeview widget to populate
            data: Dictionary with 'files' and 'directories' keys containing lists of paths
        """
        # Clear existing items
        for item in treeview.get_children():
            treeview.delete(item)
        
        # Insert directories first (typically shown at top)
        for directory in data.get('directories', []):
            # Extract just the folder name from the full path
            folder_name = os.path.basename(directory)
            # Insert with folder icon/indicator and make expandable
            item_id = treeview.insert('', 'end', text=folder_name, values=(directory, 'directory'))
            # Add a placeholder child to make the directory expandable
            treeview.insert(item_id, 'end', text='', values=('', 'placeholder'))
        
        # Insert files after directories
        for file_path in data.get('files', []):
            # Extract just the filename from the full path
            filename = os.path.basename(file_path)
            # Insert with file icon/indicator
            treeview.insert('', 'end', text=filename, values=(file_path, 'file'))
    
    def setup_tree_events(self, treeview):
        """Setup event bindings for tree view expand/collapse and selection functionality
        
        Args:
            treeview: The ttk.Treeview widget to bind events to
        """
        # Bind tree expansion event
        treeview.bind('<<TreeviewOpen>>', self.on_tree_item_expand)
        
        # Bind tree selection event
        treeview.bind('<<TreeviewSelect>>', self.on_tree_item_select)
        
        # Bind double-click event for folder navigation
        treeview.bind('<Double-1>', self.on_tree_item_double_click)
    
    def on_tree_item_expand(self, event):
        """Handle tree item expansion to load directory contents
        
        Args:
            event: Tkinter event object containing widget and item information
        """
        try:
            treeview = event.widget
            selected_items = treeview.selection()
            
            if not selected_items:
                # If no selection, get the item that was actually opened
                # This is a bit tricky with TreeviewOpen - we need to find the opened item
                focus_item = treeview.focus()
                if focus_item:
                    selected_items = [focus_item]
                else:
                    return
            
            item_id = selected_items[0]
            item_data = treeview.item(item_id)
            values = item_data.get('values', [])
            
            if len(values) < 2 or values[1] != 'directory':
                # Only expand directories, not files
                return
            
            directory_path = values[0]
            
            # Check if already expanded (has real children, not just placeholder)
            children = treeview.get_children(item_id)
            if children:
                # Check if the first child is a placeholder
                first_child = children[0]
                first_child_data = treeview.item(first_child)
                first_child_values = first_child_data.get('values', [])
                if len(first_child_values) >= 2 and first_child_values[1] == 'placeholder':
                    # Remove placeholder
                    treeview.delete(first_child)
                else:
                    # Already has real children, don't reload
                    return
            
            # Scan directory and populate children
            try:
                scan_result = self.file_explorer.scan_directory(directory_path)
                
                # Insert subdirectories first
                for subdirectory in scan_result.get('directories', []):
                    subfolder_name = os.path.basename(subdirectory)
                    child_id = treeview.insert(item_id, 'end', text=subfolder_name, values=(subdirectory, 'directory'))
                    # Add placeholder to make subdirectory expandable
                    treeview.insert(child_id, 'end', text='', values=('', 'placeholder'))
                
                # Insert files
                for file_path in scan_result.get('files', []):
                    filename = os.path.basename(file_path)
                    treeview.insert(item_id, 'end', text=filename, values=(file_path, 'file'))
                    
            except (OSError, PermissionError) as e:
                # Handle directory access errors gracefully
                # Insert an error indicator
                treeview.insert(item_id, 'end', text='[Access Denied]', values=('', 'error'))
                
        except Exception as e:
            # Catch any other unexpected errors and handle gracefully
            pass
    
    def refresh_tree(self):
        """Refresh the tree view by calling FileExplorer.refresh() and updating the display
        
        Returns:
            bool: True if refresh was successful, False or None if no directory or refresh failed
        """
        try:
            # Call FileExplorer.refresh() to get updated directory contents
            refreshed_data = self.file_explorer.refresh()
            
            # If no current directory or refresh failed, return gracefully
            if refreshed_data is None:
                return None
            
            # Update the tree view with the refreshed data
            self.populate_tree(self.tree_view, refreshed_data)
            
            return True
            
        except Exception as e:
            # Handle any errors gracefully
            return False
    
    def on_tree_item_select(self, event):
        """Handle tree item selection to load file content
        
        Args:
            event: Tkinter event object containing widget and item information
        """
        try:
            treeview = event.widget
            selected_items = treeview.selection()
            
            # If no selection, return gracefully
            if not selected_items:
                return
            
            item_id = selected_items[0]
            item_data = treeview.item(item_id)
            values = item_data.get('values', [])
            
            # Check if we have valid values and it's a file
            if len(values) < 2 or values[1] != 'file':
                # Only load content for files, not directories
                return
            
            file_path = values[0]
            
            # Read file content using FileExplorer
            content = self.file_explorer.read_file(file_path)
            
            # Update the CodeView widget with content and filename for syntax highlighting
            if content is not None:
                self.update_file_content(content, filename=file_path)
            else:
                # If file is unreadable, show appropriate message
                self.update_file_content("[Unable to read file - may be binary or protected]")
                
        except Exception as e:
            # Handle any errors gracefully
            self.update_file_content("[Error loading file content]")
    
    def update_file_content(self, content, filename=None):
        """Update the file content using CodeEditor with proper syntax highlighting
        
        Args:
            content (str): Content to display in the CodeView widget
            filename (str, optional): Filename for syntax highlighting detection
        """
        try:
            if filename:
                # Get appropriate lexer for syntax highlighting
                lexer = self.syntax_manager.get_lexer_for_file(filename)
                
                # Always recreate widget to ensure proper syntax highlighting and color scheme
                if True:  # Simplified approach - always recreate for syntax highlighting
                    # Need to create new widget with different lexer
                    old_widget = self.code_editor.current_widget
                    
                    # Create new widget with proper lexer and color scheme
                    new_widget = self.code_editor.create_widget(lexer=lexer)
                    
                    # Replace the old widget in the GUI layout
                    if old_widget:
                        try:
                            # Safely unpack and destroy old widget
                            old_widget.pack_forget()
                            old_widget.destroy()
                        except tk.TclError:
                            # Widget may already be destroyed
                            pass
                    
                    try:
                        # Pack the new widget
                        new_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                        
                        # Update CodeEditor state
                        self.code_editor.current_widget = new_widget
                        self.code_editor.configure_scrollbar(new_widget)
                        
                        # Update GUI reference
                        self.file_content_codeview = new_widget
                    except tk.TclError as e:
                        print(f"Widget packing error: {e}")
                        # Fall back to current widget
                        pass
            
            # Update content in the current widget
            widget = self.code_editor.current_widget
            if widget:
                # Enable for editing
                widget.config(state='normal')
                
                # Clear and insert content
                widget.delete('1.0', 'end')
                if filename:
                    # Read content from file for proper encoding handling
                    try:
                        with open(filename, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        widget.insert('1.0', file_content)
                    except Exception:
                        widget.insert('1.0', content)
                else:
                    widget.insert('1.0', content)
                
                # Set back to read-only and scroll to top
                widget.config(state='disabled')
                widget.see('1.0')
                
                print(f"✅ Updated content for {filename or 'text file'} with syntax highlighting")
            
        except Exception as e:
            print(f"❌ Error in update_file_content: {e}")
            # Fallback to basic content update
            try:
                widget = self.code_editor.current_widget
                if widget:
                    widget.config(state='normal')
                    widget.delete('1.0', 'end')
                    widget.insert('1.0', content)
                    widget.config(state='disabled')
                    widget.see('1.0')
            except:
                pass
    
    def on_tree_item_double_click(self, event):
        """Handle double-click on tree items for navigation
        
        Args:
            event: Tkinter event object containing widget and item information
        """
        try:
            treeview = event.widget
            selected_items = treeview.selection()
            
            if not selected_items:
                return
            
            item_id = selected_items[0]
            item_data = treeview.item(item_id)
            values = item_data.get('values', [])
            
            # Check if it's a directory
            if len(values) >= 2 and values[1] == 'directory':
                directory_path = values[0]
                
                # Navigate to this directory (make it the current directory)
                self.current_directory = directory_path
                self.file_explorer.current_directory = directory_path
                
                # Scan and populate the tree with this directory as root
                try:
                    scan_result = self.file_explorer.scan_directory(directory_path)
                    self.populate_tree(self.tree_view, scan_result)
                except Exception as e:
                    # Handle errors gracefully
                    self.populate_tree(self.tree_view, {'directories': [], 'files': []})
                    
        except Exception as e:
            # Handle any errors gracefully
            pass
    
    def on_closing(self):
        """Handle window closing with proper cleanup"""
        try:
            # Clean up CodeEditor resources
            if hasattr(self, 'code_editor') and self.code_editor:
                self.code_editor.destroy_widget_safely()
                if hasattr(self.code_editor, 'invalidate_cache'):
                    self.code_editor.invalidate_cache()
        except Exception as e:
            print(f"Cleanup warning: {e}")
        finally:
            # Destroy the window
            self.root.destroy()