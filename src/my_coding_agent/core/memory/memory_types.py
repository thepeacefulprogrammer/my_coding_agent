"""Pydantic data models for memory system types."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchStrategy(str, Enum):
    """Search strategy enumeration for memory retrieval."""

    TEXT_SEARCH = "text_search"
    SEMANTIC_SEARCH = "semantic_search"
    HYBRID = "hybrid"


class ConversationMessage(BaseModel):
    """Model for storing conversation messages in short-term memory."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int | None = None
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = Field(..., description="Message content")
    role: str = Field(..., description="Message role (user, assistant)")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    tokens: int | None = Field(None, description="Token count for this message")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def metadata_json(self) -> str:
        """Get metadata as JSON string for database storage."""
        return json.dumps(self.metadata)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Validate role is one of the allowed values."""
        allowed_roles = ["user", "assistant", "system"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of {allowed_roles}")
        return v


class LongTermMemory(BaseModel):
    """Model for storing long-term memories with importance scoring."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int | None = None
    content: str = Field(..., description="Memory content")
    memory_type: str = Field(
        ..., description="Type of memory (preference, fact, lesson, instruction)"
    )
    importance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Importance score from 0.0 to 1.0"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    embedding: bytes | None = Field(
        None, description="Vector embedding for semantic search"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_accessed: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def tags_json(self) -> str:
        """Get tags as JSON string for database storage."""
        return json.dumps(self.tags)

    @property
    def metadata_json(self) -> str:
        """Get metadata as JSON string for database storage."""
        return json.dumps(self.metadata)

    @field_validator("memory_type")
    @classmethod
    def validate_memory_type(cls, v):
        """Validate memory type is one of the allowed values."""
        allowed_types = [
            "preference",
            "fact",
            "lesson",
            "instruction",
            "project_info",
            "user_info",
        ]
        if v not in allowed_types:
            raise ValueError(f"Memory type must be one of {allowed_types}")
        return v

    def update_last_accessed(self):
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.now(timezone.utc).isoformat()


class ProjectHistory(BaseModel):
    """Model for storing project history and evolution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int | None = None
    event_type: str = Field(
        ...,
        description="Type of event (file_modification, feature_addition, bug_fix, etc.)",
    )
    description: str = Field(..., description="Human-readable description of the event")
    file_path: str | None = Field(None, description="Path to the file involved")
    code_changes: str | None = Field(None, description="Summary of code changes")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def metadata_json(self) -> str:
        """Get metadata as JSON string for database storage."""
        return json.dumps(self.metadata)

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v):
        """Validate event type is one of the allowed values."""
        allowed_types = [
            "file_modification",
            "file_creation",
            "file_deletion",
            "feature_addition",
            "bug_fix",
            "refactoring",
            "architecture_change",
            "dependency_update",
            "configuration_change",
        ]
        if v not in allowed_types:
            raise ValueError(f"Event type must be one of {allowed_types}")
        return v


class MemorySearchResult(BaseModel):
    """Model for memory search results with relevance scoring."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    memory_id: int
    memory_type: str  # 'conversation', 'longterm', 'project'
    content: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SemanticSearchResult(BaseModel):
    """Model for semantic search results with similarity scoring."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    content: str
    memory_type: str
    importance_score: float
    tags: list[str]
    similarity_score: float = Field(
        ge=0.0, le=1.0, description="Cosine similarity score"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    last_accessed: str


class MemoryRetrievalResult(BaseModel):
    """Model for unified memory retrieval results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    memory_id: int
    source_type: str = Field(
        ..., description="Source type: conversation, longterm, or project"
    )
    content: str
    search_score: float = Field(
        ge=0.0, le=1.0, description="Combined search relevance score"
    )
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    recency_score: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    memory_type: str | None = Field(
        None, description="Memory type for long-term memories"
    )
    event_type: str | None = Field(None, description="Event type for project history")


class MemoryFilter(BaseModel):
    """Model for filtering memory search results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    memory_types: list[str] | None = Field(None, description="Filter by memory types")
    source_types: list[str] | None = Field(None, description="Filter by source types")
    min_importance: float | None = Field(None, ge=0.0, le=1.0)
    max_importance: float | None = Field(None, ge=0.0, le=1.0)
    min_recency: float | None = Field(None, ge=0.0, le=1.0)
    date_range: tuple[datetime, datetime] | None = Field(
        None, description="Date range filter"
    )
    tags: list[str] | None = Field(None, description="Filter by tags")
    event_types: list[str] | None = Field(
        None, description="Filter by project event types"
    )
    exclude_tags: list[str] | None = Field(
        None, description="Exclude memories with these tags"
    )
    session_id: str | None = Field(None, description="Filter by conversation session")
    file_path: str | None = Field(
        None, description="Filter by file path for project history"
    )
