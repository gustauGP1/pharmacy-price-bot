"""
MongoDB client for Pharmacy Price Bot.
Handles connection, initialization, and database operations.
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config.settings import get_settings
from utils.logger import logger


class MongoDBClient:
    """MongoDB client wrapper using Motor (async driver)."""
    
    def __init__(self):
        """Initialize MongoDB client."""
        self.settings = get_settings()
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._is_connected = False
    
    async def connect(self) -> None:
        """
        Connect to MongoDB.
        
        Raises:
            ConnectionFailure: If connection fails
        """
        try:
            logger.info("🔌 Connecting to MongoDB...")
            
            self.client = AsyncIOMotorClient(
                self.settings.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10,
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            self.db = self.client[self.settings.mongodb_db_name]
            self._is_connected = True
            
            logger.info(f"✅ Connected to MongoDB: {self.settings.mongodb_db_name}")
            
            # Create indexes
            await self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self._is_connected = False
            logger.info("👋 Disconnected from MongoDB")
    
    async def _create_indexes(self) -> None:
        """Create database indexes for optimal performance."""
        try:
            logger.info("📑 Creating database indexes...")
            
            # Pharmacies indexes
            await self.db.pharmacies.create_index("name", unique=True)
            await self.db.pharmacies.create_index("is_active")
            
            # Medicines indexes
            await self.db.medicines.create_index("normalized_name")
            await self.db.medicines.create_index("search_keywords")
            await self.db.medicines.create_index([("name", "text"), ("description", "text")])
            await self.db.medicines.create_index("search_count")
            
            # Prices indexes
            await self.db.prices.create_index([("medicine_id", 1), ("pharmacy", 1)])
            await self.db.prices.create_index("pharmacy")
            await self.db.prices.create_index("current_price")
            await self.db.prices.create_index("in_stock")
            await self.db.prices.create_index("last_checked")
            
            # Searches indexes
            await self.db.searches.create_index("user_id")
            await self.db.searches.create_index("normalized_query")
            await self.db.searches.create_index("created_at")
            await self.db.searches.create_index([("user_id", 1), ("created_at", -1)])
            
            # Users indexes
            await self.db.users.create_index("telegram_id", unique=True)
            await self.db.users.create_index("is_active")
            await self.db.users.create_index("last_interaction")
            
            # Analytics indexes
            await self.db.analytics.create_index([("period_start", 1), ("period_type", 1)])
            await self.db.analytics.create_index("period_type")
            
            # Cache indexes (fallback)
            await self.db.cache.create_index("key", unique=True)
            await self.db.cache.create_index("expires_at", expireAfterSeconds=0)
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Error creating indexes: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._is_connected
    
    def get_collection(self, collection_name: str):
        """
        Get a collection from the database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection object
            
        Raises:
            RuntimeError: If not connected to database
        """
        if not self.is_connected or not self.db:
            raise RuntimeError("Not connected to MongoDB")
        return self.db[collection_name]
    
    async def health_check(self) -> dict:
        """
        Perform health check on MongoDB connection.
        
        Returns:
            dict: Health status information
        """
        try:
            if not self.is_connected:
                return {
                    "status": "disconnected",
                    "healthy": False,
                }
            
            # Ping database
            await self.client.admin.command('ping')
            
            # Get server info
            server_info = await self.client.server_info()
            
            # Get database stats
            stats = await self.db.command("dbStats")
            
            return {
                "status": "connected",
                "healthy": True,
                "database": self.settings.mongodb_db_name,
                "version": server_info.get("version"),
                "collections": stats.get("collections"),
                "data_size": stats.get("dataSize"),
                "storage_size": stats.get("storageSize"),
            }
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
            }
    
    async def get_stats(self) -> dict:
        """
        Get database statistics.
        
        Returns:
            dict: Database statistics
        """
        try:
            stats = {}
            
            # Count documents in each collection
            collections = [
                "pharmacies",
                "medicines",
                "prices",
                "searches",
                "users",
                "analytics",
            ]
            
            for collection in collections:
                count = await self.db[collection].count_documents({})
                stats[collection] = count
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}


# Global MongoDB client instance
_mongodb_client: Optional[MongoDBClient] = None


async def get_mongodb_client() -> MongoDBClient:
    """
    Get or create MongoDB client instance.
    
    Returns:
        MongoDBClient: MongoDB client instance
    """
    global _mongodb_client
    
    if _mongodb_client is None:
        _mongodb_client = MongoDBClient()
        await _mongodb_client.connect()
    
    return _mongodb_client


async def close_mongodb_client() -> None:
    """Close MongoDB client connection."""
    global _mongodb_client
    
    if _mongodb_client is not None:
        await _mongodb_client.disconnect()
        _mongodb_client = None


__all__ = [
    "MongoDBClient",
    "get_mongodb_client",
    "close_mongodb_client",
]

# Made with Bob