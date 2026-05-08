"""
Data models using Pydantic for MongoDB collections.
Defines the structure for pharmacies, medicines, prices, searches, and analytics.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, ConfigDict
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v, info):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class PharmacyEnum(str, Enum):
    """Enum for pharmacy names."""
    CRUZ_VERDE = "cruz_verde"
    SALCOBRAND = "salcobrand"
    FARMACIAS_AHUMADA = "farmacias_ahumada"


class BaseMongoModel(BaseModel):
    """Base model for MongoDB documents."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# PHARMACY MODEL
# ============================================
class PharmacyLocation(BaseModel):
    """Pharmacy location information."""
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Pharmacy(BaseMongoModel):
    """Pharmacy model."""
    name: PharmacyEnum
    display_name: str
    url: str
    logo_url: Optional[str] = None
    is_active: bool = True
    locations: List[PharmacyLocation] = Field(default_factory=list)
    scraper_config: dict = Field(default_factory=dict)
    
    # Metadata
    total_products: int = 0
    last_scraped: Optional[datetime] = None
    scrape_success_rate: float = 100.0


# ============================================
# MEDICINE MODEL
# ============================================
class Medicine(BaseMongoModel):
    """Medicine/Product model."""
    name: str
    normalized_name: str  # Normalized for search
    generic_name: Optional[str] = None
    brand: Optional[str] = None
    
    # Product details
    description: Optional[str] = None
    active_ingredient: Optional[str] = None
    dosage: Optional[str] = None
    presentation: Optional[str] = None  # e.g., "20 comprimidos"
    
    # Categories
    category: Optional[str] = None
    subcategory: Optional[str] = None
    requires_prescription: bool = False
    
    # Search optimization
    search_keywords: List[str] = Field(default_factory=list)
    search_count: int = 0
    
    @field_validator("normalized_name", mode="before")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """Normalize medicine name for search."""
        return v.lower().strip()


# ============================================
# PRICE MODEL
# ============================================
class PriceHistory(BaseModel):
    """Historical price point."""
    price: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    in_stock: bool = True


class Price(BaseMongoModel):
    """Price model for a medicine at a specific pharmacy."""
    medicine_id: PyObjectId
    pharmacy: PharmacyEnum
    
    # Current price info
    current_price: float
    original_price: Optional[float] = None  # If on sale
    discount_percentage: Optional[float] = None
    in_stock: bool = True
    
    # Product details from pharmacy
    product_url: str
    product_image_url: Optional[str] = None
    sku: Optional[str] = None
    
    # Stock and availability
    stock_quantity: Optional[int] = None
    available_for_delivery: bool = True
    available_for_pickup: bool = True
    
    # Price history
    price_history: List[PriceHistory] = Field(default_factory=list)
    
    # Metadata
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    check_count: int = 0
    
    @field_validator("current_price", "original_price")
    @classmethod
    def validate_price(cls, v: Optional[float]) -> Optional[float]:
        """Validate price is positive."""
        if v is not None and v < 0:
            raise ValueError("Price must be positive")
        return v
    
    def calculate_discount(self) -> Optional[float]:
        """Calculate discount percentage."""
        if self.original_price and self.original_price > self.current_price:
            return round(((self.original_price - self.current_price) / self.original_price) * 100, 2)
        return None
    
    def add_to_history(self) -> None:
        """Add current price to history."""
        history_entry = PriceHistory(
            price=self.current_price,
            in_stock=self.in_stock
        )
        self.price_history.append(history_entry)
        
        # Keep only last 30 days of history
        if len(self.price_history) > 720:  # ~24 checks per day * 30 days
            self.price_history = self.price_history[-720:]


# ============================================
# SEARCH MODEL
# ============================================
class SearchResult(BaseModel):
    """Individual search result."""
    medicine_id: PyObjectId
    medicine_name: str
    pharmacy: PharmacyEnum
    price: float
    in_stock: bool
    product_url: str


class Search(BaseMongoModel):
    """User search model."""
    user_id: int  # Telegram user ID
    username: Optional[str] = None
    
    # Search details
    query: str
    normalized_query: str
    results_count: int = 0
    results: List[SearchResult] = Field(default_factory=list)
    
    # AI processing
    ai_processed: bool = False
    ai_suggestions: List[str] = Field(default_factory=list)
    
    # Performance
    search_duration_ms: Optional[int] = None
    cache_hit: bool = False
    
    # User interaction
    clicked_results: List[str] = Field(default_factory=list)
    
    @field_validator("normalized_query", mode="before")
    @classmethod
    def normalize_query(cls, v: str) -> str:
        """Normalize search query."""
        return v.lower().strip()


# ============================================
# ANALYTICS MODEL
# ============================================
class DailyStats(BaseModel):
    """Daily statistics."""
    date: datetime
    total_searches: int = 0
    unique_users: int = 0
    total_results: int = 0
    avg_search_duration_ms: float = 0.0
    cache_hit_rate: float = 0.0


class PharmacyStats(BaseModel):
    """Statistics per pharmacy."""
    pharmacy: PharmacyEnum
    total_products: int = 0
    avg_price: float = 0.0
    total_searches: int = 0
    scrape_errors: int = 0


class Analytics(BaseMongoModel):
    """Analytics and metrics model."""
    
    # Time period
    period_start: datetime
    period_end: datetime
    period_type: str = "daily"  # daily, weekly, monthly
    
    # Overall stats
    total_searches: int = 0
    unique_users: int = 0
    total_users: int = 0
    new_users: int = 0
    
    # Search stats
    top_searches: List[dict] = Field(default_factory=list)  # [{"query": str, "count": int}]
    avg_results_per_search: float = 0.0
    avg_search_duration_ms: float = 0.0
    
    # Cache stats
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    
    # Pharmacy stats
    pharmacy_stats: List[PharmacyStats] = Field(default_factory=list)
    
    # AI stats
    ai_requests: int = 0
    ai_errors: int = 0
    ai_avg_response_time_ms: float = 0.0
    
    # Error tracking
    total_errors: int = 0
    error_types: dict = Field(default_factory=dict)
    
    # Daily breakdown
    daily_stats: List[DailyStats] = Field(default_factory=list)


# ============================================
# USER MODEL
# ============================================
class UserPreferences(BaseModel):
    """User preferences."""
    favorite_pharmacies: List[PharmacyEnum] = Field(default_factory=list)
    notification_enabled: bool = True
    preferred_language: str = "es"


class User(BaseMongoModel):
    """User model."""
    telegram_id: int = Field(..., unique=True)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Activity
    is_active: bool = True
    is_blocked: bool = False
    last_interaction: datetime = Field(default_factory=datetime.utcnow)
    
    # Stats
    total_searches: int = 0
    total_clicks: int = 0
    
    # Preferences
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    # Rate limiting
    searches_today: int = 0
    last_search_date: Optional[datetime] = None


# ============================================
# CACHE MODEL (for MongoDB fallback)
# ============================================
class CacheEntry(BaseMongoModel):
    """Cache entry model (fallback if Redis unavailable)."""
    key: str = Field(..., unique=True)
    value: dict
    ttl: int  # seconds
    expires_at: datetime
    
    @classmethod
    def create(cls, key: str, value: dict, ttl: int):
        """Create a cache entry with expiration."""
        expires_at = datetime.utcnow()
        from datetime import timedelta
        expires_at += timedelta(seconds=ttl)
        
        return cls(
            key=key,
            value=value,
            ttl=ttl,
            expires_at=expires_at
        )
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at


# Export all models
__all__ = [
    "PyObjectId",
    "PharmacyEnum",
    "BaseMongoModel",
    "Pharmacy",
    "PharmacyLocation",
    "Medicine",
    "Price",
    "PriceHistory",
    "Search",
    "SearchResult",
    "Analytics",
    "DailyStats",
    "PharmacyStats",
    "User",
    "UserPreferences",
    "CacheEntry",
]

# Made with Bob