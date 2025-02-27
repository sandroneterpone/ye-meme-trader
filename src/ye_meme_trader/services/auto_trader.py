"""
Automated trading service for Ye-related tokens.
"""
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional, List
import json

import redis.asyncio as redis
from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey

from ..core.solana import SolanaService
from ..services.api_service import APIService
from ..models.trade import Trade, TradeType, TradeStatus, TradeParams
from ..models.token import Token
from config.settings import (
    REDIS_CONFIG, 
    TRADING_CONFIG,
    SOLANA_CONFIG,
    API_CONFIG,
    JUPITER_CONFIG,
)

logger = logging.getLogger(__name__)

class AutoTrader:
    """Automated trading service for Ye-related tokens."""

    def __init__(self):
        """Initialize the auto trader."""
        self.redis = redis.Redis(
            host=REDIS_CONFIG["host"],
            port=REDIS_CONFIG["port"],
            db=REDIS_CONFIG["db"],
            decode_responses=True
        )
        self.wallet = Keypair.from_base58_string(SOLANA_CONFIG["wallet_key"])
        self.wallet_address = str(self.wallet.pubkey())
        self.active_trades: Dict[str, Trade] = {}
        self.usd_budget = Decimal("20.0")  # Budget in USD
        self.sol_budget = Decimal("0")  # Will be calculated
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.update_sol_budget()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.redis.close()

    async def get_sol_price(self) -> Optional[Decimal]:
        """Get current SOL price in USD."""
        try:
            async with APIService() as api:
                # Get SOL price from Birdeye
                sol_info = await api.get_birdeye_token_info(JUPITER_CONFIG["default_token"])
                if sol_info and "price" in sol_info:
                    return Decimal(str(sol_info["price"]))
            return None
        except Exception as e:
            logger.error(f"Error getting SOL price: {str(e)}")
            return None

    async def update_sol_budget(self):
        """Update SOL budget based on USD budget and current SOL price."""
        try:
            sol_price = await self.get_sol_price()
            if not sol_price or sol_price <= 0:
                logger.error("Invalid SOL price")
                return
                
            self.sol_budget = self.usd_budget / sol_price
            logger.info(f"Updated trading budget: ${self.usd_budget} = {self.sol_budget} SOL")
            
            # Store in Redis for monitoring
            await self.redis.set("trading_budget_sol", str(self.sol_budget))
            await self.redis.set("trading_budget_usd", str(self.usd_budget))
            
        except Exception as e:
            logger.error(f"Error updating SOL budget: {str(e)}")

    async def calculate_trade_amount(self, confidence: float) -> Decimal:
        """Calculate trade amount in SOL based on confidence and available budget."""
        try:
            # Update SOL budget first
            await self.update_sol_budget()
            
            # Calculate base amount (50% of budget for single trade)
            base_amount = self.sol_budget * Decimal("0.5")
            
            # Adjust based on confidence
            trade_amount = base_amount * Decimal(str(confidence))
            
            # Ensure within limits
            trade_amount = min(
                trade_amount,
                TRADING_CONFIG["max_trade_amount_sol"],
                self.sol_budget
            )
            
            return max(trade_amount, TRADING_CONFIG["min_trade_amount_sol"])
            
        except Exception as e:
            logger.error(f"Error calculating trade amount: {str(e)}")
            return TRADING_CONFIG["min_trade_amount_sol"]

    async def get_pending_trades(self) -> List[Trade]:
        """Get list of pending trades from Redis."""
        try:
            # Get all trade signals
            trade_keys = await self.redis.keys("trade_signal:*")
            trades = []
            
            for key in trade_keys:
                trade_data = await self.redis.get(key)
                if trade_data:
                    trade_dict = json.loads(trade_data)
                    if trade_dict["status"] == TradeStatus.PENDING.value:
                        trades.append(Trade.from_dict(trade_dict))
            
            return trades
        except Exception as e:
            logger.error(f"Error getting pending trades: {str(e)}")
            return []

    async def check_trade_conditions(self, trade: Trade) -> bool:
        """Verify trading conditions before execution."""
        try:
            async with APIService() as api:
                # Get current token data
                token_info = await api.get_birdeye_token_info(trade.token_address)
                if not token_info:
                    return False
                
                current_price = Decimal(str(token_info.get("price", 0)))
                if current_price <= 0:
                    return False
                
                # Check liquidity
                dex_pairs = await api.get_dexscreener_pairs(trade.token_address)
                total_liquidity = sum(
                    Decimal(str(pair.get("liquidity", {}).get("usd", 0)))
                    for pair in dex_pairs
                )
                
                if total_liquidity < TRADING_CONFIG["min_liquidity_sol"]:
                    return False
                
                # Get quote to check price impact
                quote = await api.get_jupiter_quote(
                    JUPITER_CONFIG["default_token"],
                    trade.token_address,
                    int(trade.amount_sol * Decimal("1e9"))  # Convert SOL to lamports
                )
                
                if not quote or Decimal(str(quote.get("priceImpactPct", 100))) > TRADING_CONFIG["max_price_impact_pct"]:
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Error checking trade conditions: {str(e)}")
            return False

    async def execute_trade(self, trade: Trade) -> bool:
        """Execute a trade through Jupiter."""
        try:
            # Update SOL budget before trading
            await self.update_sol_budget()
            
            # Check if we have enough budget
            if trade.type == TradeType.BUY and trade.amount_sol > self.sol_budget:
                logger.error(f"Insufficient budget for trade {trade.id}")
                return False
                
            async with SolanaService() as solana:
                # Get quote first
                quote = await solana.get_quote(
                    JUPITER_CONFIG["default_token"],
                    trade.token_address,
                    int(trade.amount_sol * Decimal("1e9"))
                )
                
                if not quote:
                    logger.error(f"Failed to get quote for trade {trade.id}")
                    return False
                
                trade.params = quote
                
                # Execute the swap
                success = await solana.execute_swap(trade)
                if success:
                    # Update trade status in Redis
                    await self.redis.set(
                        f"trade_signal:{trade.id}",
                        json.dumps(trade.to_dict())
                    )
                    
                    # Add to active trades
                    self.active_trades[trade.id] = trade
                    
                    # Update budget after successful trade
                    if trade.type == TradeType.BUY:
                        self.sol_budget -= trade.amount_sol
                    else:
                        self.sol_budget += trade.amount_sol
                    await self.redis.set("trading_budget_sol", str(self.sol_budget))
                    
                    logger.info(f"Successfully executed trade {trade.id}")
                    return True
                else:
                    logger.error(f"Failed to execute trade {trade.id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error executing trade {trade.id}: {str(e)}")
            return False

    async def monitor_position(self, trade: Trade):
        """Monitor an active trade position."""
        try:
            async with APIService() as api:
                initial_price = trade.params.amount_out / trade.params.amount_in
                
                while True:
                    # Get current price
                    token_info = await api.get_birdeye_token_info(trade.token_address)
                    if not token_info:
                        await asyncio.sleep(5)
                        continue
                    
                    current_price = Decimal(str(token_info.get("price", 0)))
                    if current_price <= 0:
                        await asyncio.sleep(5)
                        continue
                    
                    # Calculate price change
                    price_change_pct = ((current_price - initial_price) / initial_price) * 100
                    
                    # Check take profit
                    if price_change_pct >= TRADING_CONFIG["take_profit_pct"]:
                        await self.close_position(trade, "take_profit")
                        break
                    
                    # Check stop loss
                    if price_change_pct <= TRADING_CONFIG["stop_loss_pct"]:
                        await self.close_position(trade, "stop_loss")
                        break
                    
                    # Check trailing stop
                    highest_price = max(initial_price, current_price)
                    trailing_stop_price = highest_price * (1 - TRADING_CONFIG["trailing_stop_pct"] / 100)
                    
                    if current_price < trailing_stop_price:
                        await self.close_position(trade, "trailing_stop")
                        break
                    
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error monitoring position {trade.id}: {str(e)}")

    async def close_position(self, trade: Trade, reason: str):
        """Close a trading position."""
        try:
            # Create sell trade
            sell_trade = Trade(
                id=f"sell_{trade.id}_{int(datetime.now().timestamp())}",
                token_address=trade.token_address,
                type=TradeType.SELL,
                amount_sol=trade.amount_sol,
                timestamp=datetime.now(timezone.utc),
                status=TradeStatus.PENDING
            )
            
            # Execute sell
            if await self.execute_trade(sell_trade):
                logger.info(f"Closed position {trade.id} due to {reason}")
                
                # Remove from active trades
                self.active_trades.pop(trade.id, None)
                
                # Update Redis
                await self.redis.delete(f"trade_signal:{trade.id}")
            else:
                logger.error(f"Failed to close position {trade.id}")
                
        except Exception as e:
            logger.error(f"Error closing position {trade.id}: {str(e)}")

    async def run(self):
        """Main auto-trading loop."""
        logger.info("Starting auto-trader...")
        
        while True:
            try:
                # Get pending trades
                pending_trades = await self.get_pending_trades()
                
                for trade in pending_trades:
                    # Verify trading conditions
                    if not await self.check_trade_conditions(trade):
                        logger.info(f"Trade conditions not met for {trade.id}")
                        continue
                    
                    # Execute trade
                    if await self.execute_trade(trade):
                        # Start position monitoring in background
                        asyncio.create_task(self.monitor_position(trade))
                
                # Sleep before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in auto-trading loop: {str(e)}")
                await asyncio.sleep(5)
