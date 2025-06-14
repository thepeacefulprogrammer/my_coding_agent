"""Memory system for AI Agent chat persistence and intelligence."""

from __future__ import annotations

from .chroma_rag_engine import ChromaRAGEngine
from .chroma_utils import (
    CONVERSATIONS_COLLECTION,
    MEMORIES_COLLECTION,
    PROJECT_HISTORY_COLLECTION,
    add_documents_to_collection,
    get_chroma_client,
    get_or_create_collection,
    query_collection,
    validate_azure_environment,
)
from .memory_classifier import MemoryClassifier
from .memory_transparency import (
    MemoryTransparencyManager,
    MemoryTransparencySettings,
    MemoryUsageEvent,
    TransparencyLevel,
)
from .memory_types import ConversationMessage, LongTermMemory, ProjectHistory

__all__ = [
    "ConversationMessage",
    "LongTermMemory",
    "ProjectHistory",
    "MemoryClassifier",
    "MemoryTransparencyManager",
    "MemoryTransparencySettings",
    "MemoryUsageEvent",
    "TransparencyLevel",
    "ChromaRAGEngine",
    "get_chroma_client",
    "get_or_create_collection",
    "add_documents_to_collection",
    "query_collection",
    "validate_azure_environment",
    "MEMORIES_COLLECTION",
    "CONVERSATIONS_COLLECTION",
    "PROJECT_HISTORY_COLLECTION",
]
