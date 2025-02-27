import os
import json
import base64
import aiohttp
import logging
from typing import Optional, Dict, Any
from solders.keypair import Keypair
from solders.transaction import Transaction, VersionedTransaction
from solders.instruction import Instruction, AccountMeta
from solana.rpc.async_api import AsyncClient

logger = logging.getLogger(__name__)

class RaydiumClient:
    def __init__(self, keypair: Keypair, client: AsyncClient, test_mode: bool = True):
        self.wallet = keypair
        self.client = client
        self.test_mode = test_mode
        self.api_url = "https://quote-api.jup.ag/v6"
        logger.info(f"RaydiumClient initialized in {'TEST' if test_mode else 'LIVE'} mode")

    async def get_token_price(self, token_mint: str) -> Optional[float]:
        """Ottiene il prezzo di un token da Raydium"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.api_url}/compute/price"
                params = {"mints": [token_mint]}
                async with session.get(url, params=params) as response:
                    response_text = await response.text()
                    logger.info(f"Raw response: {response_text}")
                    
                    if response.status == 200:
                        data = await response.json()
                        if data and "data" in data and token_mint in data["data"]:
                            return float(data["data"][token_mint]["price"])
        except Exception as e:
            logger.error(f"Error getting token price: {e}")
        return None

    async def get_pool_info(self, input_mint: str, output_mint: str) -> Optional[Dict]:
        """Ottiene informazioni sulla pool di liquidità"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.api_url}/compute/pool-info"
                params = {"inputMint": input_mint, "outputMint": output_mint}
                async with session.get(url, params=params) as response:
                    response_text = await response.text()
                    logger.info(f"Raw response: {response_text}")
                    
                    if response.status == 200:
                        data = await response.json()
                        if data and "data" in data:
                            return data["data"]
        except Exception as e:
            logger.error(f"Error getting pool info: {e}")
        return None

    async def get_quote(self, input_mint: str, output_mint: str, amount: float, slippage: float = 0.5) -> Optional[Dict]:
        """Ottiene una quotazione per uno swap su Jupiter"""
        try:
            # Convert amount to integer (lamports)
            amount_lamports = int(amount * 1e6)  # Assuming USDC with 6 decimals
            
            url = f"{self.api_url}/quote"
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount_lamports),
                "slippageBps": str(int(slippage * 100)),
                "onlyDirectRoutes": "true",
                "asLegacyTransaction": "true"
            }
            
            logger.info(f"Getting quote with params: {params}")
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params) as response:
                    response_text = await response.text()
                    logger.info(f"Raw response: {response_text}")
                    
                    if response.status == 200:
                        quote = await response.json()
                        logger.info(f"Got quote response: {json.dumps(quote, indent=2)}")
                        return quote
                    else:
                        error_text = await response.text()
                        logger.error(f"Error getting quote. Status: {response.status}, Response: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
        return None

    async def get_sol_balance(self) -> float:
        """Get SOL balance for the wallet"""
        try:
            balance = await self.client.get_balance(self.wallet.pubkey())
            return balance / 1e9  # Convert lamports to SOL
        except Exception as e:
            logger.error(f"Error getting SOL balance: {e}")
            return 0.0

    async def swap(self, quote: Dict[str, Any]) -> Optional[str]:
        """Esegue uno swap su Jupiter"""
        if self.test_mode:
            logger.info("Test mode: skipping actual swap")
            return "test_transaction_signature"

        try:
            url = f"{self.api_url}/swap"
            swap_data = {
                "quoteResponse": quote,
                "userPublicKey": str(self.wallet.pubkey()),
                "wrapUnwrapSOL": False,
                "asLegacyTransaction": True
            }
            
            logger.info(f"Preparing swap with data: {swap_data}")
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, json=swap_data) as response:
                    response_text = await response.text()
                    logger.info(f"Raw response: {response_text}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to prepare swap transaction. Status: {response.status}, Response: {error_text}")
                        return None
                    
                    swap_response = await response.json()
                    logger.info(f"Got swap response: {swap_response}")
                    
                    if "error" in swap_response:
                        logger.error(f"Swap response error: {swap_response['error']}")
                        return None
                    
                    # Get transaction data
                    tx_data = swap_response["swapTransaction"]
                    tx_buffer = base64.b64decode(tx_data)
                    
                    # Deserialize and sign transaction
                    tx = Transaction.from_bytes(tx_buffer)
                    tx.sign([self.wallet])
                    
                    # Send the signed transaction
                    result = await self.client.send_raw_transaction(
                        bytes(tx)
                    )
                    
                    if result["result"]:
                        return result["result"]
                    
                    logger.error(f"Failed to send transaction: {result}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error executing swap: {e}")
            return None
