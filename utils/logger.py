"""
Logging configuration using loguru.
Provides structured logging with rotation and formatting.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from config.settings import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    rotation: str = "100 MB",
    retention: str = "10 days",
) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: logs/pharmacy_bot.log)
        rotation: When to rotate log file (default: 100 MB)
        retention: How long to keep old logs (default: 10 days)
    """
    settings = get_settings()
    
    # Remove default handler
    logger.remove()
    
    # Get log level from settings if not provided
    if log_level is None:
        log_level = settings.log_level
    
    # Console handler with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    
    # File handler with rotation
    if log_file is None:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "pharmacy_bot.log"
    
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=log_level,
        rotation=rotation,
        retention=retention,
        compression="zip",
        encoding="utf-8",
    )
    
    # Error file handler
    error_log_file = Path(log_file).parent / "errors.log"
    logger.add(
        error_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation=rotation,
        retention=retention,
        compression="zip",
        encoding="utf-8",
    )
    
    logger.info(f"Logging configured with level: {log_level}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Environment: {settings.environment}")


def get_logger(name: str):
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module/logger
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)


# Initialize logging on module import
setup_logging()


__all__ = ["setup_logging", "get_logger", "logger"]

# Made with Bob
