"""
Project event recording system for tracking and categorizing project changes.

This module provides comprehensive project event recording including:
- Event creation and categorization
- Automatic event classification based on file patterns and content
- Integration with ChromaDB storage system
- Manual event annotation interface
- Event type support and validation
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from my_coding_agent.core.file_change_detector import (
    ChangeType,
    FileChangeEvent,
    FileChangeFilter,
)
from my_coding_agent.core.memory.memory_types import ProjectHistory

logger = logging.getLogger(__name__)


class ProjectEventType(Enum):
    """Types of project events that can be recorded."""

    FILE_MODIFICATION = "file_modification"
    FILE_CREATION = "file_creation"
    FILE_DELETION = "file_deletion"
    FEATURE_ADDITION = "feature_addition"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    ARCHITECTURE_CHANGE = "architecture_change"
    DEPENDENCY_UPDATE = "dependency_update"
    CONFIGURATION_CHANGE = "configuration_change"


@dataclass
class ProjectEvent:
    """Represents a project event with metadata and classification."""

    event_type: ProjectEventType
    description: str
    timestamp: float = field(default_factory=time.time)
    file_path: Path | None = None
    change_summary: str | None = None
    auto_classified: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_project_history(self) -> ProjectHistory:
        """Convert to ProjectHistory model for storage."""
        return ProjectHistory(
            event_type=self.event_type.value,
            description=self.description,
            file_path=str(self.file_path) if self.file_path else None,
            code_changes=self.change_summary,
            metadata=self.metadata.copy(),
        )


class EventClassifier:
    """Automatic event classification system based on file patterns and content."""

    def __init__(self):
        """Initialize the event classifier with pattern rules."""
        self.file_patterns = {
            ProjectEventType.DEPENDENCY_UPDATE: [
                r".*requirements\.txt$",
                r".*setup\.py$",
                r".*Pipfile$",
                r".*package\.json$",
                r".*yarn\.lock$",
                r".*package-lock\.json$",
                r".*Gemfile$",
                r".*go\.mod$",
                r".*cargo\.toml$",
            ],
            ProjectEventType.CONFIGURATION_CHANGE: [
                r".*pyproject\.toml$",
                r".*setup\.cfg$",
                r".*\.ini$",
                r".*\.cfg$",
                r".*\.config$",
                r".*\.conf$",
                r".*\.yaml$",
                r".*\.yml$",
                r".*\.json$",
                r".*dockerfile$",
                r".*\.env.*$",
            ],
        }

        self.content_patterns = {
            ProjectEventType.BUG_FIX: [
                r"(?i)fix(ed|es)?.*bug",
                r"(?i)fix(ed|es)?.*issue",
                r"(?i)fix(ed|es)?.*error",
                r"(?i)fix(ed|es)?.*crash",
                r"(?i)fix(ed|es)?.*leak",
                r"(?i)resolve(d|s)?.*bug",
                r"(?i)patch.*bug",
                r"(?i)correct.*bug",
            ],
            ProjectEventType.FEATURE_ADDITION: [
                r"(?i)add(ed|s)?.*feature",
                r"(?i)new.*feature",
                r"(?i)implement(ed|s)?.*feature",
                r"(?i)add(ed|s)?.*functionality",
                r"(?i)introduce(d|s)?.*feature",
                r"(?i)create(d|s)?.*feature",
                r"(?i)add(ed|s)?.*(dashboard|component|module|system|interface)",
                r"(?i)new.*(dashboard|component|module|system|interface)",
                r"(?i)implement(ed|s)?.*(dashboard|component|module|system|interface)",
            ],
            ProjectEventType.REFACTORING: [
                r"(?i)refactor(ed|s)?",
                r"(?i)restructure(d|s)?",
                r"(?i)reorganize(d|s)?",
                r"(?i)clean.*up",
                r"(?i)improve.*structure",
                r"(?i)optimize(d|s)?.*code",
            ],
            ProjectEventType.ARCHITECTURE_CHANGE: [
                r"(?i)architect(ure|ural).*change",
                r"(?i)major.*refactor",
                r"(?i)redesign(ed|s)?",
                r"(?i)restructure.*entire",
                r"(?i)migrate.*architecture",
            ],
        }

    def classify_by_file_path(self, file_path: Path) -> ProjectEventType:
        """Classify event based on file path patterns."""
        file_str = str(file_path).lower()

        for event_type, patterns in self.file_patterns.items():
            for pattern in patterns:
                if re.search(pattern, file_str):
                    return event_type

        # Default to file modification
        return ProjectEventType.FILE_MODIFICATION

    def classify_by_content(self, content: str) -> ProjectEventType:
        """Classify event based on content patterns."""
        if not content:
            return ProjectEventType.FILE_MODIFICATION

        content_lower = content.lower()

        for event_type, patterns in self.content_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return event_type

        # Default to file modification
        return ProjectEventType.FILE_MODIFICATION

    def classify_change_event(self, change_event: FileChangeEvent) -> ProjectEventType:
        """Classify a FileChangeEvent comprehensively."""
        # First check for basic file operations
        if change_event.change_type == ChangeType.CREATED:
            return ProjectEventType.FILE_CREATION
        elif change_event.change_type == ChangeType.DELETED:
            return ProjectEventType.FILE_DELETION

        # For modifications, check file patterns first
        file_classification = self.classify_by_file_path(change_event.file_path)
        if file_classification != ProjectEventType.FILE_MODIFICATION:
            return file_classification

        # Then check content patterns
        content_to_analyze = ""
        if change_event.new_content:
            content_to_analyze += change_event.new_content
        if change_event.old_content:
            content_to_analyze += " " + change_event.old_content

        if content_to_analyze:
            content_classification = self.classify_by_content(content_to_analyze)
            if content_classification != ProjectEventType.FILE_MODIFICATION:
                return content_classification

        # Default to file modification
        return ProjectEventType.FILE_MODIFICATION


class ProjectEventRecorder(QObject):
    """Main project event recorder that coordinates event capture and storage."""

    # Qt signals
    event_recorded = pyqtSignal(ProjectEvent)

    def __init__(
        self, chroma_engine: Any, project_root: Path, parent: QObject | None = None
    ):
        """Initialize the project event recorder.

        Args:
            chroma_engine: ChromaRAGEngine instance for storage
            project_root: Root directory of the project
            parent: Optional Qt parent object
        """
        super().__init__(parent)

        self.chroma_engine = chroma_engine
        self.project_root = project_root
        self.enabled = True

        # Initialize components
        self.classifier = EventClassifier()
        self.file_filter = FileChangeFilter()
        self.event_history: list[ProjectEvent] = []

    def record_file_change(self, change_event: FileChangeEvent) -> ProjectEvent | None:
        """Record a file change event.

        Args:
            change_event: FileChangeEvent to record

        Returns:
            ProjectEvent if recorded, None if ignored or disabled
        """
        if not self.enabled:
            return None

        # Check if file should be ignored
        if self.file_filter.should_ignore(change_event.file_path):
            return None

        # Classify the event
        event_type = self.classifier.classify_change_event(change_event)

        # Create project event
        project_event = ProjectEvent(
            event_type=event_type,
            description=f"{event_type.value.replace('_', ' ').title()} in {change_event.file_path.name}",
            file_path=change_event.file_path,
            change_summary=self._generate_change_summary(change_event),
            auto_classified=True,
            metadata={
                "change_type": change_event.change_type.value,
                "timestamp": change_event.timestamp,
                "original_metadata": change_event.metadata,
            },
        )

        # Store the event
        self._store_event(project_event)

        return project_event

    def record_manual_event(
        self,
        event_type: ProjectEventType,
        description: str,
        file_path: Path | None = None,
        change_summary: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProjectEvent | None:
        """Record a manual event annotation.

        Args:
            event_type: Type of event
            description: Event description
            file_path: Optional file path
            change_summary: Optional change summary
            metadata: Optional metadata

        Returns:
            ProjectEvent if recorded, None if disabled
        """
        if not self.enabled:
            return None

        project_event = ProjectEvent(
            event_type=event_type,
            description=description,
            file_path=file_path,
            change_summary=change_summary,
            auto_classified=False,
            metadata=metadata or {},
        )

        # Store the event
        self._store_event(project_event)

        return project_event

    def get_event_history(
        self, event_type: ProjectEventType | None = None
    ) -> list[ProjectEvent]:
        """Get event history, optionally filtered by type.

        Args:
            event_type: Optional event type filter

        Returns:
            List of project events
        """
        if event_type is None:
            return self.event_history.copy()

        return [event for event in self.event_history if event.event_type == event_type]

    def get_events_for_file(self, file_path: Path) -> list[ProjectEvent]:
        """Get events for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            List of events for the file
        """
        return [event for event in self.event_history if event.file_path == file_path]

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable event recording.

        Args:
            enabled: Whether to enable recording
        """
        self.enabled = enabled

    def get_event_statistics(self) -> dict[str, Any]:
        """Get statistics about recorded events.

        Returns:
            Dictionary with event statistics
        """
        stats = {
            "total_events": len(self.event_history),
            "events_by_type": {},
            "auto_classified_count": 0,
            "manual_events_count": 0,
        }

        for event in self.event_history:
            # Count by type
            event_type_str = event.event_type.value
            stats["events_by_type"][event_type_str] = (
                stats["events_by_type"].get(event_type_str, 0) + 1
            )

            # Count classification type
            if event.auto_classified:
                stats["auto_classified_count"] += 1
            else:
                stats["manual_events_count"] += 1

        return stats

    def connect_to_file_change_detector(self, detector: Any) -> None:
        """Connect to a FileChangeDetector to receive change events.

        Args:
            detector: FileChangeDetector instance
        """
        detector.file_changed.connect(self._handle_file_change)

    def _handle_file_change(self, change_event: FileChangeEvent) -> ProjectEvent | None:
        """Handle file change signal from detector.

        Args:
            change_event: FileChangeEvent from detector

        Returns:
            ProjectEvent if recorded, None if ignored
        """
        return self.record_file_change(change_event)

    def _store_event(self, project_event: ProjectEvent) -> None:
        """Store a project event in local history and ChromaDB.

        Args:
            project_event: Event to store
        """
        # Add to local history
        self.event_history.append(project_event)

        # Store in ChromaDB
        try:
            project_history = project_event.to_project_history()
            content = f"{project_history.description}"
            if project_history.code_changes:
                content += f"\n\nChanges: {project_history.code_changes}"

            self.chroma_engine.store_project_history_with_embedding(
                file_path=project_history.file_path or "",
                event_type=project_history.event_type,
                content=content,
            )
        except Exception as e:
            logger.error(f"Failed to store project event in ChromaDB: {e}")

        # Emit signal
        self.event_recorded.emit(project_event)

    def _generate_change_summary(self, change_event: FileChangeEvent) -> str:
        """Generate a summary of the change.

        Args:
            change_event: FileChangeEvent to summarize

        Returns:
            Summary string
        """
        if change_event.change_type == ChangeType.CREATED:
            return f"Created new file: {change_event.file_path.name}"
        elif change_event.change_type == ChangeType.DELETED:
            return f"Deleted file: {change_event.file_path.name}"
        elif change_event.change_type == ChangeType.MODIFIED:
            # Try to extract meaningful info from content
            if hasattr(change_event, "metadata") and change_event.metadata:
                metadata = change_event.metadata
                if "lines_added" in metadata or "lines_removed" in metadata:
                    lines_added = metadata.get("lines_added", 0)
                    lines_removed = metadata.get("lines_removed", 0)
                    return f"Modified {change_event.file_path.name}: +{lines_added} -{lines_removed} lines"

            return f"Modified file: {change_event.file_path.name}"
        else:
            return f"Changed file: {change_event.file_path.name}"


class ManualAnnotationInterface:
    """Interface for creating manual event annotations."""

    def __init__(self, chroma_engine: Any):
        """Initialize the manual annotation interface.

        Args:
            chroma_engine: ChromaRAGEngine instance for storage
        """
        self.chroma_engine = chroma_engine

    def create_annotation(
        self,
        event_type: ProjectEventType | None,
        description: str,
        file_path: Path | None = None,
        change_summary: str | None = None,
        rationale: str | None = None,
        impact_assessment: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProjectEvent:
        """Create a manual annotation.

        Args:
            event_type: Type of event
            description: Event description
            file_path: Optional file path
            change_summary: Optional change summary
            rationale: Optional rationale
            impact_assessment: Optional impact assessment
            metadata: Optional additional metadata

        Returns:
            ProjectEvent created

        Raises:
            ValueError: If required fields are missing
        """
        if event_type is None:
            raise ValueError("Event type is required")
        if not description:
            raise ValueError("Description is required")

        # Build metadata
        full_metadata = metadata or {}
        if rationale:
            full_metadata["rationale"] = rationale
        if impact_assessment:
            full_metadata["impact_assessment"] = impact_assessment

        # Create project event
        project_event = ProjectEvent(
            event_type=event_type,
            description=description,
            file_path=file_path,
            change_summary=change_summary,
            auto_classified=False,
            metadata=full_metadata,
        )

        # Store in ChromaDB
        try:
            project_history = project_event.to_project_history()
            content = f"{project_history.description}"
            if project_history.code_changes:
                content += f"\n\nChanges: {project_history.code_changes}"
            if rationale:
                content += f"\n\nRationale: {rationale}"
            if impact_assessment:
                content += f"\n\nImpact: {impact_assessment}"

            self.chroma_engine.store_project_history_with_embedding(
                file_path=project_history.file_path or "",
                event_type=project_history.event_type,
                content=content,
            )
        except Exception as e:
            logger.error(f"Failed to store manual annotation in ChromaDB: {e}")

        return project_event

    def create_batch_annotations(
        self, annotations_data: list[dict[str, Any]]
    ) -> list[ProjectEvent]:
        """Create multiple annotations in batch.

        Args:
            annotations_data: List of annotation data dictionaries

        Returns:
            List of created ProjectEvents
        """
        annotations = []

        for data in annotations_data:
            annotation = self.create_annotation(**data)
            annotations.append(annotation)

        return annotations
