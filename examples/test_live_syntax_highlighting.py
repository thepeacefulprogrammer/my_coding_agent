#!/usr/bin/env python3
"""
Manual Test Application for Syntax Highlighting Verification

This application provides a visual interface to test and verify syntax highlighting
functionality across multiple programming languages using the Nord color scheme.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from code_editor import CodeEditor
    from syntax_manager import SyntaxManager
    from color_scheme_config import ColorSchemeConfig
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

class SyntaxHighlightingTestApp:
    """Visual test application for syntax highlighting verification."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Syntax Highlighting Visual Test Application")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2E3440')  # Nord background
        
        # Initialize components
        self.syntax_manager = SyntaxManager()
        self.color_config = ColorSchemeConfig()
        self.code_editor = None
        
        # Sample code for different languages
        self.sample_code = {
            'Python': '''#!/usr/bin/env python3
"""
Sample Python code for syntax highlighting test
"""

import os
import sys
from typing import List, Dict, Optional

class SampleClass:
    """A sample class with various Python features."""
    
    def __init__(self, name: str):
        self.name = name
        self._private_var = 42
        
    @property
    def display_name(self) -> str:
        """Get formatted display name."""
        return f"Name: {self.name}"
    
    @staticmethod
    def utility_function(data: List[int]) -> Dict[str, int]:
        """Process data and return statistics."""
        result = {
            'count': len(data),
            'sum': sum(data),
            'max': max(data) if data else 0
        }
        return result

def main():
    # Create instance and test
    obj = SampleClass("Test Object")
    numbers = [1, 2, 3, 4, 5]
    
    try:
        stats = obj.utility_function(numbers)
        print(f"Statistics: {stats}")
    except Exception as e:
        print(f"Error: {e}")
    
    # List comprehension and lambda
    squares = [x**2 for x in numbers if x % 2 == 0]
    filtered = list(filter(lambda x: x > 10, squares))
    
    return filtered

if __name__ == "__main__":
    main()
''',
            
            'JavaScript': '''// Sample JavaScript code for syntax highlighting test
/**
 * A sample JavaScript module with various language features
 */

import { EventEmitter } from 'events';

class SampleClass extends EventEmitter {
    constructor(name) {
        super();
        this.name = name;
        this._privateVar = 42;
    }
    
    get displayName() {
        return `Name: ${this.name}`;
    }
    
    async processData(data) {
        try {
            const result = await this.calculateStats(data);
            this.emit('processed', result);
            return result;
        } catch (error) {
            console.error('Processing failed:', error);
            throw error;
        }
    }
    
    calculateStats(data) {
        return new Promise((resolve) => {
            const stats = {
                count: data.length,
                sum: data.reduce((a, b) => a + b, 0),
                average: data.length > 0 ? data.reduce((a, b) => a + b, 0) / data.length : 0
            };
            
            setTimeout(() => resolve(stats), 100);
        });
    }
}

// Arrow functions and destructuring
const numbers = [1, 2, 3, 4, 5];
const processNumbers = (arr) => arr.filter(x => x % 2 === 0).map(x => x ** 2);

// Template literals and spread operator
const formatResult = (name, ...values) => {
    return `Results for ${name}: [${values.join(', ')}]`;
};

export { SampleClass, processNumbers, formatResult };
''',
            
            'HTML': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sample HTML for Syntax Highlighting Test</title>
    <link rel="stylesheet" href="styles.css">
    <style>
        .highlight {
            background-color: #EBCB8B;
            color: #2E3440;
            padding: 2px 4px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <!-- Main content section -->
    <header class="main-header">
        <h1 id="title">Syntax Highlighting Test</h1>
        <nav>
            <ul class="nav-list">
                <li><a href="#section1" data-section="1">Section 1</a></li>
                <li><a href="#section2" data-section="2">Section 2</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section id="section1" class="content-section">
            <h2>Sample Content</h2>
            <p>This is a <span class="highlight">highlighted</span> paragraph with various HTML elements.</p>
            
            <form action="/submit" method="post">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
                
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" placeholder="user@example.com">
                
                <button type="submit">Submit</button>
            </form>
        </section>
        
        <section id="section2">
            <h3>Code Example</h3>
            <pre><code>
function example() {
    console.log("Hello, World!");
}
            </code></pre>
        </section>
    </main>
    
    <script src="script.js"></script>
    <script>
        // Inline JavaScript
        document.addEventListener('DOMContentLoaded', function() {
            const title = document.getElementById('title');
            title.addEventListener('click', () => {
                alert('Title clicked!');
            });
        });
    </script>
</body>
</html>
''',
            
            'CSS': '''/* Sample CSS for syntax highlighting test */

:root {
    --nord-bg: #2E3440;
    --nord-fg: #D8DEE9;
    --nord-accent: #88C0D0;
    --nord-highlight: #EBCB8B;
}

/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    background-color: var(--nord-bg);
    color: var(--nord-fg);
    line-height: 1.6;
}

/* Header styles */
.main-header {
    background: linear-gradient(135deg, #434C5E, #4C566A);
    padding: 1rem 2rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.main-header h1 {
    color: var(--nord-accent);
    font-size: 2.5rem;
    font-weight: 300;
    text-align: center;
    margin-bottom: 1rem;
}

/* Navigation styles */
.nav-list {
    display: flex;
    justify-content: center;
    list-style: none;
    gap: 2rem;
}

.nav-list li a {
    color: var(--nord-fg);
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: all 0.3s ease;
}

.nav-list li a:hover {
    background-color: var(--nord-accent);
    color: var(--nord-bg);
    transform: translateY(-2px);
}

/* Content sections */
.content-section {
    max-width: 800px;
    margin: 2rem auto;
    padding: 2rem;
    background-color: #3B4252;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

/* Form styles */
form {
    margin-top: 1.5rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: var(--nord-accent);
}

input[type="text"],
input[type="email"] {
    width: 100%;
    padding: 0.75rem;
    margin-bottom: 1rem;
    border: 2px solid #4C566A;
    border-radius: 4px;
    background-color: var(--nord-bg);
    color: var(--nord-fg);
    font-size: 1rem;
}

input[type="text"]:focus,
input[type="email"]:focus {
    outline: none;
    border-color: var(--nord-accent);
    box-shadow: 0 0 0 3px rgba(136, 192, 208, 0.3);
}

button[type="submit"] {
    background-color: var(--nord-highlight);
    color: var(--nord-bg);
    padding: 0.75rem 2rem;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
}

button[type="submit"]:hover {
    background-color: #D08770;
    transform: translateY(-1px);
}

/* Code block styles */
pre {
    background-color: var(--nord-bg);
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
    border-left: 4px solid var(--nord-accent);
}

code {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    color: var(--nord-highlight);
}

/* Responsive design */
@media (max-width: 768px) {
    .main-header {
        padding: 1rem;
    }
    
    .main-header h1 {
        font-size: 2rem;
    }
    
    .nav-list {
        flex-direction: column;
        gap: 1rem;
    }
    
    .content-section {
        margin: 1rem;
        padding: 1rem;
    }
}
''',
            
            'JSON': '''{
    "name": "syntax-highlighting-test",
    "version": "1.0.0",
    "description": "Sample JSON for syntax highlighting verification",
    "main": "index.js",
    "scripts": {
        "start": "node index.js",
        "test": "jest",
        "lint": "eslint . --ext .js,.ts",
        "build": "webpack --mode production"
    },
    "dependencies": {
        "express": "^4.18.2",
        "lodash": "^4.17.21",
        "axios": "^1.4.0"
    },
    "devDependencies": {
        "jest": "^29.5.0",
        "eslint": "^8.42.0",
        "webpack": "^5.88.0"
    },
    "config": {
        "port": 3000,
        "environment": "development",
        "features": {
            "authentication": true,
            "logging": true,
            "caching": false
        }
    },
    "repository": {
        "type": "git",
        "url": "https://github.com/user/syntax-highlighting-test.git"
    },
    "keywords": ["syntax", "highlighting", "test", "colors", "nord"],
    "author": "Test Author <test@example.com>",
    "license": "MIT",
    "engines": {
        "node": ">=16.0.0",
        "npm": ">=8.0.0"
    }
}
''',
            
            'Markdown': '''# Syntax Highlighting Test Document

This is a **sample Markdown document** for testing syntax highlighting capabilities with the Nord color scheme.

## Table of Contents

1. [Basic Formatting](#basic-formatting)
2. [Code Examples](#code-examples)
3. [Lists and Tables](#lists-and-tables)
4. [Links and Images](#links-and-images)

## Basic Formatting

Here are some basic Markdown formatting examples:

- **Bold text** using double asterisks
- *Italic text* using single asterisks
- ~~Strikethrough text~~ using tildes
- `Inline code` using backticks

### Blockquotes

> This is a blockquote example.
> It can span multiple lines and provides 
> emphasis for important information.

## Code Examples

### Inline Code
Use `console.log()` to output messages in JavaScript.

### Code Blocks

```python
def fibonacci(n):
    """Generate Fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    
    return sequence

# Example usage
fib_numbers = fibonacci(10)
print(f"First 10 Fibonacci numbers: {fib_numbers}")
```

```javascript
// JavaScript example with async/await
async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        const userData = await response.json();
        return userData;
    } catch (error) {
        console.error('Failed to fetch user data:', error);
        throw error;
    }
}
```

## Lists and Tables

### Unordered List
- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
- Item 3

### Ordered List
1. First step
2. Second step
3. Third step

### Task List
- [x] Completed task
- [ ] Pending task
- [ ] Another pending task

### Table Example

| Language   | Extension | Syntax Highlighting |
|------------|-----------|-------------------|
| Python     | .py       | ✅ Supported      |
| JavaScript | .js       | ✅ Supported      |
| HTML       | .html     | ✅ Supported      |
| CSS        | .css      | ✅ Supported      |
| JSON       | .json     | ✅ Supported      |
| Markdown   | .md       | ✅ Supported      |

## Links and Images

[GitHub Repository](https://github.com/user/repo) - Link to repository

![Alt text](https://via.placeholder.com/300x200 "Sample image")

### Horizontal Rule

---

## Special Elements

### Math (if supported)
E = mc²

### Footnotes
This text has a footnote[^1].

[^1]: This is the footnote content.

### Definition Lists
Term 1
:   Definition for term 1

Term 2
:   Definition for term 2
    with multiple lines

---

*This document demonstrates various Markdown syntax elements for testing syntax highlighting.*
'''
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Test Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Language selection
        ttk.Label(control_frame, text="Language:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.language_var = tk.StringVar(value='Python')
        language_combo = ttk.Combobox(control_frame, textvariable=self.language_var, 
                                    values=list(self.sample_code.keys()), state='readonly')
        language_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        language_combo.bind('<<ComboboxSelected>>', self.on_language_change)
        
        # Color scheme selection
        ttk.Label(control_frame, text="Color Scheme:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.scheme_var = tk.StringVar(value='nord')
        scheme_combo = ttk.Combobox(control_frame, textvariable=self.scheme_var,
                                  values=['nord', 'monokai'], state='readonly')
        scheme_combo.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        scheme_combo.bind('<<ComboboxSelected>>', self.on_scheme_change)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        ttk.Button(button_frame, text="Load Sample", command=self.load_sample).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Load File", command=self.load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test All Languages", command=self.test_all_languages).pack(side=tk.LEFT, padx=5)
        
        # Editor container
        editor_frame = ttk.LabelFrame(main_frame, text="Code Editor with Syntax Highlighting", padding=5)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create inner frame for grid layout (CodeEditor expects grid)
        inner_frame = ttk.Frame(editor_frame)
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(inner_frame)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        
        # Initialize code editor  
        self.code_editor = CodeEditor(
            parent=inner_frame,
            syntax_manager=self.syntax_manager,
            scrollbar=scrollbar,
            color_scheme='nord',
            use_token_mapping=True,
            color_scheme_config=self.color_config
        )
        
        # Setup initial widget with proper grid options
        try:
            self.code_editor.setup_initial_widget(row=0, column=0, sticky=tk.NSEW)
            # Configure grid weights so the editor expands
            inner_frame.grid_rowconfigure(0, weight=1)
            inner_frame.grid_columnconfigure(0, weight=1)
        except Exception as e:
            print(f"Warning: Could not setup initial widget: {e}")
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Select a language and load sample code")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Load initial sample
        self.load_sample()
        
    def on_language_change(self, event=None):
        """Handle language selection change."""
        self.load_sample()
        
    def on_scheme_change(self, event=None):
        """Handle color scheme change."""
        scheme = self.scheme_var.get()
        if self.code_editor:
            try:
                self.code_editor.switch_color_scheme(scheme)
                self.status_var.set(f"Color scheme changed to: {scheme}")
            except Exception as e:
                self.status_var.set(f"Error changing color scheme: {e}")
            
    def load_sample(self):
        """Load sample code for the selected language."""
        language = self.language_var.get()
        if language in self.sample_code:
            content = self.sample_code[language]
            filename = f"sample.{self.get_file_extension(language)}"
            
            if self.code_editor:
                try:
                    # Ensure we have a widget
                    if not self.code_editor.has_widget():
                        self.code_editor.setup_initial_widget()
                    
                    # Update content with proper filename for lexer detection
                    self.code_editor.update_file_content(content, filename)
                    self.status_var.set(f"Loaded {language} sample code ({len(content)} characters)")
                except Exception as e:
                    self.status_var.set(f"Error loading sample: {e}")
        else:
            self.status_var.set(f"No sample available for {language}")
            
    def load_file(self):
        """Load code from a file."""
        filetypes = [
            ("Python files", "*.py"),
            ("JavaScript files", "*.js"),
            ("HTML files", "*.html"),
            ("CSS files", "*.css"),
            ("JSON files", "*.json"),
            ("Markdown files", "*.md"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select a file to load",
            filetypes=filetypes
        )
        
        if filename:
            try:
                if self.code_editor:
                    self.code_editor.load_file(filename)
                    self.status_var.set(f"Loaded file: {os.path.basename(filename)}")
                    
                    # Update language combo based on file extension
                    ext = os.path.splitext(filename)[1].lower()
                    language = self.get_language_from_extension(ext)
                    if language:
                        self.language_var.set(language)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                self.status_var.set(f"Error loading file: {e}")
                
    def clear_editor(self):
        """Clear the editor content."""
        if self.code_editor:
            self.code_editor.update_file_content("", "empty.txt")
            self.status_var.set("Editor cleared")
            
    def test_all_languages(self):
        """Test syntax highlighting for all supported languages."""
        def test_next_language(languages, index=0):
            if index < len(languages):
                language = languages[index]
                self.language_var.set(language)
                self.load_sample()
                self.status_var.set(f"Testing {language} ({index + 1}/{len(languages)})")
                
                # Schedule next language test
                self.root.after(2000, lambda: test_next_language(languages, index + 1))
            else:
                self.status_var.set("All language tests completed")
                
        languages = list(self.sample_code.keys())
        test_next_language(languages)
        
    def get_file_extension(self, language):
        """Get file extension for a programming language."""
        extensions = {
            'Python': 'py',
            'JavaScript': 'js',
            'HTML': 'html',
            'CSS': 'css',
            'JSON': 'json',
            'Markdown': 'md'
        }
        return extensions.get(language, 'txt')
        
    def get_language_from_extension(self, ext):
        """Get language name from file extension."""
        mapping = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.html': 'HTML',
            '.htm': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.md': 'Markdown',
            '.markdown': 'Markdown'
        }
        return mapping.get(ext)

def main():
    """Run the visual test application."""
    try:
        # Create and run the application
        root = tk.Tk()
        app = SyntaxHighlightingTestApp(root)
        
        print("Syntax Highlighting Visual Test Application")
        print("=" * 50)
        print("Instructions:")
        print("1. Select a programming language from the dropdown")
        print("2. Click 'Load Sample' to load sample code")
        print("3. Or click 'Load File' to load your own file")
        print("4. Verify syntax highlighting colors and accuracy")
        print("5. Test different color schemes")
        print("6. Use 'Test All Languages' for automated testing")
        print()
        print("Expected Results:")
        print("- Keywords should be colored (Nord: light blue)")
        print("- Strings should be colored (Nord: green)")
        print("- Comments should be colored (Nord: gray)")
        print("- Functions/classes should be colored (Nord: yellow/blue)")
        print("- Numbers should be colored (Nord: purple)")
        print("- Operators should be visible and readable")
        print()
        
        root.mainloop()
        
    except Exception as e:
        print(f"Error running test application: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 