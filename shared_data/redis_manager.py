"""
Redis manager for shared data between trading bot and Telegram bot.
"""
import json
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

import redis.asyncio as redis
from config.settings import REDIS_CONFIG

logger = logging.getLogger(__name__)

class RedisManager:
    """Manager for Redis operations and data sharing."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis = redis.Redis(
            host=REDIS_CONFIG["host"],
            port=REDIS_CONFIG["port"],
            db=REDIS_CONFIG["db"],
            decode_responses=True
        )
        
    async def close(self):
        """Close Redis connection."""
        await self.redis.close()
        
    async def set_trade_signal(self, trade_data: Dict[str, Any]):
        """Store trade signal in Redis."""
        try:
            key = f"trade_signal:{trade_data['id']}"
            await self.redis.set(key, json.dumps(trade_data))
            # Set expiry to 1 hour to prevent stale signals
            await self.redis.expire(key, 3600)
        except Exception as e:
            logger.error(f"Error setting trade signal: {str(e)}")
            
    async def get_trade_signal(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """Get trade signal from Redis."""
        try:
            data = await self.redis.get(f"trade_signal:{trade_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting trade signal: {str(e)}")
            return None
            
    async def set_token_info(self, token_address: str, token_data: Dict[str, Any]):
        """Store token information in Redis."""
        try:
            key = f"token:{token_address}"
            await self.redis.set(key, json.dumps(token_data))
        except Exception as e:
            logger.error(f"Error setting token info: {str(e)}")
            
    async def get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get token information from Redis."""
        try:
            data = await self.redis.get(f"token:{token_address}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting token info: {str(e)}")
            return None
            
    async def set_trading_status(self, status_data: Dict[str, Any]):
        """Update trading bot status in Redis."""
        try:
            await self.redis.set("trading_status", json.dumps(status_data))
        except Exception as e:
            logger.error(f"Error setting trading status: {str(e)}")
            
    async def get_trading_status(self) -> Dict[str, Any]:
        """Get trading bot status from Redis."""
        try:
            data = await self.redis.get("trading_status")
            return json.loads(data) if data else {}
        except Exception as e:
            logger.error(f"Error getting trading status: {str(e)}")
            return {}
            
    async def get_active_trades(self) -> List[Dict[str, Any]]:
        """Get all active trades from Redis."""
        try:
            trade_keys = await self.redis.keys("trade:active:*")
            trades = []
            
            for key in trade_keys:
                data = await self.redis.get(key)
                if data:
                    trades.append(json.loads(data))
                    
            return trades
        except Exception as e:
            logger.error(f"Error getting active trades: {str(e)}")
            return []
            
    async def set_trade_action(self, trade_id: str, action: str):
        """Set trade action (e.g., cancel) in Redis."""
        try:
            key = f"trade_action:{trade_id}"
            await self.redis.set(key, action)
            # Set expiry to 5 minutes
            await self.redis.expire(key, 300)
        except Exception as e:
            logger.error(f"Error setting trade action: {str(e)}")
            
    async def get_trade_action(self, trade_id: str) -> Optional[str]:
        """Get pending trade action from Redis."""
        try:
            return await self.redis.get(f"trade_action:{trade_id}")
        except Exception as e:
            logger.error(f"Error getting trade action: {str(e)}")
            return None
            
    async def set_balance_info(self, balance_data: Dict[str, Any]):
        """Update wallet balance information in Redis."""
        try:
            await self.redis.set("balance_info", json.dumps(balance_data))
        except Exception as e:
            logger.error(f"Error setting balance info: {str(e)}")
            
    async def get_balance_info(self) -> Dict[str, Any]:
        """Get wallet balance information from Redis."""
        try:
            data = await self.redis.get("balance_info")
            return json.loads(data) if data else {}
        except Exception as e:
            logger.error(f"Error getting balance info: {str(e)}")
            return {}
            
    async def set_trading_settings(self, settings: Dict[str, Any]):
        """Update trading settings in Redis."""
        try:
            await self.redis.set("trading_settings", json.dumps(settings))
        except Exception as e:
            logger.error(f"Error setting trading settings: {str(e)}")
            
    async def get_trading_settings(self) -> Dict[str, Any]:
        """Get trading settings from Redis."""
        try:
            data = await self.redis.get("trading_settings")
            return json.loads(data) if data else {}
        except Exception as e:
            logger.error(f"Error getting trading settings: {str(e)}")
            return {}
