"""
Main entry point for running the Pharmacy Price Bot locally.
This script is used for development and testing.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import logger


def main():
    """Main entry point."""
    try:
        logger.info("=" * 60)
        logger.info("🏥 Pharmacy Price Bot - Starting...")
        logger.info("=" * 60)
        
        # Import here to ensure logging is configured first
        from bot.main import run_bot
        
        # Run the bot
        asyncio.run(run_bot())
        
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped by user")
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
