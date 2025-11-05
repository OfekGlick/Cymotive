"""
Shared configuration for RAG system with Pinecone and Gemini.
"""

import os
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec


class RAGConfig:
    """Configuration for RAG Assistant with Pinecone and Gemini."""

    def __init__(
        self,
        gemini_api_key: str = None,
        pinecone_api_key: str = None,
        index_name: str = "incident_report-database",
        model: str = "models/gemini-2.0-flash",
        embedding_model: str = "models/text-embedding-004",
        embedding_dimension: int = 768,
        cloud: str = "aws",
        region: str = "us-east-1"
    ):
        """
        Initialize RAG configuration.

        Args:
            gemini_api_key: Google Gemini API key (or set GEMINI_API_KEY env var)
            pinecone_api_key: Pinecone API key (or set PINECONE_API_KEY env var)
            index_name: Name of the Pinecone index
            model: Gemini model for text generation (gemini-1.5-flash-latest, gemini-1.5-pro-latest, gemini-pro)
            embedding_model: Gemini embedding model
            embedding_dimension: Dimension of embedding vectors (768 for text-embedding-004)
            cloud: Cloud provider for Pinecone serverless (aws, gcp, azure)
            region: Region for Pinecone serverless
        """
        # Initialize Gemini
        gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            raise ValueError("Gemini API key must be provided or set as GEMINI_API_KEY environment variable")

        genai.configure(api_key=gemini_key)

        # Try to initialize the model, fall back to gemini-pro if the specified model is not available
        try:
            self.gemini_model = genai.GenerativeModel(model)
            print(f"Successfully initialized model: {model}")
        except Exception as e:
            print(f"Warning: Could not initialize {model}, falling back to gemini-pro. Error: {e}")
            try:
                self.gemini_model = genai.GenerativeModel("gemini-pro")
                print("Successfully initialized fallback model: gemini-pro")
            except Exception as e2:
                raise ValueError(f"Could not initialize any Gemini model. Error: {e2}")

        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension

        # Initialize Pinecone
        pinecone_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        if not pinecone_key:
            raise ValueError("Pinecone API key must be provided or set as PINECONE_API_KEY environment variable")

        self.pc = Pinecone(api_key=pinecone_key)
        self.index_name = index_name

        # Create index if it doesn't exist
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        if index_name not in existing_indexes:
            print(f"Creating new Pinecone index: {index_name}")
            self.pc.create_index(
                name=index_name,
                dimension=embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=cloud,
                    region=region
                )
            )
            print(f"Index {index_name} created successfully!")
        else:
            print(f"Using existing Pinecone index: {index_name}")

        # Connect to the index
        self.index = self.pc.Index(index_name)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens for the given text using the model's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            # Use Gemini's native token counting
            result = self.gemini_model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            # Fallback estimation if API fails
            # Gemini models: approximately 1 token ≈ 4 characters (similar to GPT)
            print(f"Warning: Token counting failed ({e}), using estimation")
            return len(text) // 4