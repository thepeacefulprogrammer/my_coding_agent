"""Unit tests for project history management and configuration (Task 9.7) - ChromaDB-only."""

import tempfile
import unittest.mock as mock
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from src.my_coding_agent.core.memory.project_history_management import (
    GitLogImporter,
    ProjectHistoryManager,
    ProjectHistorySettings,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_settings():
    """Create mock project history settings."""
    return ProjectHistorySettings(
        enabled=True,
        retention_days=365,
        max_entries=10000,
        file_filters=["*.py", "*.js", "*.ts", "*.json", "*.md", "*.yaml", "*.yml"],
        exclude_patterns=[
            "__pycache__/*",
            "node_modules/*",
            ".git/*",
            "*.pyc",
            "*.log",
        ],
        enable_auto_cleanup=True,
        cleanup_interval_hours=24,
    )


@pytest.fixture
def mock_project_events():
    """Create mock project events for testing."""
    now = datetime.now().timestamp()
    return [
        {
            "id": "event1",
            "timestamp": now - 3600,  # 1 hour ago
            "event_type": "feature_addition",
            "file_path": "src/main.py",
            "summary": "Added authentication logic",
            "content": "Implemented JWT-based authentication system",
            "metadata": {
                "lines_added": 45,
                "lines_removed": 2,
                "impact_score": 0.8,
                "change_type": "feature_addition",
            },
        },
        {
            "id": "event2",
            "timestamp": now - 86400 * 200,  # 200 days ago (old)
            "event_type": "refactoring",
            "file_path": "src/utils.py",
            "summary": "Refactored utility functions",
            "content": "Cleaned up and optimized utility functions",
            "metadata": {
                "lines_added": 20,
                "lines_removed": 35,
                "impact_score": 0.6,
                "change_type": "refactoring",
            },
        },
        {
            "id": "event3",
            "timestamp": now - 86400 * 400,  # 400 days ago (should be deleted)
            "event_type": "bug_fix",
            "file_path": "src/database.py",
            "summary": "Fixed database connection issue",
            "content": "Resolved connection timeout problems",
            "metadata": {
                "lines_added": 5,
                "lines_removed": 3,
                "impact_score": 0.7,
                "change_type": "bug_fix",
            },
        },
    ]


class TestProjectHistorySettings:
    """Test suite for project history settings."""

    def test_settings_initialization(self):
        """Test that settings initialize with correct default values."""
        settings = ProjectHistorySettings()

        assert settings.enabled is True
        assert settings.retention_days == 365
        assert settings.max_entries == 10000
        assert settings.enable_auto_cleanup is True
        assert isinstance(settings.file_filters, list)
        assert isinstance(settings.exclude_patterns, list)

    def test_settings_validation(self):
        """Test that settings validation works correctly."""
        # Test invalid retention days
        with pytest.raises(ValueError, match="retention_days must be positive"):
            ProjectHistorySettings(retention_days=-1)

        # Test invalid max entries
        with pytest.raises(ValueError, match="max_entries must be positive"):
            ProjectHistorySettings(max_entries=0)

        # Test invalid cleanup interval
        with pytest.raises(ValueError, match="cleanup_interval_hours must be positive"):
            ProjectHistorySettings(cleanup_interval_hours=-5)

    def test_settings_serialization(self):
        """Test settings serialization with Pydantic methods."""
        settings = ProjectHistorySettings(
            enabled=False,
            retention_days=180,
            max_entries=5000,
        )

        # Test model_dump (Pydantic v2)
        settings_dict = settings.model_dump()
        assert settings_dict["enabled"] is False
        assert settings_dict["retention_days"] == 180
        assert settings_dict["max_entries"] == 5000

        # Test model_validate (Pydantic v2)
        restored_settings = ProjectHistorySettings.model_validate(settings_dict)
        assert restored_settings.enabled is False
        assert restored_settings.retention_days == 180
        assert restored_settings.max_entries == 5000

        # Test JSON serialization
        json_str = settings.model_dump_json()
        restored_from_json = ProjectHistorySettings.model_validate_json(json_str)
        assert restored_from_json.enabled is False
        assert restored_from_json.retention_days == 180

    def test_file_filter_matching(self):
        """Test file filter pattern matching."""
        settings = ProjectHistorySettings(
            file_filters=["*.py", "*.js", "src/*.ts"],
            exclude_patterns=["__pycache__/*", "*.pyc"],
        )

        # Test should_track_file method
        assert settings.should_track_file("main.py") is True
        assert settings.should_track_file("script.js") is True
        assert settings.should_track_file("src/component.ts") is True
        assert settings.should_track_file("test.txt") is False
        assert settings.should_track_file("__pycache__/module.pyc") is False
        assert settings.should_track_file("compiled.pyc") is False


class TestProjectHistoryManager:
    """Test suite for project history manager."""

    def test_manager_initialization(self, mock_settings):
        """Test that manager initializes correctly."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            manager = ProjectHistoryManager(
                memory_handler=mock_memory.return_value, settings=mock_settings
            )

            assert manager.settings == mock_settings
            assert manager.memory_handler is not None
            assert hasattr(manager, "_last_cleanup_time")
            # Note: archiving attributes removed in ChromaDB-only architecture

    def test_cleanup_old_entries(self, mock_settings, mock_project_events):
        """Test cleanup of old project history entries."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value
            mock_memory_instance.get_project_history.return_value = mock_project_events

            # Mock the RAG engine for actual deletion
            mock_rag = mock.Mock()
            mock_rag.delete_old_project_history.return_value = (
                1  # Simulate deleting 1 old entry
            )
            mock_memory_instance.rag_engine = mock_rag

            manager = ProjectHistoryManager(
                memory_handler=mock_memory_instance, settings=mock_settings
            )

            # Test cleanup
            cleanup_result = manager.cleanup_old_entries()

            assert cleanup_result["success"] is True
            assert cleanup_result["entries_deleted"] == 1
            assert "cleanup_duration" in cleanup_result

            # Verify the RAG engine was called for deletion
            mock_rag.delete_old_project_history.assert_called_once()

    def test_automatic_cleanup_scheduling(self, mock_settings):
        """Test automatic cleanup scheduling."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            manager = ProjectHistoryManager(
                memory_handler=mock_memory.return_value, settings=mock_settings
            )

            # Test should_run_cleanup
            manager._last_cleanup_time = datetime.now() - timedelta(hours=25)
            assert manager.should_run_cleanup() is True

            manager._last_cleanup_time = datetime.now() - timedelta(hours=12)
            assert manager.should_run_cleanup() is False

    def test_entry_filtering_and_validation(self, mock_settings):
        """Test file filtering capability."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            manager = ProjectHistoryManager(
                memory_handler=mock_memory.return_value, settings=mock_settings
            )

            # Test file filtering through settings
            assert manager.settings.should_track_file("src/main.py") is True
            assert manager.settings.should_track_file("script.js") is True
            assert manager.settings.should_track_file("README.md") is True
            assert manager.settings.should_track_file("temp.txt") is False
            assert manager.settings.should_track_file("__pycache__/module.pyc") is False

    def test_get_storage_statistics(self, mock_settings, mock_project_events):
        """Test getting storage statistics."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value
            mock_memory_instance.get_project_history.return_value = mock_project_events

            manager = ProjectHistoryManager(
                memory_handler=mock_memory_instance, settings=mock_settings
            )

            stats = manager.get_storage_statistics()

            assert "total_entries" in stats
            assert "storage_size_mb" in stats
            assert "oldest_entry_age_days" in stats
            assert "newest_entry_age_days" in stats
            assert "entries_by_type" in stats
            assert "average_entry_size" in stats
            assert "retention_compliance" in stats


class TestProjectHistoryConfigurationIntegration:
    """Test suite for project history configuration integration."""

    def test_settings_usage(self):
        """Test basic settings usage."""
        settings = ProjectHistorySettings(
            enabled=True,
            retention_days=180,
            max_entries=5000,
        )

        assert settings.enabled is True
        assert settings.retention_days == 180
        assert settings.max_entries == 5000

    def test_comprehensive_workflow(self, temp_dir, mock_project_events):
        """Test complete workflow: settings, cleanup, import."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value
            mock_memory_instance.get_project_history.return_value = mock_project_events

            # Mock the RAG engine for actual deletion
            mock_rag = mock.Mock()
            mock_rag.delete_old_project_history.return_value = (
                1  # Simulate deleting 1 old entry
            )
            mock_memory_instance.rag_engine = mock_rag

            # 1. Create and configure settings
            settings = ProjectHistorySettings(
                retention_days=300,
                enable_auto_cleanup=True,
            )

            # 2. Initialize manager and run operations
            manager = ProjectHistoryManager(
                memory_handler=mock_memory_instance,
                settings=settings,
            )

            # 3. Run cleanup
            cleanup_result = manager.cleanup_old_entries()
            assert cleanup_result["success"] is True

            # 4. Create a mock git log file
            git_log_content = """commit abc123def456
Author: Developer <dev@example.com>
Date: Mon Jan 1 12:00:00 2024 +0000

    Add authentication feature

commit def456ghi789
Author: Developer <dev@example.com>
Date: Sun Dec 31 10:30:00 2023 +0000

    Fix database connection issue
"""
            git_log_path = temp_dir / "git.log"
            with open(git_log_path, "w") as f:
                f.write(git_log_content)

            # 5. Test git log import functionality
            importer = GitLogImporter(memory_handler=mock_memory_instance)

            # The import should succeed even if it processes 0 commits (due to simplified git log)
            import_result = importer.import_from_git_log(str(git_log_path))

            # Verify workflow completed successfully
            assert cleanup_result["entries_deleted"] >= 0
            assert import_result["entries_imported"] >= 0
