# PRD: Simple Code Viewer - Complete Redesign

## Introduction/Overview

The current code editor suffers from maintainability issues due to workarounds for third-party library bugs (particularly with chlorophyll), causing performance lag and complex error handling. This PRD outlines a complete redesign to create a **simple, fast, and maintainable code viewer** focused on syntax highlighting and file navigation.

The new viewer will be a **read-only code viewing application** that prioritizes simplicity, performance, and developer maintainability over advanced editing features.

## Goals

1. **Eliminate performance lag** by removing problematic third-party dependencies
2. **Create a maintainable codebase** with clean architecture and minimal workarounds
3. **Provide excellent syntax highlighting** for Python, JavaScript, and other common languages
4. **Deliver intuitive file navigation** with a modern file tree interface
5. **Support dark mode** with a clean, modern UI design
6. **Handle files up to 10MB** without performance degradation

## User Stories

1. **As a developer**, I want to quickly browse and view code files in a project directory so that I can understand the codebase structure.

2. **As a developer**, I want syntax highlighting for Python and JavaScript files so that I can easily read and understand the code.

3. **As a developer**, I want to navigate through a file tree so that I can quickly find and open different files.

4. **As a developer**, I want the application to start quickly and respond smoothly so that my workflow isn't interrupted.

5. **As a developer**, I want a dark mode interface so that I can work comfortably in low-light environments.

6. **As a developer**, I want to view large files (up to 10MB) without the application becoming unresponsive.

## Functional Requirements

### Core Functionality
1. **File Tree Navigation**: The system must display a collapsible file tree showing directories and files
2. **File Opening**: Users must be able to click on files in the tree to view their contents
3. **Syntax Highlighting**: The system must provide syntax highlighting for at minimum Python (.py) and JavaScript (.js, .jsx, .ts, .tsx) files
4. **Read-Only Viewing**: All file content must be displayed in read-only mode (no editing capabilities)
5. **Scrolling**: The text viewer must support smooth vertical and horizontal scrolling with working scrollbars
6. **Line Numbers**: The system must display line numbers that sync correctly with content scrolling

### User Interface
7. **Split Layout**: The interface must have a left panel for file tree and right panel for file content
8. **Dark Mode**: The application must support a dark color scheme
9. **Resizable Panels**: Users must be able to resize the file tree and content panels
10. **File Type Recognition**: The system must automatically detect file types and apply appropriate syntax highlighting

### Performance
11. **Fast Startup**: The application must start in under 2 seconds
12. **Large File Support**: The system must handle files up to 10MB without lag
13. **Responsive Navigation**: File tree expansion and file opening must complete in under 500ms
14. **Memory Efficiency**: The application must not consume more than 100MB of RAM for typical usage

### Technical Requirements
15. **Cross-Platform**: The application must run on Linux, Windows, and macOS
16. **No External Dependencies**: Minimize dependencies on third-party GUI libraries that could introduce bugs
17. **Error Handling**: The system must gracefully handle file permission errors, corrupted files, and missing files

## Non-Goals (Out of Scope)

1. **Code Editing**: No text editing, saving, or modification capabilities
2. **Multiple File Tabs**: Single file view only, no tab interface
3. **Search Functionality**: No find/replace or search across files
4. **Code Folding**: No collapsible code sections
5. **Auto-completion**: No IntelliSense or code suggestions
6. **Plugin System**: No extensibility or plugin architecture
7. **Version Control Integration**: No Git integration or diff viewing
8. **Project Management**: No project-specific settings or configurations
9. **Terminal Integration**: No embedded terminal or command execution
10. **File Creation/Deletion**: No file system modification capabilities

## Technical Considerations

### Recommended Technology Stack
- **GUI Framework**: PyQt6 or PySide6 (modern, reliable, native widgets)
- **Syntax Highlighting**: Pygments library (supports 500+ languages, actively maintained)
- **File System**: Python's native `pathlib` and `os` modules
- **Architecture**: Model-View-Controller (MVC) pattern

### Architecture Components
1. **FileTreeModel**: Handles file system scanning and tree data structure
2. **CodeViewerWidget**: Manages text display and syntax highlighting
3. **MainWindow**: Coordinates UI layout and component communication
4. **SyntaxHighlighter**: Wraps Pygments functionality for Qt integration
5. **ThemeManager**: Handles dark/light mode styling

### Key Technical Decisions
- **No chlorophyll dependency**: Use Qt's native text widgets with Pygments integration
- **Lazy loading**: Only load file contents when actually viewed
- **Virtual scrolling**: For large files, implement viewport-based rendering
- **Asynchronous file operations**: Prevent UI blocking during large file loads

## Design Considerations

### Layout
- **Left Panel (30%)**: File tree with expand/collapse functionality
- **Right Panel (70%)**: Code viewer with line numbers and scrollbars
- **Splitter**: Resizable divider between panels
- **Status Bar**: Show current file path and basic file information

### Dark Mode Theme
- **Background**: Dark gray (#2d2d2d)
- **Text**: Light gray (#f0f0f0)
- **Syntax Colors**: Use a popular dark theme like Monokai or VS Code Dark+
- **UI Elements**: Consistent dark styling for scrollbars, splitters, and tree view

### File Tree Icons
- **Folders**: Standard folder icons with expand/collapse indicators
- **Files**: Language-specific icons (Python snake, JavaScript logo, etc.)
- **File Status**: Different colors for different file types

## Success Metrics

1. **Performance**: Application startup time < 2 seconds
2. **Responsiveness**: File opening time < 500ms for files under 10MB
3. **Reliability**: Zero crashes during normal file viewing operations
4. **Code Quality**: Test coverage > 80%, clean architecture with separation of concerns
5. **User Experience**: Smooth scrolling with no lag or jitter
6. **Maintainability**: New language support can be added in < 1 hour of development time

## Implementation Phases

### Phase 1: Core Infrastructure
- Set up PyQt6/PySide6 application framework
- Implement basic file tree navigation
- Create main window layout with resizable panels

### Phase 2: File Viewing
- Implement code viewer widget with Qt's QTextEdit
- Integrate Pygments for syntax highlighting
- Add line numbers with proper scrolling synchronization

### Phase 3: Polish & Performance
- Implement dark mode theming
- Optimize large file handling with virtual scrolling
- Add comprehensive error handling and edge case management

### Phase 4: Testing & Documentation
- Write unit tests for all components
- Performance testing with large files and directories
- Create user documentation and developer guide

## Open Questions

1. **Theme Customization**: Should users be able to customize syntax highlighting colors, or is a fixed dark theme sufficient?

2. **File Type Support**: Should the viewer support non-text files (images, PDFs) or focus purely on code files?

3. **Directory Scanning**: Should the file tree auto-refresh when files change on disk, or manual refresh only?

4. **Keyboard Shortcuts**: What keyboard shortcuts should be supported for navigation and file opening?

5. **Configuration**: Should the application remember window size, panel splits, and last opened directory?

## Dependencies

### Required Libraries
- **PyQt6** or **PySide6**: GUI framework
- **Pygments**: Syntax highlighting engine
- **Python 3.9+**: Minimum Python version for modern features

### Development Dependencies
- **pytest**: Unit testing framework
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking

## Acceptance Criteria

- [ ] Application starts in under 2 seconds
- [ ] File tree displays directories and files correctly
- [ ] Clicking on files opens them in the viewer panel
- [ ] Python and JavaScript files display proper syntax highlighting
- [ ] Line numbers display and scroll correctly with content
- [ ] Dark mode theme is applied throughout the interface
- [ ] Files up to 10MB open without noticeable lag
- [ ] No crashes occur during normal file viewing operations
- [ ] Application runs on Linux, Windows, and macOS
- [ ] Memory usage stays under 100MB for typical usage
- [ ] All components have unit tests with >80% coverage
- [ ] Code follows clean architecture principles with clear separation of concerns
