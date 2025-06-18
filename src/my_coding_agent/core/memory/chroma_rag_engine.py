"""
ChromaDB-based RAG engine for efficient semantic search and memory retrieval.

This module provides a ChromaDB implementation that replaces the manual SQLite + cosine similarity
and memory retrieval, replacing the manual SQLite + cosine similarity approach.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

import chromadb
from crawl4ai import AsyncWebCrawler  # type: ignore[import-untyped]
from crawl4ai.extraction_strategy import (
    LLMExtractionStrategy,  # type: ignore[import-untyped]
)

from .chroma_utils import (
    CONVERSATIONS_COLLECTION,
    MEMORIES_COLLECTION,
    PROJECT_HISTORY_COLLECTION,
    add_documents_to_collection,
    get_chroma_client,
    get_collection_info,
    get_or_create_collection,
    query_collection,
    validate_azure_environment,
)
from .memory_types import LongTermMemory, SemanticSearchResult

logger = logging.getLogger(__name__)


class ChromaRAGEngine:
    """ChromaDB-based RAG engine for efficient semantic search and memory retrieval."""

    def __init__(
        self,
        memory_manager: Any = None,  # Optional for backward compatibility
        db_path: str | None = None,
        use_azure: bool = True,
        embedding_model: str = "azure",
    ):
        """Initialize ChromaDB RAG engine.

        Args:
            memory_manager: Optional MemoryManager instance (deprecated)
            db_path: Path to ChromaDB database directory
            use_azure: Whether to use Azure OpenAI embeddings
            embedding_model: Embedding model to use
        """
        self.memory_manager = memory_manager  # Keep for backward compatibility
        self.use_azure = use_azure
        self.embedding_model = embedding_model

        # Set up database path
        if db_path is None:
            if memory_manager and hasattr(memory_manager, "db_path"):
                # Create ChromaDB directory alongside SQLite database
                sqlite_path = Path(memory_manager.db_path)
                self.db_path = str(sqlite_path.parent / "chroma_db")
            else:
                # Use default path
                self.db_path = str(
                    Path.home() / ".config" / "my_coding_agent" / "chroma_db"
                )
        else:
            self.db_path = db_path

        # Ensure directory exists
        Path(self.db_path).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client and collections
        self.client = get_chroma_client(self.db_path)

        # Initialize collections for different memory types
        self.memories_collection = get_or_create_collection(
            self.client,
            MEMORIES_COLLECTION,
            embedding_model_name=self.embedding_model,
            use_azure=self.use_azure,
        )

        self.conversations_collection = get_or_create_collection(
            self.client,
            CONVERSATIONS_COLLECTION,
            embedding_model_name=self.embedding_model,
            use_azure=self.use_azure,
        )

        self.project_history_collection = get_or_create_collection(
            self.client,
            PROJECT_HISTORY_COLLECTION,
            embedding_model_name=self.embedding_model,
            use_azure=self.use_azure,
        )

        # Initialize crawl4ai for web content extraction
        self._crawler = None

        # Validate Azure configuration if using Azure embeddings
        if self.use_azure and self.embedding_model == "azure":
            validation = validate_azure_environment()
            if not validation["all_set"]:
                logger.warning(
                    f"Azure configuration incomplete: {validation['missing_vars']}"
                )

        logger.info(f"ChromaRAGEngine initialized with database at {self.db_path}")

    async def _get_crawler(self) -> AsyncWebCrawler:
        """Get or create crawler instance."""
        if self._crawler is None:
            self._crawler = AsyncWebCrawler(verbose=False)
            await self._crawler.start()
        return self._crawler

    def store_memory_with_embedding(self, memory: LongTermMemory) -> str:
        """Store a memory in ChromaDB with automatic embedding generation.

        Args:
            memory: LongTermMemory instance to store

        Returns:
            Document ID for the stored memory
        """
        try:
            # Generate unique ID for the memory
            doc_id = f"memory_{memory.id}_{int(time.time())}"

            # Prepare document content
            content = memory.content

            # Prepare metadata
            metadata = {
                "memory_id": memory.id,
                "memory_type": memory.memory_type,
                "importance_score": memory.importance_score,
                "created_at": memory.created_at if memory.created_at else "",
                "updated_at": getattr(memory, "updated_at", memory.last_accessed)
                if hasattr(memory, "updated_at")
                else memory.last_accessed,
                "tags": ",".join(memory.tags) if memory.tags else "",
                "source": "memory_manager",
            }

            # Add additional metadata if available
            if memory.metadata:
                for key, value in memory.metadata.items():
                    # Ensure metadata values are strings for ChromaDB
                    metadata[f"meta_{key}"] = str(value)

            # Add to ChromaDB collection
            add_documents_to_collection(
                self.memories_collection,
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata],
            )

            logger.info(f"Stored memory {memory.id} in ChromaDB with ID: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to store memory with embedding: {e}")
            raise

    def store_conversation_with_embedding(
        self, message_content: str, role: str, session_id: str
    ) -> str:
        """Store a conversation message in ChromaDB.

        Args:
            message_content: Content of the message
            role: Role of the message sender (user/assistant)
            session_id: Session ID for the conversation

        Returns:
            Document ID for the stored conversation
        """
        try:
            doc_id = f"conv_{session_id}_{role}_{int(time.time())}"

            metadata = {
                "role": role,
                "session_id": session_id,
                "timestamp": time.time(),
                "source": "conversation",
            }

            add_documents_to_collection(
                self.conversations_collection,
                ids=[doc_id],
                documents=[message_content],
                metadatas=[metadata],
            )

            return doc_id

        except Exception as e:
            logger.error(f"Failed to store conversation with embedding: {e}")
            raise

    def store_project_history_with_embedding(
        self, file_path: str, event_type: str, content: str
    ) -> str:
        """Store project history in ChromaDB.

        Args:
            file_path: Path to the file
            event_type: Type of event (file_created, file_modified, etc.)
            content: Content or description of the change

        Returns:
            Document ID for the stored project history
        """
        try:
            doc_id = f"project_{event_type}_{int(time.time())}"

            metadata = {
                "file_path": file_path,
                "event_type": event_type,
                "timestamp": time.time(),
                "source": "project_history",
            }

            add_documents_to_collection(
                self.project_history_collection,
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata],
            )

            return doc_id

        except Exception as e:
            logger.error(f"Failed to store project history with embedding: {e}")
            raise

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.0,
        memory_types: list[str] | None = None,
        importance_threshold: float | None = None,
    ) -> list[SemanticSearchResult]:
        """Perform semantic search across all memory types.

        Args:
            query: Search query
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            memory_types: Optional list of memory types to filter by
            importance_threshold: Optional minimum importance score

        Returns:
            List of SemanticSearchResult objects
        """
        try:
            results = []

            # Search memories collection
            memory_results = self._search_collection(
                self.memories_collection,
                query,
                limit,
                similarity_threshold,
                memory_types,
                importance_threshold,
            )
            results.extend(memory_results)

            # Search conversations if no specific memory types requested
            if not memory_types or "conversation" in memory_types:
                conv_results = self._search_collection(
                    self.conversations_collection, query, limit, similarity_threshold
                )
                results.extend(conv_results)

            # Search project history if no specific memory types requested
            if not memory_types or "project_history" in memory_types:
                project_results = self._search_collection(
                    self.project_history_collection, query, limit, similarity_threshold
                )
                results.extend(project_results)

            # Sort by similarity score and limit results
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            return []

    def _search_collection(
        self,
        collection: chromadb.Collection,
        query: str,
        limit: int,
        similarity_threshold: float = 0.0,
        memory_types: list[str] | None = None,
        importance_threshold: float | None = None,
    ) -> list[SemanticSearchResult]:
        """Search a specific ChromaDB collection.

        Args:
            collection: ChromaDB collection to search
            query: Search query
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            memory_types: Optional memory types filter
            importance_threshold: Optional importance threshold

        Returns:
            List of SemanticSearchResult objects
        """
        try:
            # Build where clause for filtering
            where_clause = {}

            if memory_types and collection.name == MEMORIES_COLLECTION:
                if len(memory_types) == 1:
                    where_clause["memory_type"] = {"$eq": memory_types[0]}
                else:
                    where_clause["memory_type"] = {"$in": memory_types}

            if (
                importance_threshold is not None
                and collection.name == MEMORIES_COLLECTION
            ):
                where_clause["importance_score"] = {"$gte": importance_threshold}

            # Query the collection
            chroma_results = query_collection(
                collection,
                query,
                n_results=limit,
                where=where_clause if where_clause else None,
            )

            # Convert to SemanticSearchResult objects
            results = []
            if chroma_results and chroma_results.get("documents"):
                for doc, metadata, distance in zip(
                    chroma_results["documents"][0],
                    chroma_results["metadatas"][0],
                    chroma_results["distances"][0],
                    strict=False,
                ):
                    similarity = 1 - distance  # Convert distance to similarity

                    # Apply similarity threshold
                    if similarity < similarity_threshold:
                        continue

                    # Create SemanticSearchResult
                    result = SemanticSearchResult(
                        id=metadata.get("memory_id", 0),
                        content=doc,
                        similarity_score=similarity,
                        memory_type=metadata.get("memory_type", "unknown"),
                        importance_score=float(metadata.get("importance_score", 0.0)),
                        tags=metadata.get("tags", "").split(",")
                        if metadata.get("tags")
                        else [],
                        created_at=metadata.get("created_at", ""),
                        last_accessed=metadata.get(
                            "last_accessed", metadata.get("created_at", "")
                        ),
                        metadata=metadata,
                    )
                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"Failed to search collection {collection.name}: {e}")
            return []

    def find_similar_memories(
        self,
        memory_id: int,
        limit: int = 5,
        similarity_threshold: float = 0.3,
    ) -> list[SemanticSearchResult]:
        """Find memories similar to a given memory.

        Args:
            memory_id: ID of the reference memory
            limit: Maximum number of similar memories to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of similar memories
        """
        try:
            # First, get the reference memory content
            memory = self.memory_manager.get_long_term_memory(memory_id)
            if not memory:
                logger.warning(f"Memory {memory_id} not found")
                return []

            # Use the memory content as query to find similar ones
            similar_results = self.semantic_search(
                query=memory.content,
                limit=limit + 1,  # +1 to account for the original memory
                similarity_threshold=similarity_threshold,
            )

            # Filter out the original memory and return others
            filtered_results = [
                result for result in similar_results if result.id != memory_id
            ]

            return filtered_results[:limit]

        except Exception as e:
            logger.error(f"Failed to find similar memories: {e}")
            return []

    async def extract_and_embed_web_content(self, url: str) -> dict[str, Any]:
        """Extract content from web URL and generate embeddings using crawl4ai.

        Args:
            url: URL to extract content from

        Returns:
            Dictionary containing extracted content and metadata
        """
        try:
            crawler = await self._get_crawler()

            # Extract content using crawl4ai
            result = await crawler.arun(
                url=url,
                extraction_strategy=LLMExtractionStrategy(
                    provider="openai",
                    api_token=os.getenv("AZURE_OPENAI_API_KEY"),
                    instruction="Extract the main content, removing navigation, ads, and boilerplate text.",
                ),
            )

            if result.success:
                content = result.extracted_content or result.cleaned_html

                # Store in ChromaDB
                doc_id = f"web_{int(time.time())}"
                metadata = {
                    "url": url,
                    "title": result.title or "Untitled",
                    "source": "web_crawl",
                    "extracted_at": time.time(),
                }

                add_documents_to_collection(
                    self.memories_collection,
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[metadata],
                )

                return {
                    "success": True,
                    "content": content,
                    "title": result.title,
                    "url": url,
                    "doc_id": doc_id,
                    "metadata": metadata,
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to extract content",
                    "url": url,
                }

        except Exception as e:
            logger.error(f"Failed to extract and embed web content: {e}")
            return {"success": False, "error": str(e), "url": url}

    def get_memory_statistics(self) -> dict[str, Any]:
        """Get statistics about stored memories in ChromaDB.

        Returns:
            Dictionary containing memory statistics
        """
        try:
            stats = {
                "memories": get_collection_info(self.memories_collection),
                "conversations": get_collection_info(self.conversations_collection),
                "project_history": get_collection_info(self.project_history_collection),
                "total_documents": (
                    self.memories_collection.count()
                    + self.conversations_collection.count()
                    + self.project_history_collection.count()
                ),
                "database_path": self.db_path,
                "embedding_model": self.embedding_model,
                "use_azure": self.use_azure,
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get memory statistics: {e}")
            return {"error": str(e)}

    def delete_old_project_history(self, retention_cutoff_timestamp: float) -> int:
        """Delete old project history entries from ChromaDB.

        Args:
            retention_cutoff_timestamp: Timestamp cutoff for deletion

        Returns:
            Number of entries deleted
        """
        try:
            # Get all project history entries
            all_results = self.project_history_collection.get(
                include=["metadatas", "documents"]
            )

            if not all_results["ids"]:
                return 0

            # Find entries older than cutoff
            ids_to_delete = []
            metadatas = all_results["metadatas"]
            if metadatas:
                for i, metadata in enumerate(metadatas):
                    timestamp_val = metadata.get("timestamp", 0) if metadata else 0
                    try:
                        timestamp = (
                            float(timestamp_val) if timestamp_val is not None else 0
                        )
                        if timestamp < retention_cutoff_timestamp:
                            ids_to_delete.append(all_results["ids"][i])
                    except (ValueError, TypeError):
                        continue

            if not ids_to_delete:
                return 0

            # Delete the old entries
            self.project_history_collection.delete(ids=ids_to_delete)

            logger.info(f"Deleted {len(ids_to_delete)} old project history entries")
            return len(ids_to_delete)

        except Exception as e:
            logger.error(f"Failed to delete old project history: {e}")
            return 0

    def delete_old_conversations(self, retention_cutoff_timestamp: float) -> int:
        """Delete old conversation entries from ChromaDB.

        Args:
            retention_cutoff_timestamp: Timestamp cutoff for deletion

        Returns:
            Number of entries deleted
        """
        try:
            # Get all conversation entries
            all_results = self.conversations_collection.get(
                include=["metadatas", "documents"]
            )

            if not all_results["ids"]:
                return 0

            # Find entries older than cutoff
            ids_to_delete = []
            metadatas = all_results["metadatas"]
            if metadatas:
                for i, metadata in enumerate(metadatas):
                    timestamp_val = metadata.get("timestamp", 0) if metadata else 0
                    try:
                        timestamp = (
                            float(timestamp_val) if timestamp_val is not None else 0
                        )
                        if timestamp < retention_cutoff_timestamp:
                            ids_to_delete.append(all_results["ids"][i])
                    except (ValueError, TypeError):
                        continue

            if not ids_to_delete:
                return 0

            # Delete the old entries
            self.conversations_collection.delete(ids=ids_to_delete)

            logger.info(f"Deleted {len(ids_to_delete)} old conversation entries")
            return len(ids_to_delete)

        except Exception as e:
            logger.error(f"Failed to delete old conversations: {e}")
            return 0

    def delete_old_memories(self, retention_cutoff_timestamp: float) -> int:
        """Delete old memory entries from ChromaDB.

        Args:
            retention_cutoff_timestamp: Timestamp cutoff for deletion

        Returns:
            Number of entries deleted
        """
        try:
            # Get all memory entries
            all_results = self.memories_collection.get(
                include=["metadatas", "documents"]
            )

            if not all_results["ids"]:
                return 0

            # Find entries older than cutoff (use created_at or updated_at)
            ids_to_delete = []
            metadatas = all_results["metadatas"]
            if metadatas:
                for i, metadata in enumerate(metadatas):
                    # Try multiple timestamp fields
                    timestamp = 0
                    for field in ["timestamp", "created_at", "updated_at"]:
                        if field in metadata and metadata[field]:
                            try:
                                field_value = metadata[field]
                                timestamp = (
                                    float(field_value) if field_value is not None else 0
                                )
                                break
                            except (ValueError, TypeError):
                                continue

                    if timestamp > 0 and timestamp < retention_cutoff_timestamp:
                        ids_to_delete.append(all_results["ids"][i])

            if not ids_to_delete:
                return 0

            # Delete the old entries
            self.memories_collection.delete(ids=ids_to_delete)

            logger.info(f"Deleted {len(ids_to_delete)} old memory entries")
            return len(ids_to_delete)

        except Exception as e:
            logger.error(f"Failed to delete old memories: {e}")
            return 0

    def clear_all_memories(self) -> bool:
        """Clear all memories from ChromaDB collections.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete and recreate collections
            self.client.delete_collection(MEMORIES_COLLECTION)
            self.client.delete_collection(CONVERSATIONS_COLLECTION)
            self.client.delete_collection(PROJECT_HISTORY_COLLECTION)

            # Recreate collections
            self.memories_collection = get_or_create_collection(
                self.client,
                MEMORIES_COLLECTION,
                embedding_model_name=self.embedding_model,
                use_azure=self.use_azure,
            )

            self.conversations_collection = get_or_create_collection(
                self.client,
                CONVERSATIONS_COLLECTION,
                embedding_model_name=self.embedding_model,
                use_azure=self.use_azure,
            )

            self.project_history_collection = get_or_create_collection(
                self.client,
                PROJECT_HISTORY_COLLECTION,
                embedding_model_name=self.embedding_model,
                use_azure=self.use_azure,
            )

            logger.info("Cleared all memories from ChromaDB")
            return True

        except Exception as e:
            logger.error(f"Failed to clear all memories: {e}")
            return False

    async def close(self) -> None:
        """Close the RAG engine and cleanup resources."""
        try:
            if self._crawler:
                await self._crawler.close()
                self._crawler = None

            logger.info("ChromaRAGEngine closed successfully")

        except Exception as e:
            logger.error(f"Error closing ChromaRAGEngine: {e}")

    def __del__(self):
        """Cleanup on deletion."""
        # Note: Cannot use async in __del__, so we just log
        if hasattr(self, "_crawler") and self._crawler:
            logger.warning(
                "ChromaRAGEngine deleted with active crawler - call close() explicitly"
            )
