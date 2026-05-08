"""
Base scraper class with common functionality for all pharmacy scrapers.
Implements retry logic, rate limiting, and error handling.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import aiohttp
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config.settings import get_settings
from utils.logger import logger


class ScraperStatus(str, Enum):
    """Scraper execution status."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    NO_RESULTS = "no_results"


@dataclass
class ProductResult:
    """Individual product result from scraping."""
    name: str
    price: float
    original_price: Optional[float] = None
    url: str = ""
    image_url: Optional[str] = None
    in_stock: bool = True
    sku: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    presentation: Optional[str] = None


@dataclass
class ScraperResult:
    """Result from scraper execution."""
    status: ScraperStatus
    products: List[ProductResult]
    pharmacy_name: str
    query: str
    execution_time_ms: int
    error_message: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Check if scraping was successful."""
        return self.status in [ScraperStatus.SUCCESS, ScraperStatus.PARTIAL]
    
    @property
    def has_results(self) -> bool:
        """Check if any products were found."""
        return len(self.products) > 0


class BaseScraper(ABC):
    """
    Base class for pharmacy scrapers.
    Provides common functionality for HTTP requests, parsing, and error handling.
    """
    
    def __init__(self, pharmacy_name: str, base_url: str):
        """
        Initialize scraper.
        
        Args:
            pharmacy_name: Name of the pharmacy
            base_url: Base URL of the pharmacy website
        """
        self.pharmacy_name = pharmacy_name
        self.base_url = base_url
        self.settings = get_settings()
        
        # HTTP session configuration
        self.timeout = aiohttp.ClientTimeout(total=self.settings.scraper_timeout)
        self.headers = {
            "User-Agent": self.settings.scraper_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = 0
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()
    
    async def _create_session(self) -> None:
        """Create HTTP session."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.headers,
            )
    
    async def _close_session(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.settings.scraper_delay:
            await asyncio.sleep(self.settings.scraper_delay - elapsed)
        self._last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    )
    async def _fetch(self, url: str, **kwargs) -> str:
        """
        Fetch URL content with retry logic.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for aiohttp request
            
        Returns:
            str: Response text
            
        Raises:
            aiohttp.ClientError: If request fails after retries
        """
        await self._rate_limit()
        
        if not self._session:
            await self._create_session()
        
        logger.debug(f"Fetching: {url}")
        
        async with self._session.get(url, **kwargs) as response:
            response.raise_for_status()
            return await response.text()
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content.
        
        Args:
            html: HTML string
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        return BeautifulSoup(html, "lxml")
    
    def _clean_price(self, price_str: str) -> Optional[float]:
        """
        Clean and convert price string to float.
        
        Args:
            price_str: Price string (e.g., "$1.990", "1990", "$1.990,00")
            
        Returns:
            float: Cleaned price or None if invalid
        """
        try:
            # Remove currency symbols and whitespace
            cleaned = price_str.replace("$", "").replace(".", "").replace(",", ".").strip()
            
            # Remove any non-numeric characters except decimal point
            cleaned = "".join(c for c in cleaned if c.isdigit() or c == ".")
            
            return float(cleaned) if cleaned else None
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse price: {price_str}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace and special characters.
        
        Args:
            text: Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = " ".join(text.split())
        
        # Remove special characters but keep accents
        return cleaned.strip()
    
    def _extract_sku(self, text: str) -> Optional[str]:
        """
        Extract SKU from text.
        
        Args:
            text: Text containing SKU
            
        Returns:
            str: SKU or None
        """
        # Implementation depends on pharmacy format
        return None
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 20) -> ScraperResult:
        """
        Search for products.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            ScraperResult: Scraping results
        """
        pass
    
    @abstractmethod
    def _build_search_url(self, query: str) -> str:
        """
        Build search URL for the pharmacy.
        
        Args:
            query: Search query
            
        Returns:
            str: Complete search URL
        """
        pass
    
    @abstractmethod
    def _parse_product(self, element: Any) -> Optional[ProductResult]:
        """
        Parse a product element from HTML.
        
        Args:
            element: BeautifulSoup element containing product info
            
        Returns:
            ProductResult: Parsed product or None if parsing fails
        """
        pass
    
    async def _execute_search(
        self,
        query: str,
        max_results: int = 20
    ) -> ScraperResult:
        """
        Execute search with error handling and timing.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            ScraperResult: Search results
        """
        start_time = time.time()
        products = []
        status = ScraperStatus.FAILED
        error_message = None
        
        try:
            logger.info(f"🔍 Searching {self.pharmacy_name} for: {query}")
            
            # Build search URL
            search_url = self._build_search_url(query)
            
            # Fetch page
            html = await self._fetch(search_url)
            
            # Parse HTML
            soup = self._parse_html(html)
            
            # Extract products
            products = await self._extract_products(soup, max_results)
            
            # Determine status
            if products:
                status = ScraperStatus.SUCCESS
                logger.info(f"✅ Found {len(products)} products in {self.pharmacy_name}")
            else:
                status = ScraperStatus.NO_RESULTS
                logger.warning(f"⚠️ No products found in {self.pharmacy_name}")
            
        except aiohttp.ClientError as e:
            error_message = f"HTTP error: {str(e)}"
            logger.error(f"❌ {self.pharmacy_name} scraping failed: {error_message}")
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.exception(f"❌ {self.pharmacy_name} scraping failed: {error_message}")
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return ScraperResult(
            status=status,
            products=products,
            pharmacy_name=self.pharmacy_name,
            query=query,
            execution_time_ms=execution_time,
            error_message=error_message,
        )
    
    async def _extract_products(
        self,
        soup: BeautifulSoup,
        max_results: int
    ) -> List[ProductResult]:
        """
        Extract products from parsed HTML.
        
        Args:
            soup: Parsed HTML
            max_results: Maximum products to extract
            
        Returns:
            List[ProductResult]: List of extracted products
        """
        products = []
        
        # Find product elements (to be implemented by subclasses)
        product_elements = self._find_product_elements(soup)
        
        for element in product_elements[:max_results]:
            try:
                product = self._parse_product(element)
                if product and product.price:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Failed to parse product: {e}")
                continue
        
        return products
    
    @abstractmethod
    def _find_product_elements(self, soup: BeautifulSoup) -> List[Any]:
        """
        Find product elements in parsed HTML.
        
        Args:
            soup: Parsed HTML
            
        Returns:
            List: List of product elements
        """
        pass
    
    def _validate_product(self, product: ProductResult) -> bool:
        """
        Validate product data.
        
        Args:
            product: Product to validate
            
        Returns:
            bool: True if valid
        """
        if not product.name or not product.price:
            return False
        
        if product.price <= 0:
            return False
        
        return True


__all__ = [
    "BaseScraper",
    "ScraperResult",
    "ProductResult",
    "ScraperStatus",
]

# Made with Bob