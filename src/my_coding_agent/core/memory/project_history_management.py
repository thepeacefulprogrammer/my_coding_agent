#!/usr/bin/env python3
"""
Project history management and configuration system.

Provides comprehensive project history management capabilities including:
- Settings and configuration management for project history tracking
- ChromaDB-based cleanup operations for old project history entries
- Git log import functionality for migrating existing project history

This module focuses on ChromaDB-only storage, removing JSON archiving complexity
to maintain a clean, scalable architecture.
"""

import fnmatch
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from ..memory_integration import ConversationMemoryHandler

logger = logging.getLogger(__name__)


class ProjectHistorySettings(BaseModel):
    """Configuration settings for project history management."""

    # Core settings
    enabled: bool = Field(default=True, description="Enable project history tracking")
    retention_days: int = Field(
        default=365, description="Number of days to retain project history"
    )
    max_entries: int = Field(
        default=10000, description="Maximum number of entries to store"
    )

    # File filtering
    file_filters: list[str] = Field(
        default_factory=lambda: [
            "*.py",
            "*.js",
            "*.ts",
            "*.jsx",
            "*.tsx",
            "*.json",
            "*.md",
            "*.yaml",
            "*.yml",
            "*.toml",
            "*.ini",
            "*.cfg",
        ],
        description="File patterns to track",
    )
    exclude_patterns: list[str] = Field(
        default_factory=lambda: [
            "__pycache__/*",
            "node_modules/*",
            ".git/*",
            "*.pyc",
            "*.log",
            "*.tmp",
            ".DS_Store",
            "Thumbs.db",
            "*.egg-info/*",
        ],
        description="File patterns to exclude from tracking",
    )

    # Cleanup settings
    enable_auto_cleanup: bool = Field(
        default=True, description="Enable automatic cleanup"
    )
    cleanup_interval_hours: int = Field(
        default=24, description="Hours between automatic cleanup runs"
    )

    # Storage optimization
    max_content_length: int = Field(
        default=10000, description="Maximum content length to store"
    )

    @field_validator("retention_days")
    @classmethod
    def validate_retention_days(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("retention_days must be positive")
        return v

    @field_validator("max_entries")
    @classmethod
    def validate_max_entries(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_entries must be positive")
        return v

    @field_validator("cleanup_interval_hours")
    @classmethod
    def validate_cleanup_interval(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("cleanup_interval_hours must be positive")
        return v

    def should_track_file(self, file_path: str) -> bool:
        """Check if a file should be tracked based on filters."""
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return False

        # Check include patterns
        return any(fnmatch.fnmatch(file_path, pattern) for pattern in self.file_filters)


class ProjectHistoryManager:
    """Manages project history cleanup and configuration for ChromaDB storage."""

    def __init__(
        self,
        memory_handler: "ConversationMemoryHandler",
        settings: ProjectHistorySettings | None = None,
    ) -> None:
        """Initialize project history manager.

        Args:
            memory_handler: ConversationMemoryHandler instance for ChromaDB access
            settings: Configuration settings (creates defaults if None)
        """
        self.memory_handler = memory_handler
        self.settings = settings or ProjectHistorySettings()
        self._last_cleanup_time: datetime | None = None

        logger.info("Project history manager initialized")

    def should_run_cleanup(self) -> bool:
        """Check if cleanup should be run based on interval settings."""
        if not self.settings.enable_auto_cleanup:
            return False

        if self._last_cleanup_time is None:
            return True

        time_since_cleanup = datetime.now() - self._last_cleanup_time
        interval_delta = timedelta(hours=self.settings.cleanup_interval_hours)

        return time_since_cleanup >= interval_delta

    def cleanup_old_entries(self) -> dict[str, Any]:
        """Clean up old project history entries from ChromaDB.

        Uses ChromaDB's native capabilities for data management.

        Returns:
            Dictionary with cleanup results
        """
        start_time = datetime.now()

        try:
            if not self.settings.enabled:
                return {
                    "success": True,
                    "message": "Project history tracking disabled",
                    "entries_deleted": 0,
                }

            current_time = datetime.now().timestamp()
            retention_cutoff = current_time - (self.settings.retention_days * 24 * 3600)

            # Actually delete old entries from ChromaDB
            project_deleted = self.memory_handler.rag_engine.delete_old_project_history(
                retention_cutoff
            )

            # Update cleanup time
            self._last_cleanup_time = datetime.now()

            cleanup_duration = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Cleanup completed: {project_deleted} project history entries deleted"
            )

            return {
                "success": True,
                "entries_deleted": project_deleted,
                "cleanup_duration": cleanup_duration,
                "retention_cutoff": retention_cutoff,
                "message": f"ChromaDB cleanup completed - deleted {project_deleted} entries",
            }

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {
                "success": False,
                "error": str(e),
                "entries_deleted": 0,
                "cleanup_duration": (datetime.now() - start_time).total_seconds(),
            }

    def get_storage_statistics(self) -> dict[str, Any]:
        """Get comprehensive storage statistics for project history.

        Returns:
            Dictionary with storage statistics and analytics
        """
        try:
            all_entries = self.memory_handler.get_project_history(limit=10000)

            if not all_entries:
                return {
                    "total_entries": 0,
                    "storage_size_mb": 0,
                    "oldest_entry_age_days": 0,
                    "newest_entry_age_days": 0,
                    "entries_by_type": {},
                    "average_entry_size": 0,
                    "retention_compliance": 100.0,
                }

            current_time = datetime.now().timestamp()
            retention_cutoff = current_time - (self.settings.retention_days * 24 * 3600)

            # Calculate statistics
            timestamps = [entry.get("timestamp", current_time) for entry in all_entries]
            oldest_timestamp = min(timestamps)
            newest_timestamp = max(timestamps)

            oldest_age_days = (current_time - oldest_timestamp) / (24 * 3600)
            newest_age_days = (current_time - newest_timestamp) / (24 * 3600)

            # Count entries by type
            entries_by_type = {}
            total_content_size = 0
            entries_within_retention = 0

            for entry in all_entries:
                event_type = entry.get("event_type", "unknown")
                entries_by_type[event_type] = entries_by_type.get(event_type, 0) + 1

                # Estimate entry size
                entry_content = json.dumps(entry)
                total_content_size += len(entry_content)

                # Check retention compliance
                if entry.get("timestamp", current_time) >= retention_cutoff:
                    entries_within_retention += 1

            # Calculate retention compliance percentage
            retention_compliance = (entries_within_retention / len(all_entries)) * 100

            return {
                "total_entries": len(all_entries),
                "storage_size_mb": total_content_size / (1024 * 1024),
                "oldest_entry_age_days": oldest_age_days,
                "newest_entry_age_days": newest_age_days,
                "entries_by_type": entries_by_type,
                "average_entry_size": total_content_size / len(all_entries),
                "retention_compliance": retention_compliance,
                "settings": {
                    "retention_days": self.settings.retention_days,
                    "max_entries": self.settings.max_entries,
                    "auto_cleanup_enabled": self.settings.enable_auto_cleanup,
                },
            }

        except Exception as e:
            logger.error(f"Error getting storage statistics: {e}")
            return {
                "error": str(e),
                "total_entries": 0,
                "storage_size_mb": 0,
            }


class GitLogImporter:
    """Import project history from git logs."""

    def __init__(self, memory_handler: "ConversationMemoryHandler") -> None:
        """Initialize the importer.

        Args:
            memory_handler: ConversationMemoryHandler instance for data operations
        """
        self.memory_handler = memory_handler
        logger.info("Git log importer initialized")

    def import_from_git_log(self, git_log_path: str) -> dict[str, Any]:
        """Import project history from git log file.

        Args:
            git_log_path: Path to git log file

        Returns:
            Dictionary with import results
        """
        start_time = datetime.now()

        try:
            if not Path(git_log_path).exists():
                return {
                    "success": False,
                    "error": f"Git log file not found: {git_log_path}",
                    "entries_imported": 0,
                }

            # Read git log content
            with open(git_log_path, encoding="utf-8") as f:
                git_log_content = f.read()

            # Parse git log
            git_commits = self._parse_git_log(git_log_content)

            if not git_commits:
                return {
                    "success": False,
                    "error": "No valid commits found in git log",
                    "entries_imported": 0,
                }

            # Store each commit as project history
            imported_count = 0
            for commit in git_commits:
                try:
                    # Store in ChromaDB via memory handler
                    self.memory_handler.rag_engine.store_project_history_with_embedding(
                        file_path=commit.get("file_path", ""),
                        event_type=commit.get("event_type", "git_commit"),
                        content=commit.get("content", ""),
                    )
                    imported_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to import commit {commit.get('hash', 'unknown')}: {e}"
                    )

            import_duration = (datetime.now() - start_time).total_seconds()

            logger.info(f"Imported {imported_count} commits from git log")

            return {
                "success": True,
                "entries_imported": imported_count,
                "import_duration": import_duration,
                "source_file": git_log_path,
            }

        except Exception as e:
            logger.error(f"Error importing from git log: {e}")
            return {
                "success": False,
                "error": str(e),
                "entries_imported": 0,
                "import_duration": (datetime.now() - start_time).total_seconds(),
            }

    def _parse_git_log(self, git_log_content: str) -> list[dict[str, Any]]:
        """Parse git log content into structured commits."""
        commits = []

        # Split by commit boundaries
        commit_pattern = r"^commit ([a-f0-9]{40})$"
        commit_sections = re.split(commit_pattern, git_log_content, flags=re.MULTILINE)

        for i in range(1, len(commit_sections), 2):
            if i + 1 < len(commit_sections):
                commit_hash = commit_sections[i]
                commit_content = commit_sections[i + 1]

                commit = self._parse_git_commit(commit_hash, commit_content)
                if commit:
                    commits.append(commit)

        return commits

    def _parse_git_commit(
        self, commit_hash: str, commit_content: str
    ) -> dict[str, Any] | None:
        """Parse individual git commit."""
        try:
            lines = commit_content.strip().split("\n")

            # Extract basic info
            author = ""
            date = ""
            message = ""

            in_message = False
            for line in lines:
                if line.startswith("Author:"):
                    author = line.replace("Author:", "").strip()
                elif line.startswith("Date:"):
                    date = line.replace("Date:", "").strip()
                elif line.strip() == "" and not in_message:
                    in_message = True
                elif in_message and line.strip():
                    if not message:
                        message = line.strip()
                    break

            if not message:
                return None

            # Classify commit type
            event_type = self._classify_git_commit(message)

            return {
                "hash": commit_hash,
                "author": author,
                "date": date,
                "message": message,
                "event_type": event_type,
                "file_path": "",  # Could be extracted from diff if available
                "content": f"Git commit: {message}\nAuthor: {author}\nHash: {commit_hash[:8]}",
            }

        except Exception as e:
            logger.warning(f"Failed to parse git commit {commit_hash}: {e}")
            return None

    def _classify_git_commit(self, commit_message: str) -> str:
        """Classify git commit into event types."""
        message_lower = commit_message.lower()

        if any(word in message_lower for word in ["fix", "bug", "error", "issue"]):
            return "bug_fix"
        elif any(
            word in message_lower for word in ["add", "new", "feature", "implement"]
        ):
            return "feature_addition"
        elif any(
            word in message_lower for word in ["refactor", "restructure", "cleanup"]
        ):
            return "refactoring"
        elif any(word in message_lower for word in ["test", "spec", "unit"]):
            return "test_addition"
        elif any(word in message_lower for word in ["doc", "readme", "comment"]):
            return "documentation"
        elif any(word in message_lower for word in ["update", "upgrade", "bump"]):
            return "dependency_update"
        else:
            return "general_change"
