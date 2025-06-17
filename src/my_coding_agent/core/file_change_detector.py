"""
File change detection system for monitoring project file modifications.

This module provides comprehensive file change detection including:
- File system watcher for detecting modifications, creations, and deletions
- File change analyzer for extracting diffs and summaries
- Filtering system for ignoring temporary files and build artifacts
- Integration with file tree widget signals
"""

from __future__ import annotations

import difflib
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object
    FileSystemEvent = object

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class ChangeType(Enum):
    """Types of file changes that can be detected."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileChangeEvent:
    """Represents a file change event with metadata."""

    file_path: Path
    change_type: ChangeType
    timestamp: float = field(default_factory=time.time)
    old_content: str | None = None
    new_content: str | None = None
    old_path: Path | None = None  # For move operations
    metadata: dict[str, Any] = field(default_factory=dict)


class FileChangeFilter:
    """Filters files to determine which should be monitored."""

    def __init__(self):
        """Initialize the file filter with default ignore patterns."""
        self.ignore_patterns = {
            r".*\.tmp$",
            r".*\.temp$",
            r".*/~.*",  # Files starting with ~ in any directory
            r".*~$",  # Files ending with ~
            r".*\.#.*",  # Files containing .#
            r".*\.DS_Store$",
            r".*Thumbs\.db$",
            r".*/__pycache__/.*",
            r".*\.pytest_cache/.*",
            r".*\.coverage$",
            r".*/htmlcov/.*",
            r".*/build/.*",
            r".*/dist/.*",
            r".*\.egg-info/.*",
            r".*/node_modules/.*",
            r".*\.npm/.*",
            r".*\.yarn/.*",
            r".*\.git/.*",
            r".*\.svn/.*",
            r".*\.hg/.*",
            r".*\.venv/.*",
            r".*/venv/.*",
            r".*/env/.*",
            r".*\.virtualenv/.*",
            r".*\.vscode/.*",
            r".*\.idea/.*",
            r".*\.swp$",
            r".*\.swo$",
            r".*\.log$",
            r".*\.log\.\d+$",
            r".*\.pyc$",
            r".*\.pyo$",
            r".*\.class$",
            r".*\.o$",
            r".*\.so$",
            r".*\.dll$",
            r".*\.exe$",
        }

        self.custom_patterns: set[str] = set()
        self.max_file_size = 50 * 1024 * 1024  # 50MB max file size

    def should_ignore(self, file_path: Path) -> bool:
        """Determine if a file should be ignored."""
        try:
            path_str = str(file_path)

            # Check against all ignore patterns
            all_patterns = self.ignore_patterns | self.custom_patterns
            for pattern in all_patterns:
                if re.search(pattern, path_str):
                    return True

            # Check file size if file exists
            try:
                if file_path.exists() and file_path.is_file():
                    if file_path.stat().st_size > self.max_file_size:
                        return True
            except (OSError, PermissionError):
                # If we can't check file size, don't ignore unless patterns matched
                pass

            return False
        except Exception:
            # Only ignore files if we can't even check their path string
            return True

    def add_ignore_pattern(self, pattern: str) -> None:
        """Add a custom ignore pattern."""
        # Convert glob patterns to regex if needed
        if "*" in pattern and not pattern.startswith("^") and not pattern.endswith("$"):
            # Convert simple glob pattern to regex
            regex_pattern = pattern.replace(".", r"\.").replace("*", ".*")
            regex_pattern = f".*{regex_pattern}$"
            self.custom_patterns.add(regex_pattern)
        else:
            self.custom_patterns.add(pattern)

    def remove_ignore_pattern(self, pattern: str) -> None:
        """Remove a custom ignore pattern."""
        self.custom_patterns.discard(pattern)


class FileChangeAnalyzer:
    """Analyzes file changes to extract meaningful information."""

    def __init__(self):
        """Initialize the file change analyzer."""
        self.code_patterns = {
            "function": [
                r"def\s+(\w+)\s*\(",
                r"function\s+(\w+)\s*\(",
                r"(\w+)\s*=\s*function\s*\(",
                r"(\w+)\s*=>\s*",
            ],
            "class": [
                r"class\s+(\w+)\s*[\(\:]",
                r"interface\s+(\w+)\s*\{",
            ],
            "import": [
                r"from\s+(\S+)\s+import",
                r"import\s+(\S+)",
                r'require\s*\(\s*[\'"]([^\'"]+)[\'"]',
            ],
        }

    def analyze_change(
        self,
        file_path: Path,
        old_content: str | None = None,
        new_content: str | None = None,
    ) -> dict[str, Any]:
        """Analyze a file change and extract meaningful information."""
        analysis = {
            "file_path": str(file_path),
            "change_type": self._determine_change_type(old_content, new_content),
            "is_binary": False,
            "lines_added": 0,
            "lines_removed": 0,
            "lines_changed": 0,
            "summary": "",
            "diff_lines": [],
            "code_elements": {
                "functions_added": 0,
                "functions_removed": 0,
                "classes_added": 0,
                "classes_removed": 0,
                "imports_added": 0,
                "imports_removed": 0,
            },
        }

        try:
            if self._is_binary_content(old_content) or self._is_binary_content(
                new_content
            ):
                analysis["is_binary"] = True
                analysis["summary"] = (
                    f"Binary file {file_path.name} was {analysis['change_type']}"
                )
                return analysis

            if analysis["change_type"] == "creation":
                creation_analysis = self._analyze_creation(file_path, new_content or "")
                for key, value in creation_analysis.items():
                    analysis[key] = value
            elif analysis["change_type"] == "deletion":
                deletion_analysis = self._analyze_deletion(file_path, old_content or "")
                for key, value in deletion_analysis.items():
                    analysis[key] = value
            elif analysis["change_type"] == "modification":
                modification_analysis = self._analyze_modification(
                    file_path, old_content or "", new_content or ""
                )
                for key, value in modification_analysis.items():
                    analysis[key] = value

            return analysis
        except Exception as e:
            analysis["summary"] = f"Error analyzing {file_path.name}: {str(e)}"
            return analysis

    def _determine_change_type(
        self, old_content: str | None, new_content: str | None
    ) -> str:
        """Determine the type of change based on content availability."""
        if old_content is None and new_content is not None:
            return "creation"
        elif old_content is not None and new_content is None:
            return "deletion"
        else:
            return "modification"

    def _is_binary_content(self, content: Any) -> bool:
        """Check if content appears to be binary."""
        if content is None:
            return False
        if isinstance(content, bytes):
            return True
        if isinstance(content, str):
            try:
                content.encode("utf-8")
                return (
                    "\x00" in content
                    or len([c for c in content if ord(c) < 32 and c not in "\n\r\t"])
                    > len(content) * 0.1
                )
            except UnicodeEncodeError:
                return True
        return False

    def _analyze_creation(self, file_path: Path, content: str) -> dict[str, Any]:
        """Analyze file creation."""
        lines = content.splitlines() if content else []
        code_elements = self._extract_code_elements(content or "")

        return {
            "lines_added": len(lines),
            "summary": f"Created {file_path.name} with {len(lines)} lines"
            + self._format_code_elements_summary(code_elements, "added"),
            "code_elements": {
                "functions_added": len(code_elements["functions"]),
                "classes_added": len(code_elements["classes"]),
                "imports_added": len(code_elements["imports"]),
                "functions_removed": 0,
                "classes_removed": 0,
                "imports_removed": 0,
            },
        }

    def _analyze_deletion(self, file_path: Path, content: str) -> dict[str, Any]:
        """Analyze file deletion."""
        lines = content.splitlines() if content else []
        code_elements = self._extract_code_elements(content or "")

        return {
            "lines_removed": len(lines),
            "summary": f"Deleted {file_path.name} with {len(lines)} lines"
            + self._format_code_elements_summary(code_elements, "removed"),
            "code_elements": {
                "functions_removed": len(code_elements["functions"]),
                "classes_removed": len(code_elements["classes"]),
                "imports_removed": len(code_elements["imports"]),
                "functions_added": 0,
                "classes_added": 0,
                "imports_added": 0,
            },
        }

    def _analyze_modification(
        self, file_path: Path, old_content: str, new_content: str
    ) -> dict[str, Any]:
        """Analyze file modification."""
        old_lines = old_content.splitlines() if old_content else []
        new_lines = new_content.splitlines() if new_content else []

        diff = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{file_path.name}",
                tofile=f"b/{file_path.name}",
                lineterm="",
            )
        )

        lines_added = sum(
            1 for line in diff if line.startswith("+") and not line.startswith("+++")
        )
        lines_removed = sum(
            1 for line in diff if line.startswith("-") and not line.startswith("---")
        )

        old_elements = self._extract_code_elements(old_content or "")
        new_elements = self._extract_code_elements(new_content or "")

        functions_added = len(new_elements["functions"]) - len(
            old_elements["functions"]
        )
        classes_added = len(new_elements["classes"]) - len(old_elements["classes"])
        imports_added = len(new_elements["imports"]) - len(old_elements["imports"])

        # Build summary with more details
        summary_parts = [
            f"Modified {file_path.name}: +{lines_added}/-{lines_removed} lines"
        ]

        # Add code element details for both additions and removals
        old_func_names = set(old_elements["functions"])
        new_func_names = set(new_elements["functions"])
        added_functions = new_func_names - old_func_names
        removed_functions = old_func_names - new_func_names

        old_class_names = set(old_elements["classes"])
        new_class_names = set(new_elements["classes"])
        added_classes = new_class_names - old_class_names
        removed_classes = old_class_names - new_class_names

        # Show function changes
        if added_functions:
            added_list = list(added_functions)[:3]  # Show up to 3
            summary_parts.append(
                f"(added: {', '.join(f'{name}()' for name in added_list)})"
            )
        if removed_functions:
            removed_list = list(removed_functions)[:3]  # Show up to 3
            summary_parts.append(
                f"(removed: {', '.join(f'{name}()' for name in removed_list)})"
            )

        # Show class changes
        if added_classes:
            added_list = list(added_classes)[:3]  # Show up to 3
            summary_parts.append(f"(added: class {', '.join(added_list)})")
        if removed_classes:
            removed_list = list(removed_classes)[:3]  # Show up to 3
            summary_parts.append(f"(removed: class {', '.join(removed_list)})")

        return {
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "lines_changed": min(lines_added, lines_removed),
            "diff_lines": diff,
            "summary": " ".join(summary_parts),
            "code_elements": {
                "functions_added": max(0, functions_added),
                "functions_removed": max(0, -functions_added),
                "classes_added": max(0, classes_added),
                "classes_removed": max(0, -classes_added),
                "imports_added": max(0, imports_added),
                "imports_removed": max(0, -imports_added),
            },
        }

    def _extract_code_elements(self, content: str) -> dict[str, list[str]]:
        """Extract code elements (functions, classes, imports) from content."""
        elements = {"functions": [], "classes": [], "imports": []}

        # Map singular pattern keys to plural element keys
        key_mapping = {"function": "functions", "class": "classes", "import": "imports"}

        try:
            for element_type, patterns in self.code_patterns.items():
                element_key = key_mapping.get(element_type, element_type)
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.MULTILINE)
                    if matches:
                        elements[element_key].extend(matches)
        except Exception:
            # Don't let regex errors break the analysis
            pass

        return elements

    def _format_code_elements_summary(
        self, elements: dict[str, list[str]], action: str
    ) -> str:
        """Format code elements for summary."""
        parts = []
        if elements["functions"]:
            func_names = elements["functions"][:3]  # Show first 3 function names
            if len(func_names) == 1:
                parts.append(f"{action}: {func_names[0]}()")
            else:
                parts.append(
                    f"{action}: {', '.join(f'{name}()' for name in func_names)}"
                )

        if elements["classes"]:
            class_names = elements["classes"][:3]  # Show first 3 class names
            if len(class_names) == 1:
                parts.append(f"{action}: class {class_names[0]}")
            else:
                parts.append(f"{action}: classes {', '.join(class_names)}")

        return f" ({', '.join(parts)})" if parts else ""

    def _format_modification_summary(
        self, functions_delta: int, classes_delta: int, imports_delta: int
    ) -> str:
        """Format modification summary for code elements."""
        parts = []
        if functions_delta > 0:
            parts.append(f"+{functions_delta} function(s)")
        elif functions_delta < 0:
            parts.append(f"{functions_delta} function(s)")

        if classes_delta > 0:
            parts.append(f"+{classes_delta} class(es)")
        elif classes_delta < 0:
            parts.append(f"{classes_delta} class(es)")

        if imports_delta > 0:
            parts.append(f"+{imports_delta} import(s)")
        elif imports_delta < 0:
            parts.append(f"{imports_delta} import(s)")

        return f"({', '.join(parts)})" if parts else ""


if WATCHDOG_AVAILABLE:

    class WatchdogEventHandler(FileSystemEventHandler):
        """File system event handler for watchdog."""

        def __init__(self, detector):
            """Initialize with reference to parent detector."""
            super().__init__()
            self.detector = detector
            self.file_cache: dict[str, dict[str, Any]] = {}

        def on_created(self, event) -> None:
            """Handle file creation events."""
            if not event.is_directory:
                self._handle_file_event(Path(str(event.src_path)), ChangeType.CREATED)

        def on_modified(self, event) -> None:
            """Handle file modification events."""
            if not event.is_directory:
                self._handle_file_event(Path(str(event.src_path)), ChangeType.MODIFIED)

        def on_deleted(self, event) -> None:
            """Handle file deletion events."""
            if not event.is_directory:
                self._handle_file_event(Path(str(event.src_path)), ChangeType.DELETED)

        def on_moved(self, event) -> None:
            """Handle file move events."""
            if not event.is_directory and hasattr(event, "dest_path"):
                # Treat as deletion of old path and creation of new path
                self._handle_file_event(Path(str(event.src_path)), ChangeType.DELETED)
                self._handle_file_event(Path(str(event.dest_path)), ChangeType.CREATED)

        def _handle_file_event(self, file_path: Path, change_type: ChangeType) -> None:
            """Handle a file system event."""
            try:
                # Check if file should be ignored
                if self.detector.file_filter.should_ignore(file_path):
                    return

                # Get file content
                old_content = None
                new_content = None

                if change_type == ChangeType.DELETED:
                    # Try to get cached content
                    old_content = self.file_cache.get(str(file_path), {}).get("content")
                    # Remove from cache
                    self.file_cache.pop(str(file_path), None)
                else:
                    try:
                        if file_path.exists():
                            new_content = file_path.read_text(
                                encoding="utf-8", errors="ignore"
                            )
                            # Cache the content
                            self.file_cache[str(file_path)] = {
                                "content": new_content,
                                "timestamp": time.time(),
                            }

                            if change_type == ChangeType.MODIFIED:
                                old_content = self.file_cache.get(
                                    str(file_path), {}
                                ).get("content")

                    except (UnicodeDecodeError, PermissionError, OSError):
                        # Handle as binary or inaccessible file
                        pass

                # Create and emit event
                event = FileChangeEvent(
                    file_path=file_path,
                    change_type=change_type,
                    old_content=old_content,
                    new_content=new_content,
                )

                self.detector._emit_change_event(event)

            except Exception as e:
                # Log error but don't crash the watcher
                print(f"Error handling file event for {file_path}: {e}")
else:

    class FileSystemWatcher:
        """Dummy file system watcher when watchdog is not available."""

        def __init__(self, detector):
            self.detector = detector


class FileChangeDetector(QObject):
    """Main file change detector that coordinates all components."""

    # Qt signals
    file_changed = pyqtSignal(FileChangeEvent)

    def __init__(self, watch_directory: Path, parent: QObject | None = None):
        """
        Initialize the file change detector.

        Args:
            watch_directory: Directory to watch for changes
            parent: Optional parent QObject
        """
        super().__init__(parent)

        self.watch_directory = Path(watch_directory)
        self.is_watching = False

        # Initialize components
        self.file_filter = FileChangeFilter()
        self.analyzer = FileChangeAnalyzer()

        # Watchdog components
        self.observer = None
        self.event_handler = None

        # File tree integration
        self._file_tree_widget = None

        # Event processing queue to avoid overwhelming the system
        self._event_queue: list[FileChangeEvent] = []
        self._processing_timer = QTimer()
        self._processing_timer.timeout.connect(self._process_event_queue)
        self._processing_timer.setInterval(100)  # Process every 100ms

    def start_watching(self) -> None:
        """Start watching for file changes."""
        if self.is_watching or not WATCHDOG_AVAILABLE:
            return

        try:
            if Observer is not None:
                self.observer = Observer()
                self.event_handler = WatchdogEventHandler(self)

                self.observer.schedule(
                    self.event_handler, str(self.watch_directory), recursive=True
                )

                self.observer.start()
                self.is_watching = True
                self._processing_timer.start()

                print(f"Started watching directory: {self.watch_directory}")

        except Exception as e:
            print(f"Failed to start file watching: {e}")
            self.is_watching = False

    def stop_watching(self) -> None:
        """Stop watching for file changes."""
        if not self.is_watching:
            return

        try:
            self._processing_timer.stop()

            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=1.0)
                self.observer = None

            self.event_handler = None
            self.is_watching = False

            print("Stopped file watching")

        except Exception as e:
            print(f"Error stopping file watching: {e}")

    def connect_to_file_tree(self, file_tree_widget: Any) -> None:
        """Connect to file tree widget for signal integration."""
        self._file_tree_widget = file_tree_widget

        # Connect to file tree signals if available
        if hasattr(file_tree_widget, "file_selected"):
            file_tree_widget.file_selected.connect(self._on_file_selected)
        if hasattr(file_tree_widget, "file_opened"):
            file_tree_widget.file_opened.connect(self._on_file_opened)

    def set_immediate_emit(self, enable: bool = True) -> None:
        """Enable immediate signal emission for testing."""
        self._immediate_emit = enable

    def _emit_change_event(self, event: FileChangeEvent) -> None:
        """Emit a file change event (called by FileSystemWatcher)."""
        # Add to queue for batch processing
        self._event_queue.append(event)

        # For immediate processing in tests, also emit directly
        # This helps with Qt signal spy tests
        if hasattr(self, "_immediate_emit") and self._immediate_emit:
            try:
                # Analyze the change
                analysis = self.analyzer.analyze_change(
                    event.file_path, event.old_content, event.new_content
                )

                # Add analysis to event metadata
                for key, value in analysis.items():
                    event.metadata[key] = value

                # Emit the signal immediately
                self.file_changed.emit(event)
            except Exception as e:
                print(f"Error emitting immediate event: {e}")

    def _process_event_queue(self) -> None:
        """Process queued file change events."""
        if not self._event_queue:
            return

        # Process events in batches to avoid overwhelming
        batch_size = 10
        batch = self._event_queue[:batch_size]
        self._event_queue = self._event_queue[batch_size:]

        for event in batch:
            try:
                # Analyze the change
                analysis = self.analyzer.analyze_change(
                    event.file_path, event.old_content, event.new_content
                )

                # Add analysis to event metadata
                for key, value in analysis.items():
                    event.metadata[key] = value

                # Emit the signal
                self.file_changed.emit(event)

            except Exception as e:
                print(f"Error processing file change event: {e}")

    def _on_file_selected(self, file_path: Path) -> None:
        """Handle file selection from file tree."""
        # This could be used to cache file content or prepare for monitoring
        pass

    def _on_file_opened(self, file_path: Path) -> None:
        """Handle file opening from file tree."""
        # This could be used to track which files are being actively edited
        pass

    def __del__(self):
        """Cleanup when detector is destroyed."""
        self.stop_watching()
