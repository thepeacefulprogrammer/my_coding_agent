"""
ChromaDB Utilities for consistent client initialization across memory components.

This module provides standardized ChromaDB client initialization to ensure
all memory components use consistent parameters and settings.
"""

import logging
import os
from typing import Any

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from more_itertools import batched

logger = logging.getLogger(__name__)


def get_azure_embedding_function(
    azure_endpoint: str | None = None,
    api_key: str | None = None,
    api_version: str | None = None,
    deployment_name: str | None = None,
) -> embedding_functions.OpenAIEmbeddingFunction:
    """Create Azure OpenAI embedding function.

    Args:
        azure_endpoint: Azure OpenAI endpoint URL
        api_key: Azure OpenAI API key
        api_version: Azure OpenAI API version
        deployment_name: Azure deployment name for embeddings

    Returns:
        Azure OpenAI embedding function
    """
    # Use environment variables as defaults (same as AI agent)
    azure_endpoint = azure_endpoint or os.getenv("ENDPOINT")
    api_key = api_key or os.getenv("API_KEY")
    api_version = api_version or os.getenv("API_VERSION", "2024-02-01")
    deployment_name = deployment_name or os.getenv(
        "EMBEDDINGS_MODEL", "text-embedding-3-large"
    )

    if not azure_endpoint or not api_key:
        raise ValueError("Azure endpoint and API key are required")

    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        api_base=azure_endpoint,
        api_type="azure",
        api_version=api_version,
        deployment_id=deployment_name,
    )


def get_sentence_transformer_embedding_function(
    model_name: str = "all-MiniLM-L6-v2",
) -> embedding_functions.SentenceTransformerEmbeddingFunction:
    """Create SentenceTransformer embedding function.

    Args:
        model_name: Name of the SentenceTransformer model

    Returns:
        SentenceTransformer embedding function
    """
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=model_name
    )


def get_chroma_client(persist_directory: str) -> chromadb.PersistentClient:
    """Get a ChromaDB client with the specified persistence directory.

    Args:
        persist_directory: Directory where ChromaDB will store its data

    Returns:
        A ChromaDB PersistentClient
    """
    # Create the directory if it doesn't exist
    os.makedirs(persist_directory, exist_ok=True)

    # Configure settings for privacy and development
    settings = Settings(anonymized_telemetry=False, allow_reset=True)

    return chromadb.PersistentClient(path=persist_directory, settings=settings)


def get_or_create_collection(
    client: chromadb.PersistentClient,
    collection_name: str,
    embedding_model_name: str = "azure",
    distance_function: str = "cosine",
    use_azure: bool = True,
) -> chromadb.Collection:
    """Get an existing collection or create a new one if it doesn't exist.

    Args:
        client: ChromaDB client
        collection_name: Name of the collection
        embedding_model_name: Name of the embedding model to use or "azure" for Azure OpenAI
        distance_function: Distance function to use for similarity search
        use_azure: Whether to use Azure OpenAI embeddings (default: True)

    Returns:
        A ChromaDB Collection
    """
    # Create embedding function based on configuration
    if use_azure and embedding_model_name == "azure":
        try:
            embedding_func = get_azure_embedding_function()
            logger.info("Using Azure OpenAI embeddings for ChromaDB collection")
        except ValueError as e:
            logger.warning(
                f"Azure configuration missing ({e}), falling back to SentenceTransformer"
            )
            embedding_func = get_sentence_transformer_embedding_function(
                "all-MiniLM-L6-v2"
            )
    else:
        # Use SentenceTransformer for backward compatibility
        embedding_func = get_sentence_transformer_embedding_function(
            embedding_model_name
        )
        logger.info(f"Using SentenceTransformer model: {embedding_model_name}")

    # Try to get the collection, create it if it doesn't exist
    try:
        return client.get_collection(
            name=collection_name, embedding_function=embedding_func
        )
    except Exception:
        return client.create_collection(
            name=collection_name,
            embedding_function=embedding_func,
            metadata={"hnsw:space": distance_function},
        )


def add_documents_to_collection(
    collection: chromadb.Collection,
    ids: list[str],
    documents: list[str],
    metadatas: list[dict[str, Any]] | None = None,
    batch_size: int = 100,
) -> None:
    """Add documents to a ChromaDB collection in batches.

    Args:
        collection: ChromaDB collection
        ids: List of document IDs
        documents: List of document texts
        metadatas: Optional list of metadata dictionaries for each document
        batch_size: Size of batches for adding documents
    """
    # Create default metadata if none provided
    if metadatas is None:
        metadatas = [{}] * len(documents)

    # Create document indices
    document_indices = list(range(len(documents)))

    # Add documents in batches
    for batch in batched(document_indices, batch_size):
        # Get the start and end indices for the current batch
        start_idx = batch[0]
        end_idx = batch[-1] + 1  # +1 because end_idx is exclusive

        # Add the batch to the collection
        collection.add(
            ids=ids[start_idx:end_idx],
            documents=documents[start_idx:end_idx],
            metadatas=metadatas[start_idx:end_idx],
        )


def query_collection(
    collection: chromadb.Collection,
    query_text: str,
    n_results: int = 5,
    where: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Query a ChromaDB collection for similar documents.

    Args:
        collection: ChromaDB collection
        query_text: Text to search for
        n_results: Number of results to return
        where: Optional filter to apply to the query

    Returns:
        Query results containing documents, metadatas, distances, and ids
    """
    # Convert multiple filters to ChromaDB $and syntax if needed
    if where and len(where) > 1:
        # Convert {key1: val1, key2: val2} to {"$and": [{"key1": {"$eq": val1}}, {"key2": {"$eq": val2}}]}
        where = {"$and": [{key: {"$eq": value}} for key, value in where.items()]}
    elif where:
        # Single filter - convert to proper format
        for key, value in where.items():
            if not isinstance(value, dict):
                where[key] = {"$eq": value}

    # Query the collection
    return collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )


def format_results_as_context(query_results: dict[str, Any]) -> str:
    """Format ChromaDB query results as context for LLM.

    Args:
        query_results: Results from ChromaDB query

    Returns:
        Formatted context string
    """
    if not query_results or not query_results.get("documents"):
        return ""

    context_parts = []
    for doc, metadata, distance in zip(
        query_results["documents"][0],
        query_results["metadatas"][0],
        query_results["distances"][0],
        strict=False,
    ):
        similarity = 1 - distance  # Convert distance to similarity
        context_parts.append(f"[Relevance: {similarity:.3f}] {doc}")

    return "\n\n".join(context_parts)


# Constants for consistent parameter usage
DEFAULT_SETTINGS = Settings(anonymized_telemetry=False, allow_reset=True)

DEFAULT_AZURE_API_VERSION = "2024-02-01"
DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"

# Collection names for consistency
MEMORIES_COLLECTION = "memories"
CONVERSATIONS_COLLECTION = "conversations"
PROJECT_HISTORY_COLLECTION = "project_history"


def validate_azure_environment() -> dict[str, Any]:
    """Validate that required Azure environment variables are set.

    Returns:
        Dictionary with validation results and environment info
    """
    required_vars = [
        "ENDPOINT",
        "API_KEY",
        "EMBEDDINGS_MODEL",
    ]
    results = {"all_set": True, "missing_vars": [], "env_info": {}}

    for var in required_vars:
        value = os.getenv(var)
        if value:
            results["env_info"][var] = "✓ Set"
        else:
            results["all_set"] = False
            results["missing_vars"].append(var)
            results["env_info"][var] = "✗ Missing"

    return results


def get_collection_info(collection: chromadb.Collection) -> dict[str, Any]:
    """Get information about a ChromaDB collection.

    Args:
        collection: ChromaDB collection

    Returns:
        Dictionary containing collection information
    """
    try:
        count = collection.count()
        return {
            "name": collection.name,
            "count": count,
            "metadata": collection.metadata,
            "embedding_function": str(collection._embedding_function),
        }
    except Exception as e:
        logger.error(f"Error getting collection info: {e}")
        return {"error": str(e)}
