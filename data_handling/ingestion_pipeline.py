"""
Ingestion Pipeline Module

Orchestrates the complete document ingestion workflow from
parsing to embedding to vector database storage.
"""

import os
from configs.config import RAGConfig
from data_handling.incident_parser import IncidentReportParser
from data_handling.vector_store import VectorStore


class IngestionPipeline:
    """Orchestrates the complete ingestion pipeline for incident reports."""

    def __init__(self, config: RAGConfig):
        """
        Initialize the ingestion pipeline.

        Args:
            config: RAG configuration object
        """
        self.config = config
        self.parser = IncidentReportParser(config)
        self.vector_store = VectorStore(config.index, config.embedding_model)

    def ingest_incident_reports(
            self,
            directory_path: str,
            file_pattern: str = "*.txt",
    ):
        """
        Complete pipeline to ingest incident reports from a directory.

        Args:
            directory_path: Path to directory containing incident reports
            file_pattern: Glob pattern for files to load (default: "*.txt")
            use_namespaces: Whether to organize by namespace (default: True)

        Returns:
            Dictionary with upload statistics
        """
        # Load and parse incident reports
        documents, metadatas, ids = self.parser.load_incident_reports(
            directory_path=directory_path,
            file_pattern=file_pattern
        )

        results = self.vector_store.upsert_by_namespace(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        return results


def main():
    """
    Standalone script to ingest incident reports into Pinecone.
    """
    # Initialize configuration
    print("Initializing RAG Configuration...")
    config = RAGConfig(
        index_name="incident-reports",
        model="models/gemini-2.0-flash",
        embedding_model="models/text-embedding-004",
        embedding_dimension=768
    )

    # Create ingestion pipeline
    pipeline = IngestionPipeline(config)

    # Load incident reports from directory
    # Use absolute path relative to the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level from data_handling/
    incident_reports_dir = os.path.join(project_root, "demo incident reports")

    # Ingest incident reports (organized by namespace)
    results = pipeline.ingest_incident_reports(
        directory_path=incident_reports_dir,
        file_pattern="*.txt"
    )

    print("\n" + "="*80)
    print("INGESTION COMPLETE")
    print("="*80)
    print(f"Total documents uploaded: {results.get('total_uploaded', results.get('uploaded', 0))}")
    print("="*80)


if __name__ == "__main__":
    main()