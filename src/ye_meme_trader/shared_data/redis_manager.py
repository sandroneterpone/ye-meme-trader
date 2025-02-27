"""
Redis data manager for sharing data between components.
"""
import json
import logging
from typing import Dict, Any, Optional

import redis.asyncio as redis

from config.settings import REDIS_CONFIG

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis manager for sharing data between components."""

    def __init__(self):
        """Initialize Redis connection."""
        self.redis = redis.Redis(
            host=REDIS_CONFIG["host"],
            port=REDIS_CONFIG["port"],
            db=REDIS_CONFIG["db"],
            decode_responses=True
        )

    async def set_trading_status(self, status: Dict[str, Any]) -> None:
        """Set trading status in Redis."""
        await self.redis.set("trading_status", json.dumps(status))

    async def get_trading_status(self) -> Optional[Dict[str, Any]]:
        """Get trading status from Redis."""
        status = await self.redis.get("trading_status")
        return json.loads(status) if status else None

    async def add_pending_trade(self, trade_id: str, trade_data: Dict[str, Any]) -> None:
        """Add a pending trade to Redis."""
        await self.redis.hset("pending_trades", trade_id, json.dumps(trade_data))

    async def get_pending_trades(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending trades from Redis."""
        trades = await self.redis.hgetall("pending_trades")
        return {k: json.loads(v) for k, v in trades.items()}

    async def remove_pending_trade(self, trade_id: str) -> None:
        """Remove a pending trade from Redis."""
        await self.redis.hdel("pending_trades", trade_id)

    async def add_active_trade(self, trade_id: str, trade_data: Dict[str, Any]) -> None:
        """Add an active trade to Redis."""
        await self.redis.hset("active_trades", trade_id, json.dumps(trade_data))

    async def get_active_trades(self) -> Dict[str, Dict[str, Any]]:
        """Get all active trades from Redis."""
        trades = await self.redis.hgetall("active_trades")
        return {k: json.loads(v) for k, v in trades.items()}

    async def remove_active_trade(self, trade_id: str) -> None:
        """Remove an active trade from Redis."""
        await self.redis.hdel("active_trades", trade_id)

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.close()
