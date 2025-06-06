# Task List: Syntax Highlighting Implementation

Based on technical investigation, we've identified that the Chlorophyll library requires lexers to be set during CodeView widget construction for proper syntax highlighting to work. This consolidated task list preserves completed work while moving forward with the correct implementation approach.

## Relevant Files

### Completed Work ✅
- `src/gui.py` - Main GUI class with CodeView widget (initial integration done)
- `src/syntax_manager.py` - Lexer detection and management with shebang support (✅ DONE)
- `tests/test_syntax_manager.py` - Comprehensive tests for SyntaxManager class (✅ DONE)
- `tests/test_syntax_highlighting_setup.py` - Tests for dependency setup (✅ DONE)
- `tests/test_codeview_integration.py` - Basic CodeView integration tests (✅ DONE)
- `requirements.txt` - Chlorophyll dependency added (✅ DONE)

### New Work Required
- `src/code_editor.py` - New module to handle CodeView widget lifecycle and syntax highlighting (✅ DONE)
- `tests/test_code_editor.py` - Unit tests for the new code editor module (✅ DONE)
- `tests/test_nord_python_syntax.py` - Unit tests for Nord color scheme applied to Python syntax (✅ DONE)
- `tests/test_syntax_highlighting_full.py` - Integration tests for complete syntax highlighting functionality
- `test_live_app.py` - Manual testing application to verify syntax highlighting visually

### Notes

- **Root Cause**: Chlorophyll's CodeView widget must receive the lexer during construction (`CodeView(lexer=lexer)`) rather than setting it afterward
- **Current Issue**: Setting `widget.lexer = lexer` and calling `highlight_all()` does not create proper tag ranges
- **Solution**: Widget replacement strategy with careful handling of tkinter widget lifecycle
- Tests should verify both functional behavior and visual appearance of syntax highlighting
- We have a solid foundation with SyntaxManager and basic integration already working

## Completed Foundation Work

### ✅ Task 1.0: Setup and Basic Integration - COMPLETE
- [x] 1.1 Add chlorophyll dependency to requirements.txt
- [x] 1.2 Create SyntaxManager class for lexer detection and management
- [x] 1.3 Replace Text widget with CodeView in GUI layout
- [x] 1.4 Implement basic file extension to lexer mapping
- [x] 1.5 Ensure CodeView integrates with existing scrollbar and container
- [x] 1.6 Write unit tests for SyntaxManager lexer detection
- [x] 1.7 Update GUI tests to work with CodeView instead of Text widget

### ✅ Task 2.0: Language Detection and File Type Support - PARTIALLY COMPLETE
- [x] 2.1 Implement comprehensive file extension to Pygments lexer mapping
- [x] 2.2 Add support for common programming languages (Python, JS, HTML, CSS, JSON, Markdown)
- [x] 2.3 Implement fallback handling for unknown file extensions
- [x] 2.4 Add shebang detection for files without extensions (#!/usr/bin/python, etc.)
- [x] 2.5 Write comprehensive unit tests for language detection logic
- [ ] 2.6 Handle edge cases: empty files, binary files, very large files
- [ ] 2.7 Write integration tests for file type handling

## New Implementation Tasks

### ✅ Task 3.0: Design CodeView Widget Lifecycle Management - COMPLETE
- [x] 3.1 Create CodeEditor class to encapsulate CodeView widget management
- [x] 3.2 Design safe widget replacement strategy that avoids tkinter reference issues
- [x] 3.3 Implement state preservation during widget recreation (content, scroll position, selection)
- [x] 3.4 Define interface for syntax highlighting integration with existing GUI class
- [x] 3.5 Plan container structure to support clean widget replacement without breaking references

### Task 4.0: Implement Dynamic CodeView Recreation System
- [x] 4.1 Create widget factory method that constructs CodeView with proper lexer during initialization
- [x] 4.2 Implement safe widget destruction that properly cleans up tkinter references
- [x] **4.3: Build widget replacement logic that maintains container relationships**
  - Enhanced `replace_widget_with_lexer` method with comprehensive container relationship maintenance
  - Added `capture_widget_geometry_info()` method to capture complete geometry manager information (grid, pack, place)
  - Added `apply_geometry_info()` method to restore geometry configuration including parent references
  - Added `replace_widget_with_enhanced_container_relationships()` method for comprehensive replacement
  - Handles all three geometry managers: grid, pack, and place
  - Preserves focus state, parent references, and sibling order
  - Maintains scrollbar connections and widget hierarchy
  - Comprehensive test coverage with 10 additional tests
  - All 67 CodeEditor tests passing
  - Robust handling of both real tkinter widgets and Mock objects for testing
- [x] **4.4: Ensure scrollbar reconnection after widget replacement**
  - Enhanced `configure_scrollbar()` method with comprehensive error handling
  - Added `enhanced_scrollbar_reconnection()` method for advanced scrollbar state management
  - Added `capture_scrollbar_state()` and `apply_scrollbar_state()` methods for state preservation
  - Improved `create_widget()` to automatically configure scrollbar during widget creation
  - Enhanced `replace_widget_with_lexer()` with error recovery for failed widget creation
  - Bidirectional scrollbar communication (scrollbar ↔ widget)
  - Scroll position preservation during widget replacement
  - Error recovery and graceful fallback for scrollbar configuration failures
  - Support for rapid widget replacement scenarios
  - Comprehensive test coverage with 10 additional scrollbar reconnection tests
  - All 77 CodeEditor tests passing
  - Robust handling of scrollbar errors and edge cases
- [x] **4.5: Handle edge cases like rapid file switching and error conditions**
  - Implement robust error handling for rapid file switching scenarios
  - Add recovery mechanisms for widget creation failures
  - Handle concurrent widget operations safely
  - Implement memory leak prevention for rapid widget creation
  - Add error recovery for lexer setting failures
  - Handle tkinter errors during widget operations gracefully
  - Support large content handling efficiently
  - Handle empty content edge cases
  - Implement widget state corruption recovery
      - Add support for rapid destroy-create cycles
    - Implement comprehensive error state recovery after failures

### Task 4.6: Implement widget caching strategy to reduce recreation overhead for same file types
- [x] Implement LRU cache for widgets based on lexer type
- [x] Add cache size management and eviction policies  
- [x] Implement cache hit/miss optimization logic
- [x] Add cache invalidation functionality for memory management
- [x] Support caching of widgets by lexer name/type
- [x] Implement thread-safe cache operations with lock protection
- [x] Add performance optimization for rapid file type switching
- [x] Handle cache memory management with proper widget destruction
- [x] Implement cache key generation based on lexer characteristics
- [x] Add integration with existing widget replacement functionality
- [x] Support configurable cache enable/disable and size limits

### Task 5.0: Integrate Syntax Highlighting with File Loading
- [x] Implement load_file method with automatic syntax highlighting detection
- [x] Add file reading with multiple encoding support (UTF-8, Latin-1 fallback)
- [x] Integrate with existing widget caching system for performance
- [x] Handle file loading errors gracefully (FileNotFoundError, PermissionError)
- [x] Support automatic lexer detection based on file extensions
- [x] Preserve widget state during file loading operations
- [x] Implement content loading with proper cursor positioning
- [x] Add scrollbar configuration during file loading
- [x] Support empty file handling
- [x] Integrate with cached widget replacement for same file types
- [x] Add comprehensive error handling and recovery mechanisms

### Task 6.0: Apply Custom Color Schemes and Theme Support
- [x] **6.1: Implement Nord-inspired color scheme for Python syntax elements**
  - ✅ Comprehensive Nord color scheme already implemented in `src/color_schemes.py`
  - ✅ CodeEditor integration with Nord scheme working correctly
  - ✅ Python lexer detection and syntax highlighting functional
  - ✅ Created comprehensive test suite in `tests/test_nord_python_syntax.py` with 8 test methods
  - ✅ Tests verify color mappings for Python syntax elements (keywords, functions, classes, strings, numbers, comments)
  - ✅ Tests verify widget creation with Nord scheme and fallback handling
  - ✅ Tests verify color contrast and Python-specific elements (decorators, magic methods, exceptions)
  - ✅ Fixed GUI to set initial CodeView state to 'disabled' (read-only)
  - ✅ All 238 tests passing including new Nord Python syntax tests
  - ✅ Nord scheme provides excellent contrast with dark background and proper Python syntax highlighting
- [ ] 6.2 Add support for JavaScript, HTML, CSS, and other common languages
- [ ] 6.3 Create color mapping system that works with Pygments token types
- [ ] 6.4 Ensure colors are applied after widget creation with proper lexer
- [ ] 6.5 Add color scheme configuration options for future extensibility
- [ ] 6.6 Verify color visibility against dark background theme

### Task 7.0: Add Comprehensive Testing and Validation
- [ ] 7.1 Write unit tests for CodeEditor class widget management
- [ ] 7.2 Create integration tests for syntax highlighting with multiple file types
- [ ] 7.3 Add visual verification tests using manual test application
- [ ] 7.4 Test widget replacement performance and memory usage
- [ ] 7.5 Verify scrollbar functionality and state preservation
- [ ] 7.6 Test error handling and fallback scenarios
- [ ] 7.7 Add regression tests to prevent future syntax highlighting breakage

## Remaining Work from Original Tasks

### Task 8.0: Performance and Error Handling (from original plan)
- [ ] 8.1 Implement graceful fallback to plain text for unsupported files
- [ ] 8.2 Add error handling for syntax highlighting failures
- [ ] 8.3 Implement performance optimizations for large files
- [ ] 8.4 Add file size limits and warnings for very large files (>10MB)
- [ ] 8.5 Write performance tests to ensure acceptable loading times
- [ ] 8.6 Write error handling tests for edge cases and malformed files

### Task 9.0: Polish, Configuration, and Documentation (from original plan)
- [ ] 9.1 Implement color scheme configuration (start with monokai)
- [ ] 9.2 Add line number display configuration
- [ ] 9.3 Create configuration system for syntax highlighting options
- [ ] 9.4 Optimize memory usage and cleanup for syntax highlighting
- [ ] 9.5 Write tests for configuration system
- [ ] 9.6 Update documentation and add usage examples
- [ ] 9.7 Final integration testing and performance validation

## Progress Summary

**Foundation Complete**: 2/9 tasks ✅
- Basic CodeView integration and SyntaxManager working
- File type detection and language support implemented
- 105+ tests passing with solid error handling

**Next Priority**: Task 4.3 - Widget replacement logic that maintains container relationships

## Technical Implementation Notes

### Enhanced Safe Widget Destruction (Task 4.2) ✅
Successfully implemented comprehensive widget destruction with proper cleanup:

**Cleanup Sequence:**
1. **Event binding removal** - `widget.unbind_all()` clears all event handlers
2. **Scrollbar disconnection** - `scrollbar.config(command='')` breaks scrollbar connections
3. **Parent container cleanup** - `pack_forget()` and `grid_forget()` remove from layout
4. **Widget variable clearing** - Clears associated tkinter variables to prevent memory leaks
5. **Child widget destruction** - Recursively destroys child widgets first
6. **Main widget destruction** - `widget.destroy()` removes the primary widget
7. **Reference cleanup** - Clears internal references and triggers garbage collection
8. **Memory cleanup** - Forces garbage collection for optimal memory management

**Error Handling:**
- Comprehensive exception handling for each cleanup step
- Graceful handling of already-destroyed widgets
- Multiple destruction call safety
- Robust error recovery for edge cases

**Test Coverage:**
- 10 new comprehensive safe destruction tests
- All 57 CodeEditor tests passing
- Complete TDD implementation with edge cases
- Mock setup for complex widget hierarchies

### Widget Factory Enhancement (Task 4.1) ✅
Successfully implemented sophisticated widget factory methods:

**New Factory Methods:**
- `