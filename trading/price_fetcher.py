import os
import logging
import aiohttp
import ssl
from datetime import datetime

logger = logging.getLogger(__name__)

class PriceFetcher:
    def __init__(self):
        self.birdeye_api_key = os.getenv('BIRDEYE_API_KEY')
        self.coingecko_api = "https://api.coingecko.com/api/v3"
        self.last_sol_price = None
        self.last_update = None
        
    async def get_sol_price(self):
        """Get current SOL price in USD"""
        try:
            # Check if we have a recent price (less than 1 minute old)
            if self.last_sol_price and self.last_update:
                if (datetime.now() - self.last_update).seconds < 60:
                    return self.last_sol_price
            
            # Try Birdeye first
            price = await self._get_sol_price_birdeye()
            if price:
                self.last_sol_price = price
                self.last_update = datetime.now()
                return price
                
            # Fallback to CoinGecko
            price = await self._get_sol_price_coingecko()
            if price:
                self.last_sol_price = price
                self.last_update = datetime.now()
                return price
                
            # If all fails, return the default from .env
            return float(os.getenv('SOL_TO_USD_RATE', 20.0))
            
        except Exception as e:
            logger.error(f"Error fetching SOL price: {str(e)}")
            return float(os.getenv('SOL_TO_USD_RATE', 20.0))
            
    async def _get_sol_price_birdeye(self):
        """Get SOL price from Birdeye"""
        try:
            if not self.birdeye_api_key or self.birdeye_api_key == "your_birdeye_api_key_here":
                logger.warning("No valid Birdeye API key found. Get one at https://birdeye.so/")
                return None
                
            url = "https://public-api.birdeye.so/v1/token/price?address=So11111111111111111111111111111111111111112"
            headers = {'x-api-key': self.birdeye_api_key}
            
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data.get('data', {}).get('value')
                        if price is not None:
                            return float(price)
                    elif response.status == 401:
                        logger.error("Invalid Birdeye API key. Get a valid key at https://birdeye.so/")
                    elif response.status == 429:
                        logger.warning("Birdeye API rate limit exceeded")
                    else:
                        logger.warning(f"Birdeye API returned status {response.status}")
            return None
        except Exception as e:
            logger.error(f"Birdeye price fetch error: {str(e)}")
            return None
            
    async def _get_sol_price_coingecko(self):
        """Get SOL price from CoinGecko"""
        try:
            url = f"{self.coingecko_api}/simple/price?ids=solana&vs_currencies=usd"
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data.get('solana', {}).get('usd', 0))
            return None
        except Exception as e:
            logger.error(f"CoinGecko price fetch error: {str(e)}")
            return None
