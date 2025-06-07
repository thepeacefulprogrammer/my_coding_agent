# Simple Code Viewer

A clean, fast, and maintainable code viewer built with PyQt6. Focused on simplicity and performance for viewing code files with syntax highlighting.

## Features

- **File Tree Navigation**: Browse project directories with collapsible tree view
- **Syntax Highlighting**: Support for Python, JavaScript, and 500+ other languages via Pygments
- **Read-Only Viewing**: Clean, distraction-free code viewing
- **Dark Mode**: Modern dark theme optimized for coding
- **High Performance**: Handles files up to 10MB without lag
- **Cross-Platform**: Runs on Linux, Windows, and macOS

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd my_coding_agent
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python src/main.py
```

## Architecture

Built with clean MVC architecture:
- **PyQt6**: Modern, reliable GUI framework
- **Pygments**: Industry-standard syntax highlighting
- **Native Python**: File system operations
- **No complex dependencies**: Eliminates maintenance overhead

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/ tests/
```

### Type Checking
```bash
mypy src/
```

## Design Goals

- **Simplicity**: Focus on core functionality without feature bloat
- **Performance**: Fast startup and responsive file operations
- **Maintainability**: Clean code architecture with minimal dependencies
- **Reliability**: No workarounds or complex error handling

## Non-Goals

This is intentionally a simple viewer, not a full editor:
- No editing capabilities
- No multiple file tabs
- No search functionality
- No plugins or extensions