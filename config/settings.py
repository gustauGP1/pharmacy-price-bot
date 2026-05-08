"""
Settings and configuration management for Pharmacy Price Bot.
Uses pydantic-settings for environment variable management.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================
    # TELEGRAM CONFIGURATION
    # ============================================
    telegram_bot_token: str = Field(
        ...,
        description="Telegram Bot API token from @BotFather",
    )
    telegram_webhook_url: Optional[str] = Field(
        default=None,
        description="Webhook URL for production deployment",
    )

    # ============================================
    # MONGODB CONFIGURATION
    # ============================================
    mongodb_uri: str = Field(
        ...,
        description="MongoDB Atlas connection URI",
    )
    mongodb_db_name: str = Field(
        default="pharmacy_bot",
        description="MongoDB database name",
    )

    # ============================================
    # REDIS CONFIGURATION
    # ============================================
    redis_url: str = Field(
        ...,
        description="Redis/Upstash connection URL",
    )
    cache_ttl: int = Field(
        default=21600,  # 6 hours
        description="Cache TTL in seconds",
    )

    # ============================================
    # GROQ AI CONFIGURATION
    # ============================================
    groq_api_key: str = Field(
        ...,
        description="Groq AI API key",
    )
    groq_model: str = Field(
        default="llama3-70b-8192",
        description="Groq model to use",
    )

    # ============================================
    # GOOGLE CLOUD CONFIGURATION
    # ============================================
    google_cloud_project: Optional[str] = Field(
        default=None,
        description="Google Cloud Project ID",
    )
    google_application_credentials: Optional[str] = Field(
        default=None,
        description="Path to Google Cloud credentials JSON",
    )

    # ============================================
    # APPLICATION CONFIGURATION
    # ============================================
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    port: int = Field(
        default=8080,
        description="Port for web server",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    # ============================================
    # RATE LIMITING
    # ============================================
    rate_limit_per_minute: int = Field(
        default=10,
        description="Max requests per user per minute",
    )
    rate_limit_per_day: int = Field(
        default=100,
        description="Max searches per user per day",
    )

    # ============================================
    # SCRAPER CONFIGURATION
    # ============================================
    scraper_delay: int = Field(
        default=2,
        description="Delay between scraper requests in seconds",
    )
    scraper_timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
    )
    scraper_max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests",
    )
    scraper_user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        description="User-Agent for scraper requests",
    )

    # ============================================
    # MONITORING & ANALYTICS
    # ============================================
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error monitoring",
    )
    enable_analytics: bool = Field(
        default=True,
        description="Enable analytics tracking",
    )

    # ============================================
    # FEATURE FLAGS
    # ============================================
    enable_cache: bool = Field(
        default=True,
        description="Enable Redis caching",
    )
    enable_ai: bool = Field(
        default=True,
        description="Enable AI features (Groq)",
    )

    # ============================================
    # PHARMACY URLS
    # ============================================
    cruz_verde_url: str = Field(
        default="https://www.cruzverde.cl",
        description="Cruz Verde pharmacy URL",
    )
    salcobrand_url: str = Field(
        default="https://www.salcobrand.cl",
        description="Salcobrand pharmacy URL",
    )
    farmacias_ahumada_url: str = Field(
        default="https://www.farmaciasahumada.cl",
        description="Farmacias Ahumada URL",
    )

    # ============================================
    # VALIDATORS
    # ============================================
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()

    @field_validator("groq_model")
    @classmethod
    def validate_groq_model(cls, v: str) -> str:
        """Validate Groq model name."""
        allowed = [
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
            "gemma-7b-it",
        ]
        if v not in allowed:
            raise ValueError(f"Groq model must be one of {allowed}")
        return v

    # ============================================
    # COMPUTED PROPERTIES
    # ============================================
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def use_webhooks(self) -> bool:
        """Check if webhooks should be used."""
        return self.is_production and self.telegram_webhook_url is not None

    @property
    def cache_enabled(self) -> bool:
        """Check if cache is enabled."""
        return self.enable_cache and self.redis_url is not None

    @property
    def ai_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return self.enable_ai and self.groq_api_key is not None

    # ============================================
    # HELPER METHODS
    # ============================================
    def get_pharmacy_urls(self) -> dict[str, str]:
        """Get all pharmacy URLs as a dictionary."""
        return {
            "cruz_verde": self.cruz_verde_url,
            "salcobrand": self.salcobrand_url,
            "farmacias_ahumada": self.farmacias_ahumada_url,
        }

    def get_scraper_config(self) -> dict:
        """Get scraper configuration as a dictionary."""
        return {
            "delay": self.scraper_delay,
            "timeout": self.scraper_timeout,
            "max_retries": self.scraper_max_retries,
            "user_agent": self.scraper_user_agent,
        }

    def get_rate_limits(self) -> dict:
        """Get rate limit configuration."""
        return {
            "per_minute": self.rate_limit_per_minute,
            "per_day": self.rate_limit_per_day,
        }

    def __repr__(self) -> str:
        """String representation (hiding sensitive data)."""
        return (
            f"Settings(environment={self.environment}, "
            f"debug={self.debug}, "
            f"cache_enabled={self.cache_enabled}, "
            f"ai_enabled={self.ai_enabled})"
        )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Convenience function to get settings
settings = get_settings()


# Export for easy access
__all__ = ["Settings", "get_settings", "settings"]

# Made with Bob
