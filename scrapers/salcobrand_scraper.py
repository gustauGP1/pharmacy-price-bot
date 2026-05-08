"""
Salcobrand pharmacy scraper.
Scrapes medicine prices from www.salcobrand.cl
"""

from typing import List, Any, Optional
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, ScraperResult, ProductResult
from config.settings import get_settings
from utils.logger import logger


class SalcobrandScraper(BaseScraper):
    """Scraper for Salcobrand pharmacy."""
    
    def __init__(self):
        """Initialize Salcobrand scraper."""
        settings = get_settings()
        super().__init__(
            pharmacy_name="Salcobrand",
            base_url=settings.salcobrand_url
        )
    
    def _build_search_url(self, query: str) -> str:
        """
        Build search URL for Salcobrand.
        
        Args:
            query: Search query
            
        Returns:
            str: Complete search URL
        """
        encoded_query = quote_plus(query)
        return f"{self.base_url}/search?q={encoded_query}"
    
    def _find_product_elements(self, soup: BeautifulSoup) -> List[Any]:
        """
        Find product elements in Salcobrand HTML.
        
        Args:
            soup: Parsed HTML
            
        Returns:
            List: Product elements
        """
        product_elements = []
        
        # Try common selectors for Salcobrand
        selectors = [
            "div.product-tile",
            "div.product-item",
            "div.product-card",
            "article.product",
            "li.product",
            "div[data-product]",
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                product_elements = elements
                logger.debug(f"Found {len(elements)} products using selector: {selector}")
                break
        
        return product_elements
    
    def _parse_product(self, element: Any) -> Optional[ProductResult]:
        """
        Parse a product element from Salcobrand.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            ProductResult: Parsed product or None
        """
        try:
            name = self._extract_name(element)
            if not name:
                return None
            
            price = self._extract_price(element)
            if not price:
                return None
            
            original_price = self._extract_original_price(element)
            url = self._extract_url(element)
            image_url = self._extract_image(element)
            in_stock = self._extract_stock_status(element)
            sku = self._extract_sku_from_element(element)
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
            logger.warning(f"Failed to parse Salcobrand product: {e}")
            return None
    
    def _extract_name(self, element: Any) -> Optional[str]:
        """Extract product name."""
        selectors = [
            "h2.product-name",
            "h3.product-name",
            "div.product-name",
            "a.product-link",
            "span.product-title",
        ]
        
        for selector in selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                return self._clean_text(name_elem.get_text())
        
        # Fallback
        for tag in ["h2", "h3", "a"]:
            elem = element.find(tag)
            if elem:
                text = self._clean_text(elem.get_text())
                if text and len(text) > 5:
                    return text
        
        return None
    
    def _extract_price(self, element: Any) -> Optional[float]:
        """Extract current price."""
        selectors = [
            "span.price-sales",
            "span.price",
            "div.price",
            "span.product-price",
            "span.price-current",
        ]
        
        for selector in selectors:
            price_elem = element.select_one(selector)
            if price_elem:
                price = self._clean_price(price_elem.get_text())
                if price:
                    return price
        
        return None
    
    def _extract_original_price(self, element: Any) -> Optional[float]:
        """Extract original price."""
        selectors = [
            "span.price-standard",
            "span.price-old",
            "del.price",
            "s.price",
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
        link = element.find("a", href=True)
        if link:
            href = link["href"]
            if href.startswith("/"):
                return f"{self.base_url}{href}"
            elif href.startswith("http"):
                return href
            else:
                return f"{self.base_url}/{href}"
        
        return self.base_url
    
    def _extract_image(self, element: Any) -> Optional[str]:
        """Extract product image URL."""
        img = element.find("img")
        if img:
            for attr in ["src", "data-src", "data-lazy"]:
                if img.get(attr):
                    img_url = img[attr]
                    if img_url.startswith("/"):
                        return f"{self.base_url}{img_url}"
                    elif img_url.startswith("http"):
                        return img_url
        
        return None
    
    def _extract_stock_status(self, element: Any) -> bool:
        """Extract stock status."""
        text = element.get_text().lower()
        
        if any(indicator in text for indicator in ["sin stock", "agotado", "no disponible"]):
            return False
        
        return True
    
    def _extract_sku_from_element(self, element: Any) -> Optional[str]:
        """Extract SKU."""
        for attr in ["data-sku", "data-pid", "data-product-id"]:
            if element.get(attr):
                return str(element[attr])
        
        return None
    
    def _extract_brand(self, element: Any) -> Optional[str]:
        """Extract brand."""
        selectors = ["span.brand", "div.brand", "span.product-brand"]
        
        for selector in selectors:
            brand_elem = element.select_one(selector)
            if brand_elem:
                return self._clean_text(brand_elem.get_text())
        
        return None
    
    def _extract_presentation(self, element: Any) -> Optional[str]:
        """Extract presentation."""
        text = element.get_text()
        
        import re
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
        Search for products in Salcobrand.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            ScraperResult: Search results
        """
        return await self._execute_search(query, max_results)


__all__ = ["SalcobrandScraper"]

# Made with Bob