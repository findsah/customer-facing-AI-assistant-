"""
Web Scraper Module for VodafoneZiggo

This module handles scraping content from the VodafoneZiggo website.
It uses BeautifulSoup for HTML parsing and requests for HTTP communication.

Why BeautifulSoup + requests?
- BeautifulSoup: Lightweight, easy to use for simple HTML parsing without JavaScript execution
- requests: Simple synchronous HTTP client, suitable for basic web scraping
- Alternative: Selenium/Playwright would be needed for JavaScript-rendered content

The scraper focuses on text content extraction, ignoring styling and scripts.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VodafoneZiggoScraper:
    """Scrapes content from VodafoneZiggo website."""

    # User-Agent header to avoid being blocked by the website
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def __init__(self, url: str, timeout: int = 10):
        """
        Initialize the scraper.

        Args:
            url: The URL to scrape (e.g., https://ziggo.nl/internet)
            timeout: Request timeout in seconds
        """
        self.url = url
        self.timeout = timeout
        self.content: Optional[str] = None

    def fetch_page(self) -> bool:
        """
        Fetch the web page content.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Fetching content from {self.url}")
            response = requests.get(
                self.url, headers=self.HEADERS, timeout=self.timeout
            )
            response.raise_for_status()
            self.content = response.text
            logger.info(f"Successfully fetched {len(self.content)} characters")
            return True
        except requests.RequestException as e:
            logger.error(f"Error fetching {self.url}: {e}")
            return False

    def extract_text(self) -> str:
        """
        Extract text content from the fetched page.

        Returns:
            str: Extracted text content
        """
        if not self.content:
            logger.warning("No content to extract. Call fetch_page() first.")
            return ""

        soup = BeautifulSoup(self.content, "html.parser")

        # Remove script and style elements (they clutter the text)
        for script in soup(["script", "style"]):
            script.decompose()

        # Get the text content
        text = soup.get_text(separator=" ", strip=True)

        # Clean up excessive whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        logger.info(f"Extracted {len(text)} characters of clean text")
        return text

    def scrape(self) -> Optional[str]:
        """
        Perform complete scraping: fetch and extract text.

        Returns:
            str: Extracted text content, or None if scraping failed
        """
        if not self.fetch_page():
            return None
        return self.extract_text()
