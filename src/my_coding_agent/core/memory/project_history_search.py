"""
Project history search and filtering functionality.

This module provides advanced search, filtering, and analytics capabilities
for project history including semantic search, related event discovery,
and comprehensive project statistics.
"""

import fnmatch
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..project_event_recorder import ProjectEvent

if TYPE_CHECKING:
    from ..memory_integration import ConversationMemoryHandler


@dataclass
class SearchResult:
    """Represents a search result with relevance scoring."""

    event: ProjectEvent
    relevance_score: float
    match_fields: list[str]
    match_highlights: dict[str, str]


@dataclass
class EventChain:
    """Represents a chain of related events."""

    chain_id: str
    events: list[ProjectEvent]
    relationship_type: str
    confidence_score: float
    description: str


class ProjectHistorySearch:
    """Advanced search functionality for project history."""

    def __init__(self, memory_integration: "ConversationMemoryHandler" = None) -> None:
        """Initialize the project history search system."""
        self.memory_integration = memory_integration

    def search_text(
        self,
        query: str,
        fields: list[str] | None = None,
        limit: int = 50,
        start_date: datetime | float | None = None,
        end_date: datetime | float | None = None,
        case_sensitive: bool = False,
    ) -> list[ProjectEvent]:
        """
        Perform text-based search across project history.

        Args:
            query: Search query string
            fields: Fields to search in ['description', 'file_path', 'change_summary', 'event_type']
            limit: Maximum number of results
            start_date: Filter events after this date
            end_date: Filter events before this date
            case_sensitive: Whether search should be case-sensitive

        Returns:
            List of matching ProjectEvent objects
        """
        if not self.memory_integration:
            return []

        # Get all events
        events = self.memory_integration.get_project_history()

        if not events:
            return []

        # Default search fields
        if fields is None:
            fields = ["description", "change_summary", "event_type"]

        # Apply date filters - handle both datetime and timestamp inputs
        if start_date or end_date:
            start_timestamp = (
                start_date.timestamp()
                if isinstance(start_date, datetime)
                else start_date
            )
            end_timestamp = (
                end_date.timestamp() if isinstance(end_date, datetime) else end_date
            )
            events = self._filter_by_date_range(events, start_timestamp, end_timestamp)

        # Perform text search
        matching_events = []
        search_query = query if case_sensitive else query.lower()

        for event in events:
            if self._event_matches_text_query(
                event, search_query, fields, case_sensitive
            ):
                matching_events.append(event)

        # Sort by relevance (newer events first, then by relevance)
        matching_events.sort(key=lambda e: e.timestamp, reverse=True)

        return matching_events[:limit]

    def search_semantic(
        self, query: str, limit: int = 20, threshold: float = 0.7
    ) -> list[ProjectEvent]:
        """
        Perform semantic search using embeddings.

        Args:
            query: Semantic search query
            limit: Maximum number of results
            threshold: Minimum similarity threshold

        Returns:
            List of semantically similar ProjectEvent objects
        """
        if not self.memory_integration:
            return []

        try:
            # Use memory integration's semantic search capability
            results = self.memory_integration.search_project_history(
                query=query, limit=limit
            )
            return results if results else []
        except Exception as e:
            print(f"Semantic search failed: {e}")
            return []

    def search_hybrid(
        self,
        query: str,
        text_weight: float = 0.6,
        semantic_weight: float = 0.4,
        limit: int = 30,
    ) -> list[ProjectEvent]:
        """
        Perform hybrid search combining text and semantic results.

        Args:
            query: Search query
            text_weight: Weight for text search results
            semantic_weight: Weight for semantic search results
            limit: Maximum number of results

        Returns:
            Combined and ranked list of ProjectEvent objects
        """
        # Get text search results
        text_results = self.search_text(query, limit=limit * 2)

        # Get semantic search results
        semantic_results = self.search_semantic(query, limit=limit * 2)

        # Combine and deduplicate results
        combined_events = {}

        # Helper function to get unique event identifier
        def get_event_key(event: dict[str, Any]) -> str:  # type: ignore[misc]
            # Try to use event_id from metadata first
            if event.metadata and "event_id" in event.metadata:
                return event.metadata["event_id"]
            # Fall back to using object id for deduplication
            return id(event)

        # Add text results with text weight
        for i, event in enumerate(text_results):
            score = text_weight * (1.0 - i / len(text_results))
            event_key = get_event_key(event)
            combined_events[event_key] = {
                "event": event,
                "score": score,
                "sources": ["text"],
            }

        # Add semantic results with semantic weight
        for i, event in enumerate(semantic_results):
            score = semantic_weight * (1.0 - i / len(semantic_results))
            event_key = get_event_key(event)
            if event_key in combined_events:
                # Boost score for events found in both searches
                combined_events[event_key]["score"] += score
                combined_events[event_key]["sources"].append("semantic")
            else:
                combined_events[event_key] = {
                    "event": event,
                    "score": score,
                    "sources": ["semantic"],
                }

        # Sort by combined score
        sorted_results = sorted(
            combined_events.values(), key=lambda x: x["score"], reverse=True
        )

        return [result["event"] for result in sorted_results[:limit]]

    def _event_matches_text_query(
        self, event: ProjectEvent, query: str, fields: list[str], case_sensitive: bool
    ) -> bool:
        """Check if event matches text query in specified fields."""
        if not query:
            return True

        for field in fields:
            field_value = self._get_event_field_value(event, field)
            search_value = field_value if case_sensitive else field_value.lower()

            if query in search_value:
                return True

        return False

    def _get_event_field_value(self, event: ProjectEvent, field: str) -> str:
        """Get field value from event for searching."""
        if field == "description":
            return event.description or ""
        elif field == "file_path":
            return str(event.file_path) if event.file_path else ""
        elif field == "change_summary":
            return event.change_summary or ""
        elif field == "event_type":
            return event.event_type.value if event.event_type else ""
        else:
            return ""

    def _filter_by_date_range(
        self,
        events: list[ProjectEvent],
        start_timestamp: float | None,
        end_timestamp: float | None,
    ) -> list[ProjectEvent]:
        """Filter events by timestamp range."""
        filtered = []
        for event in events:
            if start_timestamp is not None and event.timestamp < start_timestamp:
                continue
            if end_timestamp is not None and event.timestamp > end_timestamp:
                continue
            filtered.append(event)
        return filtered


class ProjectHistoryFilter:
    """Filter project events by various criteria."""

    def __init__(self) -> None:
        """Initialize the filter."""
        pass

    def filter_by_event_type(
        self, events: list[ProjectEvent], event_types: list[str]
    ) -> list[ProjectEvent]:
        """Filter events by event type."""
        return [event for event in events if event.event_type.value in event_types]

    def filter_by_file_path(
        self,
        events: list[ProjectEvent],
        file_path: Path | None = None,
        path_pattern: str | None = None,
    ) -> list[ProjectEvent]:
        """Filter events by file path or pattern."""
        if file_path:
            return [event for event in events if event.file_path == file_path]
        elif path_pattern:
            return [
                event
                for event in events
                if event.file_path
                and fnmatch.fnmatch(str(event.file_path), path_pattern)
            ]
        else:
            return events

    def filter_by_date_range(
        self, events: list[ProjectEvent], start_date: datetime, end_date: datetime
    ) -> list[ProjectEvent]:
        """Filter events by date range."""
        start_timestamp = start_date.timestamp()
        end_timestamp = end_date.timestamp()
        return [
            event
            for event in events
            if start_timestamp <= event.timestamp <= end_timestamp
        ]

    def filter_by_impact_score(
        self,
        events: list[ProjectEvent],
        min_score: float = 0.0,
        max_score: float = 10.0,
    ) -> list[ProjectEvent]:
        """Filter events by impact score."""
        return [
            event
            for event in events
            if (
                event.metadata
                and min_score <= event.metadata.get("impact_score", 0) <= max_score
            )
        ]

    def filter_by_change_magnitude(
        self,
        events: list[ProjectEvent],
        min_lines_added: int = 0,
        max_lines_added: int | None = None,
        min_lines_removed: int = 0,
        max_lines_removed: int | None = None,
    ) -> list[ProjectEvent]:
        """Filter events by change magnitude (lines added/removed)."""
        filtered = []
        for event in events:
            if not event.metadata:
                continue

            lines_added = event.metadata.get("lines_added", 0)
            lines_removed = event.metadata.get("lines_removed", 0)

            if lines_added < min_lines_added:
                continue
            if max_lines_added is not None and lines_added > max_lines_added:
                continue
            if lines_removed < min_lines_removed:
                continue
            if max_lines_removed is not None and lines_removed > max_lines_removed:
                continue

            filtered.append(event)

        return filtered

    def filter_by_author(
        self, events: list[ProjectEvent], author: str
    ) -> list[ProjectEvent]:
        """Filter events by author."""
        return [
            event
            for event in events
            if (event.metadata and event.metadata.get("author") == author)
        ]


class EventChainAnalyzer:
    """Analyzer for finding related events and change chains."""

    def __init__(self) -> None:
        """Initialize the event chain analyzer."""
        pass

    def find_related_events(
        self,
        target_event: ProjectEvent,
        all_events: list[ProjectEvent],
        relation_types: list[str] | None = None,
        time_window_hours: int = 48,
    ) -> list[ProjectEvent]:
        """
        Find events related to a target event.

        Args:
            target_event: The event to find relations for
            all_events: All available events to search through
            relation_types: Types of relations to look for
            time_window_hours: Time window for temporal proximity

        Returns:
            List of related ProjectEvent objects
        """
        if relation_types is None:
            relation_types = ["same_file", "temporal_proximity", "dependency"]

        related_events = []

        # Get event_id from metadata or use object id
        target_event_id = (
            target_event.metadata.get("event_id")
            if target_event.metadata
            else id(target_event)
        )

        for event in all_events:
            event_id = event.metadata.get("event_id") if event.metadata else id(event)
            if event_id == target_event_id:
                continue

            # Check for same file relation
            if (
                "same_file" in relation_types
                and event.file_path == target_event.file_path
            ):
                related_events.append(event)
                continue

            # Check for same author relation
            if (
                "same_author" in relation_types
                and event.metadata
                and target_event.metadata
                and event.metadata.get("author") == target_event.metadata.get("author")
            ):
                related_events.append(event)
                continue

            # Check for temporal proximity
            if "temporal_proximity" in relation_types:
                time_diff = abs(event.timestamp - target_event.timestamp) / 3600
                if time_diff <= time_window_hours:
                    related_events.append(event)
                    continue

            # Check for dependency relations
            if "dependency" in relation_types and self._events_have_dependency(
                target_event, event
            ):
                related_events.append(event)

        return related_events

    def analyze_change_chains(self, events: list[ProjectEvent]) -> list[dict[str, Any]]:
        """Analyze events to identify chains of related changes."""
        chains = []

        # Group events by file
        file_groups = defaultdict(list)
        for event in events:
            file_groups[str(event.file_path)].append(event)

        # Analyze each file's change chain
        for file_path, file_events in file_groups.items():
            if len(file_events) >= 2:
                # Sort by timestamp
                file_events.sort(key=lambda e: e.timestamp)

                chain = {
                    "chain_id": f"file_chain_{hash(file_path)}",
                    "events": file_events,
                    "relationship_type": "file_evolution",
                    "confidence_score": 0.9,
                    "description": f"Evolution of {file_path}",
                }
                chains.append(chain)

        # Find temporal chains (events close in time)
        events_by_time = sorted(events, key=lambda e: e.timestamp)

        current_chain = []
        for _i, event in enumerate(events_by_time):
            if not current_chain:
                current_chain = [event]
                continue

            # Check if event is close to the last event in current chain
            last_event = current_chain[-1]
            time_diff = (event.timestamp - last_event.timestamp) / 3600

            if time_diff <= 6:  # 6 hours window
                current_chain.append(event)
            else:
                # End current chain if it has multiple events
                if len(current_chain) >= 2:
                    chain = {
                        "chain_id": f"temporal_chain_{len(chains)}",
                        "events": current_chain,
                        "relationship_type": "temporal_proximity",
                        "confidence_score": 0.7,
                        "description": "Events occurring in close time sequence",
                    }
                    chains.append(chain)
                current_chain = [event]

        # Add final chain if it exists
        if len(current_chain) >= 2:
            chain = {
                "chain_id": f"temporal_chain_{len(chains)}",
                "events": current_chain,
                "relationship_type": "temporal_proximity",
                "confidence_score": 0.7,
                "description": "Events occurring in close time sequence",
            }
            chains.append(chain)

        return chains

    def find_event_dependencies(
        self, target_event: ProjectEvent, all_events: list[ProjectEvent]
    ) -> list[ProjectEvent]:
        """Find events that the target event likely depends on."""
        dependencies = []

        # Events that happened before target event
        earlier_events = [
            event for event in all_events if event.timestamp < target_event.timestamp
        ]

        # Look for related events (same file, similar changes, etc.)
        for event in earlier_events:
            if self._events_have_dependency(target_event, event):
                dependencies.append(event)

        # Sort by timestamp (most recent dependencies first)
        dependencies.sort(key=lambda e: e.timestamp, reverse=True)

        return dependencies

    def _events_have_dependency(
        self, event1: ProjectEvent, event2: ProjectEvent
    ) -> bool:
        """Check if event1 depends on event2."""
        # Simple heuristic: events in the same file or with related descriptions
        if event1.file_path == event2.file_path:
            return True

        # Check for related keywords in descriptions
        if event1.description and event2.description:
            event1_words = set(event1.description.lower().split())
            event2_words = set(event2.description.lower().split())
            common_words = event1_words.intersection(event2_words)

            # If they share significant words, they might be related
            if len(common_words) >= 2:
                return True

        return False


class ProjectHistoryAnalytics:
    """Analytics and reporting for project history."""

    def __init__(self) -> None:
        """Initialize the analytics engine."""
        pass

    def get_most_changed_files(
        self, events: list[ProjectEvent], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get files with the most changes."""
        file_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "change_count": 0,
                "total_lines_added": 0,
                "total_lines_removed": 0,
                "last_modified": 0,
                "event_types": set(),
            }
        )

        for event in events:
            if not event.file_path:
                continue

            file_path = str(event.file_path)
            stats = file_stats[file_path]

            stats["change_count"] += 1
            stats["last_modified"] = max(stats["last_modified"], event.timestamp)
            stats["event_types"].add(event.event_type.value)

            if event.metadata:
                stats["total_lines_added"] += event.metadata.get("lines_added", 0)
                stats["total_lines_removed"] += event.metadata.get("lines_removed", 0)

        # Convert to list and sort
        results = []
        for file_path, stats in file_stats.items():
            results.append(
                {
                    "file_path": file_path,
                    "change_count": stats["change_count"],
                    "total_lines_added": stats["total_lines_added"],
                    "total_lines_removed": stats["total_lines_removed"],
                    "last_modified": datetime.fromtimestamp(stats["last_modified"]),
                    "event_types": list(stats["event_types"]),
                }
            )

        results.sort(key=lambda x: x["change_count"], reverse=True)
        return results[:limit]

    def get_activity_patterns(
        self, events: list[ProjectEvent], granularity: str = "daily"
    ) -> list[dict[str, Any]]:
        """Analyze activity patterns over time."""
        if granularity == "daily":
            pattern_groups: dict[str, dict[str, Any]] = defaultdict(
                lambda: {
                    "event_count": 0,
                    "event_types": defaultdict(int),
                    "total_impact": 0.0,
                    "authors": set(),
                }
            )

            for event in events:
                event_date = datetime.fromtimestamp(event.timestamp)
                date_key = event_date.strftime("%Y-%m-%d")
                stats = pattern_groups[date_key]

                stats["event_count"] += 1
                stats["event_types"][event.event_type] += 1

                if event.metadata:
                    stats["total_impact"] += event.metadata.get("impact_score", 0)
                    author = event.metadata.get("author")
                    if author:
                        stats["authors"].add(author)

            # Convert to list format
            results = []
            for date_str, stats in pattern_groups.items():
                results.append(
                    {
                        "date": date_str,
                        "event_count": stats["event_count"],
                        "event_types": dict(stats["event_types"]),
                        "total_impact": stats["total_impact"],
                        "authors": list(stats["authors"]),
                    }
                )

            results.sort(key=lambda x: x["date"])
            return results

        return []

    def get_developer_contributions(
        self, events: list[ProjectEvent]
    ) -> list[dict[str, Any]]:
        """Analyze developer contributions."""
        dev_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "event_count": 0,
                "lines_added": 0,
                "lines_removed": 0,
                "impact_scores": [],
                "event_types": defaultdict(int),
            }
        )

        for event in events:
            if not event.metadata:
                continue

            author = event.metadata.get("author")
            if not author:
                continue

            stats = dev_stats[author]
            stats["event_count"] += 1
            stats["lines_added"] += event.metadata.get("lines_added", 0)
            stats["lines_removed"] += event.metadata.get("lines_removed", 0)
            stats["impact_scores"].append(event.metadata.get("impact_score", 0))
            stats["event_types"][event.event_type] += 1

        # Convert to results format
        results = []
        for author, stats in dev_stats.items():
            avg_impact = (
                sum(stats["impact_scores"]) / len(stats["impact_scores"])
                if stats["impact_scores"]
                else 0
            )

            results.append(
                {
                    "author": author,
                    "total_events": stats["event_count"],  # Fix key name
                    "lines_added": stats["lines_added"],
                    "lines_removed": stats["lines_removed"],
                    "avg_impact_score": avg_impact,
                    "event_types": dict(stats["event_types"]),
                }
            )

        results.sort(key=lambda x: x["total_events"], reverse=True)
        return results

    def get_event_type_distribution(
        self, events: list[ProjectEvent]
    ) -> dict[str, dict[str, Any]]:
        """Analyze distribution of event types."""
        type_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "impact_scores": [],
                "lines_added": 0,
                "lines_removed": 0,
            }
        )

        total_events = len(events)

        for event in events:
            event_type_key = event.event_type.value  # Use .value for string key
            stats = type_stats[event_type_key]
            stats["count"] += 1

            if event.metadata:
                stats["impact_scores"].append(event.metadata.get("impact_score", 0))
                stats["lines_added"] += event.metadata.get("lines_added", 0)
                stats["lines_removed"] += event.metadata.get("lines_removed", 0)

        # Convert to final format
        results = {}
        for event_type, stats in type_stats.items():
            avg_impact = (
                sum(stats["impact_scores"]) / len(stats["impact_scores"])
                if stats["impact_scores"]
                else 0
            )

            results[event_type] = {
                "count": stats["count"],
                "percentage": (stats["count"] / total_events * 100)
                if total_events > 0
                else 0,
                "avg_impact": avg_impact,
                "total_lines_added": stats["lines_added"],
                "total_lines_removed": stats["lines_removed"],
            }

        return results

    def get_impact_analysis(self, events: list[ProjectEvent]) -> dict[str, Any]:
        """Perform comprehensive impact analysis."""
        impact_scores = []
        high_impact_events = []

        for event in events:
            if event.metadata and "impact_score" in event.metadata:
                score = event.metadata["impact_score"]
                impact_scores.append(score)

                if score >= 7.0:
                    high_impact_events.append(event)

        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0

        # Analyze trends over time
        events_by_time = sorted(events, key=lambda e: e.timestamp)
        impact_trends = []

        for i in range(0, len(events_by_time), max(1, len(events_by_time) // 10)):
            batch = events_by_time[i : i + max(1, len(events_by_time) // 10)]
            batch_impacts = [
                e.metadata.get("impact_score", 0) for e in batch if e.metadata
            ]
            avg_batch_impact = (
                sum(batch_impacts) / len(batch_impacts) if batch_impacts else 0
            )

            batch_date = datetime.fromtimestamp(batch[0].timestamp)

            impact_trends.append(
                {
                    "period": batch_date.strftime("%Y-%m-%d"),
                    "avg_impact": avg_batch_impact,
                    "event_count": len(batch),
                }
            )

        return {
            "total_events": len(events),
            "average_impact": avg_impact,  # Fix key name
            "high_impact_events": high_impact_events,
            "impact_trends": impact_trends,
            "critical_changes": [
                e
                for e in events
                if e.metadata and e.metadata.get("impact_score", 0) >= 9.0
            ],
        }

    def get_file_evolution_timeline(
        self, events: list[ProjectEvent], file_path: Path
    ) -> list[dict[str, Any]]:
        """Generate evolution timeline for a specific file."""
        file_events = [event for event in events if event.file_path == file_path]

        file_events.sort(key=lambda e: e.timestamp)

        timeline = []
        cumulative_lines = 0

        for event in file_events:
            if event.metadata:
                lines_added = event.metadata.get("lines_added", 0)
                lines_removed = event.metadata.get("lines_removed", 0)
                cumulative_lines += lines_added - lines_removed

            timeline.append(
                {
                    "timestamp": event.timestamp,
                    "event_type": event.event_type.value,
                    "description": event.description,
                    "cumulative_lines": cumulative_lines,
                    "lines_changed": event.metadata.get("lines_added", 0)
                    + event.metadata.get("lines_removed", 0)
                    if event.metadata
                    else 0,
                }
            )

        return timeline


class ChangeImpactAnalyzer:
    """Analyzer for change impact and risk assessment."""

    def __init__(self) -> None:
        """Initialize the change impact analyzer."""
        pass

    def analyze_change_impact(
        self, target_event: ProjectEvent, all_events: list[ProjectEvent]
    ) -> dict[str, Any]:
        """Analyze the impact of a specific change."""
        # Find related events after this change
        related_events = []
        target_timestamp = target_event.timestamp

        for event in all_events:
            time_diff = event.timestamp - target_timestamp
            if (
                0 < time_diff <= 7 * 24 * 3600  # Within 7 days after
                and self._changes_are_related(target_event, event)
            ):
                related_events.append(event)

        # Analyze impact patterns
        impact_score = (
            target_event.metadata.get("impact_score", 0) if target_event.metadata else 0
        )

        # Look for subsequent changes in the same area
        affected_areas = set()
        if target_event.file_path:
            affected_areas.add(str(target_event.file_path.parent))

        for event in related_events:
            if event.file_path:
                affected_areas.add(str(event.file_path.parent))

        return {
            "impact_score": impact_score,
            "affected_areas": list(affected_areas),
            "subsequent_changes": len(related_events),
            "risk_indicators": self._assess_risk_indicators(
                target_event, related_events
            ),
        }

    def predict_affected_files(
        self, change_description: str, historical_events: list[ProjectEvent]
    ) -> list[dict[str, Any]]:
        """Predict files that might be affected by a change."""
        # Simple prediction based on historical patterns
        predictions = []

        # Look for similar changes in the past
        keywords = change_description.lower().split()

        for event in historical_events:
            if event.description:
                event_words = event.description.lower().split()
                common_words = set(keywords).intersection(set(event_words))

                if len(common_words) >= 2 and event.file_path:
                    relevance = len(common_words) / len(keywords)
                    predictions.append(
                        {
                            "file_path": str(event.file_path),
                            "relevance_score": relevance,
                            "historical_event": event.description,
                        }
                    )

        # Remove duplicates and sort by relevance
        unique_predictions = {}
        for pred in predictions:
            file_path = pred["file_path"]
            if (
                file_path not in unique_predictions
                or pred["relevance_score"]
                > unique_predictions[file_path]["relevance_score"]
            ):
                unique_predictions[file_path] = pred

        return sorted(
            unique_predictions.values(),
            key=lambda x: x["relevance_score"],
            reverse=True,
        )

    def calculate_change_risk(
        self, file_path: Path, change_type: str, historical_events: list[ProjectEvent]
    ) -> dict[str, Any]:
        """Calculate risk score for a proposed change."""
        # Find historical events for this file
        file_events = [
            event for event in historical_events if event.file_path == file_path
        ]

        if not file_events:
            return {"risk_score": 0.5, "risk_factors": ["No historical data"]}

        # Calculate risk factors
        risk_factors = []
        risk_score = 0.0

        # Recent change frequency
        now = datetime.now().timestamp()
        recent_changes = [
            event
            for event in file_events
            if (now - event.timestamp) <= 30 * 24 * 3600  # 30 days
        ]

        if len(recent_changes) > 5:
            risk_score += 0.3
            risk_factors.append("High recent change frequency")

        # Historical bug patterns
        bug_fixes = [
            event for event in file_events if event.event_type.value == "bug_fix"
        ]

        if len(bug_fixes) > len(file_events) * 0.3:
            risk_score += 0.4
            risk_factors.append("High bug fix ratio")

        # File complexity (lines of code changes)
        total_changes = sum(
            event.metadata.get("lines_added", 0)
            + event.metadata.get("lines_removed", 0)
            for event in file_events
            if event.metadata
        )

        if total_changes > 1000:
            risk_score += 0.2
            risk_factors.append("High complexity (many changes)")

        return {
            "risk_score": min(risk_score, 1.0),
            "risk_factors": risk_factors,
            "historical_changes": len(file_events),
            "recent_changes": len(recent_changes),
        }

    def _assess_risk_indicators(
        self, target_event: ProjectEvent, related_events: list[ProjectEvent]
    ) -> list[str]:
        """Assess risk indicators from change patterns."""
        indicators = []

        # Multiple quick changes indicate instability
        if len(related_events) > 3:
            indicators.append("Multiple subsequent changes")

        # Bug fixes following a change indicate issues
        bug_fixes = [e for e in related_events if e.event_type.value == "bug_fix"]
        if bug_fixes:
            indicators.append("Subsequent bug fixes required")

        # Large changes are inherently risky
        if target_event.metadata:
            total_lines = target_event.metadata.get(
                "lines_added", 0
            ) + target_event.metadata.get("lines_removed", 0)
            if total_lines > 100:
                indicators.append("Large change size")

        return indicators

    def _changes_are_related(self, event1: ProjectEvent, event2: ProjectEvent) -> bool:
        """Check if two changes are related."""
        # Same file
        if event1.file_path == event2.file_path:
            return True

        # Similar file paths (same directory)
        if (
            event1.file_path
            and event2.file_path
            and event1.file_path.parent == event2.file_path.parent
        ):
            return True

        # Similar descriptions
        if event1.description and event2.description:
            words1 = set(event1.description.lower().split())
            words2 = set(event2.description.lower().split())
            common_words = words1.intersection(words2)
            if len(common_words) >= 2:
                return True

        return False
