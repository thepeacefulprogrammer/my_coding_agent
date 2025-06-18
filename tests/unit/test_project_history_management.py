"""Unit tests for project history management and configuration (Task 9.7)."""

import json
import tempfile
import unittest.mock as mock
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from src.my_coding_agent.core.memory.project_history_management import (
    ProjectHistoryExporter,
    ProjectHistoryImporter,
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
        enable_archiving=True,
        archive_threshold_days=180,
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
            "timestamp": now - 86400 * 200,  # 200 days ago (should be archived)
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
        assert settings.enable_archiving is True
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
        """Test settings serialization to/from dict and JSON."""
        settings = ProjectHistorySettings(
            enabled=False,
            retention_days=180,
            max_entries=5000,
        )

        # Test to_dict
        settings_dict = settings.to_dict()
        assert settings_dict["enabled"] is False
        assert settings_dict["retention_days"] == 180
        assert settings_dict["max_entries"] == 5000

        # Test from_dict
        restored_settings = ProjectHistorySettings.from_dict(settings_dict)
        assert restored_settings.enabled is False
        assert restored_settings.retention_days == 180
        assert restored_settings.max_entries == 5000

        # Test JSON serialization
        json_str = settings.to_json()
        restored_from_json = ProjectHistorySettings.from_json(json_str)
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
            assert hasattr(manager, "_last_archive_time")

    def test_cleanup_old_entries(self, mock_settings, mock_project_events):
        """Test cleanup of old project history entries."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value
            mock_memory_instance.get_project_history.return_value = mock_project_events

            manager = ProjectHistoryManager(
                memory_handler=mock_memory_instance, settings=mock_settings
            )

            # Test cleanup
            cleanup_result = manager.cleanup_old_entries()

            assert cleanup_result["success"] is True
            assert cleanup_result["entries_deleted"] > 0
            assert cleanup_result["entries_archived"] >= 0
            assert "cleanup_duration" in cleanup_result

    def test_archive_old_entries(self, mock_settings, mock_project_events, temp_dir):
        """Test archiving of old project history entries."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value
            mock_memory_instance.get_project_history.return_value = mock_project_events

            manager = ProjectHistoryManager(
                memory_handler=mock_memory_instance, settings=mock_settings
            )

            # Test archiving
            archive_path = temp_dir / "archive.json"
            archive_result = manager.archive_old_entries(str(archive_path))

            assert archive_result["success"] is True
            assert archive_result["entries_archived"] > 0
            assert archive_path.exists()

            # Verify archive content
            with open(archive_path) as f:
                archive_data = json.load(f)
                assert "metadata" in archive_data
                assert "entries" in archive_data
                assert len(archive_data["entries"]) > 0

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
        """Test entry filtering and validation."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            manager = ProjectHistoryManager(
                memory_handler=mock_memory.return_value, settings=mock_settings
            )

            # Test validate_entry
            valid_entry = {
                "id": "test1",
                "timestamp": datetime.now().timestamp(),
                "event_type": "feature_addition",
                "file_path": "src/main.py",
                "summary": "Test change",
            }
            assert manager.validate_entry(valid_entry) is True

            # Test invalid entry (missing required fields)
            invalid_entry = {"id": "test2"}
            assert manager.validate_entry(invalid_entry) is False


class TestProjectHistoryExporter:
    """Test suite for project history export functionality."""

    def test_exporter_initialization(self):
        """Test that exporter initializes correctly."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            exporter = ProjectHistoryExporter(memory_handler=mock_memory.return_value)
            assert exporter.memory_handler is not None

    def test_export_to_json(self, mock_project_events, temp_dir):
        """Test exporting project history to JSON format."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value
            mock_memory_instance.get_project_history.return_value = mock_project_events

            exporter = ProjectHistoryExporter(memory_handler=mock_memory_instance)

            # Test JSON export
            export_path = temp_dir / "export.json"
            result = exporter.export_to_json(str(export_path))

            assert result["success"] is True
            assert result["entries_exported"] == len(mock_project_events)
            assert export_path.exists()

            # Verify export content
            with open(export_path) as f:
                export_data = json.load(f)
                assert "metadata" in export_data
                assert "entries" in export_data
                assert len(export_data["entries"]) == len(mock_project_events)

    def test_export_to_csv(self, mock_project_events, temp_dir):
        """Test exporting project history to CSV format."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value
            mock_memory_instance.get_project_history.return_value = mock_project_events

            exporter = ProjectHistoryExporter(memory_handler=mock_memory_instance)

            # Test CSV export
            export_path = temp_dir / "export.csv"
            result = exporter.export_to_csv(str(export_path))

            assert result["success"] is True
            assert result["entries_exported"] == len(mock_project_events)
            assert export_path.exists()

            # Verify CSV content
            import csv

            with open(export_path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == len(mock_project_events)
                assert "timestamp" in rows[0]
                assert "event_type" in rows[0]
                assert "file_path" in rows[0]

    def test_export_filtering(self, mock_project_events, temp_dir):
        """Test export with date range and type filtering."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value
            mock_memory_instance.get_project_history.return_value = mock_project_events

            exporter = ProjectHistoryExporter(memory_handler=mock_memory_instance)

            # Test filtered export
            start_date = datetime.now() - timedelta(days=100)
            end_date = datetime.now()

            export_path = temp_dir / "filtered_export.json"
            result = exporter.export_to_json(
                str(export_path),
                start_date=start_date,
                end_date=end_date,
                event_types=["feature_addition"],
            )

            assert result["success"] is True
            assert export_path.exists()


class TestProjectHistoryImporter:
    """Test suite for project history import functionality."""

    def test_importer_initialization(self):
        """Test that importer initializes correctly."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            importer = ProjectHistoryImporter(memory_handler=mock_memory.return_value)
            assert importer.memory_handler is not None

    def test_import_from_json(self, temp_dir):
        """Test importing project history from JSON format."""
        # Create test JSON file
        test_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "total_entries": 2,
                "format_version": "1.0",
            },
            "entries": [
                {
                    "id": "import_test1",
                    "timestamp": datetime.now().timestamp(),
                    "event_type": "feature_addition",
                    "file_path": "src/imported.py",
                    "summary": "Imported feature",
                    "content": "This is imported content",
                    "metadata": {"lines_added": 10},
                },
                {
                    "id": "import_test2",
                    "timestamp": datetime.now().timestamp() - 3600,
                    "event_type": "bug_fix",
                    "file_path": "src/fixed.py",
                    "summary": "Imported bug fix",
                    "content": "This is imported bug fix",
                    "metadata": {"lines_added": 2, "lines_removed": 1},
                },
            ],
        }

        import_path = temp_dir / "import.json"
        with open(import_path, "w") as f:
            json.dump(test_data, f)

        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value

            importer = ProjectHistoryImporter(memory_handler=mock_memory_instance)

            # Test JSON import
            result = importer.import_from_json(str(import_path))

            assert result["success"] is True
            assert result["entries_imported"] == 2
            assert "import_duration" in result

    def test_import_from_git_log(self, temp_dir):
        """Test importing project history from git log."""
        # Create mock git log output
        git_log_content = """commit abc123def456
Author: Developer <dev@example.com>
Date: Mon Jan 1 12:00:00 2024 +0000

    Add authentication feature

    Implemented JWT-based authentication system with login/logout functionality

 src/auth.py       | 45 ++++++++++++++++++++++++++++++++++++++++++++
 src/routes.py     |  5 +++++
 tests/test_auth.py| 20 ++++++++++++++++++++
 3 files changed, 70 insertions(+)

commit def456ghi789
Author: Developer <dev@example.com>
Date: Sun Dec 31 10:30:00 2023 +0000

    Fix database connection issue

    Resolved timeout problems with database connections

 src/database.py | 8 ++++----
 1 file changed, 4 insertions(+), 4 deletions(-)
"""

        git_log_path = temp_dir / "git.log"
        with open(git_log_path, "w") as f:
            f.write(git_log_content)

        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value

            importer = ProjectHistoryImporter(memory_handler=mock_memory_instance)

            # Test git log import
            result = importer.import_from_git_log(str(git_log_path))

            assert result["success"] is True
            assert result["entries_imported"] >= 2
            assert "import_duration" in result

    def test_import_validation_and_deduplication(self, temp_dir):
        """Test import validation and duplicate entry handling."""
        # Create test data with duplicate IDs
        test_data = {
            "metadata": {"export_timestamp": datetime.now().isoformat()},
            "entries": [
                {
                    "id": "duplicate_test",
                    "timestamp": datetime.now().timestamp(),
                    "event_type": "feature_addition",
                    "file_path": "src/test.py",
                    "summary": "Test entry 1",
                },
                {
                    "id": "duplicate_test",  # Same ID - should be deduplicated
                    "timestamp": datetime.now().timestamp() - 1000,
                    "event_type": "bug_fix",
                    "file_path": "src/test.py",
                    "summary": "Test entry 2",
                },
                {
                    # Missing required fields - should be rejected
                    "id": "invalid_entry",
                    "timestamp": datetime.now().timestamp(),
                },
            ],
        }

        import_path = temp_dir / "import_validation.json"
        with open(import_path, "w") as f:
            json.dump(test_data, f)

        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value

            importer = ProjectHistoryImporter(memory_handler=mock_memory_instance)

            # Test import with validation
            result = importer.import_from_json(str(import_path))

            assert result["success"] is True
            assert result["entries_imported"] == 1  # Only 1 valid, unique entry
            assert result["entries_skipped"] == 2  # 1 duplicate + 1 invalid
            assert "validation_errors" in result


class TestProjectHistoryConfigurationIntegration:
    """Test suite for project history configuration integration."""

    def test_settings_file_management(self, temp_dir):
        """Test loading and saving settings to configuration file."""
        settings_file = temp_dir / "project_history_settings.json"

        # Test saving settings
        settings = ProjectHistorySettings(
            enabled=True,
            retention_days=180,
            max_entries=5000,
        )
        settings.save_to_file(str(settings_file))

        assert settings_file.exists()

        # Test loading settings
        loaded_settings = ProjectHistorySettings.load_from_file(str(settings_file))
        assert loaded_settings.enabled is True
        assert loaded_settings.retention_days == 180
        assert loaded_settings.max_entries == 5000

    def test_settings_migration(self, temp_dir):
        """Test settings migration from older versions."""
        # Create old format settings file
        old_settings = {
            "enabled": True,
            "retention_days": 365,
            # Missing newer fields like max_entries, enable_archiving, etc.
        }

        settings_file = temp_dir / "old_settings.json"
        with open(settings_file, "w") as f:
            json.dump(old_settings, f)

        # Test migration
        settings = ProjectHistorySettings.load_from_file(str(settings_file))
        assert settings.enabled is True
        assert settings.retention_days == 365
        assert settings.max_entries == 10000  # Should use default value
        assert settings.enable_archiving is True  # Should use default value

    def test_comprehensive_workflow(self, temp_dir, mock_project_events):
        """Test complete workflow: settings, cleanup, export, import."""
        with mock.patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_memory:
            mock_memory_instance = mock_memory.return_value
            mock_memory_instance.get_project_history.return_value = mock_project_events

            # 1. Create and configure settings
            settings = ProjectHistorySettings(
                retention_days=300,
                enable_auto_cleanup=True,
                enable_archiving=True,
            )

            # 2. Initialize manager
            manager = ProjectHistoryManager(
                memory_handler=mock_memory_instance, settings=settings
            )

            # 3. Run cleanup and archiving
            cleanup_result = manager.cleanup_old_entries()
            assert cleanup_result["success"] is True

            # 4. Export data
            exporter = ProjectHistoryExporter(memory_handler=mock_memory_instance)
            export_path = temp_dir / "workflow_export.json"
            export_result = exporter.export_to_json(str(export_path))
            assert export_result["success"] is True

            # 5. Import data (simulating restore)
            importer = ProjectHistoryImporter(memory_handler=mock_memory_instance)
            import_result = importer.import_from_json(str(export_path))
            assert import_result["success"] is True
