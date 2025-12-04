"""
Standalone script to initialize the vector store

This can be run independently to test scraping and embedding
without starting the full FastAPI server.

Usage:
    python init_vector_store.py
    python init_vector_store.py --url https://example.com
    python init_vector_store.py --test-only  # Use sample data
"""

import logging
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from scraper import VodafoneZiggoScraper
from embedding_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main initialization function."""
    import argparse

    parser = argparse.ArgumentParser(description="Initialize vector store")
    parser.add_argument(
        "--url",
        default="https://ziggo.nl/internet",
        help="URL to scrape (default: https://ziggo.nl/internet)",
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Use sample test data instead of scraping",
    )
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="Directory to store vector database",
    )
    args = parser.parse_args()

    logger.info("╔════════════════════════════════════════════════╗")
    logger.info("║  Vector Store Initialization                   ║")
    logger.info("╚════════════════════════════════════════════════╝")

    # Initialize vector store
    vector_store = VectorStore(persist_directory=f"{args.data_dir}/chroma_db")

    if args.test_only:
        # Use sample data
        logger.info("Using sample test data...")
        sample_content = """
        VodafoneZiggo Internet Services - Complete Overview
        
        Our Services:
        1. Fiber Optic Internet: Ultra-fast speeds up to 1 Gbps with our fiber network.
           - Download speeds: Up to 1000 Mbps
           - Upload speeds: Up to 100 Mbps
           - Latency: <10ms
           - Availability: Urban and suburban areas
        
        2. Cable Internet: Reliable and fast through our cable infrastructure.
           - Download speeds: Up to 500 Mbps
           - Upload speeds: Up to 50 Mbps
           - Data: Unlimited
           - Available: Nationwide
        
        3. Mobile 5G: Latest generation mobile connectivity.
           - Coverage: Major cities and highways
           - Speed: Up to 1 Gbps
           - Data: Various plans from 10GB to unlimited
           - Devices: Compatible with all 5G phones
        
        4. Residential Packages:
           - Starter: 100 Mbps for €35/month
           - Pro: 500 Mbps for €55/month
           - Elite: 1000 Mbps for €75/month
        
        Customer Support:
        - Phone: +31 XX XXX XXXX (24/7)
        - Email: support@ziggo.nl
        - Chat: Available on website
        - Response time: <2 hours
        
        Installation & Setup:
        - Professional installation available
        - Cost: €50 one-time (waived for annual plans)
        - Router provided with service
        - Setup time: 2-4 hours
        - Technician includes network setup
        
        Billing & Payments:
        - Monthly billing available
        - Annual discounts: 10% off
        - Multiple payment methods accepted
        - Cancellation: 30 days notice
        """
        content = sample_content
    else:
        # Scrape website
        logger.info(f"Scraping from: {args.url}")
        scraper = VodafoneZiggoScraper(args.url)
        content = scraper.scrape()

        if not content:
            logger.error("Failed to scrape content. Aborting.")
            return False

    # Create vector store
    logger.info(f"Creating vector store...")
    if not vector_store.create_vector_store_from_text(content, chunk_size=500):
        logger.error("Failed to create vector store")
        return False

    # Get statistics
    stats = vector_store.get_store_stats()
    logger.info("Vector store created successfully!")
    logger.info(f"Statistics: {stats}")

    # Test retrieval
    logger.info("\n╔════════════════════════════════════════════════╗")
    logger.info("║  Testing Retrieval                             ║")
    logger.info("╚════════════════════════════════════════════════╝")

    test_questions = [
        "What internet speeds do you offer?",
        "How much does internet cost?",
        "Do you have 5G coverage?",
        "What is your customer support phone number?",
    ]

    for question in test_questions:
        logger.info(f"\nQuestion: {question}")
        results = vector_store.retrieve(question, k=2)

        if results:
            for i, result in enumerate(results, 1):
                logger.info(f"  Result {i} (score: {result['score']:.3f}):")
                # Show first 100 chars of content
                content_preview = result["content"][:100].replace("\n", " ")
                logger.info(f"    {content_preview}...")
        else:
            logger.warning("  No results found")

    logger.info("\n╔════════════════════════════════════════════════╗")
    logger.info("║  ✓ Initialization Complete                    ║")
    logger.info("╚════════════════════════════════════════════════╝")

    logger.info(f"\nVector store saved to: {args.data_dir}/chroma_db")
    logger.info("You can now start the FastAPI server with:")
    logger.info("  docker-compose up")
    logger.info("  or")
    logger.info("  python -m uvicorn src.main:app --reload")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
