# Data Handling Package

Components for document ingestion, embedding generation, and vector database operations for the Incident Copilot system.

---

## Overview

The `data_handling` package provides a clean architecture for:
- **Parsing** incident reports and extracting structured sections
- **Embedding** text using Google's embedding models
- **Storing** vectors in Pinecone with namespace-based organization
- **Querying** the vector database for semantic similarity search

---

## Package Structure

```
data_handling/
├── __init__.py              
├── embeddings.py            # Embedding generation (shared)
├── vector_store.py          # Pinecone operations
├── document_parser.py       # Generic document utilities
├── incident_parser.py       # Incident report parsing
└── ingestion_pipeline.py    # Orchestration & batch processing
```

---

## Modules

### `embeddings.py` - Embedding Generation

Shared embedding logic for both ingestion and retrieval.

**Functions:**
- `embed_documents(documents, embedding_model)` - Batch embedding for document ingestion
- `embed_query(query, embedding_model)` - Single query embedding for semantic search

### `vector_store.py` - Pinecone Operations

Abstraction over Pinecone database operations.

**Class: VectorStore**

**Methods:**
- `upsert_vectors(documents, metadatas, ids, namespace)` - Add documents to Pinecone
- `upsert_by_namespace(documents, metadatas, ids)` - Namespace-organized uploads
- `query(query_vector, top_k, namespace)` - Semantic similarity search
---

### `document_parser.py` - Generic Parsing Utilities

Generic document parsing utilities for any document type.

**Functions:**
- `extract_section(text, section_headers, next_section_headers)` - Regex-based section extraction

---

### `incident_parser.py` - Incident Report Parsing

Specialized parsing for cybersecurity incident reports.

**Class: IncidentReportParser**

**Section Configuration:**
- `description` - Incident description section
- `impact` - Impact assessment section
- `response` - Response and forensic analysis section
- `recommendations` - Lessons learned and recommendations section

**Methods:**
- `extract_metadata(text, file_name)` - Extract incident metadata (ID, date, vehicle ID, threat category, severity, etc.)
- `parse_incident_report(file_path)` - Parse single incident report with cross-section metadata
- `load_incident_reports(directory_path, file_pattern)` - Batch load incident reports from directory

**Cross-Section Metadata:**
Each section's metadata contains text from ALL sections:
- `section_description_text`
- `section_impact_text`
- `section_response_text`
- `section_recommendations_text`

This enables querying one namespace (e.g., descriptions) while having access to recommendations in metadata.


---

### `ingestion_pipeline.py` - Complete Workflow

Orchestrates the complete ingestion workflow from parsing to embedding to storage.

**Class: IngestionPipeline**

**Methods:**
- `ingest_incident_reports(directory_path, file_pattern)` - Complete pipeline: parse → embed → store

---

## Demo Notebook

See `data_handling_demo.ipynb` in the project root for an interactive demonstration of all components.