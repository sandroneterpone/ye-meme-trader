"""
API integration service for token discovery and trading.
"""
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
import ssl

import aiohttp
from bs4 import BeautifulSoup

from ..models.token import Token, TokenMetrics
from config.settings import API_CONFIG, JUPITER_CONFIG

logger = logging.getLogger(__name__)

class APIService:
    """Service for integrating various APIs for token discovery and analysis."""
    
    def __init__(self):
        """Initialize the API service."""
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        # Create a custom SSL context that doesn't verify certificates (for development only)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def get_birdeye_token_info(self, token_address: str) -> Dict[str, Any]:
        """Get token information from Birdeye API."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            url = f"{API_CONFIG['birdeye']['base_url']}/defi/token_overview"
            headers = {
                "X-API-KEY": API_CONFIG["birdeye"]["api_key"],
                "x-chain": "solana",
                "accept": "application/json"
            }
            params = {"address": token_address}
            
            logger.debug(f"Making Birdeye API request to {url} with params {params}")
            
            async with self.session.get(url, headers=headers, params=params) as response:
                logger.debug(f"Birdeye API response status: {response.status}")
                logger.debug(f"Birdeye API response headers: {response.headers}")
                
                if response.status != 200:
                    logger.error(f"Birdeye API error: {await response.text()}")
                    return {}
                    
                data = await response.json()
                logger.debug(f"Birdeye API response data: {data}")
                return data.get("data", {})
        except Exception as e:
            logger.error(f"Error fetching Birdeye token info: {str(e)}")
            return {}

    async def get_dexscreener_pairs(self, token_address: str) -> List[Dict[str, Any]]:
        """Get token pairs from DexScreener API."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            url = f"{API_CONFIG['dexscreener']['base_url']}/pairs/solana/{token_address}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"DexScreener API error: {await response.text()}")
                    return []
                    
                data = await response.json()
                return data.get("pairs", [])
        except Exception as e:
            logger.error(f"Error fetching DexScreener pairs: {str(e)}")
            return []

    async def get_solscan_token_holders(self, token_address: str) -> Dict[str, Any]:
        """Get token holder information from Solscan API."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            url = f"{API_CONFIG['solscan']['base_url']}/token/holders"
            headers = {"token": API_CONFIG["solscan"]["api_key"]}
            params = {"tokenAddress": token_address}
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    logger.error(f"Solscan API error: {await response.text()}")
                    return {}
                    
                data = await response.json()
                return data
        except Exception as e:
            logger.error(f"Error fetching Solscan holders: {str(e)}")
            return {}

    async def get_jupiter_quote(self, input_mint: str, output_mint: str, amount: int) -> Dict[str, Any]:
        """Get swap quote from Jupiter API."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            url = f"{JUPITER_CONFIG['base_url']}/quote"
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": JUPITER_CONFIG["slippage_bps"]
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Jupiter API error: {await response.text()}")
                    return {}
                    
                data = await response.json()
                return data
        except Exception as e:
            logger.error(f"Error fetching Jupiter quote: {str(e)}")
            return {}

    async def scan_telegram_groups(self, token_symbol: str) -> Dict[str, Any]:
        """Scan Telegram groups for token mentions."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Here you would implement Telegram API integration
            # For demonstration, returning placeholder data
            return {
                "group_count": 0,
                "member_count": 0,
                "message_count_24h": 0
            }
        except Exception as e:
            logger.error(f"Error scanning Telegram groups: {str(e)}")
            return {}

    async def get_twitter_metrics(self, token_name: str, token_symbol: str) -> Dict[str, Any]:
        """Get Twitter metrics for token."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Here you would implement Twitter API integration
            # For demonstration, returning placeholder data
            return {
                "tweet_count_24h": 0,
                "user_count": 0,
                "sentiment_score": 0.0
            }
        except Exception as e:
            logger.error(f"Error getting Twitter metrics: {str(e)}")
            return {}

    async def get_token_metrics(self, token: Token) -> Optional[TokenMetrics]:
        """Aggregate token metrics from multiple sources."""
        try:
            # Get data from multiple sources concurrently
            birdeye_info, dex_pairs, holder_info = await asyncio.gather(
                self.get_birdeye_token_info(token.address),
                self.get_dexscreener_pairs(token.address),
                self.get_solscan_token_holders(token.address)
            )
            
            # Get social metrics
            social_tasks = [
                self.scan_telegram_groups(token.symbol),
                self.get_twitter_metrics(token.name, token.symbol)
            ]
            telegram_metrics, twitter_metrics = await asyncio.gather(*social_tasks)
            
            # Extract key metrics
            price = Decimal(str(birdeye_info.get("price", 0)))
            volume_24h = Decimal(str(birdeye_info.get("volume24h", 0)))
            
            # Get liquidity from DEX pairs
            liquidity_sol = Decimal("0")
            for pair in dex_pairs:
                if pair.get("liquidity"):
                    liquidity_sol += Decimal(str(pair["liquidity"].get("usd", 0)))
            
            # Calculate holder metrics
            holder_count = len(holder_info.get("data", []))
            
            # Create metrics object
            return TokenMetrics(
                creation_time=int(birdeye_info.get("mintTimestamp", 0)),
                age_minutes=int((datetime.now(timezone.utc).timestamp() - int(birdeye_info.get("mintTimestamp", 0))) / 60),
                initial_price=Decimal(str(birdeye_info.get("mintPrice", price))),
                current_price=price,
                price_change_pct=Decimal(str(birdeye_info.get("priceChange24h", 0))),
                volume_24h=volume_24h,
                liquidity_sol=liquidity_sol,
                holders_count=holder_count,
                transactions_count=int(birdeye_info.get("txns24h", 0)),
                social_metrics={
                    "telegram": telegram_metrics,
                    "twitter": twitter_metrics
                }
            )
        except Exception as e:
            logger.error(f"Error aggregating token metrics: {str(e)}")
            return None

    async def get_new_tokens(self) -> List[Token]:
        """Discover new tokens from multiple sources."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Get new tokens from Birdeye
            url = f"{API_CONFIG['birdeye']['base_url']}/token/list"
            headers = {"X-API-KEY": API_CONFIG["birdeye"]["api_key"]}
            params = {"offset": 0, "limit": 100, "sortBy": "created"}
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    logger.error(f"Birdeye API error: {await response.text()}")
                    return []
                    
                data = await response.json()
                tokens_data = data.get("data", [])
                
                tokens = []
                for token_data in tokens_data:
                    token = Token(
                        address=token_data["address"],
                        name=token_data["name"],
                        symbol=token_data["symbol"],
                        decimals=token_data["decimals"],
                        total_supply=int(token_data.get("totalSupply", 0))
                    )
                    tokens.append(token)
                
                return tokens
        except Exception as e:
            logger.error(f"Error discovering new tokens: {str(e)}")
            return []
