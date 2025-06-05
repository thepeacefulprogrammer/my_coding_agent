## Relevant Files

- `src/main.py`: Application entry point with error handling
- `src/gui.py`: Main GUI class with dialogs and layout
- `src/file_explorer.py`: FileExplorer class for directory scanning
- `src/__init__.py`: Package initialization  
- `requirements.txt`: Project dependencies
- `pytest.ini`: Test configuration
- `tests/`: Comprehensive test suite with 31 tests

## Notes

- Place test files under `tests/` mirroring the structure in `src/`.
- Run tests with `pytest` from the project root.
- GUI tests may require `pytest-qt` for widget-level testing or appropriate mocking.

## Task Breakdown

**Total Progress: 2/5 tasks complete**

### Task 1.0: Project Setup and Initial Configuration
- [x] **1.1:** Create project directory structure (`src/`, `tests/`)
- [x] **1.2:** Add `requirements.txt` with necessary dependencies  
- [x] **1.3:** Configure `pytest.ini` for running tests
- [x] **1.4:** Add placeholder test files for modules
- [x] **1.5:** Run `pytest` to verify the initial setup

### Task 2.0: Implement File/Folder Selection Dialogs
- [x] **2.1:** Add "Open Folder" GUI button/menu item with handler stub
- [x] **2.2:** Implement `open_folder_dialog()` using `filedialog.askdirectory`  
- [x] **2.3:** Add "New Folder" GUI button/menu item with handler stub
- [x] **2.4:** Implement `new_folder_dialog()` using `simpledialog.askstring` and `os.mkdir`
- [x] **2.5:** Write tests mocking dialogs to verify behavior

## Tasks

- [ ] 3.0 Develop `file_explorer.py` module for directory scanning and auto-refresh
  - [x] 3.1 Create `FileExplorer` class with `scan_directory(path)` method
  - [x] 3.2 Implement `create_directory(parent_path, new_name)` method
  - [x] 3.3 Add `refresh()` method to re-scan the current directory
  - [x] 3.4 Write unit tests for `scan_directory` using `tmp_path` fixtures
  - [ ] 3.5 Write unit tests for `create_directory` using `tmp_path`
- [ ] 4.0 Build tree view component in `gui.py` to display the file hierarchy
  - [ ] 4.1 Add a `ttk.Treeview` widget to the sidebar layout
  - [ ] 4.2 Implement `populate_tree(treeview, data)` to insert items
  - [ ] 4.3 Bind expand/collapse functionality to tree items
  - [ ] 4.4 Connect tree refresh to `FileExplorer.refresh()`
  - [ ] 4.5 Write unit tests for `populate_tree` logic
- [ ] 5.0 Implement file content viewer pane in `gui.py` to load and render file contents
  - [ ] 5.1 Add a read-only `Text` widget with scrollbar to the main layout
  - [ ] 5.2 Extend `FileExplorer` with `read_file(path)` method
  - [ ] 5.3 Implement tree selection handler to call `read_file` and update text widget
  - [ ] 5.4 Ensure file viewer pane scrolls properly (scrollbar binding)
  - [ ] 5.5 Write unit tests for `read_file` method
  - [ ] 5.6 Write unit tests for selection handler logic 