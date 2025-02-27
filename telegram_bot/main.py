"""
Main entry point for the Telegram bot.
"""
import asyncio
import logging
import sys
from typing import List, Any

from telegram_service import TelegramService
from shared_data.redis_manager import RedisManager
from config.settings import LOGGING_CONFIG

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"],
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("telegram_bot.log")
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to run the Telegram bot."""
    try:
        # Initialize services
        telegram_service = TelegramService()
        
        # Start Telegram bot
        await telegram_service.start()
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        sys.exit(1)
    finally:
        if 'telegram_service' in locals():
            await telegram_service.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down Telegram bot gracefully...")
        sys.exit(0)
