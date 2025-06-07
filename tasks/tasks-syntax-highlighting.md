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
- `tests/test_nord_multi_language_syntax.py` - Unit tests for Nord color scheme applied to multiple languages (✅ DONE)
- `src/token_mapper.py` - Pygments token to Nord color mapping system (✅ DONE)
- `tests/test_pygments_token_mapping.py` - Unit tests for Pygments token mapping (✅ DONE)
- `tests/test_token_mapper_integration.py` - Integration tests for TokenMapper with CodeEditor (✅ DONE)
- `src/color_scheme_config.py` - Color scheme configuration system with dynamic management (✅ DONE)
- `tests/test_color_scheme_configuration.py` - Unit tests for ColorSchemeConfig class (✅ DONE)
- `tests/test_color_scheme_integration.py` - Integration tests for ColorSchemeConfig with CodeEditor (✅ DONE)
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
- [x] **6.2: Add support for JavaScript, HTML, CSS, and other common languages**
  - ✅ Created comprehensive test suite in `tests/test_nord_multi_language_syntax.py` with 12 test methods
  - ✅ Verified lexer detection for JavaScript (.js, .jsx, .ts), HTML (.html, .htm), CSS (.css, .scss)
  - ✅ Tested support for other common languages: JSON, Markdown, XML, YAML
  - ✅ Verified Nord color scheme compatibility with all supported languages
  - ✅ Tested syntax color mappings for JavaScript (keywords, functions, strings, comments, operators)
  - ✅ Tested syntax color mappings for HTML (tags, attributes, comments, DOCTYPE)
  - ✅ Tested syntax color mappings for CSS (selectors, properties, values, measurements, comments)
  - ✅ Verified universal syntax elements work across all languages (keywords, strings, comments, errors)
  - ✅ Tests run without creating GUI windows (proper mocking implemented)
  - ✅ All 41 syntax highlighting tests passing including 12 new multi-language tests
  - ✅ Comprehensive language support: JavaScript, TypeScript, JSX, HTML, CSS, SCSS, JSON, Markdown, XML, YAML
- [x] **6.3: Create color mapping system that works with Pygments token types**
  - ✅ Created `src/token_mapper.py` with comprehensive TokenMapper class
  - ✅ Implemented direct mapping from Pygments token types to Nord colors
  - ✅ Created comprehensive test suite in `tests/test_pygments_token_mapping.py` with 10 test methods
  - ✅ Supports all major Pygments token categories: Comment, Keyword, Name, String, Number, Operator, Punctuation, Error, Generic, Literal, Text
  - ✅ Implemented token inheritance fallback system for unmapped token subtypes
  - ✅ Extensive token coverage: 50+ specific token types mapped to appropriate Nord colors
  - ✅ Language-specific token support: decorators (NORD12), exceptions (NORD11), HTML tags (NORD9), CSS properties (NORD8)
  - ✅ Fallback system ensures all tokens have appropriate colors (defaults to NORD6)
  - ✅ Performance optimized with direct token-to-color mapping dictionary
  - ✅ All 13 token mapping and color scheme tests passing
  - ✅ Ready for integration with Chlorophyll CodeView widgets
- [x] **6.4: Ensure colors are applied after widget creation with proper lexer**
  - ✅ Enhanced CodeEditor class with token mapping integration support
  - ✅ Added `use_token_mapping` parameter to CodeEditor constructor (default: True)
  - ✅ Integrated TokenMapper initialization with automatic fallback handling
  - ✅ Enhanced `create_widget()` method to use Chlorophyll-compatible token colors
  - ✅ Automatic token color application after widget creation with lexer
  - ✅ Graceful fallback to regular color schemes when token mapping fails
  - ✅ Created comprehensive integration test suite in `tests/test_token_mapper_integration.py` with 6 test methods
  - ✅ Tests verify CodeEditor token mapping integration, fallback behavior, and multi-language consistency
  - ✅ Backwards compatibility: CodeEditor works normally when token mapping is disabled
  - ✅ Token mapping automatically applies when using Nord color scheme with lexers
  - ✅ All 16 token mapping and integration tests passing (10 TokenMapper + 6 Integration)
  - ✅ No regressions in existing CodeEditor functionality
- [x] **6.5: Add color scheme configuration options for future extensibility**
  - ✅ Created comprehensive `ColorSchemeConfig` class in `src/color_scheme_config.py`
  - ✅ Implemented dynamic color scheme management with registration, validation, and persistence
  - ✅ Added support for custom scheme creation, template-based schemes, and inheritance
  - ✅ Enhanced `CodeEditor` class with color scheme configuration integration
  - ✅ Added dynamic color scheme switching with state preservation and cache invalidation
  - ✅ Implemented configuration persistence with JSON save/load functionality
  - ✅ Created comprehensive test suite in `tests/test_color_scheme_configuration.py` with 10 test methods
  - ✅ Created integration test suite in `tests/test_color_scheme_integration.py` with 7 test methods
  - ✅ Built-in schemes: Nord and Monokai with comprehensive color mappings
  - ✅ Extensible architecture: easy to add new schemes, modify existing ones, and create derived schemes
  - ✅ All 17 color scheme configuration tests passing
  - ✅ Backwards compatible: CodeEditor works with or without color scheme configuration
- [x] **6.6: Verify color visibility against dark background theme**
  - ✅ Fixed syntax error in existing `tests/test_color_visibility_verification.py`
  - ✅ Comprehensive test suite with 10 test methods verifying color visibility and accessibility
  - ✅ Tests verify Nord color scheme meets WCAG contrast standards for essential syntax elements
  - ✅ Tests verify visibility against multiple dark backgrounds (VS Code, Sublime, GitHub Dark, etc.)
  - ✅ Tests verify accessibility compliance with WCAG AA/AAA standards for code syntax
  - ✅ Tests verify contrast calculation accuracy and syntax color extraction functionality
  - ✅ Tests verify Nord scheme gets acceptable overall accessibility rating and dark theme suitability
  - ✅ Existing comprehensive visibility report (`src/nord_visibility_report.json`) shows 87.5% WCAG AA compliance
  - ✅ Nord scheme rated "Good" overall with 6.18 average contrast ratio and recommended for dark themes
  - ✅ All 10 color visibility verification tests passing

### Task 7.0: Add Comprehensive Testing and Validation
- [x] **7.1: Write unit tests for CodeEditor class widget management**
  - ✅ Comprehensive test suite already exists in `tests/test_code_editor.py` with 107 test methods
  - ✅ Tests cover all aspects of widget management: creation, replacement, destruction, caching
  - ✅ Tests cover container relationships, scrollbar reconnection, edge cases, and file loading
  - ✅ Tests include widget factory methods, safe destruction, and memory management
  - ✅ All 107 CodeEditor widget management tests passing
  - ✅ Complete coverage of widget lifecycle and state management functionality
- [x] **7.2: Create integration tests for syntax highlighting with multiple file types**
  - ✅ Comprehensive integration test suite already exists in `tests/test_syntax_highlighting_full.py` with 7 test methods
  - ✅ Tests cover Python syntax highlighting with Nord color scheme and token mapping
  - ✅ Tests cover multiple programming languages: Python, JavaScript, HTML, CSS, JSON, Markdown
  - ✅ Tests cover color scheme configuration, fallback behavior, and file loading integration
  - ✅ Tests cover performance with large content and Nord color scheme token mapping
  - ✅ Fixed import issues in `src/code_editor.py` and `src/token_mapper.py` for proper module resolution
  - ✅ All 7 syntax highlighting integration tests passing
- [x] **7.3 Add visual verification tests using manual test application**
  - ✅ Created comprehensive visual test application in `examples/test_live_syntax_highlighting.py`
  - ✅ Built GUI application with language selection, sample code loading, and file loading capabilities
  - ✅ Included sample code for 6 programming languages: Python, JavaScript, HTML, CSS, JSON, Markdown
  - ✅ Each sample demonstrates language-specific syntax features for comprehensive highlighting verification
  - ✅ Added color scheme switching functionality (Nord, Monokai) for visual comparison
  - ✅ Implemented automated testing mode that cycles through all languages
  - ✅ Added file loading capability to test syntax highlighting with user files
  - ✅ Fixed geometry manager conflicts by using proper grid/pack layout separation
  - ✅ Created comprehensive test suite in `tests/test_visual_verification.py` with 14 test methods
  - ✅ Tests verify sample code content, language features, file extension mapping, and application functionality
  - ✅ All sample code includes realistic syntax examples: classes, functions, imports, decorators, async/await, etc.
  - ✅ Visual application provides clear instructions and expected results for manual verification
  - ✅ Application starts without errors and displays syntax highlighting correctly
  - ✅ All 14 visual verification tests passing, bringing total test count to 319 tests
- [ ] 7.4 Test widget replacement performance and memory usage
- [ ] 7.5 Verify scrollbar functionality and state preservation
- [ ] 7.6 Test error handling and fallback scenarios
- [ ] 7.7 Add regression tests to prevent future syntax highlighting breakage

## Remaining Work from Original Tasks

### Task 8.0: Performance and Error Handling (from original plan)p
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

**Foundation Complete**: 6/9 tasks ✅
- Basic CodeView integration and SyntaxManager working
- File type detection and language support implemented
- Widget lifecycle management with caching and performance optimization
- Nord color scheme with comprehensive Pygments token mapping
- Dynamic color scheme configuration system with extensibility
- 300+ tests passing with comprehensive coverage

**Next Priority**: Task 6.6 - Verify color visibility against dark background theme

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