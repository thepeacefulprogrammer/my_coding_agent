# Task List: Simple Code Viewer - Complete Redesign

## Relevant Files

- `src/my_coding_agent/core/__init__.py` - Core module initialization
- `src/my_coding_agent/core/main_window.py` - Main application window class using PyQt6 with public properties for component access
- `src/my_coding_agent/core/file_tree.py` - File tree navigation widget and model with qtawesome file type icons and performance optimizations (caching, lazy loading, debounced refresh, thread safety)
- `src/my_coding_agent/core/code_viewer.py` - Code viewing widget with syntax highlighting, comprehensive file loading error handling, and smooth scrolling
- `src/my_coding_agent/core/syntax_highlighter.py` - Pygments integration for syntax highlighting
- `src/my_coding_agent/core/theme_manager.py` - Dark mode theme management
- `src/my_coding_agent/gui/__init__.py` - GUI module initialization
- `src/my_coding_agent/gui/widgets.py` - Custom widget components (line numbers, splitter)
- `src/my_coding_agent/gui/styles.py` - Qt stylesheets for dark mode theme
- `src/my_coding_agent/config/settings.py` - Application settings and configuration
- `src/my_coding_agent/__main__.py` - Main application entry point for python -m execution
- `tests/test_application_entry.py` - Unit tests for application entry point and configuration
- `tests/fixtures/gui_fixtures.py` - PyQt6 GUI testing fixtures with QApplication management
- `tests/fixtures/__init__.py` - Fixtures package initialization
- `tests/test_gui_fixtures.py` - Unit tests for GUI testing fixtures
- `src/my_coding_agent/assets/icons/` - File type icons for the file tree
- `src/my_coding_agent/assets/themes/dark.qss` - Dark mode stylesheet
- `tests/test_main_window.py` - Unit tests for main window functionality
- `tests/test_file_tree.py` - Comprehensive unit tests for file tree navigation, performance optimizations, caching, and thread safety
- `tests/test_code_viewer.py` - Comprehensive unit tests for code viewer widget, syntax highlighting, and edge cases
- `tests/test_syntax_highlighter.py` - Unit tests for PygmentsSyntaxHighlighter class
- `tests/test_file_loading_error_handling.py` - Unit tests for comprehensive file loading error handling
- `tests/test_theme_manager.py` - Unit tests for theme management
- `tests/fixtures/sample_code/` - Sample code files for testing (Python, JavaScript)
- `tests/test_dependencies.py` - Unit tests for verifying PyQt6 and Pygments availability
- `tests/test_module_structure.py` - Unit tests for verifying core and gui module structure
- `tests/test_assets_structure.py` - Unit tests for assets directory structure, resource management, and file type icons
- `tests/test_integration.py` - Comprehensive integration tests for complete application workflow and component interactions
- `src/my_coding_agent/assets/__init__.py` - Assets management module with utility functions
- `examples/demo_viewer.py` - Example script showing basic usage
- `examples/demo_file_tree_signals.py` - Demo script showcasing file tree selection and click-to-open functionality
- `tools/debug_file_tree_signals.py` - Debug script for testing file tree signals manually

### Notes

- Use pytest for all testing with the existing conftest.py fixtures
- Follow TDD approach: write tests first, then implement functionality
- Run tests with `make test` and ensure >80% coverage with `make test-cov`
- Use PyQt6 for GUI framework as specified in PRD
- Integrate Pygments for syntax highlighting to avoid third-party GUI library issues
- Follow MVC architecture pattern for maintainability

## Tasks

- [x] 1.0 Project Setup and Core Infrastructure
  - [x] 1.1 Add PyQt6 and Pygments dependencies to pyproject.toml
  - [x] 1.2 Create core module structure (core/, gui/ directories)
  - [x] 1.3 Set up basic application entry point and configuration
  - [x] 1.4 Create base test fixtures for GUI testing with QApplication
  - [x] 1.5 Configure assets directory structure for icons and themes

- [x] 2.0 Main Application Window and Layout System
  - [x] 2.1 Create MainWindow class inheriting from QMainWindow
  - [x] 2.2 Implement split layout with QSplitter (30% left, 70% right panels)
  - [x] 2.3 Add status bar for displaying current file path and information
  - [x] 2.4 Implement window state persistence (size, splitter position)
  - [x] 2.5 Add basic menu bar with File menu and keyboard shortcuts
  - [x] 2.6 Write comprehensive unit tests for main window functionality

- [x] 3.0 File Tree Navigation Component
  - [x] 3.1 Create FileTreeModel class using QFileSystemModel
  - [x] 3.2 Implement FileTreeWidget with QTreeView for directory navigation
  - [x] 3.3 Add file type icons and folder expand/collapse functionality
  - [x] 3.4 Implement file selection handling and click-to-open behavior
  - [x] 3.5 Add context menu for file tree (refresh, expand all, collapse all)
  - [x] 3.6 Handle edge cases (permission errors, network drives, symlinks)
  - [x] 3.7 Write unit tests for file tree model and widget interactions

- [x] 4.0 Code Viewer with Syntax Highlighting
  - [x] 4.1 Create CodeViewerWidget class using QTextEdit in read-only mode
  - [x] 4.2 Integrate Pygments syntax highlighter for Python and JavaScript
  - [x] 4.3 Implement line numbers widget that syncs with text scrolling
  - [x] 4.4 Add support for large file handling (up to 10MB) with lazy loading
  - [x] 4.5 Create SyntaxHighlighter class to bridge Pygments with Qt
  - [x] 4.6 Implement file loading with error handling (encoding, file not found)
  - [x] 4.7 Add horizontal and vertical scrollbars with smooth scrolling
  - [x] 4.8 Write unit tests for code viewer widget and syntax highlighting

- [x] 5.0 UI Polish, Dark Mode Theme, and Performance Optimization
  - [x] 5.1 Create ThemeManager class for dark mode styling
  - [x] 5.2 Design and implement dark theme QSS stylesheet
  - [x] 5.3 Add file type specific icons for Python, JavaScript, and generic files
  - [x] 5.4 Implement performance optimizations for file tree scanning
  - [x] 5.5 Write integration tests for complete application workflow
