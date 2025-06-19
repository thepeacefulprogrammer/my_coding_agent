"""Project History Service for managing project history functionality.

This service was extracted from the monolithic AIAgent class to provide
focused, single-responsibility functionality for project history operations.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any as Agent
    from typing import Any as MemorySystem

logger = logging.getLogger(__name__)


class ProjectHistoryService:
    """Service for managing project history functionality."""

    def __init__(
        self,
        memory_system: MemorySystem | None = None,  # noqa: ANN401
        enable_project_history: bool = False,
    ) -> None:
        """Initialize the ProjectHistoryService.

        Args:
            memory_system: The memory system for project history operations
            enable_project_history: Whether project history functionality is enabled
        """
        self.memory_system = memory_system
        self.enabled = enable_project_history
        self._project_history_cache = {}
        self._project_understanding_cache = {}

        if enable_project_history and not memory_system:
            logger.warning("Project history enabled but no memory system provided")
            self.enabled = False

    @property
    def is_enabled(self) -> bool:
        """Check if project history service is enabled and functional."""
        return self.enabled and self.memory_system is not None

    def get_tool_names(self) -> list[str]:
        """Get list of project history tool names.

        Returns:
            List of tool names provided by this service
        """
        if not self.is_enabled:
            return []

        return [
            "get_file_project_history",
            "search_project_history",
            "get_recent_project_changes",
            "get_project_timeline",
        ]

    def get_tool_descriptions(self) -> dict[str, str]:
        """Get descriptions of project history tools.

        Returns:
            Dictionary mapping tool names to descriptions
        """
        if not self.is_enabled:
            return {}

        return {
            "get_file_project_history": "Get project history and evolution for a specific file",
            "search_project_history": "Search project history using semantic and text search",
            "get_recent_project_changes": "Get recent project changes within specified time period",
            "get_project_timeline": "Get project timeline showing chronological development",
        }

    def register_tools(self, agent: Agent) -> None:  # noqa: ANN401
        """Register project history tools with the AI Agent.

        Args:
            agent: The Pydantic AI agent to register tools with
        """
        if not self.is_enabled:
            logger.warning("Project history tools require memory system")
            return

        try:
            # Project history for specific file tool
            @agent.tool_plain
            async def get_file_project_history(file_path: str, limit: int = 20) -> str:
                """Get project history for a specific file.

                Args:
                    file_path: Path to the file to get history for
                    limit: Maximum number of history events to return (default: 20)

                Returns:
                    Formatted project history for the file
                """
                return await self._tool_get_file_project_history(file_path, limit)

            # Search project history tool
            @agent.tool_plain
            async def search_project_history(query: str, limit: int = 25) -> str:
                """Search project history using semantic and text search.

                Args:
                    query: Search query for project history
                    limit: Maximum number of results to return (default: 25)

                Returns:
                    Formatted search results from project history
                """
                return await self._tool_search_project_history(query, limit)

            # Get recent project changes tool
            @agent.tool_plain
            async def get_recent_project_changes(
                hours: int = 24, limit: int = 15
            ) -> str:
                """Get recent project changes within specified time period.

                Args:
                    hours: Number of hours to look back (default: 24)
                    limit: Maximum number of changes to return (default: 15)

                Returns:
                    Formatted list of recent project changes
                """
                return await self._tool_get_recent_project_changes(hours, limit)

            # Project timeline tool
            @agent.tool_plain
            async def get_project_timeline(
                file_path: str = "", days_back: int = 7
            ) -> str:
                """Get project timeline showing chronological development.

                Args:
                    file_path: Optional file path to focus timeline on (default: all files)
                    days_back: Number of days to look back (default: 7)

                Returns:
                    Formatted project timeline
                """
                return await self._tool_get_project_timeline(file_path, days_back)

            logger.info("Project history tools registered successfully")

        except Exception as e:
            logger.error(f"Failed to register project history tools: {e}")
            self.enabled = False

    # Tool implementation methods

    async def _tool_get_file_project_history(
        self, file_path: str, limit: int = 20
    ) -> str:
        """Get project history for a specific file."""
        try:
            if not self.memory_system:
                return "Error: Memory system not available for project history"

            # Use cached result if available
            cache_key = f"file_history_{file_path}_{limit}"
            if cache_key in self._project_history_cache:
                return self._project_history_cache[cache_key]

            # Get project history for the file
            history = self.memory_system.get_project_history_for_file(file_path, limit)

            if not history:
                result = f"No project history found for file: {file_path}"
            else:
                result_lines = [f"Project History for {file_path}:"]
                result_lines.append("=" * 50)

                for event in history:
                    timestamp = event.get("timestamp", 0)
                    if isinstance(timestamp, int | float):
                        # Use UTC to ensure consistent testing
                        time_str = datetime.fromtimestamp(
                            timestamp, timezone.utc
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        time_str = str(timestamp)

                    event_type = event.get("event_type", "unknown")
                    summary = event.get("summary", "No summary available")
                    content = event.get("content", "")

                    result_lines.append(f"[{time_str}] {event_type.upper()}")
                    result_lines.append(f"Summary: {summary}")
                    if content:
                        result_lines.append(f"Details: {content[:200]}...")
                    result_lines.append("-" * 30)

                result = "\n".join(result_lines)

            # Cache the result
            self._project_history_cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Error getting file project history: {e}")
            return f"Error retrieving project history for {file_path}: {e}"

    async def _tool_search_project_history(self, query: str, limit: int = 25) -> str:
        """Search project history using semantic and text search."""
        try:
            if not self.memory_system:
                return "Error: Memory system not available for project history search"

            # Search project history
            results = self.memory_system.search_project_history(query, limit)

            if not results:
                return f"No project history found matching query: {query}"

            result_lines = [f"Project History Search Results for '{query}':"]
            result_lines.append("=" * 60)

            for event in results:
                timestamp = event.get("timestamp", 0)
                if isinstance(timestamp, int | float):
                    time_str = datetime.fromtimestamp(timestamp).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                else:
                    time_str = str(timestamp)

                file_path = event.get("file_path", "unknown")
                event_type = event.get("event_type", "unknown")
                summary = event.get("summary", "No summary available")

                result_lines.append(f"[{time_str}] {file_path}")
                result_lines.append(f"Type: {event_type} | Summary: {summary}")
                result_lines.append("-" * 40)

            return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"Error searching project history: {e}")
            return f"Error searching project history for '{query}': {e}"

    async def _tool_get_recent_project_changes(
        self, hours: int = 24, limit: int = 15
    ) -> str:
        """Get recent project changes within specified time period."""
        try:
            if not self.memory_system:
                return "Error: Memory system not available for recent changes"

            # Get recent project history
            context = self.memory_system.get_project_context_for_ai(
                recent_hours=hours, max_events=limit
            )

            if not context or context.strip() == "":
                return f"No project changes found in the last {hours} hours"

            return (
                f"Recent Project Changes (Last {hours} hours):\n"
                + "=" * 50
                + "\n"
                + context
            )

        except Exception as e:
            logger.error(f"Error getting recent project changes: {e}")
            return f"Error retrieving recent changes: {e}"

    async def _tool_get_project_timeline(
        self, file_path: str = "", days_back: int = 7
    ) -> str:
        """Get project timeline showing chronological development."""
        try:
            if not self.memory_system:
                return "Error: Memory system not available for project timeline"

            # Calculate time range
            end_time = datetime.now().timestamp()
            start_time = (datetime.now() - timedelta(days=days_back)).timestamp()

            if file_path:
                # Generate timeline for specific file
                timeline = self.memory_system.generate_file_timeline(
                    file_path, limit=30
                )
                title = f"Timeline for {file_path} (Last {days_back} days)"
            else:
                # Generate general project timeline
                timeline = self.memory_system.generate_project_timeline(
                    start_time, end_time
                )
                title = f"Project Timeline (Last {days_back} days)"

            if not timeline:
                return "No timeline data found for the specified period"

            # Format timeline
            formatted_timeline = self.memory_system.format_timeline_for_ai(timeline)

            return f"{title}:\n" + "=" * 60 + "\n" + formatted_timeline

        except Exception as e:
            logger.error(f"Error getting project timeline: {e}")
            return f"Error generating project timeline: {e}"

    # Helper methods for project history functionality

    def should_lookup_project_history(self, message: str) -> bool:
        """Determine if a message should trigger project history lookup.

        Args:
            message: The user message to analyze

        Returns:
            Whether project history lookup should be triggered
        """
        if not self.is_enabled:
            return False

        # More specific keywords that suggest file/project history queries
        file_keywords = [
            "history",
            "changes",
            "modified",
            "evolution",
            "development",
            "timeline",
            "what happened",
            "recent changes",
            ".py",
            ".js",
            ".ts",
            ".json",
            ".md",
            ".txt",
            ".yaml",
            ".yml",
        ]

        # More specific context patterns
        context_patterns = [
            r"when (?:was|did).*(?:change|modify|update|create)",
            r"how (?:was|did).*(?:develop|evolve|change)",
            r"why (?:was|did).*(?:change|modify|update)",
            r"show.*(?:history|changes|timeline)",
            r"tell me about.*(?:history|changes|development)",
        ]

        message_lower = message.lower()

        # Check for file extensions or explicit keywords
        for keyword in file_keywords:
            if keyword in message_lower:
                return True

        # Check for contextual patterns
        return any(re.search(pattern, message_lower) for pattern in context_patterns)

    def get_recent_project_history(self, limit: int = 50) -> list[dict]:
        """Get recent project history with caching.

        Args:
            limit: Maximum number of history events to return

        Returns:
            List of recent project history events
        """
        try:
            if not self.memory_system:
                return []

            cache_key = f"recent_history_{limit}"
            if cache_key in self._project_history_cache:
                return self._project_history_cache[cache_key]

            history = self.memory_system.get_project_history(limit=limit)
            self._project_history_cache[cache_key] = history
            return history

        except Exception as e:
            logger.error(f"Error getting recent project history: {e}")
            return []

    def generate_project_evolution_context(self, file_path: str = "") -> str:
        """Generate project evolution context for AI responses.

        Args:
            file_path: Optional file path to focus context on

        Returns:
            Project evolution context string
        """
        try:
            if not self.memory_system:
                return ""

            if file_path:
                context = self.memory_system.get_project_context_for_ai(
                    file_path=file_path
                )
            else:
                context = self.memory_system.get_project_context_for_ai(recent_hours=72)

            return context or ""

        except Exception as e:
            logger.error(f"Error generating project evolution context: {e}")
            return ""

    def build_project_understanding(self, file_path: str = "") -> dict:
        """Build project understanding from historical changes.

        Args:
            file_path: Optional file path to focus understanding on

        Returns:
            Dictionary containing project understanding analysis
        """
        try:
            cache_key = f"understanding_{file_path}"
            if cache_key in self._project_understanding_cache:
                return self._project_understanding_cache[cache_key]

            if not self.memory_system:
                return {}

            # Get recent project history
            if file_path:
                history = self.memory_system.get_project_history_for_file(
                    file_path, limit=20
                )
            else:
                history = self.memory_system.get_project_history(limit=50)

            # Analyze patterns
            understanding = {
                "patterns": [],
                "key_changes": [],
                "development_focus": [],
                "recent_activities": [],
            }

            if history:
                # Extract development patterns
                event_types = [event.get("event_type", "") for event in history]
                understanding["patterns"] = list(set(event_types))

                # Identify key changes (high impact)
                key_changes = [
                    event
                    for event in history
                    if event.get("metadata", {}).get("impact_score", 0) > 0.7
                ]
                understanding["key_changes"] = key_changes[:5]  # Top 5 key changes

                # Extract focus areas from summaries
                summaries = [event.get("summary", "") for event in history]
                focus_keywords = []
                for summary in summaries:
                    words = summary.lower().split()
                    focus_keywords.extend([word for word in words if len(word) > 5])

                # Count common keywords to identify focus areas
                common_keywords = Counter(focus_keywords).most_common(5)
                understanding["development_focus"] = [
                    keyword for keyword, count in common_keywords
                ]

                # Recent activities (last 5)
                understanding["recent_activities"] = history[:5]

            # Cache the understanding
            self._project_understanding_cache[cache_key] = understanding
            return understanding

        except Exception as e:
            logger.error(f"Error building project understanding: {e}")
            return {}

    def enhance_message_with_project_context(self, message: str) -> str:
        """Enhance user message with relevant project context.

        Args:
            message: The original user message

        Returns:
            Enhanced message with project context
        """
        try:
            if not self.is_enabled or not self.should_lookup_project_history(message):
                return message

            # Extract file paths from message
            file_patterns = re.findall(r"[\w/\-\.]+\.\w+", message)

            context_parts = []
            for file_path in file_patterns:
                context = self.generate_project_evolution_context(file_path)
                if context:
                    context_parts.append(f"Project Context for {file_path}:\n{context}")

            # If no specific files, add general context
            if not context_parts:
                general_context = self.generate_project_evolution_context()
                if general_context:
                    context_parts.append(f"Recent Project Context:\n{general_context}")

            if context_parts:
                enhanced_message = message + "\n\n" + "\n\n".join(context_parts)
                return enhanced_message

            return message

        except Exception as e:
            logger.error(f"Error enhancing message with project context: {e}")
            return message

    def generate_file_evolution_timeline(self, file_path: str) -> list:
        """Generate evolution timeline for a specific file.

        Args:
            file_path: Path to the file to generate timeline for

        Returns:
            List of timeline events sorted by timestamp (most recent first)
        """
        try:
            if not self.memory_system:
                return []

            timeline = self.memory_system.generate_file_timeline(file_path, limit=20)

            # Sort by timestamp (most recent first)
            if timeline:
                timeline.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

            return timeline

        except Exception as e:
            logger.error(f"Error generating file evolution timeline: {e}")
            return []

    def clear_cache(self) -> None:
        """Clear all cached project history data."""
        self._project_history_cache.clear()
        self._project_understanding_cache.clear()
        logger.info("Project history cache cleared")
