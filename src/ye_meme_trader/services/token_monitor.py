"""
Token monitoring and analysis service with Ye-specific criteria.
"""
import asyncio
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple

import aiohttp
import redis.asyncio as redis

from ..core.solana import SolanaService
from ..models.token import Token, TokenMetrics
from ..models.trade import Trade, TradeType, TradeStatus
from config.settings import REDIS_CONFIG, TOKEN_FILTERS, TRADING_CONFIG

logger = logging.getLogger(__name__)

# Ye-specific token criteria
YE_KEYWORDS = [
    "ye", "kanye", "west", "yeezy", "pablo", "donda", 
    "graduation", "808s", "yeezus", "dropout"
]

YE_EXCLUDED_WORDS = [
    "scam", "rug", "fake", "test", "honeypot"
]

class TokenMonitorService:
    """Service for monitoring and analyzing Ye-related tokens."""
    
    def __init__(self):
        """Initialize the token monitor service."""
        self.redis = redis.Redis(
            host=REDIS_CONFIG["host"],
            port=REDIS_CONFIG["port"],
            db=REDIS_CONFIG["db"],
            decode_responses=True
        )
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        await self.redis.close()

    def calculate_ye_relevance_score(self, name: str, symbol: str) -> float:
        """Calculate how relevant a token is to Ye/Kanye West."""
        name_lower = name.lower()
        symbol_lower = symbol.lower()
        score = 0.0
        
        # Check for exact matches in name
        for keyword in YE_KEYWORDS:
            if keyword in name_lower:
                score += 1.0
            # Bonus for exact word matches
            if re.search(rf'\b{keyword}\b', name_lower):
                score += 0.5
                
        # Check symbol
        for keyword in YE_KEYWORDS:
            if keyword in symbol_lower:
                score += 0.5
                
        # Penalize for excluded words
        for word in YE_EXCLUDED_WORDS:
            if word in name_lower or word in symbol_lower:
                score -= 2.0
                
        # Normalize score between 0 and 1
        return max(0.0, min(1.0, score / 3.0))

    def _is_token_name_valid(self, name: str, symbol: str) -> Tuple[bool, float]:
        """Check if token name matches our Ye-specific criteria."""
        # Calculate Ye relevance score
        ye_score = self.calculate_ye_relevance_score(name, symbol)
        
        # Must have minimum Ye relevance
        if ye_score < TRADING_CONFIG["min_ye_relevance_score"]:
            return False, ye_score
            
        # Check length
        if not TOKEN_FILTERS["min_name_length"] <= len(name) <= TOKEN_FILTERS["max_name_length"]:
            return False, ye_score
            
        # Check for excluded patterns
        name_lower = name.lower()
        if any(word in name_lower for word in YE_EXCLUDED_WORDS):
            return False, ye_score
            
        return True, ye_score

    async def analyze_token_social_metrics(self, token: Token) -> Dict[str, Any]:
        """Analyze token's social metrics and community engagement."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Here you would implement social analysis:
            # - Twitter mentions/sentiment
            # - Telegram group activity
            # - Discord presence
            # For now returning placeholder data
            return {
                "twitter_mentions_24h": 0,
                "telegram_members": 0,
                "sentiment_score": 0.0
            }
        except Exception as e:
            logger.error(f"Error analyzing social metrics: {str(e)}")
            return {}

    async def analyze_token(self, token: Token) -> Optional[TokenMetrics]:
        """Analyze token metrics with Ye-specific focus."""
        try:
            async with SolanaService() as solana:
                # Get current price
                current_price = await solana.get_token_price(token.address)
                if not current_price:
                    return None

                # Get token account data
                account_data = await solana.get_token_account(token.address)
                
                # Calculate metrics
                creation_time = int(account_data["data"]["parsed"]["info"]["mintAuthority"]["initialized"])
                age_minutes = int((datetime.now(timezone.utc).timestamp() - creation_time) / 60)
                
                # Get initial price (from cache or calculate)
                initial_price_key = f"token:{token.address}:initial_price"
                initial_price = await self.redis.get(initial_price_key)
                if not initial_price:
                    initial_price = current_price
                    await self.redis.set(initial_price_key, str(initial_price))
                else:
                    initial_price = Decimal(initial_price)

                # Calculate price change
                price_change_pct = ((current_price - initial_price) / initial_price) * 100
                
                # Get social metrics
                social_metrics = await self.analyze_token_social_metrics(token)

                # Store Ye relevance score
                _, ye_score = self._is_token_name_valid(token.name, token.symbol)
                await self.redis.set(
                    f"token:{token.address}:ye_score",
                    str(ye_score)
                )

                return TokenMetrics(
                    creation_time=creation_time,
                    age_minutes=age_minutes,
                    initial_price=initial_price,
                    current_price=current_price,
                    price_change_pct=price_change_pct,
                    volume_24h=Decimal("0"),  # Would need to implement volume tracking
                    liquidity_sol=Decimal("0"),  # Would need to implement liquidity tracking
                    holders_count=0,  # Would need to implement holder tracking
                    transactions_count=0,  # Would need to implement transaction tracking
                    social_metrics=social_metrics,
                    ye_relevance_score=ye_score
                )
        except Exception as e:
            logger.error(f"Error analyzing token {token.address}: {str(e)}")
            return None

    def calculate_trade_confidence(self, token: Token) -> float:
        """Calculate confidence score for trading a token."""
        if not token.metrics:
            return 0.0
            
        score = 0.0
        
        # Ye relevance (highest weight)
        ye_score = float(token.metrics.ye_relevance_score)
        score += ye_score * 0.4
        
        # Price momentum
        if token.metrics.price_change_pct > 0:
            momentum_score = min(1.0, token.metrics.price_change_pct / 100.0)
            score += momentum_score * 0.2
            
        # Liquidity (normalized)
        liquidity_score = min(1.0, float(token.metrics.liquidity_sol) / TRADING_CONFIG["target_liquidity_sol"])
        score += liquidity_score * 0.2
        
        # Age factor (prefer newer tokens but not too new)
        age_hours = token.metrics.age_minutes / 60
        if 1 <= age_hours <= 24:
            age_score = 1.0 - (age_hours - 1) / 23  # 1 hour = 1.0, 24 hours = 0.0
            score += age_score * 0.1
            
        # Social engagement
        if token.metrics.social_metrics:
            social_score = min(1.0, token.metrics.social_metrics["sentiment_score"])
            score += social_score * 0.1
            
        return score

    def should_trade(self, token: Token) -> Tuple[bool, float]:
        """Determine if we should trade this token based on Ye-specific metrics."""
        if not token.metrics:
            return False, 0.0
            
        # Check token name
        is_valid, ye_score = self._is_token_name_valid(token.name, token.symbol)
        if not is_valid:
            return False, ye_score
            
        # Calculate trade confidence
        confidence = self.calculate_trade_confidence(token)
        
        # Must meet minimum confidence threshold
        if confidence < TRADING_CONFIG["min_trade_confidence"]:
            return False, confidence
            
        # Basic safety checks
        if (token.metrics.age_minutes < TRADING_CONFIG["min_age_minutes"] or
            token.metrics.liquidity_sol < TRADING_CONFIG["min_liquidity_sol"] or
            token.metrics.price_change_pct < TRADING_CONFIG["min_price_increase_pct"]):
            return False, confidence
            
        return True, confidence

    async def monitor_tokens(self):
        """Main token monitoring loop with Ye-specific focus."""
        while True:
            try:
                # Get new tokens
                new_tokens = await self.get_new_tokens()
                
                for token in new_tokens:
                    # Skip if already processed
                    processed_key = f"processed_token:{token.address}"
                    if await self.redis.exists(processed_key):
                        continue
                        
                    # Analyze token
                    metrics = await self.analyze_token(token)
                    if not metrics:
                        continue
                        
                    token.metrics = metrics
                    
                    # Check if we should trade
                    should_trade, confidence = self.should_trade(token)
                    if should_trade:
                        # Calculate trade amount based on confidence
                        base_amount = TRADING_CONFIG["base_trade_amount_sol"]
                        trade_amount = base_amount * confidence
                        
                        # Create trade signal
                        trade = Trade(
                            id=f"trade_{token.address}_{int(datetime.now().timestamp())}",
                            token_address=token.address,
                            type=TradeType.BUY,
                            amount_sol=Decimal(str(trade_amount)),
                            timestamp=datetime.now(timezone.utc),
                            status=TradeStatus.PENDING,
                            confidence_score=confidence
                        )
                        
                        # Store trade signal in Redis
                        await self.redis.set(
                            f"trade_signal:{trade.id}",
                            trade.to_dict()
                        )
                        
                        logger.info(f"Created trade signal for token {token.address} with confidence {confidence:.2f}")
                    
                    # Mark token as processed
                    await self.redis.set(processed_key, "1")
                
                # Sleep before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in token monitoring loop: {str(e)}")
                await asyncio.sleep(5)  # Sleep longer on error

    async def get_new_tokens(self) -> List[Token]:
        """Get list of newly created tokens."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Here you would implement the logic to fetch new tokens
            # This could be from a token listing API, DEX, or blockchain explorer
            # For now, we'll return an empty list as placeholder
            return []
        except Exception as e:
            logger.error(f"Error getting new tokens: {str(e)}")
            return []
