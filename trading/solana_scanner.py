import os
import json
import aiohttp
import ssl
import certifi
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class SolanaScanner:
    def __init__(self):
        # Configurazione SSL
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Base URLs
        self.solana_base_url = "https://api.mainnet-beta.solana.com"
        self.jupiter_base_url = "https://token.jup.ag/all"
        
        # Rate limiting
        self.request_delay = 2  # seconds between requests
        self.last_request_time = 0
        
        # Cache dei token
        self.token_cache = None
        self.last_cache_update = 0
        self.cache_ttl = 3600  # 1 ora
        
        logger.info("SolanaScanner initialized with Solana public API")
        
    async def _wait_for_rate_limit(self):
        """Wait to respect rate limits"""
        now = datetime.now().timestamp()
        time_since_last = now - self.last_request_time
        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)
        self.last_request_time = datetime.now().timestamp()
        
    async def _make_request(self, url, data, retries=3):
        """Make a request with proper error handling and retries"""
        await self._wait_for_rate_limit()
        
        for attempt in range(retries):
            try:
                logger.info(f"Making request to {url} (attempt {attempt + 1}/{retries})")
                conn = aiohttp.TCPConnector(ssl=self.ssl_context)
                timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds timeout
                
                async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
                    async with session.post(url, json=data) as response:
                        logger.info(f"Response status: {response.status}")
                        
                        if response.status == 429:  # Rate limit
                            wait_time = int(response.headers.get('Retry-After', 60))
                            logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                            await asyncio.sleep(wait_time)
                            continue
                            
                        response_text = await response.text()
                        logger.info(f"Response text: {response_text[:200]}...")
                            
                        if response.status != 200:
                            logger.error(f"API request failed with status {response.status}: {response_text}")
                            if attempt < retries - 1:
                                wait_time = 2 ** attempt
                                logger.info(f"Retrying in {wait_time} seconds...")
                                await asyncio.sleep(wait_time)
                                continue
                            return None
                            
                        try:
                            return await response.json()
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON response: {response_text}")
                            return None
                            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error(f"Error making request to {url}: {str(e)}")
                if attempt < retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                return None
                
        return None
        
    async def _update_token_cache(self):
        """Update token cache from Jupiter API"""
        now = datetime.now().timestamp()
        if self.token_cache is None or (now - self.last_cache_update) > self.cache_ttl:
            try:
                conn = aiohttp.TCPConnector(ssl=self.ssl_context)
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
                    async with session.get(self.jupiter_base_url) as response:
                        if response.status == 200:
                            self.token_cache = await response.json()
                            self.last_cache_update = now
                            logger.info(f"Updated token cache with {len(self.token_cache)} tokens")
                        else:
                            logger.error(f"Failed to update token cache: {response.status}")
            except Exception as e:
                logger.error(f"Error updating token cache: {str(e)}")

    async def get_token_info(self, token_address):
        """Get token info using Solana API"""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenSupply",
            "params": [token_address]
        }
        
        response = await self._make_request(self.solana_base_url, data)
        if response and "result" in response:
            return response["result"]
        return None

    async def get_token_accounts(self, token_address):
        """Get token accounts using Solana API"""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenLargestAccounts",
            "params": [token_address]
        }
        
        response = await self._make_request(self.solana_base_url, data)
        if response and "result" in response:
            return response["result"].get("value", [])
        return []

    async def scan_tokens(self, search_term):
        """Scan for tokens using Jupiter API"""
        await self._update_token_cache()
        
        if not self.token_cache:
            return []
            
        search_term = search_term.lower()
        filtered_tokens = [
            token for token in self.token_cache
            if search_term in token.get("name", "").lower()
            or search_term in token.get("symbol", "").lower()
        ]
        
        logger.info(f"Found {len(filtered_tokens)} tokens matching '{search_term}'")
        return filtered_tokens

    async def get_token_price(self, token_address):
        """Get token price using Jupiter API"""
        await self._update_token_cache()
        
        if not self.token_cache:
            return 0
            
        token = next((t for t in self.token_cache if t.get("address") == token_address), None)
        if token:
            return float(token.get("price", 0))
        return 0

    async def get_token_holders(self, token_address):
        """Get number of token holders (approssimato usando il numero di account)"""
        accounts = await self.get_token_accounts(token_address)
        return len(accounts)
