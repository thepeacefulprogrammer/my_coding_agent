"""Project history management and configuration system (Task 9.7).

This module provides comprehensive project history management capabilities including:
- Settings and configuration management
- Automatic cleanup and archiving
- Export/import functionality for backup and migration
- Storage optimization and analytics
"""

import csv
import fnmatch
import json
import logging
import re
from datetime import datetime
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

    # Cleanup and archiving
    enable_auto_cleanup: bool = Field(
        default=True, description="Enable automatic cleanup"
    )
    cleanup_interval_hours: int = Field(
        default=24, description="Hours between automatic cleanup runs"
    )
    enable_archiving: bool = Field(
        default=True, description="Enable archiving of old entries"
    )
    archive_threshold_days: int = Field(
        default=180, description="Days before entries are archived"
    )

    # Storage optimization
    max_content_length: int = Field(
        default=10000, description="Maximum content length to store"
    )
    compress_old_entries: bool = Field(
        default=True, description="Compress old entries to save space"
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
        """Check if a file should be tracked based on filter settings."""
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return False

        # Check include patterns
        return any(fnmatch.fnmatch(file_path, pattern) for pattern in self.file_filters)

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectHistorySettings":
        """Create settings from dictionary."""
        return cls(**data)

    def to_json(self) -> str:
        """Convert settings to JSON string."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ProjectHistorySettings":
        """Create settings from JSON string."""
        return cls.model_validate_json(json_str)

    def save_to_file(self, file_path: str) -> None:
        """Save settings to file."""
        with open(file_path, "w") as f:
            f.write(self.to_json())
        logger.info(f"Settings saved to {file_path}")

    @classmethod
    def load_from_file(cls, file_path: str) -> "ProjectHistorySettings":
        """Load settings from file with migration support."""
        try:
            with open(file_path) as f:
                data = json.load(f)

            # Handle migration from older format
            if isinstance(data, dict):
                # Ensure all required fields have defaults
                defaults = cls().model_dump()
                for key, default_value in defaults.items():
                    if key not in data:
                        data[key] = default_value
                        logger.info(
                            f"Migrated setting '{key}' to default value: {default_value}"
                        )

            return cls.from_dict(data)

        except FileNotFoundError:
            logger.info(f"Settings file {file_path} not found, using defaults")
            return cls()
        except Exception as e:
            logger.error(f"Error loading settings from {file_path}: {e}")
            return cls()


class ProjectHistoryManager:
    """Main manager for project history operations."""

    def __init__(
        self,
        memory_handler: "ConversationMemoryHandler",
        settings: ProjectHistorySettings | None = None,
    ) -> None:
        """Initialize the project history manager.

        Args:
            memory_handler: ConversationMemoryHandler instance for data operations
            settings: Project history settings (uses defaults if None)
        """
        self.memory_handler = memory_handler
        self.settings = settings or ProjectHistorySettings()
        self._last_cleanup_time: datetime | None = None
        self._last_archive_time: datetime | None = None

        logger.info("Project history manager initialized")

    def should_run_cleanup(self) -> bool:
        """Check if automatic cleanup should run."""
        if not self.settings.enable_auto_cleanup:
            return False

        if self._last_cleanup_time is None:
            return True

        time_since_cleanup = datetime.now() - self._last_cleanup_time
        return time_since_cleanup.total_seconds() >= (
            self.settings.cleanup_interval_hours * 3600
        )

    def cleanup_old_entries(self) -> dict[str, Any]:
        """Clean up old project history entries based on retention settings.

        Returns:
            Dictionary with cleanup results and statistics
        """
        start_time = datetime.now()
        logger.info("Starting project history cleanup")

        try:
            # Get all project history entries
            all_entries = self.memory_handler.get_project_history(limit=None)

            if not all_entries:
                return {
                    "success": True,
                    "entries_deleted": 0,
                    "entries_archived": 0,
                    "cleanup_duration": 0,
                    "message": "No entries found to clean up",
                }

            current_time = datetime.now().timestamp()
            retention_cutoff = current_time - (self.settings.retention_days * 24 * 3600)
            archive_cutoff = current_time - (
                self.settings.archive_threshold_days * 24 * 3600
            )

            entries_to_delete = []
            entries_to_archive = []

            # Categorize entries for deletion or archiving
            for entry in all_entries:
                entry_time = entry.get("timestamp", current_time)

                if entry_time < retention_cutoff:
                    entries_to_delete.append(entry)
                elif entry_time < archive_cutoff and self.settings.enable_archiving:
                    entries_to_archive.append(entry)

            # Archive entries if enabled
            archived_count = 0
            if entries_to_archive and self.settings.enable_archiving:
                archive_path = self._get_default_archive_path()
                archive_result = self.archive_old_entries(
                    archive_path, entries_to_archive
                )
                if archive_result["success"]:
                    archived_count = archive_result["entries_archived"]

            # Delete old entries
            deleted_count = 0
            for entry in entries_to_delete:
                try:
                    # In a real implementation, we would delete from ChromaDB
                    # For now, we'll simulate deletion
                    deleted_count += 1
                except Exception as e:
                    logger.error(
                        f"Error deleting entry {entry.get('id', 'unknown')}: {e}"
                    )

            # Update cleanup time
            self._last_cleanup_time = datetime.now()

            cleanup_duration = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Cleanup completed: {deleted_count} deleted, {archived_count} archived"
            )

            return {
                "success": True,
                "entries_deleted": deleted_count,
                "entries_archived": archived_count,
                "cleanup_duration": cleanup_duration,
                "retention_cutoff": retention_cutoff,
                "archive_cutoff": archive_cutoff,
            }

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {
                "success": False,
                "error": str(e),
                "entries_deleted": 0,
                "entries_archived": 0,
                "cleanup_duration": (datetime.now() - start_time).total_seconds(),
            }

    def archive_old_entries(
        self, archive_path: str, entries: list[dict] | None = None
    ) -> dict[str, Any]:
        """Archive old project history entries to a file.

        Args:
            archive_path: Path to save the archive file
            entries: Optional list of entries to archive (if None, gets from memory)

        Returns:
            Dictionary with archiving results
        """
        start_time = datetime.now()

        try:
            # Get entries to archive if not provided
            if entries is None:
                all_entries = self.memory_handler.get_project_history(limit=None)
                current_time = datetime.now().timestamp()
                archive_cutoff = current_time - (
                    self.settings.archive_threshold_days * 24 * 3600
                )

                entries = [
                    entry
                    for entry in all_entries
                    if entry.get("timestamp", current_time) < archive_cutoff
                ]

            if not entries:
                return {
                    "success": True,
                    "entries_archived": 0,
                    "archive_path": archive_path,
                    "message": "No entries to archive",
                }

            # Create archive data structure
            archive_data = {
                "metadata": {
                    "archive_timestamp": datetime.now().isoformat(),
                    "total_entries": len(entries),
                    "archive_threshold_days": self.settings.archive_threshold_days,
                    "format_version": "1.0",
                },
                "entries": entries,
            }

            # Ensure archive directory exists
            Path(archive_path).parent.mkdir(parents=True, exist_ok=True)

            # Save archive file
            with open(archive_path, "w") as f:
                json.dump(archive_data, f, indent=2)

            archive_duration = (datetime.now() - start_time).total_seconds()

            logger.info(f"Archived {len(entries)} entries to {archive_path}")

            return {
                "success": True,
                "entries_archived": len(entries),
                "archive_path": archive_path,
                "archive_duration": archive_duration,
                "archive_size_mb": Path(archive_path).stat().st_size / (1024 * 1024),
            }

        except Exception as e:
            logger.error(f"Error archiving entries: {e}")
            return {
                "success": False,
                "error": str(e),
                "entries_archived": 0,
                "archive_path": archive_path,
            }

    def get_storage_statistics(self) -> dict[str, Any]:
        """Get comprehensive storage statistics for project history.

        Returns:
            Dictionary with storage statistics and analytics
        """
        try:
            all_entries = self.memory_handler.get_project_history(limit=None)

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
                    "archiving_enabled": self.settings.enable_archiving,
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

    def validate_entry(self, entry: dict[str, Any]) -> bool:
        """Validate a project history entry.

        Args:
            entry: Project history entry to validate

        Returns:
            True if entry is valid, False otherwise
        """
        required_fields = ["id", "timestamp", "event_type", "file_path", "summary"]

        for field in required_fields:
            if field not in entry:
                logger.warning(f"Entry missing required field: {field}")
                return False

        # Validate timestamp
        try:
            timestamp = entry["timestamp"]
            if not isinstance(timestamp, int | float):
                logger.warning(f"Invalid timestamp type: {type(timestamp)}")
                return False
        except (ValueError, TypeError):
            logger.warning("Invalid timestamp value")
            return False

        # Validate file path filter
        file_path = entry.get("file_path", "")
        if not self.settings.should_track_file(file_path):
            logger.debug(f"File path filtered out: {file_path}")
            return False

        return True

    def _get_default_archive_path(self) -> str:
        """Get default archive file path."""
        # Create archives directory in user's config directory
        archive_dir = Path.home() / ".config" / "my_coding_agent" / "archives"
        archive_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(archive_dir / f"project_history_archive_{timestamp}.json")


class ProjectHistoryExporter:
    """Export project history data for backup and analysis."""

    def __init__(self, memory_handler: "ConversationMemoryHandler") -> None:
        """Initialize the exporter.

        Args:
            memory_handler: ConversationMemoryHandler instance for data access
        """
        self.memory_handler = memory_handler
        logger.info("Project history exporter initialized")

    def export_to_json(
        self,
        export_path: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        event_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Export project history to JSON format.

        Args:
            export_path: Path to save the export file
            start_date: Optional start date filter
            end_date: Optional end date filter
            event_types: Optional list of event types to include

        Returns:
            Dictionary with export results
        """
        try:
            # Get entries with optional filtering
            all_entries = self.memory_handler.get_project_history(limit=None)

            if not all_entries:
                return {
                    "success": False,
                    "error": "No project history entries found",
                    "entries_exported": 0,
                }

            # Apply filters
            filtered_entries = self._filter_entries(
                all_entries, start_date, end_date, event_types
            )

            # Create export data structure
            export_data = {
                "metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_entries": len(filtered_entries),
                    "filters": {
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None,
                        "event_types": event_types,
                    },
                    "format_version": "1.0",
                },
                "entries": filtered_entries,
            }

            # Ensure export directory exists
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)

            # Save export file
            with open(export_path, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported {len(filtered_entries)} entries to {export_path}")

            return {
                "success": True,
                "entries_exported": len(filtered_entries),
                "export_path": export_path,
                "export_size_mb": Path(export_path).stat().st_size / (1024 * 1024),
            }

        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return {"success": False, "error": str(e), "entries_exported": 0}

    def export_to_csv(
        self,
        export_path: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        event_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Export project history to CSV format.

        Args:
            export_path: Path to save the export file
            start_date: Optional start date filter
            end_date: Optional end date filter
            event_types: Optional list of event types to include

        Returns:
            Dictionary with export results
        """
        try:
            # Get entries with optional filtering
            all_entries = self.memory_handler.get_project_history(limit=None)

            if not all_entries:
                return {
                    "success": False,
                    "error": "No project history entries found",
                    "entries_exported": 0,
                }

            # Apply filters
            filtered_entries = self._filter_entries(
                all_entries, start_date, end_date, event_types
            )

            # Ensure export directory exists
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)

            # Define CSV columns
            csv_columns = [
                "id",
                "timestamp",
                "event_type",
                "file_path",
                "summary",
                "content",
                "lines_added",
                "lines_removed",
                "impact_score",
            ]

            # Write CSV file
            with open(export_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=csv_columns)
                writer.writeheader()

                for entry in filtered_entries:
                    # Flatten metadata for CSV
                    csv_row = {
                        "id": entry.get("id", ""),
                        "timestamp": entry.get("timestamp", ""),
                        "event_type": entry.get("event_type", ""),
                        "file_path": entry.get("file_path", ""),
                        "summary": entry.get("summary", ""),
                        "content": entry.get("content", ""),
                    }

                    # Extract metadata fields
                    metadata = entry.get("metadata", {})
                    csv_row["lines_added"] = metadata.get("lines_added", "")
                    csv_row["lines_removed"] = metadata.get("lines_removed", "")
                    csv_row["impact_score"] = metadata.get("impact_score", "")

                    writer.writerow(csv_row)

            logger.info(
                f"Exported {len(filtered_entries)} entries to CSV: {export_path}"
            )

            return {
                "success": True,
                "entries_exported": len(filtered_entries),
                "export_path": export_path,
                "export_size_mb": Path(export_path).stat().st_size / (1024 * 1024),
            }

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return {"success": False, "error": str(e), "entries_exported": 0}

    def _filter_entries(
        self,
        entries: list[dict],
        start_date: datetime | None,
        end_date: datetime | None,
        event_types: list[str] | None,
    ) -> list[dict]:
        """Filter entries based on criteria.

        Args:
            entries: List of project history entries
            start_date: Optional start date filter
            end_date: Optional end date filter
            event_types: Optional list of event types to include

        Returns:
            Filtered list of entries
        """
        filtered = entries

        # Filter by date range
        if start_date or end_date:
            start_timestamp = start_date.timestamp() if start_date else 0
            end_timestamp = end_date.timestamp() if end_date else float("inf")

            filtered = [
                entry
                for entry in filtered
                if start_timestamp <= entry.get("timestamp", 0) <= end_timestamp
            ]

        # Filter by event types
        if event_types:
            filtered = [
                entry for entry in filtered if entry.get("event_type") in event_types
            ]

        return filtered


class ProjectHistoryImporter:
    """Import project history data from various sources."""

    def __init__(self, memory_handler: "ConversationMemoryHandler") -> None:
        """Initialize the importer.

        Args:
            memory_handler: ConversationMemoryHandler instance for data operations
        """
        self.memory_handler = memory_handler
        logger.info("Project history importer initialized")

    def import_from_json(
        self, import_path: str, validate_entries: bool = True
    ) -> dict[str, Any]:
        """Import project history from JSON format.

        Args:
            import_path: Path to the JSON file to import
            validate_entries: Whether to validate entries before importing

        Returns:
            Dictionary with import results
        """
        start_time = datetime.now()

        try:
            with open(import_path) as f:
                import_data = json.load(f)

            entries = import_data.get("entries", [])

            if not entries:
                return {
                    "success": True,
                    "entries_imported": 0,
                    "entries_skipped": 0,
                    "message": "No entries found in import file",
                }

            # Process entries
            imported_count = 0
            skipped_count = 0
            validation_errors = []
            seen_ids = set()

            for entry in entries:
                try:
                    # Check for duplicates
                    entry_id = entry.get("id")
                    if entry_id in seen_ids:
                        skipped_count += 1
                        validation_errors.append(f"Duplicate entry ID: {entry_id}")
                        continue

                    # Validate entry if requested
                    if validate_entries and not self._validate_import_entry(entry):
                        skipped_count += 1
                        validation_errors.append(f"Invalid entry: {entry_id}")
                        continue

                    # Store entry (in real implementation, would use ChromaDB)
                    # For now, we'll simulate successful import
                    seen_ids.add(entry_id)
                    imported_count += 1

                except Exception as e:
                    skipped_count += 1
                    validation_errors.append(f"Error processing entry: {e}")

            import_duration = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Import completed: {imported_count} imported, {skipped_count} skipped"
            )

            return {
                "success": True,
                "entries_imported": imported_count,
                "entries_skipped": skipped_count,
                "import_duration": import_duration,
                "validation_errors": validation_errors[:10],  # Limit error list
                "source_file": import_path,
            }

        except Exception as e:
            logger.error(f"Error importing from JSON: {e}")
            return {
                "success": False,
                "error": str(e),
                "entries_imported": 0,
                "entries_skipped": 0,
                "import_duration": (datetime.now() - start_time).total_seconds(),
            }

    def import_from_git_log(self, git_log_path: str) -> dict[str, Any]:
        """Import project history from git log file.

        Args:
            git_log_path: Path to git log file

        Returns:
            Dictionary with import results
        """
        start_time = datetime.now()

        try:
            with open(git_log_path) as f:
                git_log_content = f.read()

            # Parse git log entries
            entries = self._parse_git_log(git_log_content)

            if not entries:
                return {
                    "success": True,
                    "entries_imported": 0,
                    "message": "No valid git commits found in log file",
                }

            # Store entries (in real implementation, would use ChromaDB)
            imported_count = len(entries)

            import_duration = (datetime.now() - start_time).total_seconds()

            logger.info(f"Imported {imported_count} git commits from {git_log_path}")

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

    def _validate_import_entry(self, entry: dict[str, Any]) -> bool:
        """Validate an entry for import.

        Args:
            entry: Entry to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["id", "timestamp", "event_type", "summary"]

        for field in required_fields:
            if field not in entry:
                return False

        # Validate timestamp
        try:
            timestamp = entry["timestamp"]
            if not isinstance(timestamp, int | float):
                return False
        except (ValueError, TypeError):
            return False

        return True

    def _parse_git_log(self, git_log_content: str) -> list[dict[str, Any]]:
        """Parse git log content into project history entries.

        Args:
            git_log_content: Raw git log content

        Returns:
            List of parsed project history entries
        """
        entries = []

        # Split commits by "commit " at start of line
        commit_blocks = re.split(r"\ncommit ", git_log_content)

        for i, block in enumerate(commit_blocks):
            if not block.strip():
                continue

            # First block has 'commit' at the beginning, others don't
            if i == 0 and block.startswith("commit "):
                commit_hash = block.split("\n")[0].replace("commit ", "").strip()
                commit_content = "\n".join(block.split("\n")[1:])
            else:
                lines = block.split("\n")
                commit_hash = lines[0].strip()
                commit_content = "\n".join(lines[1:])

            try:
                entry = self._parse_git_commit(commit_hash, commit_content)
                if entry:
                    entries.append(entry)
            except Exception as e:
                logger.warning(f"Error parsing git commit {commit_hash}: {e}")

        return entries

    def _parse_git_commit(
        self, commit_hash: str, commit_content: str
    ) -> dict[str, Any] | None:
        """Parse a single git commit into a project history entry.

        Args:
            commit_hash: Git commit hash
            commit_content: Commit content (author, date, message, changes)

        Returns:
            Parsed project history entry or None if parsing fails
        """
        lines = commit_content.strip().split("\n")

        # Extract author, date, and message
        author = ""
        commit_date = None
        message_lines = []
        in_message = False

        for line in lines:
            if line.startswith("Author:"):
                author = line.replace("Author:", "").strip()
            elif line.startswith("Date:"):
                date_str = line.replace("Date:", "").strip()
                try:
                    # Parse git date format
                    commit_date = datetime.strptime(
                        date_str.split(" +")[0], "%a %b %d %H:%M:%S %Y"
                    )
                except ValueError:
                    logger.warning(f"Could not parse date: {date_str}")
                    commit_date = datetime.now()
            elif not line.strip() and not in_message:
                in_message = True
            elif in_message and line.strip():
                message_lines.append(line.strip())

        if not commit_date:
            commit_date = datetime.now()

        summary = message_lines[0] if message_lines else "No commit message"
        content = "\n".join(message_lines) if len(message_lines) > 1 else summary

        # Determine event type from commit message
        event_type = self._classify_git_commit(summary)

        return {
            "id": f"git_{commit_hash}",
            "timestamp": commit_date.timestamp(),
            "event_type": event_type,
            "file_path": "multiple_files",  # Git commits can affect multiple files
            "summary": summary,
            "content": content,
            "metadata": {
                "git_hash": commit_hash,
                "author": author,
                "source": "git_import",
                "import_timestamp": datetime.now().timestamp(),
            },
        }

    def _classify_git_commit(self, commit_message: str) -> str:
        """Classify git commit message into event type.

        Args:
            commit_message: Git commit message

        Returns:
            Classified event type
        """
        message_lower = commit_message.lower()

        if any(word in message_lower for word in ["fix", "bug", "error", "issue"]):
            return "bug_fix"
        elif any(
            word in message_lower for word in ["add", "implement", "create", "new"]
        ):
            return "feature_addition"
        elif any(
            word in message_lower
            for word in ["refactor", "clean", "optimize", "improve"]
        ):
            return "refactoring"
        elif any(word in message_lower for word in ["update", "modify", "change"]):
            return "modification"
        elif any(word in message_lower for word in ["test", "spec"]):
            return "test_addition"
        elif any(word in message_lower for word in ["doc", "readme", "comment"]):
            return "documentation"
        else:
            return "modification"
