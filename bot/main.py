"""
Main entry point for the Telegram bot.
Initializes and runs the bot with all handlers and middleware.
"""

import asyncio
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot.handlers import (
    start_command,
    search_command,
    help_command,
    about_command,
    message_handler,
    button_callback,
)
from bot.middleware import BotMiddleware, error_handler
from database.mongodb_client import get_mongodb_client, close_mongodb_client
from services.cache_service import get_cache_service, close_cache_service
from services.comparison_service import get_comparison_service
from services.analytics_service import get_analytics_service
from config.settings import get_settings
from utils.logger import logger


async def setup_bot_commands(application: Application) -> None:
    """
    Set up bot commands menu.
    
    Args:
        application: Bot application
    """
    commands = [
        BotCommand("start", "Iniciar el bot"),
        BotCommand("buscar", "Buscar medicamento"),
        BotCommand("ayuda", "Mostrar ayuda"),
        BotCommand("acerca", "Información del bot"),
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("✅ Bot commands configured")


async def initialize_services(application: Application) -> None:
    """
    Initialize all services.
    
    Args:
        application: Bot application
    """
    try:
        logger.info("🔧 Initializing services...")
        
        # Initialize MongoDB
        await get_mongodb_client()
        
        # Initialize cache service
        await get_cache_service()
        
        # Initialize comparison service
        await get_comparison_service()
        
        # Initialize analytics service
        await get_analytics_service()
        
        # Initialize middleware
        middleware = BotMiddleware()
        await middleware.initialize()
        
        # Store middleware in bot_data for access in handlers
        application.bot_data["middleware"] = middleware
        
        logger.info("✅ All services initialized")
        
    except Exception as e:
        logger.exception(f"❌ Failed to initialize services: {e}")
        raise


async def shutdown_services(application: Application) -> None:
    """
    Shutdown all services gracefully.
    
    Args:
        application: Bot application
    """
    try:
        logger.info("🛑 Shutting down services...")
        
        # Close MongoDB connection
        await close_mongodb_client()
        
        # Close cache service
        await close_cache_service()
        
        logger.info("✅ All services shut down")
        
    except Exception as e:
        logger.error(f"Error shutting down services: {e}")


def create_application() -> Application:
    """
    Create and configure the bot application.
    
    Returns:
        Application: Configured bot application
    """
    settings = get_settings()
    
    # Create application
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("buscar", search_command))
    application.add_handler(CommandHandler("ayuda", help_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("acerca", about_command))
    application.add_handler(CommandHandler("about", about_command))
    
    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler for text messages (treat as search)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Add startup and shutdown hooks
    application.post_init = setup_bot_commands
    application.post_init = initialize_services
    application.post_shutdown = shutdown_services
    
    logger.info("✅ Bot application created")
    
    return application


async def run_polling(application: Application) -> None:
    """
    Run bot in polling mode (for development).
    
    Args:
        application: Bot application
    """
    logger.info("🤖 Starting bot in polling mode...")
    logger.info("Press Ctrl+C to stop")
    
    # Initialize application
    await application.initialize()
    await application.start()
    
    # Start polling
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
    
    # Keep running until interrupted
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Stopping bot...")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


async def run_webhook(application: Application) -> None:
    """
    Run bot in webhook mode (for production).
    
    Args:
        application: Bot application
    """
    settings = get_settings()
    
    if not settings.telegram_webhook_url:
        raise ValueError("TELEGRAM_WEBHOOK_URL not configured")
    
    logger.info("🤖 Starting bot in webhook mode...")
    logger.info(f"Webhook URL: {settings.telegram_webhook_url}")
    
    # Initialize application
    await application.initialize()
    await application.start()
    
    # Set webhook
    await application.bot.set_webhook(
        url=settings.telegram_webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
    
    # Start webhook server
    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=settings.port,
        url_path="webhook",
        webhook_url=settings.telegram_webhook_url,
    )
    
    logger.info(f"✅ Webhook server started on port {settings.port}")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Stopping bot...")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


async def run_bot() -> None:
    """Main function to run the bot."""
    settings = get_settings()
    
    try:
        # Create application
        application = create_application()
        
        # Run in appropriate mode
        if settings.use_webhooks:
            await run_webhook(application)
        else:
            await run_polling(application)
            
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        raise


def main() -> None:
    """Entry point for running the bot."""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()

# Made with Bob