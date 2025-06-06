# Product Requirements Document (PRD): Syntax Highlighting Enhancement

## 1. Introduction / Overview
This enhancement will upgrade the existing "Vibe Coding" IDE file explorer MVP by adding professional syntax highlighting capabilities to the file content viewer. We will integrate the Chlorophyll library to replace the current plain text viewer with a feature-rich code editor widget that supports 597+ programming languages and markup formats.

## 2. Goals
- Replace the current plain text file viewer with a syntax-highlighted code viewer
- Automatically detect file types and apply appropriate syntax highlighting
- Provide multiple color schemes for enhanced readability
- Maintain existing functionality (scrolling, read-only mode, file selection)
- Preserve all existing tests and ensure new functionality is fully tested with TDD

## 3. User Stories
1. As a developer, I want to see syntax-highlighted code when viewing files so that I can easily read and understand the code structure.
2. As a developer, I want automatic language detection based on file extensions so that I don't need to manually specify the file type.
3. As a developer, I want line numbers displayed alongside my code so that I can easily reference specific lines.
4. As a developer, I want consistent color schemes across different file types so that my viewing experience is uniform.
5. As a developer, I want the same responsive performance as the current viewer so that large files load quickly.

## 4. Functional Requirements
1. **Syntax Highlighting**: The file viewer must automatically apply syntax highlighting based on file extension detection.
2. **Language Support**: The system must support major programming languages including but not limited to:
   - Python (.py)
   - JavaScript (.js, .ts)
   - HTML (.html, .htm)
   - CSS (.css, .scss)
   - JSON (.json)
   - Markdown (.md)
   - SQL (.sql)
   - Shell scripts (.sh, .bash)
   - Configuration files (.yaml, .yml, .toml, .ini)
3. **Line Numbers**: Display line numbers for all code files in a dedicated gutter area.
4. **Color Schemes**: Implement at least one professional color scheme (monokai) with the ability to add more.
5. **Fallback Handling**: Files with unknown extensions or binary content should display as plain text without errors.
6. **Performance**: Syntax highlighting should not significantly impact file loading times for files under 10MB.
7. **Backward Compatibility**: All existing file explorer functionality must remain unchanged.

## 5. Non-Goals (Out of Scope)
- Code editing capabilities (remains read-only)
- Custom syntax highlighting rules or themes
- Code folding or collapsing functionality
- Search and replace within files
- Multiple file tabs or split view
- IntelliSense or code completion

## 6. Design Considerations
- **Library Choice**: Use Chlorophyll library which wraps Pygments for tkinter integration
- **Performance**: Leverage Chlorophyll's built-in optimizations for large files
- **UI Consistency**: Maintain the existing layout and color scheme of the application
- **Error Handling**: Graceful degradation to plain text for unsupported or problematic files

## 7. Technical Considerations
- **Dependencies**: Add `chlorophyll` to requirements.txt (which includes `pygments` as a dependency)
- **Widget Replacement**: Replace `tk.Text` with `chlorophyll.CodeView` in the file content viewer
- **Lexer Detection**: Implement file extension to Pygments lexer mapping
- **Configuration**: Ensure CodeView integrates properly with existing scrollbar and layout
- **Testing**: Update GUI tests to work with CodeView widget instead of Text widget
- **Memory Management**: Monitor memory usage with syntax highlighting enabled

## 8. Implementation Plan

### Phase 1: Setup and Integration (Task 7.0)
- Add chlorophyll dependency to requirements.txt
- Replace Text widget with CodeView in gui.py
- Implement basic lexer detection by file extension
- Ensure existing scrollbar and layout integration works

### Phase 2: Language Detection (Task 8.0)  
- Create comprehensive file extension to lexer mapping
- Implement fallback for unknown file types
- Add support for files without extensions (shebangs, etc.)
- Handle edge cases (empty files, binary files)

### Phase 3: Testing and Quality Assurance (Task 9.0)
- Update existing GUI tests to work with CodeView
- Add new tests for syntax highlighting functionality
- Test performance with various file sizes and types
- Ensure error handling and graceful degradation

### Phase 4: Polish and Documentation (Task 10.0)
- Add configuration options for color schemes
- Update user documentation
- Performance optimization if needed
- Final integration testing

## 9. Success Metrics
- All existing tests continue to pass
- Syntax highlighting works correctly for at least 10 major file types
- File loading performance degradation is less than 200ms for typical files
- Zero crashes or errors when viewing unsupported file types
- User can easily distinguish between different code elements (keywords, strings, comments)

## 10. Risk Assessment
- **Low Risk**: Chlorophyll is a mature, well-maintained library
- **Medium Risk**: Performance impact on large files - mitigated by testing and fallback options
- **Low Risk**: Breaking existing functionality - mitigated by comprehensive testing
- **Low Risk**: Compatibility issues - Chlorophyll is designed specifically for tkinter

## 11. Dependencies
- **External**: chlorophyll library (pip install chlorophyll)
- **Internal**: Existing GUI framework and file reading infrastructure
- **Testing**: pytest framework and existing test infrastructure

## 12. Open Questions
- Should we add a menu option to toggle syntax highlighting on/off?
- Do we want to support custom color schemes in the future?
- Should line numbers be toggleable or always visible?
- How should we handle very large files (>10MB) - progressive loading or plain text fallback? 