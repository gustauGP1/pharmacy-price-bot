"""
Middleware for Telegram bot.
Handles rate limiting, logging, and user tracking.
"""

from typing import Callable, Any
from functools import wraps
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from services.cache_service import get_cache_service
from services.analytics_service import get_analytics_service
from database.repositories import UserRepository
from config.settings import get_settings
from utils.logger import logger


class BotMiddleware:
    """Middleware for bot request processing."""
    
    def __init__(self):
        """Initialize middleware."""
        self.settings = get_settings()
        self.user_repo = UserRepository()
        self.cache_service = None
        self.analytics_service = None
    
    async def initialize(self) -> None:
        """Initialize services."""
        self.cache_service = await get_cache_service()
        self.analytics_service = await get_analytics_service()
        logger.info("✅ Bot middleware initialized")
    
    async def log_request(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Log incoming request.
        
        Args:
            update: Telegram update
            context: Bot context
        """
        try:
            user = update.effective_user
            chat = update.effective_chat
            message = update.effective_message
            
            log_data = {
                "user_id": user.id if user else None,
                "username": user.username if user else None,
                "chat_id": chat.id if chat else None,
                "chat_type": chat.type if chat else None,
            }
            
            if message and message.text:
                log_data["message"] = message.text[:100]  # Truncate long messages
            
            if update.callback_query:
                log_data["callback_data"] = update.callback_query.data
            
            logger.info(f"📨 Request: {log_data}")
            
        except Exception as e:
            logger.warning(f"Failed to log request: {e}")
    
    async def check_rate_limit(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Check if user has exceeded rate limit.
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            bool: True if within limit, False if exceeded
        """
        try:
            user = update.effective_user
            if not user:
                return True
            
            if not self.cache_service:
                return True
            
            # Check rate limit
            within_limit = await self.cache_service.check_rate_limit(
                user.id,
                self.settings.rate_limit_per_minute,
                window=60
            )
            
            if not within_limit:
                logger.warning(f"⚠️ Rate limit exceeded for user {user.id}")
                
                # Send warning message
                if update.effective_message:
                    await update.effective_message.reply_text(
                        "⚠️ Has excedido el límite de peticiones. "
                        "Por favor espera un momento antes de intentar nuevamente."
                    )
                
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error
    
    async def track_user(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Track user activity.
        
        Args:
            update: Telegram update
            context: Bot context
        """
        try:
            user = update.effective_user
            if not user:
                return
            
            # Get or create user
            await self.user_repo.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            
        except Exception as e:
            logger.warning(f"Failed to track user: {e}")
    
    async def handle_error(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        error: Exception
    ) -> None:
        """
        Handle errors in bot handlers.
        
        Args:
            update: Telegram update
            context: Bot context
            error: Exception that occurred
        """
        try:
            logger.exception(f"❌ Error handling update: {error}")
            
            # Send error message to user
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ Ocurrió un error al procesar tu solicitud. "
                    "Por favor intenta nuevamente más tarde."
                )
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}")


def rate_limit(func: Callable) -> Callable:
    """
    Decorator for rate limiting handlers.
    
    Args:
        func: Handler function
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    async def wrapper(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *args,
        **kwargs
    ) -> Any:
        # Get middleware from context
        middleware = context.bot_data.get("middleware")
        
        if middleware:
            # Check rate limit
            if not await middleware.check_rate_limit(update, context):
                return
        
        # Call original function
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def log_handler(func: Callable) -> Callable:
    """
    Decorator for logging handler calls.
    
    Args:
        func: Handler function
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    async def wrapper(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *args,
        **kwargs
    ) -> Any:
        # Get middleware from context
        middleware = context.bot_data.get("middleware")
        
        if middleware:
            # Log request
            await middleware.log_request(update, context)
            
            # Track user
            await middleware.track_user(update, context)
        
        # Call original function
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def track_analytics(action: str):
    """
    Decorator for tracking analytics.
    
    Args:
        action: Action name
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            *args,
            **kwargs
        ) -> Any:
            # Get middleware from context
            middleware = context.bot_data.get("middleware")
            
            if middleware and middleware.analytics_service:
                user = update.effective_user
                if user:
                    await middleware.analytics_service.track_user_action(
                        user.id,
                        action
                    )
            
            # Call original function
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    
    return decorator


def admin_only(func: Callable) -> Callable:
    """
    Decorator to restrict handler to admin users only.
    
    Args:
        func: Handler function
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    async def wrapper(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *args,
        **kwargs
    ) -> Any:
        user = update.effective_user
        
        # Check if user is admin (you can customize this)
        # For now, we'll use a simple check
        settings = get_settings()
        admin_ids = []  # Add admin user IDs here
        
        if user and user.id not in admin_ids:
            if update.effective_message:
                await update.effective_message.reply_text(
                    "⛔ Este comando solo está disponible para administradores."
                )
            return
        
        # Call original function
        return await func(update, context, *args, **kwargs)
    
    return wrapper


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Global error handler for the bot.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    try:
        logger.exception(f"❌ Exception while handling update: {context.error}")
        
        # Get middleware from context
        middleware = context.bot_data.get("middleware")
        
        if middleware and isinstance(update, Update):
            await middleware.handle_error(update, context, context.error)
        
    except Exception as e:
        logger.error(f"Error in global error handler: {e}")


__all__ = [
    "BotMiddleware",
    "rate_limit",
    "log_handler",
    "track_analytics",
    "admin_only",
    "error_handler",
]

# Made with Bob