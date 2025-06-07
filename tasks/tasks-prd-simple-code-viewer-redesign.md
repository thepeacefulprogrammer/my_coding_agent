# Task List: Simple Code Viewer - Complete Redesign

## Relevant Files

- `src/my_coding_agent/core/__init__.py` - Core module initialization
- `src/my_coding_agent/core/main_window.py` - Main application window class using PyQt6
- `src/my_coding_agent/core/file_tree.py` - File tree navigation widget and model
- `src/my_coding_agent/core/code_viewer.py` - Code viewing widget with syntax highlighting
- `src/my_coding_agent/core/syntax_highlighter.py` - Pygments integration for syntax highlighting
- `src/my_coding_agent/core/theme_manager.py` - Dark mode theme management
- `src/my_coding_agent/gui/__init__.py` - GUI module initialization
- `src/my_coding_agent/gui/widgets.py` - Custom widget components (line numbers, splitter)
- `src/my_coding_agent/gui/styles.py` - Qt stylesheets for dark mode theme
- `src/my_coding_agent/config/settings.py` - Application settings and configuration
- `src/my_coding_agent/__main__.py` - Main application entry point for python -m execution
- `tests/test_application_entry.py` - Unit tests for application entry point and configuration
- `src/my_coding_agent/assets/icons/` - File type icons for the file tree
- `src/my_coding_agent/assets/themes/dark.qss` - Dark mode stylesheet
- `tests/test_main_window.py` - Unit tests for main window functionality
- `tests/test_file_tree.py` - Unit tests for file tree navigation
- `tests/test_code_viewer.py` - Unit tests for code viewer widget
- `tests/test_syntax_highlighter.py` - Unit tests for syntax highlighting
- `tests/test_theme_manager.py` - Unit tests for theme management
- `tests/fixtures/sample_code/` - Sample code files for testing (Python, JavaScript)
- `tests/test_dependencies.py` - Unit tests for verifying PyQt6 and Pygments availability
- `tests/test_module_structure.py` - Unit tests for verifying core and gui module structure
- `examples/demo_viewer.py` - Example script showing basic usage

### Notes

- Use pytest for all testing with the existing conftest.py fixtures
- Follow TDD approach: write tests first, then implement functionality
- Run tests with `make test` and ensure >80% coverage with `make test-cov`
- Use PyQt6 for GUI framework as specified in PRD
- Integrate Pygments for syntax highlighting to avoid third-party GUI library issues
- Follow MVC architecture pattern for maintainability

## Tasks

- [ ] 1.0 Project Setup and Core Infrastructure
  - [x] 1.1 Add PyQt6 and Pygments dependencies to pyproject.toml
  - [x] 1.2 Create core module structure (core/, gui/ directories)
  - [x] 1.3 Set up basic application entry point and configuration
  - [ ] 1.4 Create base test fixtures for GUI testing with QApplication
  - [ ] 1.5 Configure assets directory structure for icons and themes

- [ ] 2.0 Main Application Window and Layout System
  - [ ] 2.1 Create MainWindow class inheriting from QMainWindow
  - [ ] 2.2 Implement split layout with QSplitter (30% left, 70% right panels)
  - [ ] 2.3 Add status bar for displaying current file path and information
  - [ ] 2.4 Implement window state persistence (size, splitter position)
  - [ ] 2.5 Add basic menu bar with File menu and keyboard shortcuts
  - [ ] 2.6 Write comprehensive unit tests for main window functionality

- [ ] 3.0 File Tree Navigation Component
  - [ ] 3.1 Create FileTreeModel class using QFileSystemModel
  - [ ] 3.2 Implement FileTreeWidget with QTreeView for directory navigation
  - [ ] 3.3 Add file type icons and folder expand/collapse functionality
  - [ ] 3.4 Implement file selection handling and click-to-open behavior
  - [ ] 3.5 Add context menu for file tree (refresh, expand all, collapse all)
  - [ ] 3.6 Handle edge cases (permission errors, network drives, symlinks)
  - [ ] 3.7 Write unit tests for file tree model and widget interactions

- [ ] 4.0 Code Viewer with Syntax Highlighting
  - [ ] 4.1 Create CodeViewerWidget class using QTextEdit in read-only mode
  - [ ] 4.2 Integrate Pygments syntax highlighter for Python and JavaScript
  - [ ] 4.3 Implement line numbers widget that syncs with text scrolling
  - [ ] 4.4 Add support for large file handling (up to 10MB) with lazy loading
  - [ ] 4.5 Create SyntaxHighlighter class to bridge Pygments with Qt
  - [ ] 4.6 Implement file loading with error handling (encoding, file not found)
  - [ ] 4.7 Add horizontal and vertical scrollbars with smooth scrolling
  - [ ] 4.8 Write unit tests for code viewer widget and syntax highlighting

- [ ] 5.0 UI Polish, Dark Mode Theme, and Performance Optimization
  - [ ] 5.1 Create ThemeManager class for dark mode styling
  - [ ] 5.2 Design and implement dark theme QSS stylesheet
  - [ ] 5.3 Add file type specific icons for Python, JavaScript, and generic files
  - [ ] 5.4 Implement performance optimizations for file tree scanning
  - [ ] 5.5 Add memory usage monitoring and optimization for large files
  - [ ] 5.6 Implement startup time optimization (target <2 seconds)
  - [ ] 5.7 Add comprehensive error handling and user feedback messages
  - [ ] 5.8 Write integration tests for complete application workflow
  - [ ] 5.9 Perform cross-platform testing (Linux, Windows, macOS compatibility)
  - [ ] 5.10 Create user documentation and developer setup guide 