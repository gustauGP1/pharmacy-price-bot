"""
Repository pattern implementation for database operations.
Provides clean interface for CRUD operations on MongoDB collections.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from database.models import (
    Pharmacy,
    Medicine,
    Price,
    Search,
    User,
    Analytics,
    PharmacyEnum,
)
from database.mongodb_client import get_mongodb_client
from utils.logger import logger


class BaseRepository:
    """Base repository with common CRUD operations."""
    
    def __init__(self, collection_name: str):
        """
        Initialize repository.
        
        Args:
            collection_name: Name of the MongoDB collection
        """
        self.collection_name = collection_name
        self._collection = None
    
    async def _get_collection(self):
        """Get collection instance."""
        if self._collection is None:
            client = await get_mongodb_client()
            self._collection = client.get_collection(self.collection_name)
        return self._collection
    
    async def find_by_id(self, doc_id: str) -> Optional[Dict]:
        """Find document by ID."""
        try:
            collection = await self._get_collection()
            return await collection.find_one({"_id": ObjectId(doc_id)})
        except Exception as e:
            logger.error(f"Error finding document by ID: {e}")
            return None
    
    async def find_one(self, query: Dict) -> Optional[Dict]:
        """Find one document matching query."""
        try:
            collection = await self._get_collection()
            return await collection.find_one(query)
        except Exception as e:
            logger.error(f"Error finding document: {e}")
            return None
    
    async def find_many(
        self,
        query: Dict,
        limit: int = 100,
        skip: int = 0,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict]:
        """Find multiple documents."""
        try:
            collection = await self._get_collection()
            cursor = collection.find(query).skip(skip).limit(limit)
            
            if sort:
                cursor = cursor.sort(sort)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error finding documents: {e}")
            return []
    
    async def insert_one(self, document: Dict) -> Optional[str]:
        """Insert one document."""
        try:
            collection = await self._get_collection()
            result = await collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting document: {e}")
            return None
    
    async def update_one(self, query: Dict, update: Dict) -> bool:
        """Update one document."""
        try:
            collection = await self._get_collection()
            update["$set"]["updated_at"] = datetime.utcnow()
            result = await collection.update_one(query, update)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    async def delete_one(self, query: Dict) -> bool:
        """Delete one document."""
        try:
            collection = await self._get_collection()
            result = await collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    async def count(self, query: Dict = None) -> int:
        """Count documents matching query."""
        try:
            collection = await self._get_collection()
            return await collection.count_documents(query or {})
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0


class PharmacyRepository(BaseRepository):
    """Repository for Pharmacy collection."""
    
    def __init__(self):
        super().__init__("pharmacies")
    
    async def get_by_name(self, name: PharmacyEnum) -> Optional[Pharmacy]:
        """Get pharmacy by name."""
        doc = await self.find_one({"name": name.value})
        return Pharmacy(**doc) if doc else None
    
    async def get_all_active(self) -> List[Pharmacy]:
        """Get all active pharmacies."""
        docs = await self.find_many({"is_active": True})
        return [Pharmacy(**doc) for doc in docs]
    
    async def create_pharmacy(self, pharmacy: Pharmacy) -> Optional[str]:
        """Create new pharmacy."""
        return await self.insert_one(pharmacy.model_dump(by_alias=True, exclude={"id"}))
    
    async def update_scrape_stats(
        self,
        pharmacy_name: PharmacyEnum,
        success: bool,
        products_count: int = 0
    ) -> bool:
        """Update pharmacy scraping statistics."""
        pharmacy = await self.get_by_name(pharmacy_name)
        if not pharmacy:
            return False
        
        # Calculate new success rate
        total_scrapes = pharmacy.scrape_success_rate * 100
        new_rate = ((total_scrapes + (100 if success else 0)) / 101)
        
        return await self.update_one(
            {"name": pharmacy_name.value},
            {
                "$set": {
                    "last_scraped": datetime.utcnow(),
                    "scrape_success_rate": new_rate,
                    "total_products": products_count,
                }
            }
        )


class MedicineRepository(BaseRepository):
    """Repository for Medicine collection."""
    
    def __init__(self):
        super().__init__("medicines")
    
    async def search_by_name(self, query: str, limit: int = 20) -> List[Medicine]:
        """Search medicines by name using text search."""
        try:
            collection = await self._get_collection()
            
            # Text search
            cursor = collection.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            docs = await cursor.to_list(length=limit)
            return [Medicine(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error searching medicines: {e}")
            return []
    
    async def search_by_normalized_name(self, normalized_name: str) -> List[Medicine]:
        """Search by normalized name (exact or partial match)."""
        docs = await self.find_many(
            {"normalized_name": {"$regex": normalized_name, "$options": "i"}},
            limit=20
        )
        return [Medicine(**doc) for doc in docs]
    
    async def get_or_create(self, medicine_data: Dict) -> Optional[Medicine]:
        """Get existing medicine or create new one."""
        # Try to find existing
        existing = await self.find_one({
            "normalized_name": medicine_data["normalized_name"]
        })
        
        if existing:
            return Medicine(**existing)
        
        # Create new
        medicine = Medicine(**medicine_data)
        doc_id = await self.insert_one(medicine.model_dump(by_alias=True, exclude={"id"}))
        
        if doc_id:
            medicine.id = ObjectId(doc_id)
            return medicine
        
        return None
    
    async def increment_search_count(self, medicine_id: str) -> bool:
        """Increment search count for a medicine."""
        try:
            collection = await self._get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(medicine_id)},
                {"$inc": {"search_count": 1}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error incrementing search count: {e}")
            return False
    
    async def get_popular_medicines(self, limit: int = 10) -> List[Medicine]:
        """Get most searched medicines."""
        docs = await self.find_many(
            {},
            limit=limit,
            sort=[("search_count", -1)]
        )
        return [Medicine(**doc) for doc in docs]


class PriceRepository(BaseRepository):
    """Repository for Price collection."""
    
    def __init__(self):
        super().__init__("prices")
    
    async def get_prices_for_medicine(
        self,
        medicine_id: str,
        only_in_stock: bool = True
    ) -> List[Price]:
        """Get all prices for a medicine across pharmacies."""
        query = {"medicine_id": ObjectId(medicine_id)}
        if only_in_stock:
            query["in_stock"] = True
        
        docs = await self.find_many(query, sort=[("current_price", 1)])
        return [Price(**doc) for doc in docs]
    
    async def get_price(
        self,
        medicine_id: str,
        pharmacy: PharmacyEnum
    ) -> Optional[Price]:
        """Get price for specific medicine at specific pharmacy."""
        doc = await self.find_one({
            "medicine_id": ObjectId(medicine_id),
            "pharmacy": pharmacy.value
        })
        return Price(**doc) if doc else None
    
    async def upsert_price(self, price: Price) -> bool:
        """Insert or update price."""
        try:
            collection = await self._get_collection()
            
            # Add to history before updating
            existing = await self.get_price(
                str(price.medicine_id),
                price.pharmacy
            )
            
            if existing:
                price.add_to_history()
            
            result = await collection.update_one(
                {
                    "medicine_id": price.medicine_id,
                    "pharmacy": price.pharmacy.value
                },
                {
                    "$set": price.model_dump(by_alias=True, exclude={"id"}),
                    "$inc": {"check_count": 1}
                },
                upsert=True
            )
            
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            logger.error(f"Error upserting price: {e}")
            return False
    
    async def get_cheapest_price(self, medicine_id: str) -> Optional[Price]:
        """Get cheapest price for a medicine."""
        docs = await self.find_many(
            {
                "medicine_id": ObjectId(medicine_id),
                "in_stock": True
            },
            limit=1,
            sort=[("current_price", 1)]
        )
        return Price(**docs[0]) if docs else None
    
    async def get_price_statistics(self, medicine_id: str) -> Dict[str, Any]:
        """Get price statistics for a medicine."""
        try:
            collection = await self._get_collection()
            
            pipeline = [
                {"$match": {"medicine_id": ObjectId(medicine_id), "in_stock": True}},
                {
                    "$group": {
                        "_id": None,
                        "avg_price": {"$avg": "$current_price"},
                        "min_price": {"$min": "$current_price"},
                        "max_price": {"$max": "$current_price"},
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            result = await collection.aggregate(pipeline).to_list(length=1)
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"Error getting price statistics: {e}")
            return {}


class SearchRepository(BaseRepository):
    """Repository for Search collection."""
    
    def __init__(self):
        super().__init__("searches")
    
    async def create_search(self, search: Search) -> Optional[str]:
        """Create new search record."""
        return await self.insert_one(search.model_dump(by_alias=True, exclude={"id"}))
    
    async def get_user_searches(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Search]:
        """Get recent searches for a user."""
        docs = await self.find_many(
            {"user_id": user_id},
            limit=limit,
            sort=[("created_at", -1)]
        )
        return [Search(**doc) for doc in docs]
    
    async def get_popular_searches(
        self,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most popular searches in the last N days."""
        try:
            collection = await self._get_collection()
            
            since = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {"$match": {"created_at": {"$gte": since}}},
                {
                    "$group": {
                        "_id": "$normalized_query",
                        "count": {"$sum": 1},
                        "avg_results": {"$avg": "$results_count"}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]
            
            return await collection.aggregate(pipeline).to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting popular searches: {e}")
            return []
    
    async def count_user_searches_today(self, user_id: int) -> int:
        """Count searches by user today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.count({
            "user_id": user_id,
            "created_at": {"$gte": today_start}
        })


class UserRepository(BaseRepository):
    """Repository for User collection."""
    
    def __init__(self):
        super().__init__("users")
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        doc = await self.find_one({"telegram_id": telegram_id})
        return User(**doc) if doc else None
    
    async def create_user(self, user: User) -> Optional[str]:
        """Create new user."""
        return await self.insert_one(user.model_dump(by_alias=True, exclude={"id"}))
    
    async def get_or_create_user(self, telegram_id: int, **kwargs) -> Optional[User]:
        """Get existing user or create new one."""
        user = await self.get_by_telegram_id(telegram_id)
        
        if user:
            # Update last interaction
            await self.update_one(
                {"telegram_id": telegram_id},
                {"$set": {"last_interaction": datetime.utcnow()}}
            )
            return user
        
        # Create new user
        user_data = {"telegram_id": telegram_id, **kwargs}
        user = User(**user_data)
        doc_id = await self.create_user(user)
        
        if doc_id:
            user.id = ObjectId(doc_id)
            return user
        
        return None
    
    async def increment_search_count(self, telegram_id: int) -> bool:
        """Increment user's search count."""
        try:
            collection = await self._get_collection()
            result = await collection.update_one(
                {"telegram_id": telegram_id},
                {
                    "$inc": {"total_searches": 1, "searches_today": 1},
                    "$set": {"last_search_date": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error incrementing search count: {e}")
            return False
    
    async def reset_daily_searches(self) -> int:
        """Reset daily search counts for all users."""
        try:
            collection = await self._get_collection()
            result = await collection.update_many(
                {},
                {"$set": {"searches_today": 0}}
            )
            return result.modified_count
        except Exception as e:
            logger.error(f"Error resetting daily searches: {e}")
            return 0
    
    async def get_active_users_count(self, days: int = 30) -> int:
        """Get count of active users in last N days."""
        since = datetime.utcnow() - timedelta(days=days)
        return await self.count({
            "last_interaction": {"$gte": since},
            "is_active": True
        })


class AnalyticsRepository(BaseRepository):
    """Repository for Analytics collection."""
    
    def __init__(self):
        super().__init__("analytics")
    
    async def create_analytics(self, analytics: Analytics) -> Optional[str]:
        """Create new analytics record."""
        return await self.insert_one(analytics.model_dump(by_alias=True, exclude={"id"}))
    
    async def get_latest(self, period_type: str = "daily") -> Optional[Analytics]:
        """Get latest analytics for period type."""
        docs = await self.find_many(
            {"period_type": period_type},
            limit=1,
            sort=[("period_start", -1)]
        )
        return Analytics(**docs[0]) if docs else None
    
    async def get_period_range(
        self,
        start_date: datetime,
        end_date: datetime,
        period_type: str = "daily"
    ) -> List[Analytics]:
        """Get analytics for a date range."""
        docs = await self.find_many(
            {
                "period_type": period_type,
                "period_start": {"$gte": start_date, "$lte": end_date}
            },
            sort=[("period_start", 1)]
        )
        return [Analytics(**doc) for doc in docs]


# Export repositories
__all__ = [
    "BaseRepository",
    "PharmacyRepository",
    "MedicineRepository",
    "PriceRepository",
    "SearchRepository",
    "UserRepository",
    "AnalyticsRepository",
]

# Made with Bob