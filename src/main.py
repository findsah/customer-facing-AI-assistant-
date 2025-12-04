"""
FastAPI Application - Customer Support AI Assistant

This module provides the REST API endpoints for the AI assistant.
Endpoints:
- POST /api/ask: Submit a question and get an answer
- GET /api/health: Health check
- GET /api/stats: Get statistics about the vector store
"""

import logging
import os
import sys
from typing import Dict
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from scraper import VodafoneZiggoScraper
from embedding_store import VectorStore
from rag_assistant import RAGAssistant

# Configure logging from env LOG_LEVEL
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_LEVEL_MAP = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}
logging.basicConfig(
    level=_LEVEL_MAP.get(_LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VodafoneZiggo Customer Assistant API",
    description="AI-powered customer support assistant",
    version="1.0.0",
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state variables
vector_store: VectorStore = None
assistant: RAGAssistant = None


class Question(BaseModel):
    """Request model for asking a question."""

    question: str


class AnswerResponse(BaseModel):
    """Response model for an answer."""

    question: str
    answer: str
    sources: list
    success: bool


class RebuildRequest(BaseModel):
    """Request model for rebuilding the vector store."""

    url: str | None = None


@app.on_event("startup")
async def startup_event():
    """Initialize vector store and assistant on startup."""
    global vector_store, assistant

    logger.info("Starting up AI Assistant...")

    # Initialize vector store - use relative path for local execution
    # Falls back to /app/data for Docker execution
    data_dir = os.getenv("DATA_DIR", "./data")
    os.makedirs(data_dir, exist_ok=True)
    vector_store = VectorStore(persist_directory=f"{data_dir}/chroma_db")

    # Try to load existing vector store, otherwise create new one
    if not vector_store.load_vector_store():
        logger.info("Existing vector store not found. Creating new one...")

        # Scrape VodafoneZiggo website
        url = os.getenv(
            "SCRAPE_URL", "https://ziggo.nl/internet"
        )
        logger.info(f"Scraping from {url}...")

        scraper = VodafoneZiggoScraper(url)
        content = scraper.scrape()

        if content:
            vector_store.create_vector_store_from_text(content)
        else:
            logger.warning("Failed to scrape content. Using sample data.")
            sample_content = """
            VodafoneZiggo Internet Services
            
            Our internet services offer high-speed connectivity for homes and businesses.
            We provide various packages tailored to your needs.
            
            Fiber Optic Internet: Experience ultra-fast speeds up to 1000 Mbps with our fiber network.
            Cable Internet: Reliable and fast internet through our extensive cable infrastructure.
            5G Mobile: Stay connected with our latest 5G technology for mobile users.
            
            Customer Support: Available 24/7 via phone, chat, and email.
            Installation: Professional installation available in most areas.
            Router: Premium routers included with our service plans.
            """
            vector_store.create_vector_store_from_text(sample_content)

    # Initialize RAG assistant
    assistant = RAGAssistant(vector_store, use_local_llm=False)

    logger.info("AI Assistant startup complete")


@app.post("/api/rebuild")
async def rebuild_index(payload: RebuildRequest) -> Dict:
    """Re-scrape content and rebuild the vector store.

    Optional body: {"url": "https://example.com/page"}
    If no URL provided, falls back to env SCRAPE_URL or the default.
    """
    global vector_store

    if vector_store is None:
        raise HTTPException(status_code=500, detail="Vector store not initialized")

    url = payload.url or os.getenv("SCRAPE_URL", "https://ziggo.nl/internet")
    logger.info(f"Rebuilding index from {url} ...")

    try:
        scraper = VodafoneZiggoScraper(url)
        content = scraper.scrape()
        if not content:
            logger.warning("Scrape returned no content; using sample data.")
            content = (
                "VodafoneZiggo Internet Services\n\n"
                "Our internet services offer high-speed connectivity for homes and businesses.\n"
                "We provide various packages tailored to your needs.\n\n"
                "Fiber Optic Internet: Experience ultra-fast speeds up to 1000 Mbps with our fiber network.\n"
                "Cable Internet: Reliable and fast internet through our extensive cable infrastructure.\n"
                "5G Mobile: Stay connected with our latest 5G technology for mobile users.\n\n"
                "Customer Support: Available 24/7 via phone, chat, and email.\n"
                "Installation: Professional installation available in most areas.\n"
                "Router: Premium routers included with our service plans.\n"
            )

        ok = vector_store.create_vector_store_from_text(content)
        if not ok:
            raise RuntimeError("Failed to rebuild vector store")

        # Re-load ensures collection handle and embedding refit
        vector_store.load_vector_store()

        stats = vector_store.get_store_stats()
        return {"status": "rebuilt", "url": url, "stats": stats}

    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {e}")


@app.get("/api/health")
async def health_check() -> Dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "VodafoneZiggo Customer Assistant",
        "version": "1.0.0",
    }


@app.get("/api/stats")
async def get_stats() -> Dict:
    """Get vector store statistics."""
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    stats = vector_store.get_store_stats()
    return stats


@app.post("/api/ask", response_model=AnswerResponse)
async def ask_question(request: Question) -> AnswerResponse:
    """
    Submit a question and get an answer from the AI assistant.

    Args:
        request: Question object containing the user's question

    Returns:
        AnswerResponse with the answer and source documents
    """
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")

    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Get the answer
    result = assistant.answer_question(request.question)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Error processing question")

    return AnswerResponse(
        question=result["question"],
        answer=result["answer"],
        sources=result["sources"],
        success=result["success"],
    )


@app.post("/api/ask-simple")
async def ask_question_simple(request: Question) -> Dict:
    """
    Simple version of ask endpoint that returns raw JSON for easy testing.

    Args:
        request: Question object containing the user's question

    Returns:
        Raw dictionary response
    """
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not initialized")

    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = assistant.answer_question(request.question)
    return result


@app.get("/")
async def root() -> Dict:
    """Root endpoint with API information."""
    return {
        "name": "VodafoneZiggo Customer Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "stats": "/api/stats",
            "ask": "/api/ask",
            "ask_simple": "/api/ask-simple",
        },
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    # Run with: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
