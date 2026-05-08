"""
Cruz Verde pharmacy scraper.
Scrapes medicine prices from www.cruzverde.cl
"""

from typing import List, Any, Optional
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, ScraperResult, ProductResult
from config.settings import get_settings
from utils.logger import logger


class CruzVerdeScraper(BaseScraper):
    """Scraper for Cruz Verde pharmacy."""
    
    def __init__(self):
        """Initialize Cruz Verde scraper."""
        settings = get_settings()
        super().__init__(
            pharmacy_name="Cruz Verde",
            base_url=settings.cruz_verde_url
        )
    
    def _build_search_url(self, query: str) -> str:
        """
        Build search URL for Cruz Verde.
        
        Args:
            query: Search query
            
        Returns:
            str: Complete search URL
        """
        encoded_query = quote_plus(query)
        return f"{self.base_url}/search/?text={encoded_query}"
    
    def _find_product_elements(self, soup: BeautifulSoup) -> List[Any]:
        """
        Find product elements in Cruz Verde HTML.
        
        Args:
            soup: Parsed HTML
            
        Returns:
            List: Product elements
        """
        # Cruz Verde typically uses product cards with specific classes
        # This is a generic implementation that may need adjustment
        product_elements = []
        
        # Try common selectors
        selectors = [
            "div.product-item",
            "div.product-card",
            "div.product",
            "article.product",
            "div[data-product-id]",
            "li.product-item",
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                product_elements = elements
                logger.debug(f"Found {len(elements)} products using selector: {selector}")
                break
        
        if not product_elements:
            # Fallback: try to find any div with price information
            product_elements = soup.find_all("div", class_=lambda x: x and "product" in x.lower())
        
        return product_elements
    
    def _parse_product(self, element: Any) -> Optional[ProductResult]:
        """
        Parse a product element from Cruz Verde.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            ProductResult: Parsed product or None
        """
        try:
            # Extract product name
            name = self._extract_name(element)
            if not name:
                return None
            
            # Extract price
            price = self._extract_price(element)
            if not price:
                return None
            
            # Extract original price (if on sale)
            original_price = self._extract_original_price(element)
            
            # Extract URL
            url = self._extract_url(element)
            
            # Extract image
            image_url = self._extract_image(element)
            
            # Extract stock status
            in_stock = self._extract_stock_status(element)
            
            # Extract SKU
            sku = self._extract_sku_from_element(element)
            
            # Extract brand and presentation
            brand = self._extract_brand(element)
            presentation = self._extract_presentation(element)
            
            product = ProductResult(
                name=name,
                price=price,
                original_price=original_price,
                url=url,
                image_url=image_url,
                in_stock=in_stock,
                sku=sku,
                brand=brand,
                presentation=presentation,
            )
            
            if self._validate_product(product):
                return product
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse Cruz Verde product: {e}")
            return None
    
    def _extract_name(self, element: Any) -> Optional[str]:
        """Extract product name."""
        # Try common selectors for product name
        selectors = [
            "h2.product-name",
            "h3.product-name",
            "div.product-name",
            "a.product-name",
            "span.product-name",
            "h2.product-title",
            "h3.product-title",
        ]
        
        for selector in selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                return self._clean_text(name_elem.get_text())
        
        # Fallback: try to find any heading or link
        for tag in ["h2", "h3", "h4", "a"]:
            elem = element.find(tag)
            if elem:
                text = self._clean_text(elem.get_text())
                if text and len(text) > 5:  # Reasonable product name length
                    return text
        
        return None
    
    def _extract_price(self, element: Any) -> Optional[float]:
        """Extract current price."""
        # Try common price selectors
        selectors = [
            "span.price",
            "div.price",
            "span.product-price",
            "div.product-price",
            "span.price-current",
            "span.price-final",
            "span[class*='price']",
            "div[class*='price']",
        ]
        
        for selector in selectors:
            price_elem = element.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text()
                price = self._clean_price(price_text)
                if price:
                    return price
        
        # Fallback: search for price pattern in text
        text = element.get_text()
        import re
        price_pattern = r'\$\s*[\d.,]+|\d+[.,]\d+'
        matches = re.findall(price_pattern, text)
        
        for match in matches:
            price = self._clean_price(match)
            if price and price > 100:  # Reasonable minimum price
                return price
        
        return None
    
    def _extract_original_price(self, element: Any) -> Optional[float]:
        """Extract original price (before discount)."""
        selectors = [
            "span.price-old",
            "span.price-original",
            "del.price",
            "s.price",
            "span.price-before",
            "span[class*='old']",
        ]
        
        for selector in selectors:
            price_elem = element.select_one(selector)
            if price_elem:
                price = self._clean_price(price_elem.get_text())
                if price:
                    return price
        
        return None
    
    def _extract_url(self, element: Any) -> str:
        """Extract product URL."""
        # Try to find link
        link = element.find("a", href=True)
        if link:
            href = link["href"]
            # Make absolute URL if relative
            if href.startswith("/"):
                return f"{self.base_url}{href}"
            elif href.startswith("http"):
                return href
            else:
                return f"{self.base_url}/{href}"
        
        return self.base_url
    
    def _extract_image(self, element: Any) -> Optional[str]:
        """Extract product image URL."""
        # Try to find image
        img = element.find("img")
        if img:
            # Try different attributes
            for attr in ["src", "data-src", "data-lazy-src"]:
                if img.get(attr):
                    img_url = img[attr]
                    # Make absolute URL if relative
                    if img_url.startswith("/"):
                        return f"{self.base_url}{img_url}"
                    elif img_url.startswith("http"):
                        return img_url
        
        return None
    
    def _extract_stock_status(self, element: Any) -> bool:
        """Extract stock status."""
        # Look for out of stock indicators
        text = element.get_text().lower()
        
        out_of_stock_indicators = [
            "sin stock",
            "agotado",
            "no disponible",
            "out of stock",
        ]
        
        for indicator in out_of_stock_indicators:
            if indicator in text:
                return False
        
        # Look for in stock indicators
        in_stock_indicators = [
            "disponible",
            "en stock",
            "agregar al carro",
            "comprar",
        ]
        
        for indicator in in_stock_indicators:
            if indicator in text:
                return True
        
        # Default to in stock if no clear indicator
        return True
    
    def _extract_sku_from_element(self, element: Any) -> Optional[str]:
        """Extract SKU from element."""
        # Try data attributes
        for attr in ["data-sku", "data-product-id", "data-id"]:
            if element.get(attr):
                return str(element[attr])
        
        # Try to find SKU in text
        text = element.get_text()
        import re
        sku_pattern = r'SKU[:\s]*([A-Z0-9-]+)'
        match = re.search(sku_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_brand(self, element: Any) -> Optional[str]:
        """Extract product brand."""
        selectors = [
            "span.brand",
            "div.brand",
            "span.product-brand",
            "div.product-brand",
        ]
        
        for selector in selectors:
            brand_elem = element.select_one(selector)
            if brand_elem:
                return self._clean_text(brand_elem.get_text())
        
        return None
    
    def _extract_presentation(self, element: Any) -> Optional[str]:
        """Extract product presentation (e.g., '20 comprimidos')."""
        # Look for presentation in product name or description
        text = element.get_text()
        
        import re
        # Common presentation patterns
        patterns = [
            r'\d+\s*(?:comprimidos?|cápsulas?|tabletas?|ml|mg|g|unidades?)',
            r'\d+\s*x\s*\d+\s*(?:ml|mg|g)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    async def search(self, query: str, max_results: int = 20) -> ScraperResult:
        """
        Search for products in Cruz Verde.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            ScraperResult: Search results
        """
        return await self._execute_search(query, max_results)


__all__ = ["CruzVerdeScraper"]

# Made with Bob