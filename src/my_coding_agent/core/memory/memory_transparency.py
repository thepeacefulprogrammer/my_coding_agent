"""
Memory transparency system for showing users when and how the AI agent uses memories.

This module provides transparency into the memory system by tracking and displaying
when memories are used to enhance AI responses, giving users insight into how
their stored information influences the conversation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .memory_types import (
    MemoryRetrievalResult,
    SemanticSearchResult,
)

logger = logging.getLogger(__name__)


class TransparencyLevel(Enum):
    """Levels of memory transparency detail."""

    MINIMAL = "minimal"  # Just show that memories were used
    SIMPLE = "simple"  # Show count and basic info
    DETAILED = "detailed"  # Show full details with sources and scores


class MemoryTransparencySettings(BaseModel):
    """Settings for memory transparency features."""

    enabled: bool = True
    level: TransparencyLevel = TransparencyLevel.DETAILED
    show_memory_sources: bool = True
    show_relevance_scores: bool = True
    show_memory_count: bool = True
    show_search_queries: bool = True
    max_displayed_memories: int = Field(default=5, gt=0)

    @field_validator("max_displayed_memories")
    def validate_max_displayed_memories(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_displayed_memories must be greater than 0")
        return v


@dataclass
class MemoryUsageEvent:
    """Represents a single memory usage event for transparency tracking."""

    query: str
    memories_used: list[SemanticSearchResult | MemoryRetrievalResult]
    search_type: str
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def memory_count(self) -> int:
        """Get the number of memories used in this event."""
        return len(self.memories_used)


class MemoryTransparencyManager:
    """
    Manages memory transparency features.

    Tracks when memories are used and provides formatted transparency messages
    to show users how their stored information is being utilized.
    """

    def __init__(self, settings: MemoryTransparencySettings | None = None):
        """Initialize the transparency manager."""
        self.settings = settings or MemoryTransparencySettings()
        self.usage_events: list[MemoryUsageEvent] = []
        self.statistics: dict[str, Any] = {
            "total_memory_uses": 0,
            "total_memories_retrieved": 0,
            "search_types_used": {},
            "most_common_queries": [],
        }

        logger.info(
            f"Memory transparency manager initialized with level: {self.settings.level.value}"
        )

    def is_enabled(self) -> bool:
        """Check if transparency features are enabled."""
        return self.settings.enabled

    def record_memory_usage(
        self,
        query: str,
        memories_used: list[SemanticSearchResult | MemoryRetrievalResult],
        search_type: str,
    ) -> None:
        """
        Record a memory usage event for transparency tracking.

        Args:
            query: The search query that triggered memory retrieval
            memories_used: List of memories that were retrieved and used
            search_type: Type of search performed (semantic, text, hybrid, etc.)
        """
        if not self.is_enabled():
            return

        event = MemoryUsageEvent(
            query=query, memories_used=memories_used, search_type=search_type
        )

        self.usage_events.append(event)

        # Update statistics
        self.statistics["total_memory_uses"] += 1
        self.statistics["total_memories_retrieved"] += len(memories_used)

        if search_type not in self.statistics["search_types_used"]:
            self.statistics["search_types_used"][search_type] = 0
        self.statistics["search_types_used"][search_type] += 1

        logger.debug(
            f"Recorded memory usage: {len(memories_used)} memories for query '{query[:50]}...'"
        )

    def generate_transparency_message(
        self,
        memories_used: list[SemanticSearchResult | MemoryRetrievalResult],
        query: str,
    ) -> str:
        """
        Generate a transparency message showing how memories were used.

        Args:
            memories_used: List of memories that were used
            query: The original search query

        Returns:
            Formatted transparency message for display to user
        """
        if not self.is_enabled() or not memories_used:
            return ""

        memory_count = len(memories_used)

        if self.settings.level == TransparencyLevel.MINIMAL:
            return "💭 Enhanced with memories"
        elif self.settings.level == TransparencyLevel.SIMPLE:
            if self.settings.show_memory_count:
                return f"💭 Using {memory_count} memories to enhance response"
            else:
                return "💭 Enhanced with stored memories"
        elif self.settings.level == TransparencyLevel.DETAILED:
            return self._generate_detailed_message(memories_used, query)

        return ""

    def _generate_detailed_message(
        self,
        memories_used: list[SemanticSearchResult | MemoryRetrievalResult],
        query: str,
    ) -> str:
        """Generate a detailed transparency message."""
        memory_count = len(memories_used)
        max_display = self.settings.max_displayed_memories

        # Header
        message_parts = ["💭 **Memory Context**"]

        if self.settings.show_memory_count:
            message_parts.append(f"Found {memory_count} relevant memories")

        if self.settings.show_search_queries:
            message_parts.append(f"Search query: {query}")

        # Memory previews
        displayed_count = min(memory_count, max_display)
        for i, memory_result in enumerate(memories_used[:displayed_count]):
            preview = self._format_memory_preview(memory_result)
            message_parts.append(f"\n{i + 1}. {preview}")

        # Show if we're limiting display
        if memory_count > max_display:
            message_parts.append(f"\n(showing top {max_display})")

        return "\n".join(message_parts)

    def _format_memory_preview(
        self, memory_result: SemanticSearchResult | MemoryRetrievalResult
    ) -> str:
        """Format a single memory for preview display."""
        preview_parts = []

        # Memory content (truncated)
        content = memory_result.content
        if len(content) > 100:
            content = content[:97] + "..."
        preview_parts.append(content)

        # Relevance score
        if self.settings.show_relevance_scores:
            if isinstance(memory_result, SemanticSearchResult):
                score_percent = int(memory_result.similarity_score * 100)
            else:  # MemoryRetrievalResult
                score_percent = int(memory_result.search_score * 100)
            preview_parts.append(f"Relevance: {score_percent}%")

        # Memory source
        if self.settings.show_memory_sources:
            if isinstance(memory_result, SemanticSearchResult):
                source = self._get_memory_source_name(memory_result.memory_type)
            else:  # MemoryRetrievalResult
                source = self._get_memory_source_name(memory_result.source_type)
            preview_parts.append(f"Source: {source}")

        # Tags (if available)
        if hasattr(memory_result, "tags") and memory_result.tags:
            tags_str = ", ".join(memory_result.tags)
            preview_parts.append(f"Tags: {tags_str}")

        return " | ".join(preview_parts)

    def _get_memory_source_name(self, memory_type: str) -> str:
        """Get human-readable name for memory source."""
        source_names = {
            "short_term": "Short-term memory",
            "long_term": "Long-term memory",
            "project_history": "Project history",
            "conversation": "Conversation history",
            "longterm": "Long-term memory",
            "project": "Project history",
        }
        return source_names.get(memory_type, memory_type.replace("_", " ").title())

    def get_memory_usage_statistics(self) -> dict[str, Any]:
        """Get statistics about memory usage for transparency."""
        stats = self.statistics.copy()

        if stats["total_memory_uses"] > 0:
            stats["average_memories_per_query"] = (
                stats["total_memories_retrieved"] / stats["total_memory_uses"]
            )
        else:
            stats["average_memories_per_query"] = 0

        return stats

    def get_recent_usage_events(self, limit: int = 10) -> list[MemoryUsageEvent]:
        """Get recent memory usage events for transparency display."""
        return list(reversed(self.usage_events[-limit:]))

    def clear_usage_history(self) -> None:
        """Clear memory usage history and reset statistics."""
        self.usage_events.clear()
        self.statistics = {
            "total_memory_uses": 0,
            "total_memories_retrieved": 0,
            "search_types_used": {},
            "most_common_queries": [],
        }
        logger.info("Memory usage history cleared")
