# Product Requirements Document (PRD): File Explorer GUI MVP

## 1. Introduction / Overview
This desktop application will serve as the first MVP of our custom "Vibe Coding" IDE. It provides a Python-based GUI that allows users to select or create a project folder, view its file structure in a sidebar, and click on files to display their contents in a scrollable pane. We will drive development with Test-Driven Development (TDD) to ensure high test coverage and reliability.

## 2. Goals
- Enable users to open an existing folder or create a new one via a GUI dialog.  
- Display the project's directory tree in a collapsible sidebar.  
- Render the contents of selected files in a scrollable text pane.  
- Use TDD: all core behaviors must be covered by automated tests with passing results.

## 3. User Stories
1. As a developer, I want to open an existing folder so that I can browse and inspect my project files.  
2. As a developer, I want to create a new folder so that I can start a fresh project workspace.  
3. As a developer, I want to see a hierarchical tree of files and directories so that I can navigate the project structure.  
4. As a developer, I want to click on a file and view its contents in a pane so that I can read (and later edit) code.

## 4. Functional Requirements
1. The application must allow users to launch a system-native file dialog to select an existing directory.  
2. The application must allow users to create a new directory from within the GUI.  
3. The sidebar must display all files and subdirectories of the chosen folder in a collapsible tree view.  
4. Clicking a file in the tree must load and render its contents in a scrollable, read-only text pane.  
5. The file tree must refresh automatically when a new subdirectory is created inside the workspace.  
6. Every core function must have associated automated tests (unit and integration), and all tests must pass before merging.

## 5. Non-Goals (Out of Scope)
- Editing, saving, or modifying file contents.  
- Syntax highlighting, linting, or code formatting.  
- AI chat interface, plugin system, or other advanced IDE features.  
- Version control or project import/export.  
- Cross-platform packaging (initial target: Linux/Debian).

## 6. Design Considerations
- **Language & Framework:** Python 3.10+; prototype using Tkinter for lightweight UI.  
- **Layout:** Left sidebar for file tree; right pane for file viewer.  
- **Dialogs:** Use native OS file/folder dialogs for consistency.

## 7. Technical Considerations
- **Architecture:** Follow MVC or MVP to separate UI and file-system logic for easier testing.  
- **Testing:** Use `pytest` and `pytest-qt` (if needed) to test both backend and GUI components.  
- **File I/O Abstraction:** Wrap file reads/writes in interfaces that can be mocked during tests.

## 8. Success Metrics
- 100% of defined tests pass in continuous integration.  
- Successful opening and creation of directories without errors.  
- Accurate and responsive rendering of the file tree and file contents.

## 9. Open Questions
- Which GUI toolkit (Tkinter vs PyQt) will best balance simplicity and future extensibility?  
- How should we structure the project (module/package layout) for testability?  
- Where will we place tests (e.g., `/tests`), and what coverage threshold will we enforce? 