"""
Comparison service for orchestrating scrapers and comparing prices.
Coordinates scraping, caching, and price comparison across pharmacies.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from scrapers.cruz_verde_scraper import CruzVerdeScraper
from scrapers.salcobrand_scraper import SalcobrandScraper
from scrapers.ahumada_scraper import AhumadaScraper
from scrapers.base_scraper import ScraperResult, ProductResult, ScraperStatus
from services.cache_service import get_cache_service
from services.ai_service import get_ai_service
from database.repositories import (
    MedicineRepository,
    PriceRepository,
    PharmacyRepository,
    SearchRepository,
)
from database.models import PharmacyEnum, Medicine, Price, Search, SearchResult
from config.settings import get_settings
from utils.logger import logger


class ComparisonService:
    """
    Service for comparing medicine prices across pharmacies.
    Orchestrates scraping, caching, and data persistence.
    """
    
    def __init__(self):
        """Initialize comparison service."""
        self.settings = get_settings()
        
        # Initialize scrapers
        self.scrapers = {
            PharmacyEnum.CRUZ_VERDE: CruzVerdeScraper(),
            PharmacyEnum.SALCOBRAND: SalcobrandScraper(),
            PharmacyEnum.FARMACIAS_AHUMADA: AhumadaScraper(),
        }
        
        # Initialize repositories
        self.medicine_repo = MedicineRepository()
        self.price_repo = PriceRepository()
        self.pharmacy_repo = PharmacyRepository()
        self.search_repo = SearchRepository()
        
        # Services
        self.cache_service = None
        self.ai_service = None
    
    async def initialize(self) -> None:
        """Initialize services."""
        self.cache_service = await get_cache_service()
        self.ai_service = get_ai_service()
        logger.info("✅ Comparison service initialized")
    
    async def search_and_compare(
        self,
        query: str,
        user_id: int,
        use_cache: bool = True,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Search for medicine and compare prices across pharmacies.
        
        Args:
            query: Search query
            user_id: Telegram user ID
            use_cache: Whether to use cache
            use_ai: Whether to use AI for query processing
            
        Returns:
            dict: Comparison results with prices from all pharmacies
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"🔍 Starting search for: '{query}' (user: {user_id})")
            
            # Step 1: Check cache
            if use_cache and self.cache_service:
                cached = await self.cache_service.get_search_results(query)
                if cached:
                    logger.info(f"✅ Cache HIT for query: '{query}'")
                    return {
                        **cached,
                        "cache_hit": True,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
            
            # Step 2: Process query with AI
            processed_query = query
            suggestions = []
            
            if use_ai and self.ai_service and self.ai_service.is_initialized:
                try:
                    # Normalize query
                    processed_query = await self.ai_service.normalize_query(query)
                    
                    # Get suggestions
                    suggestions = await self.ai_service.suggest_alternatives(processed_query)
                    
                    logger.info(f"AI processed: '{query}' -> '{processed_query}'")
                except Exception as e:
                    logger.warning(f"AI processing failed: {e}")
            
            # Step 3: Scrape all pharmacies concurrently
            scrape_results = await self._scrape_all_pharmacies(processed_query)
            
            # Step 4: Process and organize results
            comparison_data = await self._process_scrape_results(
                scrape_results,
                processed_query
            )
            
            # Step 5: Save search to database
            await self._save_search(
                user_id=user_id,
                original_query=query,
                processed_query=processed_query,
                results=comparison_data["results"],
                ai_suggestions=suggestions,
            )
            
            # Step 6: Cache results
            if use_cache and self.cache_service:
                await self.cache_service.cache_search_results(
                    query,
                    comparison_data
                )
            
            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                **comparison_data,
                "original_query": query,
                "processed_query": processed_query,
                "suggestions": suggestions,
                "cache_hit": False,
                "duration_seconds": round(duration, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            logger.info(f"✅ Search completed in {duration:.2f}s - Found {len(comparison_data['results'])} results")
            
            return result
            
        except Exception as e:
            logger.exception(f"❌ Error in search_and_compare: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "original_query": query,
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def _scrape_all_pharmacies(
        self,
        query: str
    ) -> Dict[PharmacyEnum, ScraperResult]:
        """
        Scrape all pharmacies concurrently.
        
        Args:
            query: Search query
            
        Returns:
            dict: Scraper results by pharmacy
        """
        tasks = []
        pharmacy_names = []
        
        for pharmacy, scraper in self.scrapers.items():
            tasks.append(self._scrape_pharmacy(scraper, query))
            pharmacy_names.append(pharmacy)
        
        # Run all scrapers concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results to pharmacies
        scrape_results = {}
        for pharmacy, result in zip(pharmacy_names, results):
            if isinstance(result, Exception):
                logger.error(f"Scraper error for {pharmacy.value}: {result}")
                scrape_results[pharmacy] = ScraperResult(
                    status=ScraperStatus.FAILED,
                    products=[],
                    pharmacy_name=pharmacy.value,
                    query=query,
                    execution_time_ms=0,
                    error_message=str(result),
                )
            else:
                scrape_results[pharmacy] = result
        
        return scrape_results
    
    async def _scrape_pharmacy(
        self,
        scraper,
        query: str
    ) -> ScraperResult:
        """
        Scrape a single pharmacy with context manager.
        
        Args:
            scraper: Scraper instance
            query: Search query
            
        Returns:
            ScraperResult: Scraping results
        """
        async with scraper:
            return await scraper.search(query)
    
    async def _process_scrape_results(
        self,
        scrape_results: Dict[PharmacyEnum, ScraperResult],
        query: str
    ) -> Dict[str, Any]:
        """
        Process scraper results and organize by product.
        
        Args:
            scrape_results: Results from all scrapers
            query: Search query
            
        Returns:
            dict: Organized comparison data
        """
        # Group products by normalized name
        products_by_name: Dict[str, List[Dict]] = {}
        total_results = 0
        successful_pharmacies = 0
        
        for pharmacy, result in scrape_results.items():
            if result.success:
                successful_pharmacies += 1
                
                for product in result.products:
                    total_results += 1
                    
                    # Normalize product name for grouping
                    normalized_name = product.name.lower().strip()
                    
                    product_data = {
                        "pharmacy": pharmacy.value,
                        "pharmacy_display": pharmacy.value.replace("_", " ").title(),
                        "name": product.name,
                        "price": product.price,
                        "original_price": product.original_price,
                        "discount": self._calculate_discount(product.price, product.original_price),
                        "in_stock": product.in_stock,
                        "url": product.url,
                        "image_url": product.image_url,
                        "brand": product.brand,
                        "presentation": product.presentation,
                    }
                    
                    if normalized_name not in products_by_name:
                        products_by_name[normalized_name] = []
                    
                    products_by_name[normalized_name].append(product_data)
        
        # Create comparison results
        comparison_results = []
        
        for normalized_name, pharmacy_prices in products_by_name.items():
            # Sort by price
            pharmacy_prices.sort(key=lambda x: x["price"])
            
            # Find best price
            best_price = pharmacy_prices[0]["price"] if pharmacy_prices else None
            
            comparison_results.append({
                "product_name": pharmacy_prices[0]["name"] if pharmacy_prices else normalized_name,
                "normalized_name": normalized_name,
                "prices": pharmacy_prices,
                "best_price": best_price,
                "price_range": {
                    "min": min(p["price"] for p in pharmacy_prices),
                    "max": max(p["price"] for p in pharmacy_prices),
                    "avg": round(sum(p["price"] for p in pharmacy_prices) / len(pharmacy_prices), 2),
                } if pharmacy_prices else None,
                "available_in": len(pharmacy_prices),
            })
        
        # Sort results by best price
        comparison_results.sort(key=lambda x: x["best_price"] if x["best_price"] else float('inf'))
        
        return {
            "success": True,
            "results": comparison_results,
            "total_results": total_results,
            "unique_products": len(comparison_results),
            "pharmacies_searched": len(scrape_results),
            "pharmacies_successful": successful_pharmacies,
            "scraper_details": {
                pharmacy.value: {
                    "status": result.status.value,
                    "products_found": len(result.products),
                    "execution_time_ms": result.execution_time_ms,
                    "error": result.error_message,
                }
                for pharmacy, result in scrape_results.items()
            },
        }
    
    def _calculate_discount(
        self,
        current_price: float,
        original_price: Optional[float]
    ) -> Optional[float]:
        """Calculate discount percentage."""
        if original_price and original_price > current_price:
            return round(((original_price - current_price) / original_price) * 100, 1)
        return None
    
    async def _save_search(
        self,
        user_id: int,
        original_query: str,
        processed_query: str,
        results: List[Dict],
        ai_suggestions: List[str]
    ) -> None:
        """
        Save search to database.
        
        Args:
            user_id: User ID
            original_query: Original search query
            processed_query: AI-processed query
            results: Search results
            ai_suggestions: AI suggestions
        """
        try:
            # Create search results list
            search_results = []
            
            for result in results[:10]:  # Save top 10
                for price_info in result["prices"][:3]:  # Top 3 prices per product
                    search_results.append(
                        SearchResult(
                            medicine_id=None,  # Will be set if we save medicine
                            medicine_name=result["product_name"],
                            pharmacy=PharmacyEnum(price_info["pharmacy"]),
                            price=price_info["price"],
                            in_stock=price_info["in_stock"],
                            product_url=price_info["url"],
                        )
                    )
            
            # Create search record
            search = Search(
                user_id=user_id,
                query=original_query,
                normalized_query=processed_query,
                results_count=len(results),
                results=search_results,
                ai_processed=len(ai_suggestions) > 0,
                ai_suggestions=ai_suggestions,
            )
            
            await self.search_repo.create_search(search)
            logger.debug(f"Search saved for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to save search: {e}")
    
    async def get_best_deals(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get best deals across all pharmacies.
        
        Args:
            limit: Maximum number of deals
            
        Returns:
            List of best deals
        """
        # This would query the database for products with best discounts
        # Implementation depends on having historical price data
        return []
    
    async def get_price_history(
        self,
        medicine_id: str,
        pharmacy: Optional[PharmacyEnum] = None
    ) -> Dict[str, Any]:
        """
        Get price history for a medicine.
        
        Args:
            medicine_id: Medicine ID
            pharmacy: Specific pharmacy (optional)
            
        Returns:
            dict: Price history data
        """
        try:
            if pharmacy:
                price = await self.price_repo.get_price(medicine_id, pharmacy)
                if price:
                    return {
                        "medicine_id": medicine_id,
                        "pharmacy": pharmacy.value,
                        "current_price": price.current_price,
                        "history": [
                            {
                                "price": h.price,
                                "timestamp": h.timestamp.isoformat(),
                                "in_stock": h.in_stock,
                            }
                            for h in price.price_history
                        ],
                    }
            else:
                prices = await self.price_repo.get_prices_for_medicine(medicine_id)
                return {
                    "medicine_id": medicine_id,
                    "pharmacies": [
                        {
                            "pharmacy": p.pharmacy.value,
                            "current_price": p.current_price,
                            "history": [
                                {
                                    "price": h.price,
                                    "timestamp": h.timestamp.isoformat(),
                                }
                                for h in p.price_history[-30:]  # Last 30 entries
                            ],
                        }
                        for p in prices
                    ],
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return {}


# Global comparison service instance
_comparison_service: Optional[ComparisonService] = None


async def get_comparison_service() -> ComparisonService:
    """
    Get or create comparison service instance.
    
    Returns:
        ComparisonService: Comparison service instance
    """
    global _comparison_service
    
    if _comparison_service is None:
        _comparison_service = ComparisonService()
        await _comparison_service.initialize()
    
    return _comparison_service


__all__ = [
    "ComparisonService",
    "get_comparison_service",
]

# Made with Bob