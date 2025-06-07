#!/usr/bin/env python3
"""
Manual testing application to verify syntax highlighting functionality.

This application creates a visual test environment to verify that the Nord color scheme
and syntax highlighting are working correctly for various programming languages.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.code_editor import CodeEditor
from src.syntax_manager import SyntaxManager
from src.color_schemes import get_available_color_schemes


class SyntaxHighlightingTestApp:
    """Visual test application for syntax highlighting."""
    
    def __init__(self, root):
        """Initialize the test application."""
        self.root = root
        self.root.title("Syntax Highlighting Test - Nord Color Scheme")
        self.root.geometry("1200x800")
        
        # Initialize components
        self.syntax_manager = SyntaxManager()
        self.current_editor = None
        
        # Setup UI
        self.setup_ui()
        
        # Load default Python example
        self.load_python_example()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Language selection
        ttk.Label(control_frame, text="Language:").pack(side="left", padx=(0, 5))
        self.language_var = tk.StringVar(value="Python")
        language_combo = ttk.Combobox(control_frame, textvariable=self.language_var, 
                                     values=["Python", "JavaScript", "HTML", "CSS", "JSON", "Markdown"],
                                     state="readonly", width=15)
        language_combo.pack(side="left", padx=(0, 10))
        language_combo.bind("<<ComboboxSelected>>", self.on_language_change)
        
        # Color scheme selection
        ttk.Label(control_frame, text="Color Scheme:").pack(side="left", padx=(10, 5))
        self.color_scheme_var = tk.StringVar(value="nord")
        available_schemes = list(get_available_color_schemes().keys()) + ["monokai", "dracula"]
        scheme_combo = ttk.Combobox(control_frame, textvariable=self.color_scheme_var,
                                   values=available_schemes, state="readonly", width=15)
        scheme_combo.pack(side="left", padx=(0, 10))
        scheme_combo.bind("<<ComboboxSelected>>", self.on_color_scheme_change)
        
        # Buttons
        ttk.Button(control_frame, text="Load File", command=self.load_file).pack(side="left", padx=(10, 5))
        ttk.Button(control_frame, text="Refresh", command=self.refresh_display).pack(side="left", padx=(0, 5))
        
        # Editor frame with scrollbar
        editor_frame = ttk.Frame(main_frame)
        editor_frame.pack(fill="both", expand=True)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(editor_frame)
        self.scrollbar.pack(side="right", fill="y")
        
        # Create initial editor
        self.create_editor(editor_frame)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Nord color scheme loaded")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief="sunken")
        status_bar.pack(fill="x", pady=(10, 0))
        
    def create_editor(self, parent):
        """Create a new code editor with current settings."""
        color_scheme = self.color_scheme_var.get()
        
        # Create editor
        self.current_editor = CodeEditor(
            parent, 
            self.syntax_manager, 
            scrollbar=self.scrollbar,
            color_scheme=color_scheme,
            width=100, 
            height=30
        )
        
        # Create widget
        language = self.language_var.get()
        filename = self.get_filename_for_language(language)
        lexer = self.syntax_manager.get_lexer_for_file(filename)
        
        widget = self.current_editor.create_widget(lexer=lexer)
        widget.pack(side="left", fill="both", expand=True)
        
        # Set as current widget
        self.current_editor.current_widget = widget
        
        self.status_var.set(f"Editor created with {color_scheme} color scheme for {language}")
        
    def get_filename_for_language(self, language):
        """Get a representative filename for the language."""
        language_map = {
            "Python": "test.py",
            "JavaScript": "test.js", 
            "HTML": "test.html",
            "CSS": "test.css",
            "JSON": "test.json",
            "Markdown": "test.md"
        }
        return language_map.get(language, "test.txt")
        
    def get_sample_code(self, language):
        """Get sample code for the specified language."""
        if language == "Python":
            return '''#!/usr/bin/env python3
"""
Sample Python code to demonstrate Nord syntax highlighting.
"""

import os
import sys
from typing import List, Dict, Optional

# Global constants
VERSION = "1.0.0"
DEBUG = True

class SyntaxDemo:
    """A demonstration class for syntax highlighting."""
    
    def __init__(self, name: str, items: List[str] = None):
        """Initialize the demo."""
        self.name = name
        self.items = items or []
        self._count = 0
    
    @property
    def count(self) -> int:
        """Get the current count."""
        return self._count
    
    @staticmethod
    def create_greeting(name: str) -> str:
        """Create a personalized greeting."""
        if not name:
            return "Hello, Anonymous!"
        return f"Hello, {name.title()}! 👋"
    
    def process_items(self, filter_func=None) -> Dict[str, int]:
        """Process items with optional filtering."""
        result = {}
        
        for i, item in enumerate(self.items):
            # This is a comment
            if filter_func and not filter_func(item):
                continue
                
            # Multi-line string with f-string
            description = f"""
            Item {i}: {item.upper()}
            Length: {len(item)}
            Type: {type(item).__name__}
            """
            
            result[item] = len(item)
            self._count += 1
        
        return result

def main():
    """Main function demonstrating syntax highlighting."""
    # Create demo instance
    demo = SyntaxDemo("Test Demo", ["apple", "banana", "cherry"])
    
    # Lambda function
    vowel_filter = lambda x: x[0].lower() in 'aeiou'
    
    # List comprehension
    filtered_items = [item for item in demo.items if len(item) > 4]
    
    # Dictionary comprehension
    item_lengths = {item: len(item) for item in demo.items}
    
    # Exception handling
    try:
        result = demo.process_items(vowel_filter)
        print("✅ Processing successful!")
        
        for item, length in result.items():
            print(f"  {item}: {length} characters")
            
    except (ValueError, TypeError) as e:
        print(f"❌ Error: {e}")
    finally:
        print(f"🔄 Total processed: {demo.count}")
    
    # Format strings
    summary = f"""
    Demo Summary:
    =============
    Name: {demo.name}
    Items: {demo.items}
    Greeting: {demo.create_greeting("Developer")}
    """
    
    print(summary)

if __name__ == "__main__":
    main()
'''
        else:
            return f"# Sample {language} code\nprint('Hello, World!')"
        
    def load_python_example(self):
        """Load the default Python example."""
        if self.current_editor and self.current_editor.current_widget:
            sample_code = self.get_sample_code("Python")
            self.current_editor.current_widget.delete("1.0", tk.END)
            self.current_editor.current_widget.insert("1.0", sample_code)
            self.status_var.set("Python example loaded with Nord color scheme")
            
    def on_language_change(self, event=None):
        """Handle language selection change."""
        self.refresh_display()
        
    def on_color_scheme_change(self, event=None):
        """Handle color scheme selection change."""
        self.refresh_display()
        
    def refresh_display(self):
        """Refresh the display with current settings."""
        if self.current_editor and self.current_editor.current_widget:
            # Destroy current widget
            self.current_editor.current_widget.destroy()
            
        # Get parent frame
        editor_frame = self.scrollbar.master
        
        # Create new editor with current settings
        self.create_editor(editor_frame)
        
        # Load appropriate sample code
        language = self.language_var.get()
        sample_code = self.get_sample_code(language)
        
        if self.current_editor and self.current_editor.current_widget:
            self.current_editor.current_widget.delete("1.0", tk.END)
            self.current_editor.current_widget.insert("1.0", sample_code)
            
        color_scheme = self.color_scheme_var.get()
        self.status_var.set(f"{language} example loaded with {color_scheme} color scheme")
        
    def load_file(self):
        """Load a file for syntax highlighting."""
        filename = filedialog.askopenfilename(
            title="Select a file to highlight",
            filetypes=[
                ("Python files", "*.py"),
                ("JavaScript files", "*.js"),
                ("HTML files", "*.html"),
                ("CSS files", "*.css"),
                ("JSON files", "*.json"),
                ("Markdown files", "*.md"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if self.current_editor and self.current_editor.current_widget:
                    self.current_editor.current_widget.delete("1.0", tk.END)
                    self.current_editor.current_widget.insert("1.0", content)
                    
                # Update language based on file extension
                ext = os.path.splitext(filename)[1].lower()
                language_map = {
                    '.py': 'Python',
                    '.js': 'JavaScript',
                    '.html': 'HTML',
                    '.css': 'CSS',
                    '.json': 'JSON',
                    '.md': 'Markdown'
                }
                
                if ext in language_map:
                    self.language_var.set(language_map[ext])
                    self.refresh_display()
                    
                self.status_var.set(f"Loaded file: {os.path.basename(filename)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")


def main():
    """Main function to run the test application."""
    root = tk.Tk()
    app = SyntaxHighlightingTestApp(root)
    
    print("🎨 Nord Syntax Highlighting Test App")
    print("=" * 40)
    print("Features:")
    print("• Nord color scheme implementation")
    print("• Multiple programming languages")
    print("• Visual syntax highlighting verification")
    print("• File loading capability")
    print("• Color scheme comparison")
    print()
    print("Instructions:")
    print("1. Select different languages from the dropdown")
    print("2. Compare color schemes (Nord vs built-in)")
    print("3. Load your own files for testing")
    print("4. Verify syntax highlighting works correctly")
    print()
    
    root.mainloop()


if __name__ == "__main__":
    main() 