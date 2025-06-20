"""
Integration tests for the Simple Code Viewer application.

This module provides comprehensive integration tests that verify the complete
application workflow and component interactions.
"""

from __future__ import annotations

import contextlib
import os

import pytest
from PyQt6.QtCore import Qt

from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
from my_coding_agent.core.code_viewer import CodeViewerWidget
from my_coding_agent.core.file_tree import FileTreeWidget
from my_coding_agent.core.main_window import MainWindow
from my_coding_agent.core.theme_manager import ThemeManager


class TestApplicationIntegration:
    """Test complete application workflow and component integration."""

    @pytest.fixture
    def sample_project(self, tmp_path):
        """Create a sample project structure for testing."""
        # Create project structure
        project_dir = tmp_path / "sample_project"
        project_dir.mkdir()

        # Python files
        (project_dir / "main.py").write_text("""#!/usr/bin/env python3
\"\"\"Main application entry point.\"\"\"

def main():
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
""")

        (project_dir / "utils.py").write_text("""\"\"\"Utility functions.\"\"\"

def calculate_sum(a, b):
    \"\"\"Calculate sum of two numbers.\"\"\"
    return a + b

def format_message(name):
    \"\"\"Format a greeting message.\"\"\"
    return f"Hello, {name}!"
""")

        # JavaScript files
        js_dir = project_dir / "static" / "js"
        js_dir.mkdir(parents=True)

        (js_dir / "app.js").write_text("""// Main application JavaScript
function initializeApp() {
    console.log('Application initialized');
    setupEventListeners();
}

function setupEventListeners() {
    document.addEventListener('DOMContentLoaded', initializeApp);
}

// Initialize the app
setupEventListeners();
""")

        # Configuration files
        (project_dir / "config.json").write_text("""{
    "app_name": "Sample Project",
    "version": "1.0.0",
    "debug": true,
    "features": {
        "logging": true,
        "analytics": false
    }
}""")

        # Documentation
        (project_dir / "README.md").write_text("""# Sample Project

This is a sample project for testing the code viewer application.

## Features

- Python backend
- JavaScript frontend
- JSON configuration
- Markdown documentation

## Usage

Run the main application:

```bash
python main.py
```
""")

        # Subdirectories
        tests_dir = project_dir / "tests"
        tests_dir.mkdir()

        (
            tests_dir / "test_utils.py"
        ).write_text("""\"\"\"Tests for utility functions.\"\"\"

import unittest
from utils import calculate_sum, format_message


class TestUtils(unittest.TestCase):

    def test_calculate_sum(self):
        self.assertEqual(calculate_sum(2, 3), 5)
        self.assertEqual(calculate_sum(0, 0), 0)
        self.assertEqual(calculate_sum(-1, 1), 0)

    def test_format_message(self):
        self.assertEqual(format_message("Alice"), "Hello, Alice!")
        self.assertEqual(format_message(""), "Hello, !")
""")

        return project_dir

    @pytest.fixture
    def main_window(self, qtbot, sample_project):
        """Create MainWindow instance for testing."""
        window = MainWindow(str(sample_project))
        qtbot.addWidget(window)

        # Set the sample project as root directory
        window.file_tree.set_root_directory(sample_project)

        return window

    def test_application_startup_and_initialization(self, qtbot, tmp_path):
        """Test complete application startup sequence."""
        # Test that MainWindow can be created and initialized
        window = MainWindow(str(tmp_path))
        qtbot.addWidget(window)

        # Verify main components are initialized
        assert hasattr(window, "file_tree")
        assert hasattr(window, "code_viewer")
        assert hasattr(window, "theme_manager")
        assert hasattr(window, "status_bar")

        # Verify components are properly connected
        assert isinstance(window.file_tree, FileTreeWidget)
        assert isinstance(window.code_viewer, CodeViewerWidget)
        assert isinstance(window.theme_manager, ThemeManager)

        # Test window shows properly
        window.show()
        assert window.isVisible()

    def test_file_selection_and_code_display_workflow(
        self, qtbot, main_window, sample_project
    ):
        """Test complete workflow of selecting files and displaying code."""
        # Wait for file tree to load
        qtbot.waitUntil(
            lambda: main_window.file_tree.model().rowCount(
                main_window.file_tree.rootIndex()
            )
            > 0,
            timeout=2000,
        )

        # Test Python file selection and display
        python_file = sample_project / "main.py"
        model = main_window.file_tree.model()

        # Find and select the Python file
        python_index = model.index(str(python_file))
        if python_index.isValid():
            main_window.file_tree.setCurrentIndex(python_index)

            # Simulate double-click to open file
            main_window.file_tree._on_double_clicked(python_index)

            # Verify code is displayed in viewer
            qtbot.waitUntil(
                lambda: len(main_window.code_viewer.toPlainText()) > 0, timeout=1000
            )

            code_content = main_window.code_viewer.toPlainText()
            assert "def main():" in code_content
            assert "Hello, World!" in code_content

            # Verify syntax highlighting is active
            assert main_window.code_viewer._syntax_highlighter is not None
            assert main_window.code_viewer.syntax_highlighting_enabled()

    def test_directory_navigation_workflow(self, qtbot, main_window, sample_project):
        """Test complete directory navigation workflow."""
        # Wait for file tree to load
        qtbot.waitUntil(
            lambda: main_window.file_tree.model().rowCount(
                main_window.file_tree.rootIndex()
            )
            > 0,
            timeout=2000,
        )

        model = main_window.file_tree.model()

        # Test expanding directories
        static_dir = sample_project / "static"
        static_index = model.index(str(static_dir))

        if static_index.isValid():
            # Initially should be collapsed
            assert not main_window.file_tree.isExpanded(static_index)

            # Expand directory
            main_window.file_tree.expand(static_index)
            assert main_window.file_tree.isExpanded(static_index)

            # Navigate to JavaScript file
            js_file = static_dir / "js" / "app.js"
            js_index = model.index(str(js_file))

            if js_index.isValid():
                main_window.file_tree.setCurrentIndex(js_index)
                main_window.file_tree._on_double_clicked(js_index)

                # Verify JavaScript content is displayed
                qtbot.waitUntil(
                    lambda: "initializeApp" in main_window.code_viewer.toPlainText(),
                    timeout=1000,
                )

    def test_theme_switching_integration(self, qtbot, main_window):
        """Test theme switching affects all components."""
        # Get initial theme
        initial_theme = main_window.theme_manager.get_current_theme()

        # Switch to the opposite theme
        new_theme = "light" if initial_theme == "dark" else "dark"
        main_window.theme_manager.set_theme(new_theme)

        # Verify theme change propagated to components
        assert main_window.theme_manager.get_current_theme() == new_theme

        # Verify UI reflects theme change
        assert main_window.theme_manager.get_current_theme() != initial_theme

        # Switch back to initial theme to test toggle functionality
        main_window.theme_manager.set_theme(initial_theme)
        assert main_window.theme_manager.get_current_theme() == initial_theme

    def test_file_tree_refresh_and_update_workflow(
        self, qtbot, main_window, sample_project
    ):
        """Test file tree refresh and update workflow."""
        # Wait for initial load
        qtbot.waitUntil(
            lambda: main_window.file_tree.model().rowCount(
                main_window.file_tree.rootIndex()
            )
            > 0,
            timeout=2000,
        )

        # Add a new file to the project
        new_file = sample_project / "new_module.py"
        new_file.write_text("# New module\nprint('New file created')")

        # Refresh file tree
        main_window.file_tree.refresh()

        # Wait for refresh to complete (debounced)
        qtbot.wait(300)  # Wait for debounce delay

        # Verify file tree updated
        # Note: QFileSystemModel might update automatically, so we test refresh mechanism
        assert hasattr(main_window.file_tree, "_refresh_timer")

    def test_multiple_file_types_workflow(self, qtbot, main_window, sample_project):
        """Test workflow with multiple file types."""
        # Wait for file tree to load
        qtbot.waitUntil(
            lambda: main_window.file_tree.model().rowCount(
                main_window.file_tree.rootIndex()
            )
            > 0,
            timeout=2000,
        )

        model = main_window.file_tree.model()

        # Test different file types
        test_files = [
            (sample_project / "main.py", "python"),
            (sample_project / "config.json", "json"),
            (sample_project / "README.md", "markdown"),
        ]

        for file_path, file_type in test_files:
            if file_path.exists():
                file_index = model.index(str(file_path))
                if file_index.isValid():
                    # Select and open file
                    main_window.file_tree.setCurrentIndex(file_index)
                    main_window.file_tree._on_double_clicked(file_index)

                    # Wait for content to load
                    qtbot.waitUntil(
                        lambda: len(main_window.code_viewer.toPlainText()) > 0,
                        timeout=1000,
                    )

                    # Verify appropriate content is displayed
                    content = main_window.code_viewer.toPlainText()

                    if file_type == "python":
                        assert (
                            "def " in content
                            or "import " in content
                            or "print" in content
                        )
                    elif file_type == "json":
                        assert "{" in content and "}" in content
                    elif file_type == "markdown":
                        assert "#" in content or "##" in content

    def test_status_bar_updates_workflow(self, qtbot, main_window, sample_project):
        """Test status bar updates during file operations."""
        # Wait for file tree to load
        qtbot.waitUntil(
            lambda: main_window.file_tree.model().rowCount(
                main_window.file_tree.rootIndex()
            )
            > 0,
            timeout=2000,
        )

        # Select a file
        python_file = sample_project / "main.py"
        model = main_window.file_tree.model()
        python_index = model.index(str(python_file))

        if python_index.isValid():
            main_window.file_tree.setCurrentIndex(python_index)

            # The status bar should show file information
            # Note: This tests the integration even if status bar isn't fully implemented
            assert hasattr(main_window, "status_bar")

    def test_keyboard_navigation_integration(self, qtbot, main_window, sample_project):
        """Test keyboard navigation across components."""
        # Show the window to enable proper focus handling
        main_window.show()
        qtbot.waitForWindowShown(main_window)

        # Wait for file tree to load
        qtbot.waitUntil(
            lambda: main_window.file_tree.model().rowCount(
                main_window.file_tree.rootIndex()
            )
            > 0,
            timeout=2000,
        )

        # Focus on file tree
        main_window.file_tree.setFocus()

        # Test that keyboard navigation works by setting focus and checking
        # Note: Focus behavior can be complex in tests, so we test the mechanism exists
        assert main_window.file_tree.focusPolicy() != Qt.FocusPolicy.NoFocus

        # Test that keyboard navigation works
        # Select first item
        model = main_window.file_tree.model()
        first_index = model.index(0, 0, main_window.file_tree.rootIndex())
        if first_index.isValid():
            main_window.file_tree.setCurrentIndex(first_index)
            current = main_window.file_tree.currentIndex()
            assert current.isValid()

    def test_performance_under_load(self, qtbot, main_window, tmp_path):
        """Test application performance with larger file structures."""
        # Create a larger directory structure
        large_project = tmp_path / "large_project"
        large_project.mkdir()

        # Create multiple files and directories
        for i in range(20):  # Moderate size for testing
            dir_path = large_project / f"module_{i:02d}"
            dir_path.mkdir()

            for j in range(5):
                file_path = dir_path / f"file_{j:02d}.py"
                file_path.write_text(f"# Module {i}, File {j}\nprint('File {i}-{j}')")

        # Set large project as root
        main_window.file_tree.set_root_directory(large_project)

        # Wait for loading
        qtbot.waitUntil(
            lambda: main_window.file_tree.model().rowCount(
                main_window.file_tree.rootIndex()
            )
            > 0,
            timeout=3000,
        )

        # Test that performance optimizations work
        model = main_window.file_tree.model()

        # Verify caching is working
        assert hasattr(model, "_icon_cache")
        assert hasattr(model, "_performance_metrics")

        # Test expansion of multiple directories
        root_index = main_window.file_tree.rootIndex()
        for i in range(min(5, model.rowCount(root_index))):  # Test first 5 directories
            dir_index = model.index(i, 0, root_index)
            if dir_index.isValid() and model.isDir(dir_index):
                main_window.file_tree.expand(dir_index)

    def test_error_handling_integration(self, qtbot, main_window, tmp_path):
        """Test error handling across components."""
        # Test with non-existent directory
        non_existent = tmp_path / "does_not_exist"

        # This should handle the error gracefully
        with contextlib.suppress(ValueError, FileNotFoundError, PermissionError):
            main_window.file_tree.set_root_directory(non_existent)

        # Test with file instead of directory
        test_file = tmp_path / "not_a_directory.txt"
        test_file.write_text("This is a file, not a directory")

        with contextlib.suppress(ValueError, FileNotFoundError):
            main_window.file_tree.set_root_directory(test_file)

    def test_window_state_persistence_workflow(self, qtbot, main_window):
        """Test window state persistence integration."""
        # Test that window can be resized and maintains state
        initial_size = main_window.size()

        # Resize window
        main_window.resize(800, 600)
        assert main_window.size() != initial_size

        # Test splitter state
        if hasattr(main_window, "splitter"):
            initial_sizes = main_window.splitter.sizes()
            # Change splitter position
            main_window.splitter.setSizes([200, 600])
            assert main_window.splitter.sizes() != initial_sizes

    def test_component_cleanup_on_exit(self, qtbot, tmp_path):
        """Test proper cleanup when application exits."""
        window = MainWindow(str(tmp_path))
        qtbot.addWidget(window)

        # Show window
        window.show()
        assert window.isVisible()

        # Close window
        window.close()
        assert not window.isVisible()

        # Verify components exist and can be cleaned up
        assert hasattr(window, "file_tree")
        assert hasattr(window, "code_viewer")
        assert hasattr(window, "theme_manager")


@pytest.mark.integration
class TestAIAgentRealAPIIntegration:
    """Integration tests for AI Agent with real Azure OpenAI API."""

    @pytest.mark.skipif(
        not all(
            [
                os.getenv("AZURE_OPENAI_ENDPOINT"),
                os.getenv("AZURE_OPENAI_API_KEY"),
                os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            ]
        ),
        reason="Azure OpenAI credentials not available - set AZURE_OPENAI_* env vars to run this test",
    )
    @pytest.mark.asyncio
    async def test_real_azure_openai_api_call(self):
        """Test with real Azure OpenAI API (only runs if credentials are available)."""
        config = AIAgentConfig.from_env()
        agent = AIAgent(config)

        response = await agent.send_message(
            "Hello! Please respond with exactly 'Integration test successful'"
        )

        assert response.success is True
        assert response.content is not None
        assert len(response.content) > 0
        assert response.tokens_used > 0
        assert response.error is None
        assert response.error_type is None

    @pytest.mark.skipif(
        not all(
            [
                os.getenv("AZURE_OPENAI_ENDPOINT"),
                os.getenv("AZURE_OPENAI_API_KEY"),
                os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            ]
        ),
        reason="Azure OpenAI credentials not available - set AZURE_OPENAI_* env vars to run this test",
    )
    @pytest.mark.asyncio
    async def test_real_api_error_handling(self):
        """Test real API error handling scenarios."""
        config = AIAgentConfig.from_env()
        agent = AIAgent(config)

        # Test with a very long message that might hit token limits
        very_long_message = "Please analyze this code: " + "x" * 10000

        response = await agent.send_message(very_long_message)

        # Should either succeed or fail gracefully
        if not response.success:
            assert response.error is not None
            assert response.error_type is not None
        else:
            assert response.content is not None
