import time
import uuid
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

import google.generativeai as genai
from config import RAGConfig


class DocumentIngestion:
    """Handles document ingestion into Pinecone."""

    def __init__(self, config: RAGConfig):
        """
        Initialize the document ingestion pipeline.

        Args:
            config: RAG configuration object
        """
        self.config = config

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.

        Args:
            documents: List of document texts

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for i, doc in enumerate(documents, 1):
            result = genai.embed_content(
                model=self.config.embedding_model,
                content=doc,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        print(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings

    def add_documents(
            self,
            documents: List[str],
            metadatas: List[Dict[str, Any]] = None,
            ids: List[str] = None,
            batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Add documents to the Pinecone vector database.

        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries (optional)
            ids: List of document IDs (optional, will auto-generate if not provided)
            batch_size: Number of vectors to upload per batch

        Returns:
            Dictionary with upload statistics
        """
        # Auto-generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
            print(f"Generated {len(ids)} unique document IDs")

        # Create empty metadata if not provided
        if metadatas is None:
            metadatas = [{} for _ in documents]

        # Validate inputs
        if not (len(documents) == len(metadatas) == len(ids)):
            raise ValueError(
                f"Length mismatch: documents={len(documents)}, "
                f"metadatas={len(metadatas)}, ids={len(ids)}"
            )

        # Generate embeddings
        embeddings = self.embed_documents(documents)

        # Prepare vectors for Pinecone
        vectors = []
        for doc_id, embedding, doc_text, metadata in zip(ids, embeddings, documents, metadatas):
            # Add the document text to metadata so we can retrieve it later
            metadata_with_text = metadata.copy()
            metadata_with_text['text'] = doc_text
            metadata_with_text['length'] = len(doc_text)

            vectors.append({
                'id': doc_id,
                'values': embedding,
                'metadata': metadata_with_text
            })

        # Upsert to Pinecone in batches
        uploaded_count = 0
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.config.index.upsert(vectors=batch)
            uploaded_count += len(batch)
            print(f"  Uploaded batch {i // batch_size + 1}: {uploaded_count}/{len(vectors)} vectors")
            time.sleep(0.1)  # Small delay to avoid rate limiting

        # Get index statistics
        time.sleep(1)  # Wait for index to update
        stats = self.config.index.describe_index_stats()

        return {
            "uploaded": uploaded_count,
            "total_in_index": stats.total_vector_count,
            "dimension": stats.dimension,
            "index_stats": stats
        }

    def load_from_file(self, file_path: str, text_column: str = "text") -> List[str]:
        """
        Load documents from a file (CSV, JSON, or TXT).

        Args:
            file_path: Path to the file
            text_column: Column name containing text (for CSV/JSON)

        Returns:
            List of document texts
        """
        import os
        with open(file_path, 'r', encoding='utf-8') as f:
            # Each line is a document
            documents = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(documents)} documents from {file_path}")
        return documents

    def extract_section(
            self,
            text: str,
            section_headers: List[str],
            next_section_headers: List[str]
    ) -> str:
        """
        Extract a specific section from the incident report.

        Args:
            text: Full incident report text
            section_headers: Possible headers marking the start of the section
            next_section_headers: Headers that mark the end of this section

        Returns:
            Extracted section text (empty string if not found)
        """
        # Try each possible section header
        start_pos = -1
        for header in section_headers:
            pattern = re.escape(header) + r'\s*'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start_pos = match.end()
                break

        if start_pos == -1:
            return ""

        # Find the section end
        end_pos = len(text)

        if next_section_headers:
            for next_header in next_section_headers:
                next_pattern = re.escape(next_header) + r'\s*'
                next_match = re.search(next_pattern, text[start_pos:], re.IGNORECASE)
                if next_match:
                    potential_end = start_pos + next_match.start()
                    end_pos = min(end_pos, potential_end)

        section_text = text[start_pos:end_pos].strip()
        return section_text

    def parse_incident_report_with_sections(
            self,
            file_path: str
    ) -> List[Tuple[str, Dict[str, Any], str]]:
        """
        Parse incident report and extract both full text and individual sections.

        Args:
            file_path: Path to the incident report text file

        Returns:
            List of tuples (text, metadata, document_id) for full report and each section
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()

        # Get base metadata (same extraction logic as parse_incident_report)
        base_metadata = {
            'source': 'incident_report',
            'file_name': os.path.basename(file_path)
        }

        def clean_value(value: str) -> str:
            return value.strip().rstrip('.,;:')

        # Extract all the metadata fields
        incident_id_match = re.search(r'Incident ID:\s*([A-Z0-9-]+)', full_text, re.IGNORECASE)
        if incident_id_match:
            base_metadata['incident_id'] = incident_id_match.group(1).strip()

        date_match = re.search(
            r'Date of Detection:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}(?:\s+[0-9]{2}:[0-9]{2})?(?:\s+UTC)?)',
            full_text, re.IGNORECASE
        )
        if date_match:
            base_metadata['date_of_detection'] = date_match.group(1).strip()
            year_match = re.search(r'([0-9]{4})', date_match.group(1))
            month_match = re.search(r'[0-9]{4}-([0-9]{2})', date_match.group(1))
            if year_match:
                base_metadata['year'] = year_match.group(1)
            if month_match:
                base_metadata['month'] = month_match.group(1)

        vehicle_id_match = re.search(r'Vehicle ID:\s*([A-Z0-9/-]+)(?:\s*\(([^)]+)\))?', full_text, re.IGNORECASE)
        if vehicle_id_match:
            base_metadata['vehicle_id'] = vehicle_id_match.group(1).strip()
            if vehicle_id_match.group(2):
                base_metadata['vehicle_id_note'] = vehicle_id_match.group(2).strip()

        fleet_match = re.search(r'Fleet:\s*["\']([^"\']+)["\']', full_text, re.IGNORECASE)
        if fleet_match:
            base_metadata['fleet'] = fleet_match.group(1).strip()

        threat_match = re.search(
            r'Threat Category:\s*([^.\n]+?)(?=\s+Detection Method:|\s+Severity:|\n|$)',
            full_text, re.IGNORECASE
        )
        if threat_match:
            base_metadata['threat_category'] = clean_value(threat_match.group(1))

        detection_match = re.search(
            r'Detection Method:\s*([^.\n]+?)(?=\s+Severity:|\s+Status:|\n|\.)',
            full_text, re.IGNORECASE
        )
        if detection_match:
            base_metadata['detection_method'] = clean_value(detection_match.group(1))

        severity_match = re.search(r'Severity:\s*([^.\n]+)', full_text, re.IGNORECASE)
        if severity_match:
            base_metadata['severity'] = clean_value(severity_match.group(1))

        status_match = re.search(r'Status:\s*([^.\n]+)', full_text, re.IGNORECASE)
        if status_match:
            base_metadata['status'] = clean_value(status_match.group(1))

        # Prepare results list
        results = []
        incident_id = base_metadata.get('incident_id', os.path.splitext(os.path.basename(file_path))[0])

        # 1. Add full report
        full_metadata = base_metadata.copy()
        full_metadata['section_type'] = 'full_report'
        full_metadata['token_count'] = self.config.count_tokens(full_text)
        results.append((full_text, full_metadata, f"{incident_id}_full"))

        # 2. Extract and add sections
        section_configs = {
            'description': {
                'headers': ['Detailed Incident Description:', 'Incident Description:'],
                'next_headers': ['Impact Assessment:', 'Response and Forensic Analysis:',
                                 'Response:', 'Lessons Learned:', 'Recommendations:']
            },
            'impact': {
                'headers': ['Impact Assessment:', 'Impact:'],
                'next_headers': ['Response and Forensic Analysis:', 'Response:',
                                 'Lessons Learned:', 'Recommendations:']
            },
            'response': {
                'headers': ['Response and Forensic Analysis:', 'Response:', 'Forensic Analysis:'],
                'next_headers': ['Lessons Learned:', 'Recommendations:']
            },
            'recommendations': {
                'headers': ['Lessons Learned:', 'Recommendations:'],
                'next_headers': []
            }
        }

        for section_key, config in section_configs.items():
            section_text = self.extract_section(
                full_text,
                config['headers'],
                config['next_headers']
            )

            if section_text:
                section_metadata = base_metadata.copy()
                section_metadata['section_type'] = section_key
                section_metadata['token_count'] = self.config.count_tokens(section_text)

                doc_id = f"{incident_id}_{section_key}"
                results.append((section_text, section_metadata, doc_id))

        return results

    def load_incident_reports_with_sections(
            self,
            directory_path: str,
            file_pattern: str = "*.txt"
    ) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """
        Load incident reports and extract full text + individual sections.
        Each report generates multiple documents (full + sections).

        Args:
            directory_path: Path to directory containing incident reports
            file_pattern: Glob pattern for files to load (default: "*.txt")

        Returns:
            Tuple of (documents, metadatas, ids) including full reports and sections
        """
        dir_path = Path(directory_path)
        files = sorted(dir_path.glob(file_pattern))

        all_documents = []
        all_metadatas = []
        all_ids = []

        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] Processing: {file_path.name}")

            # Parse report and extract all sections
            sections = self.parse_incident_report_with_sections(str(file_path))

            # Add all sections (full report + individual sections)
            for text, metadata, doc_id in sections:
                all_documents.append(text)
                all_metadatas.append(metadata)
                all_ids.append(doc_id)

                section_type = metadata.get('section_type', 'unknown')
                tokens = metadata.get('token_count', 0)
                print(f"  ✓ {section_type}: {tokens} tokens (ID: {doc_id})")

            print(f"  → Generated {len(sections)} documents from this report\n")
        return all_documents, all_metadatas, all_ids


def main():
    """
    Load and ingest incident reports from the demo directory.
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
    ingestion = DocumentIngestion(config)

    # Load incident reports from directory
    incident_reports_dir = os.path.join("demo incident reports", "Gemini")

    # Load incident reports WITH SECTIONS (full report + individual sections)
    documents, metadatas, ids = ingestion.load_incident_reports_with_sections(
        directory_path=incident_reports_dir,
        file_pattern="*.txt"
    )

    # Ingest documents to Pinecone
    results = ingestion.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )


if __name__ == "__main__":
    main()
