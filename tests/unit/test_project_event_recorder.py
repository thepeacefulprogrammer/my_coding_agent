"""Unit tests for ProjectEventRecorder - Project event recording system.

Tests cover:
- Event creation and categorization
- Automatic event classification based on file patterns and content
- Integration with ChromaDB storage system
- Manual event annotation interface
- Event type support and validation
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt6.QtCore import QObject

from my_coding_agent.core.file_change_detector import ChangeType, FileChangeEvent
from my_coding_agent.core.memory.memory_types import ProjectHistory


class TestProjectEventTypes:
    """Test event type definitions and validation."""

    def test_event_type_enum_values(self):
        """Test that event type enum contains expected values."""
        from my_coding_agent.core.project_event_recorder import ProjectEventType

        expected_types = {
            "FILE_MODIFICATION",
            "FILE_CREATION",
            "FILE_DELETION",
            "FEATURE_ADDITION",
            "BUG_FIX",
            "REFACTORING",
            "ARCHITECTURE_CHANGE",
            "DEPENDENCY_UPDATE",
            "CONFIGURATION_CHANGE",
        }

        actual_types = {item.name for item in ProjectEventType}
        assert actual_types == expected_types

    def test_event_type_values(self):
        """Test that event type enum values match expected strings."""
        from my_coding_agent.core.project_event_recorder import ProjectEventType

        assert ProjectEventType.FILE_MODIFICATION.value == "file_modification"
        assert ProjectEventType.FEATURE_ADDITION.value == "feature_addition"
        assert ProjectEventType.BUG_FIX.value == "bug_fix"
        assert ProjectEventType.REFACTORING.value == "refactoring"


class TestProjectEvent:
    """Test ProjectEvent data model."""

    def test_project_event_creation(self):
        """Test basic ProjectEvent creation."""
        from my_coding_agent.core.project_event_recorder import (
            ProjectEvent,
            ProjectEventType,
        )

        event = ProjectEvent(
            event_type=ProjectEventType.FILE_MODIFICATION,
            file_path=Path("test.py"),
            description="Modified test.py",
            change_summary="Added new function",
            metadata={"lines_added": 10},
        )

        assert event.event_type == ProjectEventType.FILE_MODIFICATION
        assert event.file_path == Path("test.py")
        assert event.description == "Modified test.py"
        assert event.change_summary == "Added new function"
        assert event.metadata["lines_added"] == 10
        assert event.timestamp > 0
        assert event.auto_classified is True  # Default value

    def test_project_event_with_manual_annotation(self):
        """Test ProjectEvent with manual annotation."""
        from my_coding_agent.core.project_event_recorder import (
            ProjectEvent,
            ProjectEventType,
        )

        event = ProjectEvent(
            event_type=ProjectEventType.ARCHITECTURE_CHANGE,
            file_path=Path("src/main.py"),
            description="Refactored main architecture",
            change_summary="Split monolithic class into modules",
            auto_classified=False,
            metadata={"manual_annotation": "This was a major architectural decision"},
        )

        assert event.auto_classified is False
        assert (
            event.metadata["manual_annotation"]
            == "This was a major architectural decision"
        )

    def test_project_event_to_project_history(self):
        """Test conversion to ProjectHistory model."""
        from my_coding_agent.core.project_event_recorder import (
            ProjectEvent,
            ProjectEventType,
        )

        event = ProjectEvent(
            event_type=ProjectEventType.FEATURE_ADDITION,
            file_path=Path("features/new_feature.py"),
            description="Added new feature",
            change_summary="Implemented user authentication",
            metadata={"complexity": "high"},
        )

        project_history = event.to_project_history()

        assert isinstance(project_history, ProjectHistory)
        assert project_history.event_type == "feature_addition"
        assert project_history.file_path == "features/new_feature.py"
        assert project_history.description == "Added new feature"
        assert project_history.code_changes == "Implemented user authentication"
        assert project_history.metadata["complexity"] == "high"


class TestEventClassifier:
    """Test automatic event classification system."""

    def test_classifier_initialization(self):
        """Test EventClassifier initialization."""
        from my_coding_agent.core.project_event_recorder import EventClassifier

        classifier = EventClassifier()

        # Check that classification patterns are loaded
        assert hasattr(classifier, "file_patterns")
        assert hasattr(classifier, "content_patterns")
        assert isinstance(classifier.file_patterns, dict)
        assert isinstance(classifier.content_patterns, dict)

    def test_classify_by_file_pattern(self):
        """Test classification based on file patterns."""
        from my_coding_agent.core.project_event_recorder import (
            EventClassifier,
            ProjectEventType,
        )

        classifier = EventClassifier()

        # Test configuration files
        event_type = classifier.classify_by_file_path(Path("requirements.txt"))
        assert event_type == ProjectEventType.DEPENDENCY_UPDATE

        event_type = classifier.classify_by_file_path(Path("setup.py"))
        assert event_type == ProjectEventType.DEPENDENCY_UPDATE

        event_type = classifier.classify_by_file_path(Path("pyproject.toml"))
        assert event_type == ProjectEventType.CONFIGURATION_CHANGE

    def test_classify_by_content_patterns(self):
        """Test classification based on content patterns."""
        from my_coding_agent.core.project_event_recorder import (
            EventClassifier,
            ProjectEventType,
        )

        classifier = EventClassifier()

        # Test bug fix patterns
        change_summary = "Fixed memory leak in cache implementation"
        event_type = classifier.classify_by_content(change_summary)
        assert event_type == ProjectEventType.BUG_FIX

        # Test feature addition patterns
        change_summary = "Added new user dashboard with analytics"
        event_type = classifier.classify_by_content(change_summary)
        assert event_type == ProjectEventType.FEATURE_ADDITION

        # Test refactoring patterns
        change_summary = "Refactored database connection handling"
        event_type = classifier.classify_by_content(change_summary)
        assert event_type == ProjectEventType.REFACTORING

    def test_classify_file_change_event(self):
        """Test classification of FileChangeEvent."""
        from my_coding_agent.core.project_event_recorder import (
            EventClassifier,
            ProjectEventType,
        )

        classifier = EventClassifier()

        # Test file creation
        change_event = FileChangeEvent(
            file_path=Path("new_feature.py"),
            change_type=ChangeType.CREATED,
            new_content="def new_feature():\n    return 'Hello World'",
        )

        event_type = classifier.classify_change_event(change_event)
        assert event_type == ProjectEventType.FILE_CREATION

        # Test file modification with bug fix content
        change_event = FileChangeEvent(
            file_path=Path("bug_fix.py"),
            change_type=ChangeType.MODIFIED,
            old_content="buggy_function()",
            new_content="fixed_function()  # Fixed null pointer bug",
        )

        event_type = classifier.classify_change_event(change_event)
        assert event_type == ProjectEventType.BUG_FIX

    def test_default_classification(self):
        """Test default classification for unrecognized patterns."""
        from my_coding_agent.core.project_event_recorder import (
            EventClassifier,
            ProjectEventType,
        )

        classifier = EventClassifier()

        # Test unknown file type
        event_type = classifier.classify_by_file_path(Path("unknown.xyz"))
        assert event_type == ProjectEventType.FILE_MODIFICATION

        # Test unknown content pattern
        event_type = classifier.classify_by_content("Some random content")
        assert event_type == ProjectEventType.FILE_MODIFICATION


class TestProjectEventRecorder:
    """Test main ProjectEventRecorder class."""

    @pytest.fixture
    def mock_chroma_engine(self):
        """Create mock ChromaRAGEngine."""
        mock_engine = Mock()
        mock_engine.store_project_history_with_embedding = Mock(
            return_value="test_doc_id"
        )
        return mock_engine

    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_recorder_initialization(self, mock_chroma_engine):
        """Test ProjectEventRecorder initialization."""
        from my_coding_agent.core.project_event_recorder import ProjectEventRecorder

        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine, project_root=Path("/test/project")
        )

        assert recorder.chroma_engine == mock_chroma_engine
        assert recorder.project_root == Path("/test/project")
        assert recorder.enabled is True
        assert hasattr(recorder, "classifier")
        assert hasattr(recorder, "event_history")

    def test_recorder_initialization_with_parent(self, mock_chroma_engine):
        """Test ProjectEventRecorder initialization with Qt parent."""
        from my_coding_agent.core.project_event_recorder import ProjectEventRecorder

        parent = QObject()
        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine,
            project_root=Path("/test/project"),
            parent=parent,
        )

        assert recorder.parent() == parent

    def test_record_file_change_event(self, mock_chroma_engine, temp_directory):
        """Test recording a file change event."""
        from my_coding_agent.core.project_event_recorder import ProjectEventRecorder

        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine, project_root=temp_directory
        )

        change_event = FileChangeEvent(
            file_path=temp_directory / "test.py",
            change_type=ChangeType.MODIFIED,
            old_content="old content",
            new_content="new content with bug fix",
        )

        project_event = recorder.record_file_change(change_event)

        assert project_event is not None
        assert project_event.file_path == temp_directory / "test.py"
        assert project_event.auto_classified is True
        assert len(recorder.event_history) == 1

        # Verify storage was called
        mock_chroma_engine.store_project_history_with_embedding.assert_called_once()

    def test_record_manual_event(self, mock_chroma_engine, temp_directory):
        """Test recording a manual event annotation."""
        from my_coding_agent.core.project_event_recorder import (
            ProjectEventRecorder,
            ProjectEventType,
        )

        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine, project_root=temp_directory
        )

        project_event = recorder.record_manual_event(
            event_type=ProjectEventType.ARCHITECTURE_CHANGE,
            description="Refactored entire authentication system",
            file_path=temp_directory / "auth.py",
            change_summary="Moved from session-based to JWT authentication",
            metadata={"impact": "high", "breaking_change": True},
        )

        assert project_event is not None
        assert project_event.event_type == ProjectEventType.ARCHITECTURE_CHANGE
        assert project_event.auto_classified is False
        assert project_event.metadata["impact"] == "high"
        assert project_event.metadata["breaking_change"] is True
        assert len(recorder.event_history) == 1

        # Verify storage was called
        mock_chroma_engine.store_project_history_with_embedding.assert_called_once()

    def test_get_event_history(self, mock_chroma_engine, temp_directory):
        """Test retrieving event history."""
        from my_coding_agent.core.project_event_recorder import (
            ProjectEventRecorder,
            ProjectEventType,
        )

        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine, project_root=temp_directory
        )

        # Record multiple events
        recorder.record_manual_event(
            event_type=ProjectEventType.FEATURE_ADDITION,
            description="Added user dashboard",
        )

        recorder.record_manual_event(
            event_type=ProjectEventType.BUG_FIX, description="Fixed login issue"
        )

        # Test getting all history
        history = recorder.get_event_history()
        assert len(history) == 2

        # Test getting filtered history
        bug_fixes = recorder.get_event_history(event_type=ProjectEventType.BUG_FIX)
        assert len(bug_fixes) == 1
        assert bug_fixes[0].event_type == ProjectEventType.BUG_FIX

    def test_get_events_for_file(self, mock_chroma_engine, temp_directory):
        """Test retrieving events for specific file."""
        from my_coding_agent.core.project_event_recorder import (
            ProjectEventRecorder,
            ProjectEventType,
        )

        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine, project_root=temp_directory
        )

        test_file = temp_directory / "test.py"
        other_file = temp_directory / "other.py"

        # Record events for different files
        recorder.record_manual_event(
            event_type=ProjectEventType.FEATURE_ADDITION,
            description="Added feature to test.py",
            file_path=test_file,
        )

        recorder.record_manual_event(
            event_type=ProjectEventType.BUG_FIX,
            description="Fixed bug in other.py",
            file_path=other_file,
        )

        recorder.record_manual_event(
            event_type=ProjectEventType.REFACTORING,
            description="Refactored test.py",
            file_path=test_file,
        )

        # Test getting events for specific file
        test_file_events = recorder.get_events_for_file(test_file)
        assert len(test_file_events) == 2

        event_types = {event.event_type for event in test_file_events}
        assert ProjectEventType.FEATURE_ADDITION in event_types
        assert ProjectEventType.REFACTORING in event_types

    def test_enable_disable_recording(self, mock_chroma_engine, temp_directory):
        """Test enabling and disabling event recording."""
        from my_coding_agent.core.project_event_recorder import (
            ProjectEventRecorder,
            ProjectEventType,
        )

        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine, project_root=temp_directory
        )

        # Disable recording
        recorder.set_enabled(False)
        assert recorder.enabled is False

        # Try to record an event
        project_event = recorder.record_manual_event(
            event_type=ProjectEventType.FEATURE_ADDITION,
            description="This should not be recorded",
        )

        assert project_event is None
        assert len(recorder.event_history) == 0
        mock_chroma_engine.store_project_history_with_embedding.assert_not_called()

        # Re-enable recording
        recorder.set_enabled(True)
        assert recorder.enabled is True

        # Record an event
        project_event = recorder.record_manual_event(
            event_type=ProjectEventType.FEATURE_ADDITION,
            description="This should be recorded",
        )

        assert project_event is not None
        assert len(recorder.event_history) == 1

    def test_error_handling_storage_failure(self, mock_chroma_engine, temp_directory):
        """Test error handling when storage fails."""
        from my_coding_agent.core.project_event_recorder import (
            ProjectEventRecorder,
            ProjectEventType,
        )

        # Make storage raise an exception
        mock_chroma_engine.store_project_history_with_embedding.side_effect = Exception(
            "Storage failed"
        )

        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine, project_root=temp_directory
        )

        # Record an event - should handle the error gracefully
        project_event = recorder.record_manual_event(
            event_type=ProjectEventType.FEATURE_ADDITION, description="Test event"
        )

        # Event should still be created and stored in local history
        assert project_event is not None
        assert len(recorder.event_history) == 1

        # Storage should have been attempted
        mock_chroma_engine.store_project_history_with_embedding.assert_called_once()

    def test_event_statistics(self, mock_chroma_engine, temp_directory):
        """Test event statistics collection."""
        from my_coding_agent.core.project_event_recorder import (
            ProjectEventRecorder,
            ProjectEventType,
        )

        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine, project_root=temp_directory
        )

        # Record various types of events
        recorder.record_manual_event(
            event_type=ProjectEventType.FEATURE_ADDITION, description="Feature 1"
        )
        recorder.record_manual_event(
            event_type=ProjectEventType.FEATURE_ADDITION, description="Feature 2"
        )
        recorder.record_manual_event(
            event_type=ProjectEventType.BUG_FIX, description="Bug fix 1"
        )

        stats = recorder.get_event_statistics()

        assert stats["total_events"] == 3
        assert stats["events_by_type"][ProjectEventType.FEATURE_ADDITION.value] == 2
        assert stats["events_by_type"][ProjectEventType.BUG_FIX.value] == 1
        assert stats["auto_classified_count"] == 0  # All manual events
        assert stats["manual_events_count"] == 3


class TestManualAnnotationInterface:
    """Test manual event annotation interface."""

    @pytest.fixture
    def mock_chroma_engine(self):
        """Create mock ChromaRAGEngine."""
        mock_engine = Mock()
        mock_engine.store_project_history_with_embedding = Mock(
            return_value="test_doc_id"
        )
        return mock_engine

    def test_annotation_interface_initialization(self, mock_chroma_engine):
        """Test manual annotation interface initialization."""
        from my_coding_agent.core.project_event_recorder import (
            ManualAnnotationInterface,
        )

        interface = ManualAnnotationInterface(chroma_engine=mock_chroma_engine)

        assert interface.chroma_engine == mock_chroma_engine
        assert hasattr(interface, "create_annotation")

    def test_create_manual_annotation(self, mock_chroma_engine):
        """Test creating manual annotations."""
        from my_coding_agent.core.project_event_recorder import (
            ManualAnnotationInterface,
            ProjectEventType,
        )

        interface = ManualAnnotationInterface(chroma_engine=mock_chroma_engine)

        annotation = interface.create_annotation(
            event_type=ProjectEventType.ARCHITECTURE_CHANGE,
            description="Major refactor of data layer",
            rationale="Needed better separation of concerns",
            impact_assessment="High impact, affects all modules",
            metadata={"reviewer": "senior_dev", "approved": True},
        )

        assert annotation is not None
        assert annotation.event_type == ProjectEventType.ARCHITECTURE_CHANGE
        assert annotation.description == "Major refactor of data layer"
        assert annotation.auto_classified is False
        assert (
            annotation.metadata["rationale"] == "Needed better separation of concerns"
        )
        assert (
            annotation.metadata["impact_assessment"]
            == "High impact, affects all modules"
        )
        assert annotation.metadata["reviewer"] == "senior_dev"

    def test_annotation_validation(self, mock_chroma_engine):
        """Test annotation input validation."""
        from my_coding_agent.core.project_event_recorder import (
            ManualAnnotationInterface,
            ProjectEventType,
        )

        interface = ManualAnnotationInterface(chroma_engine=mock_chroma_engine)

        # Test with missing required fields
        with pytest.raises(ValueError, match="Event type is required"):
            interface.create_annotation(event_type=None, description="Test description")

        with pytest.raises(ValueError, match="Description is required"):
            interface.create_annotation(
                event_type=ProjectEventType.FEATURE_ADDITION, description=""
            )

    def test_batch_annotation_creation(self, mock_chroma_engine):
        """Test creating multiple annotations in batch."""
        from my_coding_agent.core.project_event_recorder import (
            ManualAnnotationInterface,
            ProjectEventType,
        )

        interface = ManualAnnotationInterface(chroma_engine=mock_chroma_engine)

        annotations_data = [
            {
                "event_type": ProjectEventType.FEATURE_ADDITION,
                "description": "Added user authentication",
                "file_path": Path("auth.py"),
            },
            {
                "event_type": ProjectEventType.BUG_FIX,
                "description": "Fixed memory leak",
                "file_path": Path("memory.py"),
            },
        ]

        annotations = interface.create_batch_annotations(annotations_data)

        assert len(annotations) == 2
        assert annotations[0].event_type == ProjectEventType.FEATURE_ADDITION
        assert annotations[1].event_type == ProjectEventType.BUG_FIX

        # Verify all were stored
        assert mock_chroma_engine.store_project_history_with_embedding.call_count == 2


class TestIntegrationWithFileChangeDetector:
    """Test integration with FileChangeDetector system."""

    @pytest.fixture
    def mock_chroma_engine(self):
        """Create mock ChromaRAGEngine."""
        mock_engine = Mock()
        mock_engine.store_project_history_with_embedding = Mock(
            return_value="test_doc_id"
        )
        return mock_engine

    def test_connect_to_file_change_detector(self, mock_chroma_engine):
        """Test connecting ProjectEventRecorder to FileChangeDetector."""
        from my_coding_agent.core.project_event_recorder import ProjectEventRecorder

        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine, project_root=Path("/test/project")
        )

        # Mock file change detector
        mock_detector = Mock()
        mock_detector.file_changed = Mock()
        mock_detector.file_changed.connect = Mock()

        # Connect to detector
        recorder.connect_to_file_change_detector(mock_detector)

        # Verify connection was made
        mock_detector.file_changed.connect.assert_called_once()

    def test_handle_file_change_signal(self, mock_chroma_engine):
        """Test handling file change signals from detector."""
        from my_coding_agent.core.project_event_recorder import ProjectEventRecorder

        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine, project_root=Path("/test/project")
        )

        # Create a file change event
        change_event = FileChangeEvent(
            file_path=Path("/test/project/src/main.py"),
            change_type=ChangeType.MODIFIED,
            old_content="old content",
            new_content="new content with improvements",
        )

        # Handle the change event
        project_event = recorder._handle_file_change(change_event)

        assert project_event is not None
        assert project_event.file_path == Path("/test/project/src/main.py")
        assert project_event.auto_classified is True
        assert len(recorder.event_history) == 1

    def test_filter_ignored_files(self, mock_chroma_engine):
        """Test filtering of ignored files."""
        from my_coding_agent.core.project_event_recorder import ProjectEventRecorder

        recorder = ProjectEventRecorder(
            chroma_engine=mock_chroma_engine, project_root=Path("/test/project")
        )

        # Test with ignored file
        change_event = FileChangeEvent(
            file_path=Path("/test/project/.git/config"), change_type=ChangeType.MODIFIED
        )

        project_event = recorder._handle_file_change(change_event)

        # Should be None for ignored files
        assert project_event is None
        assert len(recorder.event_history) == 0
        mock_chroma_engine.store_project_history_with_embedding.assert_not_called()
