"""
Embedding Generation Module

Handles generation of embeddings for both documents (ingestion)
and queries (retrieval) using Google Generative AI.
"""

from typing import List
import google.generativeai as genai


def embed_documents(documents: List[str], embedding_model: str) -> List[List[float]]:
    """
    Generate embeddings for a list of documents.

    Args:
        documents: List of document texts
        embedding_model: Model name for embedding generation

    Returns:
        List of embedding vectors
    """
    embeddings = []

    for i, doc in enumerate(documents, 1):
        result = genai.embed_content(
            model=embedding_model,
            content=doc,
            task_type="retrieval_document"
        )
        embeddings.append(result['embedding'])

    print(f"Successfully generated {len(embeddings)} embeddings")
    return embeddings


def embed_query(query: str, embedding_model: str) -> List[float]:
    """
    Generate embedding for a single query.

    Args:
        query: Query text
        embedding_model: Model name for embedding generation

    Returns:
        Embedding vector
    """
    result = genai.embed_content(
        model=embedding_model,
        content=query,
        task_type="retrieval_query"
    )
    return result['embedding']