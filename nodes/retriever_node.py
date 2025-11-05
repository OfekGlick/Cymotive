"""
Retriever Node - Searches for similar historical incidents using semantic search.
Uses the description namespace to find similar incidents and retrieves recommendations.
"""

from typing import Dict, Any

from .base_node import BaseNode
from data_handling.embeddings import embed_query
from data_handling.vector_store import VectorStore


class RetrieverNode(BaseNode):
    """Retrieves similar historical incidents using semantic search in the description namespace."""

    def __init__(self, config):
        """
        Initialize retriever node.

        Args:
            config: RAG configuration object
        """
        super().__init__(config)
        self.vector_store = VectorStore(config.index, config.embedding_model)

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Searches for similar historical incidents based on the description section.
        Queries Pinecone directly for description and recommendation sections.

        Args:
            state: Current workflow state

        Returns:
            Updated state with retrieved similar incidents and recommendations
        """
        try:
            print(f"\n[Retriever] Searching for similar incidents based on description...")

            # Use the description from the user's incident for searching
            search_query = state['description']

            # Embed the search query using shared embedding function
            print("[Retriever] Generating query embedding...")
            query_embedding = embed_query(search_query, self.config.embedding_model)

            # Query only the 'description' namespace to find similar incidents
            print("[Retriever] Querying similar incident descriptions...")
            description_results = self.vector_store.query(
                query_vector=query_embedding,
                top_k=3,
                namespace="description",
                include_metadata=True
            )

            # Extract both description and recommendations from the results
            # Each description in the metadata contains section_recommendations_text
            state['retrieved_incidents'] = []
            seen_ids = set()

            for match in description_results.matches:
                incident_id = match.metadata.get('incident_id', 'Unknown')
                if incident_id not in seen_ids:
                    # Get description text (the main embedded text)
                    description_text = match.metadata.get('text', '')

                    # Get recommendations text from metadata (cross-section reference)
                    recommendations_text = match.metadata.get('section_recommendations_text', '')

                    state['retrieved_incidents'].append({
                        'incident_id': incident_id,
                        'description': description_text,
                        'recommendations': recommendations_text,
                        'metadata': match.metadata,
                        'score': match.score
                    })
                    seen_ids.add(incident_id)

            # Print retrieved incidents with both description and recommendations
            print(f"\n[Retriever] Found {len(state['retrieved_incidents'])} similar incidents:")
            for i, incident in enumerate(state['retrieved_incidents'], 1):
                print(f"\n  [{i}] Incident ID: {incident['incident_id']}")
                print(f"      Similarity Score: {incident['score']:.4f}")
                print(f"      Threat Category: {incident['metadata'].get('threat_category', 'N/A')}")
                print(f"      Description Preview: {incident['description'][:150]}...")
                print(f"      Recommendations Preview: {incident['recommendations'][:150]}...")

            # For backward compatibility, also populate retrieved_recommendations
            # (extracting recommendations from the incidents we found)
            state['retrieved_recommendations'] = []
            for incident in state['retrieved_incidents']:
                if incident['recommendations']:
                    state['retrieved_recommendations'].append(incident['recommendations'])

        except Exception as e:
            state['error'] = f"Error in retrieval: {str(e)}"
            state['retrieved_incidents'] = []
            state['retrieved_recommendations'] = []
            print(f"[Retriever] Error: {e}")

        return state