import os
import json
import base64
import aiohttp
import logging
from typing import Optional, Dict, Any
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction, TransactionInstruction

logger = logging.getLogger(__name__)

class RaydiumClient:
    def __init__(self, keypair: Keypair, client: AsyncClient, test_mode: bool = True):
        self.wallet = keypair
        self.client = client
        self.test_mode = test_mode
        self.api_url = "https://api.raydium.io/v2"
        logger.info(f"RaydiumClient initialized in {'TEST' if test_mode else 'LIVE'} mode")

    async def get_token_price(self, token_mint: str) -> Optional[float]:
        """Ottiene il prezzo di un token da Raydium"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.api_url}/main/price?fsym={token_mint}&tsyms=USD"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and "USD" in data:
                            return float(data["USD"])
        except Exception as e:
            logger.error(f"Error getting token price: {e}")
        return None

    async def get_pool_info(self, input_mint: str, output_mint: str) -> Optional[Dict]:
        """Ottiene informazioni sulla pool di liquidità"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.api_url}/main/pairs"
                async with session.get(url) as response:
                    if response.status == 200:
                        pools = await response.json()
                        for pool in pools:
                            if (pool["token0"]["address"] == input_mint and pool["token1"]["address"] == output_mint) or \
                               (pool["token0"]["address"] == output_mint and pool["token1"]["address"] == input_mint):
                                return pool
        except Exception as e:
            logger.error(f"Error getting pool info: {e}")
        return None

    async def get_quote(self, input_mint: str, output_mint: str, amount: float, slippage: float = 0.5) -> Optional[Dict]:
        """Ottiene una quotazione per uno swap su Raydium"""
        try:
            # Get pool info first
            pool = await self.get_pool_info(input_mint, output_mint)
            if not pool:
                logger.error("Pool not found")
                return None

            # Convert amount to integer (lamports)
            amount_lamports = int(amount * 1e6)  # Assuming USDC with 6 decimals
            
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount_lamports),
                "slippage": slippage,
                "poolId": pool["id"]
            }
            
            logger.info(f"Getting quote with params: {params}")
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.api_url}/main/quote"
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
        """Esegue uno swap su Raydium"""
        if self.test_mode:
            logger.info("Test mode: skipping actual swap")
            return "test_transaction_signature"

        try:
            # Prepare the transaction
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Get swap instructions
                url = f"{self.api_url}/main/swap"
                swap_data = {
                    "quote": quote,
                    "userPublicKey": str(self.wallet.pubkey())
                }
                
                logger.info(f"Preparing swap with data: {swap_data}")
                
                async with session.post(url, json=swap_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to prepare swap transaction. Status: {response.status}, Response: {error_text}")
                        return None
                    
                    swap_response = await response.json()
                    logger.info(f"Got swap response: {swap_response}")
                    
                    # Create transaction
                    transaction = Transaction()
                    
                    # Add instructions
                    for ix_data in swap_response["instructions"]:
                        ix = TransactionInstruction(
                            keys=ix_data["keys"],
                            program_id=ix_data["programId"],
                            data=base64.b64decode(ix_data["data"])
                        )
                        transaction.add(ix)
                    
                    # Sign and send transaction
                    transaction.sign(self.wallet)
                    
                    # Send the signed transaction
                    result = await self.client.send_transaction(
                        transaction
                    )
                    
                    if result["result"]:
                        return result["result"]
                    
                    logger.error(f"Failed to send transaction: {result}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error executing swap: {e}")
            return None
