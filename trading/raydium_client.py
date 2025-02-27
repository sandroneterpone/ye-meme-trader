import logging
import aiohttp
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class RaydiumClient:
    def __init__(self):
        self.base_url = "https://api-v3.raydium.io"
        self.pools_url = f"{self.base_url}/pools"
        self.quote_url = f"{self.base_url}/quote"
        self.swap_url = f"{self.base_url}/swap"
        
    async def get_token_price(self, token_mint: str) -> Optional[float]:
        """Ottiene il prezzo di un token usando l'API pools"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                params = {
                    "tokenMint": token_mint
                }
                async with session.get(self.pools_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            # Prendi il primo pool che contiene il token
                            for pool in data:
                                if pool.get("tokenMint") == token_mint:
                                    return float(pool.get("price", 0))
                    logger.error(f"Error getting price: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting token price: {str(e)}")
            return None
            
    async def get_swap_quote(self,
                          input_mint: str,
                          output_mint: str,
                          amount: float,
                          slippage: float = 1.0) -> Optional[Dict]:
        """Ottiene una quotazione per uno swap"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                data = {
                    "inToken": input_mint,
                    "outToken": output_mint,
                    "amount": str(int(amount)),  # Amount in lamports
                    "slippage": slippage,
                    "onlyDirectRoutes": True
                }
                
                async with session.post(self.quote_url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    logger.error(f"Error getting swap quote: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting swap quote: {str(e)}")
            return None
            
    async def create_swap_transaction(self,
                                  wallet_address: str,
                                  quote: Dict) -> Optional[Dict]:
        """Crea una transazione di swap"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                data = {
                    "wallet": wallet_address,
                    "quote": quote
                }
                
                async with session.post(self.swap_url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    logger.error(f"Error creating swap transaction: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating swap transaction: {str(e)}")
            return None
