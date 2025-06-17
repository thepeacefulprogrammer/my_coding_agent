"""
Tests for file change detection system.

This module tests the automatic file change detection system including:
- File system watcher for detecting modifications, creations, and deletions
- File change analyzer for extracting diffs and summaries
- Filtering system for ignoring temporary files and build artifacts
- Integration with file tree widget signals
"""

import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtTest import QSignalSpy
from src.my_coding_agent.core.file_change_detector import (
    ChangeType,
    FileChangeAnalyzer,
    FileChangeDetector,
    FileChangeEvent,
    FileChangeFilter,
)


class TestFileChangeEvent:
    """Test FileChangeEvent data class."""

    def test_file_change_event_creation(self):
        """Test creating a FileChangeEvent."""
        event = FileChangeEvent(
            file_path=Path("/test/file.py"),
            change_type=ChangeType.MODIFIED,
            timestamp=1234567890.0,
            old_content="old content",
            new_content="new content",
        )

        assert event.file_path == Path("/test/file.py")
        assert event.change_type == ChangeType.MODIFIED
        assert event.timestamp == 1234567890.0
        assert event.old_content == "old content"
        assert event.new_content == "new content"

    def test_file_change_event_defaults(self):
        """Test FileChangeEvent with default values."""
        event = FileChangeEvent(
            file_path=Path("/test/file.py"), change_type=ChangeType.CREATED
        )

        assert event.file_path == Path("/test/file.py")
        assert event.change_type == ChangeType.CREATED
        assert event.timestamp > 0  # Should be set automatically
        assert event.old_content is None
        assert event.new_content is None


class TestFileChangeFilter:
    """Test FileChangeFilter for filtering unwanted files."""

    @pytest.fixture
    def filter_instance(self):
        """Create a FileChangeFilter instance."""
        return FileChangeFilter()

    def test_should_ignore_temporary_files(self, filter_instance):
        """Test filtering of temporary files."""
        temp_files = [
            Path("/test/.tmp"),
            Path("/test/file.tmp"),
            Path("/test/~file.txt"),
            Path("/test/.#file.py"),
            Path("/test/file.py~"),
            Path("/test/.DS_Store"),
        ]

        for temp_file in temp_files:
            assert filter_instance.should_ignore(temp_file) is True

    def test_should_ignore_build_artifacts(self, filter_instance):
        """Test filtering of build artifacts."""
        build_files = [
            Path("/test/__pycache__/module.py"),
            Path("/test/build/output.exe"),
            Path("/test/dist/package.whl"),
            Path("/test/.pytest_cache/config"),
            Path("/test/node_modules/package/index.js"),
            Path("/test/.git/config"),
            Path("/test/.venv/lib/python3.11/site-packages/module.py"),
        ]

        for build_file in build_files:
            assert filter_instance.should_ignore(build_file) is True

    def test_should_ignore_large_files(self, filter_instance):
        """Test filtering of large files."""
        # Mock file size check
        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 100 * 1024 * 1024  # 100MB

            large_file = Path("/test/large_file.bin")
            assert filter_instance.should_ignore(large_file) is True

    def test_should_not_ignore_valid_files(self, filter_instance):
        """Test that valid files are not ignored."""
        valid_files = [
            Path("/test/main.py"),
            Path("/test/config.json"),
            Path("/test/README.md"),
            Path("/test/src/module.py"),
            Path("/test/tests/test_file.py"),
        ]

        # Create a mock stat result
        from unittest.mock import MagicMock

        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024  # 1KB

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "stat", return_value=mock_stat_result),
        ):
            for valid_file in valid_files:
                assert filter_instance.should_ignore(valid_file) is False

    def test_custom_ignore_patterns(self, filter_instance):
        """Test custom ignore patterns."""
        filter_instance.add_ignore_pattern("*.log")
        filter_instance.add_ignore_pattern("temp_*")

        assert filter_instance.should_ignore(Path("/test/app.log")) is True
        assert filter_instance.should_ignore(Path("/test/temp_file.txt")) is True
        assert filter_instance.should_ignore(Path("/test/normal.txt")) is False


class TestFileChangeAnalyzer:
    """Test FileChangeAnalyzer for analyzing file changes."""

    @pytest.fixture
    def analyzer(self):
        """Create a FileChangeAnalyzer instance."""
        return FileChangeAnalyzer()

    def test_analyze_text_file_modification(self, analyzer):
        """Test analyzing text file modifications."""
        old_content = "line 1\nline 2\nline 3"
        new_content = "line 1\nmodified line 2\nline 3\nline 4"

        analysis = analyzer.analyze_change(
            file_path=Path("/test/file.txt"),
            old_content=old_content,
            new_content=new_content,
        )

        assert analysis["change_type"] == "modification"
        assert analysis["lines_added"] == 2
        assert analysis["lines_removed"] == 1
        assert analysis["lines_changed"] == 1
        assert "Modified file.txt: +2/-1 lines" in analysis["summary"]
        assert len(analysis["diff_lines"]) > 0

    def test_analyze_file_creation(self, analyzer):
        """Test analyzing file creation."""
        new_content = "def hello():\n    print('Hello, World!')"

        analysis = analyzer.analyze_change(
            file_path=Path("/test/new_file.py"),
            old_content=None,
            new_content=new_content,
        )

        assert analysis["change_type"] == "creation"
        assert analysis["lines_added"] == 2
        assert analysis["lines_removed"] == 0
        assert analysis["lines_changed"] == 0
        assert "new_file.py" in analysis["summary"]
        assert "hello()" in analysis["summary"]  # Should show the actual function name

    def test_analyze_file_deletion(self, analyzer):
        """Test analyzing file deletion."""
        old_content = "def goodbye():\n    print('Goodbye!')"

        analysis = analyzer.analyze_change(
            file_path=Path("/test/deleted_file.py"),
            old_content=old_content,
            new_content=None,
        )

        assert analysis["change_type"] == "deletion"
        assert analysis["lines_added"] == 0
        assert analysis["lines_removed"] == 2
        assert analysis["lines_changed"] == 0
        assert "deleted_file.py" in analysis["summary"]
        assert (
            "goodbye()" in analysis["summary"]
        )  # Should show the actual function name

    def test_analyze_binary_file(self, analyzer):
        """Test analyzing binary file changes."""
        # Binary content simulation
        old_content = b"\x00\x01\x02\x03"
        new_content = b"\x00\x01\x02\x04"

        analysis = analyzer.analyze_change(
            file_path=Path("/test/binary.bin"),
            old_content=old_content,
            new_content=new_content,
        )

        assert analysis["change_type"] == "modification"
        assert analysis["is_binary"] is True
        assert "binary file" in analysis["summary"].lower()
        assert analysis["lines_added"] == 0
        assert analysis["lines_removed"] == 0

    def test_detect_code_patterns(self, analyzer):
        """Test detection of code patterns in changes."""
        old_content = "def old_function():\n    pass"
        new_content = (
            "def new_function():\n    return 'hello'\n\nclass NewClass:\n    pass"
        )

        analysis = analyzer.analyze_change(
            file_path=Path("/test/code.py"),
            old_content=old_content,
            new_content=new_content,
        )

        assert (
            "new_function()" in analysis["summary"]
        )  # Should show actual function name
        assert (
            "old_function()" in analysis["summary"]
        )  # Should show removed function name
        assert "class NewClass" in analysis["summary"]  # Should show actual class name
        assert (
            analysis["code_elements"]["functions_added"] == 0
        )  # Net change is 0 (1 added, 1 removed)
        assert analysis["code_elements"]["classes_added"] == 1


class TestFileChangeDetector:
    """Test FileChangeDetector main class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def detector(self, temp_dir):
        """Create a FileChangeDetector instance."""
        return FileChangeDetector(watch_directory=temp_dir)

    def test_detector_initialization(self, detector, temp_dir):
        """Test detector initialization."""
        assert detector.watch_directory == temp_dir
        assert detector.is_watching is False
        assert isinstance(detector.file_filter, FileChangeFilter)
        assert isinstance(detector.analyzer, FileChangeAnalyzer)

    def test_start_stop_watching(self, detector):
        """Test starting and stopping file watching."""
        # Start watching
        detector.start_watching()
        assert detector.is_watching is True

        # Stop watching
        detector.stop_watching()
        assert detector.is_watching is False

    @pytest.mark.asyncio
    async def test_file_creation_detection(self, detector, temp_dir):
        """Test detection of file creation."""
        # Enable immediate emit for testing
        detector.set_immediate_emit(True)
        detector.start_watching()

        # Create signal spy
        spy = QSignalSpy(detector.file_changed)

        # Create a test file
        test_file = temp_dir / "test_file.py"
        test_file.write_text("print('Hello, World!')")

        # Wait for detection
        await self._wait_for_signal(spy, timeout=2.0)

        assert len(spy) > 0
        event = spy[0][0]  # First signal, first argument
        assert event.file_path == test_file
        assert event.change_type == ChangeType.CREATED

        detector.stop_watching()

    @pytest.mark.asyncio
    async def test_file_modification_detection(self, detector, temp_dir):
        """Test detection of file modification."""
        # Create initial file
        test_file = temp_dir / "test_file.py"
        test_file.write_text("print('Hello')")

        # Enable immediate emit for testing
        detector.set_immediate_emit(True)
        detector.start_watching()
        spy = QSignalSpy(detector.file_changed)

        # Modify the file
        time.sleep(0.1)  # Ensure different timestamp
        test_file.write_text("print('Hello, World!')")

        # Wait for detection
        await self._wait_for_signal(spy, timeout=2.0)

        assert len(spy) > 0
        event = spy[0][0]
        assert event.file_path == test_file
        assert event.change_type == ChangeType.MODIFIED

        detector.stop_watching()

    @pytest.mark.asyncio
    async def test_file_deletion_detection(self, detector, temp_dir):
        """Test detection of file deletion."""
        # Create initial file
        test_file = temp_dir / "test_file.py"
        test_file.write_text("print('Hello')")

        # Enable immediate emit for testing
        detector.set_immediate_emit(True)
        detector.start_watching()
        spy = QSignalSpy(detector.file_changed)

        # Delete the file
        test_file.unlink()

        # Wait for detection
        await self._wait_for_signal(spy, timeout=2.0)

        assert len(spy) > 0
        event = spy[0][0]
        assert event.file_path == test_file
        assert event.change_type == ChangeType.DELETED

        detector.stop_watching()

    def test_filtered_files_ignored(self, detector, temp_dir):
        """Test that filtered files are ignored."""
        detector.start_watching()
        spy = QSignalSpy(detector.file_changed)

        # Create files that should be ignored
        (temp_dir / "__pycache__").mkdir()
        (temp_dir / "__pycache__" / "module.pyc").write_text("compiled")
        (temp_dir / ".tmp").write_text("temp")

        # Wait a bit
        time.sleep(0.5)

        # Should not receive any signals
        assert len(spy) == 0

        detector.stop_watching()

    def test_integration_with_file_tree_signals(self, detector):
        """Test integration with file tree widget signals."""
        # Mock file tree widget
        mock_file_tree = Mock()
        mock_file_tree.file_selected = Mock()
        mock_file_tree.file_opened = Mock()

        # Connect detector to file tree
        detector.connect_to_file_tree(mock_file_tree)

        # Verify connections were made
        assert hasattr(detector, "_file_tree_widget")
        assert detector._file_tree_widget == mock_file_tree

    async def _wait_for_signal(self, spy, timeout=1.0):
        """Helper to wait for signal emission."""
        start_time = time.time()
        while len(spy) == 0 and (time.time() - start_time) < timeout:
            # Process events to allow signal emission
            from PyQt6.QtWidgets import QApplication

            if QApplication.instance():
                QApplication.processEvents()
            await asyncio.sleep(0.01)


class TestFileChangeDetectorIntegration:
    """Integration tests for FileChangeDetector."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with realistic file structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create realistic project structure
            (workspace / "src").mkdir()
            (workspace / "src" / "main.py").write_text("def main():\n    pass")
            (workspace / "tests").mkdir()
            (workspace / "tests" / "test_main.py").write_text("import unittest")
            (workspace / "README.md").write_text("# Project")
            (workspace / "requirements.txt").write_text("pytest>=7.0.0")

            yield workspace

    def test_realistic_file_operations(self, temp_workspace):
        """Test realistic file operations in a project structure."""
        detector = FileChangeDetector(watch_directory=temp_workspace)
        # Enable immediate emit for testing
        detector.set_immediate_emit(True)
        detector.start_watching()

        spy = QSignalSpy(detector.file_changed)

        # Simulate real development workflow
        # 1. Modify main.py
        main_file = temp_workspace / "src" / "main.py"
        main_file.write_text(
            "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()"
        )

        # 2. Add new test file
        new_test = temp_workspace / "tests" / "test_new_feature.py"
        new_test.write_text("def test_new_feature():\n    assert True")

        # 3. Update requirements
        req_file = temp_workspace / "requirements.txt"
        req_file.write_text("pytest>=7.0.0\nrequests>=2.25.0")

        # Allow some time for detection
        time.sleep(1.0)
        from PyQt6.QtWidgets import QApplication

        if QApplication.instance():
            QApplication.processEvents()

        # Should detect multiple changes
        assert len(spy) >= 3  # At least the 3 operations above

        # Verify different change types were detected
        change_types = [event[0].change_type for event in spy]
        assert ChangeType.MODIFIED in change_types
        assert ChangeType.CREATED in change_types

        detector.stop_watching()

    @pytest.mark.slow
    def test_performance_with_many_files(self, temp_workspace):
        """Test performance with many file operations."""
        detector = FileChangeDetector(watch_directory=temp_workspace)
        detector.start_watching()

        # Create many files quickly
        files_dir = temp_workspace / "many_files"
        files_dir.mkdir()

        start_time = time.time()
        for i in range(50):
            (files_dir / f"file_{i}.py").write_text(f"# File {i}")

        # Should complete reasonably quickly
        elapsed = time.time() - start_time
        assert elapsed < 5.0  # Should complete within 5 seconds

        detector.stop_watching()
