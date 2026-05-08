"""
Analytics service for tracking metrics and generating reports.
Collects and analyzes usage data, search patterns, and system performance.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter

from database.repositories import (
    SearchRepository,
    UserRepository,
    AnalyticsRepository,
    PriceRepository,
)
from database.models import Analytics, DailyStats, PharmacyStats, PharmacyEnum
from services.cache_service import get_cache_service
from utils.logger import logger


class AnalyticsService:
    """Service for collecting and analyzing usage metrics."""
    
    def __init__(self):
        """Initialize analytics service."""
        self.search_repo = SearchRepository()
        self.user_repo = UserRepository()
        self.analytics_repo = AnalyticsRepository()
        self.price_repo = PriceRepository()
        self.cache_service = None
    
    async def initialize(self) -> None:
        """Initialize service."""
        self.cache_service = await get_cache_service()
        logger.info("✅ Analytics service initialized")
    
    async def track_search(
        self,
        user_id: int,
        query: str,
        results_count: int,
        duration_ms: int,
        cache_hit: bool
    ) -> None:
        """
        Track a search event.
        
        Args:
            user_id: User ID
            query: Search query
            results_count: Number of results found
            duration_ms: Search duration in milliseconds
            cache_hit: Whether result was from cache
        """
        try:
            # Increment counters in cache
            if self.cache_service:
                await self.cache_service.increment_counter("total_searches")
                
                if cache_hit:
                    await self.cache_service.increment_counter("cache_hits")
                else:
                    await self.cache_service.increment_counter("cache_misses")
            
            logger.debug(f"Tracked search: user={user_id}, query='{query}', results={results_count}")
            
        except Exception as e:
            logger.warning(f"Failed to track search: {e}")
    
    async def track_user_action(
        self,
        user_id: int,
        action: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Track a user action.
        
        Args:
            user_id: User ID
            action: Action name (e.g., 'click_result', 'view_price')
            metadata: Additional action metadata
        """
        try:
            counter_key = f"action_{action}"
            
            if self.cache_service:
                await self.cache_service.increment_counter(counter_key)
            
            logger.debug(f"Tracked action: user={user_id}, action={action}")
            
        except Exception as e:
            logger.warning(f"Failed to track action: {e}")
    
    async def generate_daily_report(self, date: Optional[datetime] = None) -> Analytics:
        """
        Generate daily analytics report.
        
        Args:
            date: Date for report (default: today)
            
        Returns:
            Analytics: Daily analytics data
        """
        if date is None:
            date = datetime.utcnow()
        
        # Define period
        period_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)
        
        try:
            logger.info(f"📊 Generating daily report for {period_start.date()}")
            
            # Get searches for the day
            searches = await self.search_repo.find_many(
                {
                    "created_at": {
                        "$gte": period_start,
                        "$lt": period_end
                    }
                },
                limit=10000
            )
            
            # Calculate metrics
            total_searches = len(searches)
            unique_users = len(set(s.get("user_id") for s in searches))
            
            # Get cache stats
            cache_hits = 0
            cache_misses = 0
            total_duration = 0
            
            if self.cache_service:
                cache_hits = await self.cache_service.get_counter("cache_hits")
                cache_misses = await self.cache_service.get_counter("cache_misses")
            
            for search in searches:
                if search.get("search_duration_ms"):
                    total_duration += search["search_duration_ms"]
            
            avg_duration = total_duration / total_searches if total_searches > 0 else 0
            cache_hit_rate = (cache_hits / (cache_hits + cache_misses) * 100) if (cache_hits + cache_misses) > 0 else 0
            
            # Get top searches
            query_counter = Counter(s.get("normalized_query") for s in searches)
            top_searches = [
                {"query": query, "count": count}
                for query, count in query_counter.most_common(10)
            ]
            
            # Get pharmacy stats
            pharmacy_stats = await self._get_pharmacy_stats(period_start, period_end)
            
            # Get user stats
            total_users = await self.user_repo.count({})
            new_users = await self.user_repo.count({
                "created_at": {
                    "$gte": period_start,
                    "$lt": period_end
                }
            })
            active_users = await self.user_repo.get_active_users_count(days=1)
            
            # Create analytics record
            analytics = Analytics(
                period_start=period_start,
                period_end=period_end,
                period_type="daily",
                total_searches=total_searches,
                unique_users=unique_users,
                total_users=total_users,
                new_users=new_users,
                top_searches=top_searches,
                avg_results_per_search=sum(s.get("results_count", 0) for s in searches) / total_searches if total_searches > 0 else 0,
                avg_search_duration_ms=avg_duration,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                cache_hit_rate=cache_hit_rate,
                pharmacy_stats=pharmacy_stats,
            )
            
            # Save to database
            await self.analytics_repo.create_analytics(analytics)
            
            logger.info(f"✅ Daily report generated: {total_searches} searches, {unique_users} users")
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error generating daily report: {e}")
            raise
    
    async def _get_pharmacy_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[PharmacyStats]:
        """Get statistics for each pharmacy."""
        stats = []
        
        for pharmacy in PharmacyEnum:
            try:
                # Count products
                total_products = await self.price_repo.count({"pharmacy": pharmacy.value})
                
                # Calculate average price
                prices = await self.price_repo.find_many(
                    {"pharmacy": pharmacy.value, "in_stock": True},
                    limit=1000
                )
                
                avg_price = sum(p.get("current_price", 0) for p in prices) / len(prices) if prices else 0
                
                # Count searches
                total_searches = await self.search_repo.count({
                    "created_at": {"$gte": start_date, "$lt": end_date},
                    "results.pharmacy": pharmacy.value
                })
                
                stats.append(PharmacyStats(
                    pharmacy=pharmacy,
                    total_products=total_products,
                    avg_price=round(avg_price, 2),
                    total_searches=total_searches,
                    scrape_errors=0,  # Would need error tracking
                ))
                
            except Exception as e:
                logger.warning(f"Error getting stats for {pharmacy.value}: {e}")
        
        return stats
    
    async def get_popular_searches(
        self,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most popular searches.
        
        Args:
            days: Number of days to look back
            limit: Maximum results
            
        Returns:
            List of popular searches with counts
        """
        try:
            return await self.search_repo.get_popular_searches(days, limit)
        except Exception as e:
            logger.error(f"Error getting popular searches: {e}")
            return []
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            dict: User statistics
        """
        try:
            user = await self.user_repo.get_by_telegram_id(user_id)
            
            if not user:
                return {}
            
            # Get recent searches
            recent_searches = await self.search_repo.get_user_searches(user_id, limit=10)
            
            # Count searches today
            searches_today = await self.search_repo.count_user_searches_today(user_id)
            
            return {
                "user_id": user_id,
                "total_searches": user.total_searches,
                "searches_today": searches_today,
                "member_since": user.created_at.isoformat(),
                "last_interaction": user.last_interaction.isoformat(),
                "recent_searches": [
                    {
                        "query": s.query,
                        "results_count": s.results_count,
                        "timestamp": s.created_at.isoformat(),
                    }
                    for s in recent_searches
                ],
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """
        Get overall system statistics.
        
        Returns:
            dict: System statistics
        """
        try:
            # Get latest analytics
            latest = await self.analytics_repo.get_latest("daily")
            
            # Get totals
            total_users = await self.user_repo.count({})
            total_searches = await self.search_repo.count({})
            active_users_30d = await self.user_repo.get_active_users_count(days=30)
            
            # Get cache stats
            cache_stats = {}
            if self.cache_service:
                cache_stats = await self.cache_service.health_check()
            
            return {
                "total_users": total_users,
                "active_users_30d": active_users_30d,
                "total_searches": total_searches,
                "latest_daily_report": latest.model_dump() if latest else None,
                "cache": cache_stats,
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    async def get_price_trends(
        self,
        medicine_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get price trends for a medicine.
        
        Args:
            medicine_id: Medicine ID
            days: Number of days to analyze
            
        Returns:
            dict: Price trend data
        """
        try:
            prices = await self.price_repo.get_prices_for_medicine(medicine_id)
            
            trends = {}
            for price in prices:
                pharmacy = price.pharmacy.value
                
                # Get recent history
                recent_history = [
                    h for h in price.price_history
                    if h.timestamp >= datetime.utcnow() - timedelta(days=days)
                ]
                
                if recent_history:
                    prices_list = [h.price for h in recent_history]
                    
                    trends[pharmacy] = {
                        "current_price": price.current_price,
                        "min_price": min(prices_list),
                        "max_price": max(prices_list),
                        "avg_price": round(sum(prices_list) / len(prices_list), 2),
                        "price_change": price.current_price - prices_list[0] if prices_list else 0,
                        "data_points": len(recent_history),
                    }
            
            return {
                "medicine_id": medicine_id,
                "period_days": days,
                "trends": trends,
            }
            
        except Exception as e:
            logger.error(f"Error getting price trends: {e}")
            return {}
    
    async def export_report(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export analytics report for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            format: Export format (json, csv)
            
        Returns:
            dict: Exported report data
        """
        try:
            analytics_records = await self.analytics_repo.get_period_range(
                start_date,
                end_date,
                "daily"
            )
            
            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "records": [a.model_dump() for a in analytics_records],
                "summary": {
                    "total_searches": sum(a.total_searches for a in analytics_records),
                    "unique_users": len(set(a.unique_users for a in analytics_records)),
                    "avg_cache_hit_rate": sum(a.cache_hit_rate for a in analytics_records) / len(analytics_records) if analytics_records else 0,
                },
            }
            
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return {}


# Global analytics service instance
_analytics_service: Optional[AnalyticsService] = None


async def get_analytics_service() -> AnalyticsService:
    """
    Get or create analytics service instance.
    
    Returns:
        AnalyticsService: Analytics service instance
    """
    global _analytics_service
    
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
        await _analytics_service.initialize()
    
    return _analytics_service


__all__ = [
    "AnalyticsService",
    "get_analytics_service",
]

# Made with Bob