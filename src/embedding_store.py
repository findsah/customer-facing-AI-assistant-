"""
Embedding and Vector Store Module

This module handles text embedding and storage in a vector database.

Using TF-IDF embeddings from scikit-learn:
- No heavy dependencies like sentence-transformers
- Fast and lightweight
- Works great for semantic search with RAG pipelines  
- Open source and free

Using Chroma Vector Store:
- Lightweight and runs in-memory or persistent local disk storage
- Easy to set up, no external services needed
- Excellent for prototyping and small-to-medium datasets
"""

import logging
from typing import List, Dict, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages text embedding using TF-IDF vectorizer."""

    def __init__(self):
        """Initialize the embedding model."""
        logger.info("Initializing TF-IDF embedding model")
        # Create a simple TF-IDF vectorizer for text embeddings
        # This is lightweight and works well for semantic search
        self.vectorizer = TfidfVectorizer(
            max_features=1000,  # Limit vocabulary
            lowercase=True,
            stop_words='english',
            min_df=1,
            max_df=1.0  # Allow all documents
        )
        self.fitted = False
        logger.info("TF-IDF embedding model initialized")

    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not self.fitted:
            logger.error("Vectorizer not fitted! Must call embed_texts() first to fit vocabulary.")
            # Return zero vector if not fitted
            return [0.0] * 1000
        
        try:
            embedding = self.vectorizer.transform([text]).toarray()[0]
            return embedding.tolist()
        except Exception as e:
            logger.warning(f"Error embedding text: {e}, returning zero vector")
            return [0.0] * 1000  # Return zero vector as fallback

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple text strings.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Fit on all texts if not yet fitted
        if not self.fitted:
            self.vectorizer.fit(texts)
            self.fitted = True
        
        embeddings = self.vectorizer.transform(texts).toarray()
        return [e.tolist() for e in embeddings]


class VectorStore:
    """Manages vector storage and retrieval using Chroma."""

    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "vodafone_ziggo",
    ):
        """
        Initialize the vector store.

        Args:
            persist_directory: Path to store vector database on disk
            collection_name: Name of the collection in Chroma
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_manager = EmbeddingManager()
        self.client: Optional[chromadb.Client] = None
        self.collection = None

        # Create persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize Chroma client with new API
        try:
            self.client = chromadb.PersistentClient(path=persist_directory)
        except Exception as e:
            logger.warning(f"Could not create persistent client: {e}, using ephemeral")
            self.client = chromadb.EphemeralClient()

    def create_vector_store_from_text(self, text: str, chunk_size: int = 500) -> bool:
        """
        Create a vector store from raw text.

        The text is split into chunks to handle large documents and improve
        retrieval granularity. Each chunk is embedded and stored.

        Args:
            text: Raw text content to embed and store
            chunk_size: Size of text chunks in characters

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Creating vector store with chunk size: {chunk_size}")

            # Split text into manageable chunks with overlap for context preservation
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=100
            )
            chunks = splitter.split_text(text)
            logger.info(f"Created {len(chunks)} text chunks")

            # Create or get collection
            # Delete if exists to ensure fresh start
            try:
                self.client.delete_collection(name=self.collection_name)
            except:
                pass
            
            self.collection = self.client.create_collection(name=self.collection_name)

            # Embed chunks
            embeddings = self.embedding_manager.embed_texts(chunks)
            
            # Add to collection with IDs
            ids = [f"chunk_{i}" for i in range(len(chunks))]
            metadatas = [{"text": chunk[:100]} for chunk in chunks]  # Store first 100 chars as metadata
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=chunks
            )
            
            logger.info("Vector store created and persisted successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_vector_store(self) -> bool:
        """
        Load an existing vector store from disk.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Loading vector store from {self.persist_directory}")
            self.collection = self.client.get_collection(name=self.collection_name)

            # Refit the TF-IDF vectorizer using stored documents to ensure
            # query embedding dimensionality matches the collection.
            try:
                existing = self.collection.get()
                docs = existing.get("documents") or []
                if docs:
                    logger.info(f"Refitting vectorizer with {len(docs)} documents")
                    self.embedding_manager.vectorizer.fit(docs)
                    self.embedding_manager.fitted = True
                else:
                    logger.warning("Collection has no documents; vectorizer remains unfitted")
            except Exception as e:
                logger.warning(f"Could not refit vectorizer from collection: {e}")

            logger.info("Vector store loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return False

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, str]]:
        """
        Retrieve relevant documents based on similarity to the query.

        Args:
            query: The user's question or query
            k: Number of results to retrieve

        Returns:
            List of dictionaries with 'content' and 'score' keys
        """
        if not self.collection:
            logger.warning("Vector store not initialized")
            return []

        try:
            # Embed the query
            query_embedding = self.embedding_manager.embed_text(query)
            
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )

            retrieved = []
            if results and results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                distances = results['distances'][0] if results.get('distances') else [0] * len(documents)
                
                for doc, distance in zip(documents, distances):
                    # Convert distance to similarity score (lower distance = higher similarity)
                    # Chroma returns distances, so we invert: similarity = 1 / (1 + distance)
                    similarity = 1.0 / (1.0 + distance)
                    retrieved.append({"content": doc, "score": float(similarity)})
                    logger.debug(f"Retrieved: {doc[:100]}... (score: {similarity:.4f})")

            return retrieved
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []

    def get_store_stats(self) -> Dict:
        """Get statistics about the vector store."""
        if not self.collection:
            return {"status": "not_initialized"}

        try:
            return {
                "status": "initialized",
                "collection_name": self.collection_name,
                "num_documents": self.collection.count(),
            }
        except Exception as e:
            logger.error(f"Error getting store stats: {e}")
            return {"status": "error", "error": str(e)}
