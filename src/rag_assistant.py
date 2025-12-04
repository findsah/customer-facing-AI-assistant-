"""
Retrieval-Augmented Generation (RAG) Module

This module combines retrieval from the vector store with LLM-based response generation.
It implements the core Q&A pipeline for the AI assistant.

Why Langchain?
- Provides abstractions for chaining retrieval + LLM components
- Handles prompt templating and response formatting
- Easily swappable with different LLM providers
- Alternative: LlamaIndex would also work but Langchain is more flexible

Why HuggingFace Transformers for local LLM?
- No external API dependencies
- Can run fully locally
- Models like Mistral-7B provide good quality for small footprint
- Alternative: Use OpenAI API (requires keys) or other hosted solutions

Default: We use a local inference approach, but code is structured to support
any LangChain-compatible LLM (OpenAI, Hugging Face Hub, local models, etc.)
"""

import logging
from typing import Optional, Dict, List
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.llms import HuggingFacePipeline
from langchain.embeddings import HuggingFaceEmbeddings
from transformers import pipeline as hf_pipeline
import torch

from embedding_store import VectorStore

logger = logging.getLogger(__name__)


class RAGAssistant:
    """Retrieval-Augmented Generation Assistant for Q&A."""

    def __init__(self, vector_store: VectorStore, use_local_llm: bool = True):
        """
        Initialize the RAG assistant.

        Args:
            vector_store: VectorStore instance for document retrieval
            use_local_llm: If True, uses local Mistral-7B model.
                          If False, expects OPENAI_API_KEY env var for API-based LLM
        """
        self.vector_store = vector_store
        self.use_local_llm = use_local_llm
        self.qa_chain: Optional[RetrievalQA] = None
        self.llm: Optional[object] = None

        # Initialize the LLM
        if use_local_llm:
            self._init_local_llm()
        else:
            self._init_api_llm()

        # Set up the RAG chain
        self._setup_qa_chain()

    def _init_local_llm(self):
        """
        Initialize a local LLM using HuggingFace Transformers.

        Using Mistral-7B Instruct: Compact, efficient, good quality for instruction following.
        Note: This requires ~15GB of VRAM for full model. For resource-constrained environments,
        consider smaller models like Phi-2 or Orca-Mini-3B.
        """
        try:
            logger.info("Initializing local LLM (Mistral-7B)...")

            # Detect device (CUDA if available, otherwise CPU)
            device = 0 if torch.cuda.is_available() else -1
            logger.info(f"Using device: {'CUDA' if device >= 0 else 'CPU'}")

            # Create HuggingFace pipeline for text generation
            # quantize_config can be added for 4-bit quantization to reduce memory
            text_gen_pipeline = hf_pipeline(
                "text-generation",
                model="mistralai/Mistral-7B-Instruct-v0.1",
                torch_dtype=torch.float16 if device >= 0 else torch.float32,
                device_map="auto" if device >= 0 else None,
                device=device,
                max_new_tokens=256,
                temperature=0.7,
                top_p=0.9,
            )

            # Wrap in LangChain interface
            self.llm = HuggingFacePipeline(model=text_gen_pipeline)
            logger.info("Local LLM initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing local LLM: {e}")
            logger.warning("Falling back to a simple response generation without LLM")
            self.llm = None

    def _init_api_llm(self):
        """
        Initialize an API-based LLM (OpenAI or similar).

        Expects OPENAI_API_KEY environment variable to be set.
        This is a placeholder for when using cloud-based LLMs.
        """
        try:
            # Placeholder for OpenAI integration
            # Uncomment when you have an API key
            # from langchain.llms import OpenAI
            # self.llm = OpenAI(
            #     api_key=os.getenv("OPENAI_API_KEY"),
            #     temperature=0.7,
            #     model_name="gpt-3.5-turbo"
            # )
            logger.warning("API LLM not configured. Using fallback response generation.")
            self.llm = None
        except Exception as e:
            logger.error(f"Error initializing API LLM: {e}")
            self.llm = None

    def _setup_qa_chain(self):
        """Set up the RetrievalQA chain."""
        if not self.vector_store.collection:
            logger.warning("Vector store not initialized. Cannot set up QA chain.")
            return

        if not self.llm:
            logger.warning("LLM not initialized. Will use fallback response generation.")

        try:
            # Note: With our simplified setup, we directly use the vector store's retrieve method
            # instead of LangChain's RetrievalQA chain
            logger.info("RAG Assistant ready to answer questions using vector store")

        except Exception as e:
            logger.error(f"Error setting up QA chain: {e}")

    def answer_question(self, question: str) -> Dict[str, any]:
        """
        Answer a user question using RAG.

        Args:
            question: The user's question

        Returns:
            Dictionary with 'answer', 'sources', and 'retrieval_score' keys
        """
        logger.info(f"Processing question: {question}")

        try:
            if self.qa_chain:
                # Use the full RAG chain with LLM
                result = self.qa_chain({"query": question})
                answer = result.get("result", "Unable to generate answer")
                sources = [doc.page_content for doc in result.get("source_documents", [])]
            else:
                # Fallback: Retrieve only, generate simple response
                retrieved = self.vector_store.retrieve(question, k=3)
                if not retrieved:
                    answer = "I'm sorry, I couldn't find relevant information about your question."
                    sources = []
                else:
                    # Create a simple response by combining retrieved chunks
                    sources = [item["content"] for item in retrieved]
                    answer = self._generate_fallback_response(question, sources)

            result = {
                "question": question,
                "answer": answer,
                "sources": sources,
                "success": True,
            }
            logger.info(f"Generated answer successfully")
            return result

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "question": question,
                "answer": f"Error processing question: {str(e)}",
                "sources": [],
                "success": False,
            }

    def _generate_fallback_response(self, question: str, sources: List[str]) -> str:
        """
        Generate a simple response without LLM (fallback mode).

        Args:
            question: The user's question
            sources: List of relevant text chunks

        Returns:
            A simple response combining retrieved information
        """
        # Simple fallback: concatenate relevant sources with a header
        combined_info = " ".join(sources[:2])  # Use top 2 sources
        return f"Based on the documentation: {combined_info[:500]}..."
