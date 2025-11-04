"""
Validation Node - Extracts standard information from incident reports.
Uses the Validation Agent to extract WHO, WHAT, WHERE, WHEN, IMPACT, STATUS.
"""

import re
from typing import Dict, Any
import google.generativeai as genai

from .base_node import BaseNode


class RetrieverNode(BaseNode):
    """Validates input and extracts standard information using Validation Agent."""

    def __init__(self, config):
        """
        Initialize validation node.

        Args:
            config: RAG configuration object
        """
        super().__init__(config)

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

            # Embed the search query using the same embedding model
            print("[Retriever] Generating query embedding...")
            query_embedding_result = genai.embed_content(
                model=self.config.embedding_model,
                content=search_query,
                task_type="retrieval_query"
            )
            query_embedding = query_embedding_result['embedding']

            # 1. Find similar incident DESCRIPTIONS
            print("[Retriever] Querying similar incident descriptions...")
            description_results = self.config.index.query(
                vector=query_embedding,
                top_k=3,
                filter={"section_type": {"$eq": "description"}},
                include_metadata=True
            )

            # 2. Find applicable RECOMMENDATIONS from similar incidents
            print("[Retriever] Querying recommendations...")
            recommendation_results = self.config.index.query(
                vector=query_embedding,
                top_k=10,
                filter={"section_type": {"$eq": "recommendations"}},
                include_metadata=True
            )

            # Aggregate retrieved similar incident descriptions
            state['retrieved_incidents'] = []
            seen_ids = set()

            for match in description_results.matches:
                incident_id = match.metadata.get('incident_id', 'Unknown')
                if incident_id not in seen_ids:
                    state['retrieved_incidents'].append({
                        'incident_id': incident_id,
                        'description': match.metadata.get('text', ''),
                        'metadata': match.metadata,
                        'score': match.score
                    })
                    seen_ids.add(incident_id)

            # Print retrieved incidents
            print(f"\n[Retriever] Found {len(state['retrieved_incidents'])} similar incidents:")
            for i, incident in enumerate(state['retrieved_incidents'], 1):
                print(f"\n  [{i}] Incident ID: {incident['incident_id']}")
                print(f"      Similarity Score: {incident['score']:.4f}")
                print(f"      Threat Category: {incident['metadata'].get('threat_category', 'N/A')}")
                print(f"      Description Preview: {incident['description'][:150]}...")

            # Extract recommendations from similar incidents
            state['retrieved_recommendations'] = []
            for match in recommendation_results.matches:
                text = match.metadata.get('text', '')
                if len(text) > 50:  # Filter out very short responses
                    state['retrieved_recommendations'].append(text)

            # Print retrieved recommendations
            print(f"\n[Retriever] Found {len(state['retrieved_recommendations'])} recommendations:")
            for i, rec in enumerate(state['retrieved_recommendations'][:3], 1):  # Show first 3
                print(f"\n  [{i}] {rec[:200]}...")

        except Exception as e:
            state['error'] = f"Error in retrieval: {str(e)}"
            state['retrieved_incidents'] = []
            state['retrieved_recommendations'] = []
            print(f"[Retriever] Error: {e}")

        return state