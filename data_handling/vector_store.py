"""
Vector Store Module

Handles all Pinecone vector database operations including
document upsert, namespace management, and similarity search.
"""

import time
import uuid
from typing import List, Dict, Any

from data_handling.embeddings import embed_documents


class VectorStore:
    """Manages vector database operations for the Incident Copilot system."""

    def __init__(self, index, embedding_model: str):
        """
        Initialize the vector store.

        Args:
            index: index instance
            embedding_model: Model name for embedding generation
        """
        self.index = index
        self.embedding_model = embedding_model

    def upsert_vectors(
            self,
            documents: List[str],
            metadatas: List[Dict[str, Any]] = None,
            ids: List[str] = None,
            batch_size: int = 100,
            namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Add documents to the Pinecone vector database.

        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries (optional)
            ids: List of document IDs (optional, will auto-generate if not provided)
            batch_size: Number of vectors to upload per batch
            namespace: Pinecone namespace to store vectors (optional, defaults to empty string)

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

        # Generate embeddings
        embeddings = embed_documents(documents, self.embedding_model)

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
            self.index.upsert(vectors=batch, namespace=namespace)
            uploaded_count += len(batch)
            namespace_info = f" to namespace '{namespace}'" if namespace else ""
            print(f"  Uploaded batch {i // batch_size + 1}: {uploaded_count}/{len(vectors)} vectors{namespace_info}")
            time.sleep(0.1)  # Small delay to avoid rate limiting

        # Get index statistics
        time.sleep(1)  # Wait for index to update
        stats = self.index.describe_index_stats()

        return {
            "uploaded": uploaded_count,
            "total_in_index": stats.total_vector_count,
            "dimension": stats.dimension,
            "index_stats": stats
        }

    def upsert_by_namespace(
            self,
            documents: List[str],
            metadatas: List[Dict[str, Any]],
            ids: List[str],
            batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Add documents to Pinecone, automatically organizing them by namespace based on section_type.
        Each section_type will be stored in its own namespace.

        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries (must contain 'section_type')
            ids: List of document IDs
            batch_size: Number of vectors to upload per batch

        Returns:
            Dictionary with upload statistics per namespace
        """
        # Group documents by section_type
        namespace_groups = {}
        for doc, metadata, doc_id in zip(documents, metadatas, ids):
            section_type = metadata.get('section_type', 'default')
            if section_type not in namespace_groups:
                namespace_groups[section_type] = {'docs': [], 'metas': [], 'ids': []}
            namespace_groups[section_type]['docs'].append(doc)
            namespace_groups[section_type]['metas'].append(metadata)
            namespace_groups[section_type]['ids'].append(doc_id)

        # Upload each namespace group
        results = {}
        total_uploaded = 0

        print(f"\n{'='*80}")
        print(f"UPLOADING DOCUMENTS BY NAMESPACE")
        print(f"{'='*80}")
        print(f"Found {len(namespace_groups)} namespaces: {', '.join(namespace_groups.keys())}\n")

        for namespace, group_data in namespace_groups.items():
            print(f"\n--- Namespace: '{namespace}' ---")
            print(f"Documents to upload: {len(group_data['docs'])}")

            result = self.upsert_vectors(
                documents=group_data['docs'],
                metadatas=group_data['metas'],
                ids=group_data['ids'],
                batch_size=batch_size,
                namespace=namespace
            )

            results[namespace] = result
            total_uploaded += result['uploaded']
            print(f"✓ Namespace '{namespace}': {result['uploaded']} documents uploaded")

        print(f"\n{'='*80}")
        print(f"UPLOAD SUMMARY")
        print(f"{'='*80}")
        print(f"Total documents uploaded: {total_uploaded}")
        print(f"Namespaces created: {len(namespace_groups)}")
        for namespace, result in results.items():
            print(f"  - {namespace}: {result['uploaded']} documents")
        print(f"{'='*80}\n")

        return {
            'total_uploaded': total_uploaded,
            'namespaces': results
        }

    def query(
            self,
            query_vector: List[float],
            top_k: int = 3,
            namespace: str = "",
            filter_dict: Dict[str, Any] = None,
            include_metadata: bool = True
    ):
        """
        Query the vector database for similar documents.

        Args:
            query_vector: Embedding vector for the query
            top_k: Number of results to return
            namespace: Namespace to query (optional)
            filter_dict: Metadata filters (optional)
            include_metadata: Whether to include metadata in results

        Returns:
            Query results from Pinecone
        """
        return self.index.query(
            vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            filter=filter_dict,
            include_metadata=include_metadata
        )