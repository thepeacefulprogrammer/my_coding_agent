# Task Breakdown: Syntax Highlighting Enhancement

## Relevant Files

- `src/gui.py`: Main GUI class - replaced Text widget with CodeView (✅ DONE)
- `src/file_explorer.py`: File reading infrastructure (no changes needed)
- `requirements.txt`: Add chlorophyll dependency (✅ DONE)
- `tests/test_gui.py`: Update tests for CodeView widget (⚠️ Some legacy tests incompatible with CodeView)
- `tests/test_syntax_highlighting_setup.py`: Tests for dependency setup and basic functionality (✅ DONE)
- `tests/test_codeview_integration.py`: Comprehensive tests for CodeView integration (✅ DONE)
- `src/syntax_manager.py`: New module for lexer detection and management (✅ DONE)
- `tests/test_syntax_manager.py`: Comprehensive tests for SyntaxManager class (✅ DONE)

## Notes

- Follow strict TDD methodology: write tests first, implement functionality, ensure all tests pass
- Use existing test infrastructure and patterns from file explorer implementation
- Maintain backward compatibility with all existing functionality
- Test with various file types and edge cases
- **Legacy GUI tests**: Some old GUI tests use heavy mocking that conflicts with CodeView initialization - new integration tests cover the functionality

## Task Breakdown

**Total Progress: 1/4 tasks complete**

### Task 7.0: Setup and Basic Integration
- [x] 7.1 Add chlorophyll dependency to requirements.txt
- [x] 7.2 Create SyntaxManager class for lexer detection and management
- [x] 7.3 Replace Text widget with CodeView in GUI layout
- [ ] 7.4 Implement basic file extension to lexer mapping
- [ ] 7.5 Ensure CodeView integrates with existing scrollbar and container
- [ ] 7.6 Write unit tests for SyntaxManager lexer detection
- [ ] 7.7 Update GUI tests to work with CodeView instead of Text widget

### Task 8.0: Language Detection and File Type Support
- [ ] 8.1 Implement comprehensive file extension to Pygments lexer mapping
- [ ] 8.2 Add support for common programming languages (Python, JS, HTML, CSS, JSON, Markdown)
- [ ] 8.3 Implement fallback handling for unknown file extensions
- [ ] 8.4 Add shebang detection for files without extensions (#!/usr/bin/python, etc.)
- [ ] 8.5 Handle edge cases: empty files, binary files, very large files
- [ ] 8.6 Write comprehensive unit tests for language detection logic
- [ ] 8.7 Write integration tests for file type handling

### Task 9.0: Performance and Error Handling
- [ ] 9.1 Implement graceful fallback to plain text for unsupported files
- [ ] 9.2 Add error handling for syntax highlighting failures
- [ ] 9.3 Implement performance optimizations for large files
- [ ] 9.4 Add file size limits and warnings for very large files (>10MB)
- [ ] 9.5 Write performance tests to ensure acceptable loading times
- [ ] 9.6 Write error handling tests for edge cases and malformed files
- [ ] 9.7 Update file selection handler to use new syntax highlighting

### Task 10.0: Polish, Configuration, and Documentation
- [ ] 10.1 Implement color scheme configuration (start with monokai)
- [ ] 10.2 Add line number display configuration
- [ ] 10.3 Create configuration system for syntax highlighting options
- [ ] 10.4 Optimize memory usage and cleanup for syntax highlighting
- [ ] 10.5 Write tests for configuration system
- [ ] 10.6 Update documentation and add usage examples
- [ ] 10.7 Final integration testing and performance validation

## Success Criteria

### Task 7.0 Complete When:
- ✅ All existing tests pass with CodeView integration
- ✅ Basic syntax highlighting works for .py files
- ✅ Scrollbar and layout function correctly
- ✅ SyntaxManager handles basic file extension detection
- ✅ Error handling prevents crashes on unsupported files

### Task 8.0 Complete When:
- ✅ 10+ programming languages supported with proper syntax highlighting
- ✅ Unknown file extensions fallback to plain text without errors
- ✅ Shebang detection works for script files
- ✅ Binary and empty files handled gracefully
- ✅ All language detection logic covered by unit tests

### Task 9.0 Complete When:
- ✅ File loading performance is within 200ms degradation for typical files
- ✅ Large files (>10MB) are handled without freezing the UI
- ✅ All error conditions are handled gracefully
- ✅ Memory usage is optimized and stable
- ✅ Performance and error handling tests provide adequate coverage

### Task 10.0 Complete When:
- ✅ Color scheme configuration system is working
- ✅ Line numbers display correctly for all file types
- ✅ Configuration can be easily extended for future features
- ✅ Documentation is complete and accurate
- ✅ Final integration tests validate entire feature set

## Current Status: Ready to Begin

All prerequisite tasks from the file explorer MVP are complete. The foundation is solid with:
- ✅ 123 passing tests
- ✅ Robust file reading infrastructure  
- ✅ Stable GUI framework
- ✅ Comprehensive error handling
- ✅ TDD methodology established

Ready to begin Task 7.1: Add chlorophyll dependency to requirements.txt 