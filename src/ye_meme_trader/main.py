"""
Main entry point for the trading bot.
"""
import asyncio
import logging
import sys
from typing import List, Any

from ye_meme_trader.services.token_monitor import TokenMonitorService
from ye_meme_trader.services.auto_trader import AutoTrader
from ye_meme_trader.shared_data.redis_manager import RedisManager
from ye_meme_trader.config.settings import LOGGING_CONFIG

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"],
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("trading_bot.log")
    ]
)

logger = logging.getLogger(__name__)

async def update_trading_status(redis: RedisManager, is_active: bool, active_trades: int, total_trades: int):
    """Update trading status in Redis."""
    await redis.set_trading_status({
        "is_active": is_active,
        "active_trades": active_trades,
        "total_trades": total_trades,
        "errors": []
    })

async def main():
    """Main function to run the trading bot."""
    try:
        # Initialize Redis manager
        redis = RedisManager()
        
        # Create services
        token_monitor = TokenMonitorService()
        auto_trader = AutoTrader()
        
        # Update initial status
        await update_trading_status(redis, True, 0, 0)
        
        # Start services
        async with token_monitor, auto_trader:
            # Run services concurrently
            await asyncio.gather(
                token_monitor.monitor_tokens(),
                auto_trader.run()
            )
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        if 'redis' in locals():
            await update_trading_status(redis, False, 0, 0)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down trading bot gracefully...")
        sys.exit(0)
