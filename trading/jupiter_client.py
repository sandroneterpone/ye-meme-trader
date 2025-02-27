import os
import json
import base64
import aiohttp
import logging
from typing import Optional, Dict, Any
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.async_api import AsyncClient

logger = logging.getLogger(__name__)

class JupiterClient:
    def __init__(self, keypair: Keypair, client: AsyncClient, test_mode: bool = True):
        self.wallet = keypair
        self.client = client
        self.test_mode = test_mode
        self.quote_url = "https://quote-api.jup.ag/v6"
        self.price_url = "https://price.jup.ag/v6"
        logger.info(f"JupiterClient initialized in {'TEST' if test_mode else 'LIVE'} mode")

    async def get_token_price(self, token_mint: str) -> Optional[float]:
        """Ottiene il prezzo di un token"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.price_url}/price?ids={token_mint}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and "data" in data and token_mint in data["data"]:
                            return float(data["data"][token_mint]["price"])
        except Exception as e:
            logger.error(f"Error getting token price: {e}")
        return None

    async def get_quote(self, input_mint: str, output_mint: str, amount: float, slippage: float = 0.5) -> Optional[Dict]:
        """Ottiene una quotazione per uno swap"""
        try:
            # Convert amount to integer (lamports)
            amount_lamports = int(amount * 1e6)  # Assuming USDC with 6 decimals
            
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount_lamports),
                "slippageBps": int(slippage * 100),
                "onlyDirectRoutes": "false"
            }
            
            logger.info(f"Getting quote with params: {params}")
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.quote_url}/quote"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        quote = await response.json()
                        logger.info(f"Got quote: {quote}")
                        return quote
                    else:
                        error_text = await response.text()
                        logger.error(f"Error getting quote. Status: {response.status}, Response: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
        return None

    async def swap(self, quote: Dict[str, Any]) -> Optional[str]:
        """Esegue uno swap basato su una quotazione"""
        if self.test_mode:
            logger.info("Test mode: skipping actual swap")
            return "test_transaction_signature"

        try:
            # Prepare the transaction
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Get serialized transaction
                url = f"{self.quote_url}/swap"
                swap_data = {
                    "quoteResponse": quote,
                    "userPublicKey": str(self.wallet.pubkey()),
                    "wrapUnwrapSOL": True,
                    "computeUnitPriceMicroLamports": 1000  # Add priority fee
                }
                
                logger.info(f"Preparing swap with data: {swap_data}")
                
                async with session.post(url, json=swap_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to prepare swap transaction. Status: {response.status}, Response: {error_text}")
                        return None
                    
                    swap_response = await response.json()
                    logger.info(f"Got swap response: {swap_response}")
                    
                    # Decode base64 transaction to bytes
                    tx_bytes = base64.b64decode(swap_response["swapTransaction"])
                    
                    # Deserialize transaction
                    tx = VersionedTransaction.from_bytes(tx_bytes)
                    
                    # Sign the transaction using partial_sign
                    tx.message.partial_sign([self.wallet], tx.signatures)
                    
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
