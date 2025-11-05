"""
Data Handling Package

Modular components for document ingestion, embedding generation,
and vector database operations for the Incident Copilot system.
"""

from .embeddings import embed_documents, embed_query
from .vector_store import VectorStore
from .incident_parser import IncidentReportParser
from .ingestion_pipeline import IngestionPipeline

__all__ = [
    'embed_documents',
    'embed_query',
    'VectorStore',
    'IncidentReportParser',
    'IngestionPipeline'
]