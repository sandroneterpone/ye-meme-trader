"""
Core Solana blockchain interaction service.
"""
import asyncio
import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List

import aiohttp
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey
from solana.transaction import Transaction

from ..models.token import Token, TokenMetrics
from ..models.trade import Trade, TradeParams, TradeType, TradeStatus
from config.settings import SOLANA_CONFIG, JUPITER_CONFIG

logger = logging.getLogger(__name__)

class SolanaService:
    """Service for interacting with Solana blockchain and Jupiter DEX."""
    
    def __init__(self):
        """Initialize the Solana service."""
        self.client = AsyncClient(SOLANA_CONFIG["network_url"], commitment=Confirmed)
        self.wallet = Keypair.from_base58_string(SOLANA_CONFIG["wallet_key"])
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        await self.client.close()

    async def get_token_account(self, token_address: str) -> Dict[str, Any]:
        """Get token account information."""
        try:
            token_pubkey = PublicKey(token_address)
            response = await self.client.get_account_info(token_pubkey)
            if response["result"]["value"] is None:
                raise ValueError(f"Token account {token_address} not found")
            return response["result"]["value"]
        except Exception as e:
            logger.error(f"Error getting token account {token_address}: {str(e)}")
            raise

    async def get_token_supply(self, token_address: str) -> int:
        """Get token total supply."""
        try:
            token_pubkey = PublicKey(token_address)
            response = await self.client.get_token_supply(token_pubkey)
            return int(response["result"]["value"]["amount"])
        except Exception as e:
            logger.error(f"Error getting token supply for {token_address}: {str(e)}")
            raise

    async def get_token_balance(self, token_address: str) -> Decimal:
        """Get token balance for the wallet."""
        try:
            token_pubkey = PublicKey(token_address)
            response = await self.client.get_token_accounts_by_owner(
                self.wallet.public_key,
                {"mint": str(token_pubkey)}
            )
            if not response["result"]["value"]:
                return Decimal("0")
            
            balance = int(response["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"])
            decimals = int(response["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["decimals"])
            return Decimal(balance) / Decimal(10 ** decimals)
        except Exception as e:
            logger.error(f"Error getting token balance for {token_address}: {str(e)}")
            return Decimal("0")

    async def get_token_price(self, token_address: str) -> Optional[Decimal]:
        """Get current token price in SOL."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            amount = 1_000_000  # 1 SOL in lamports
            url = f"{JUPITER_CONFIG['base_url']}/quote"
            params = {
                "inputMint": JUPITER_CONFIG["default_token"],
                "outputMint": token_address,
                "amount": str(amount),
                "slippageBps": JUPITER_CONFIG["slippage_bps"]
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                if "data" not in data or "price" not in data["data"]:
                    return None
                    
                return Decimal(str(data["data"]["price"]))
        except Exception as e:
            logger.error(f"Error getting token price for {token_address}: {str(e)}")
            return None

    async def get_quote(self, input_token: str, output_token: str, amount: int) -> Optional[TradeParams]:
        """Get quote for token swap."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            url = f"{JUPITER_CONFIG['base_url']}/quote"
            params = {
                "inputMint": input_token,
                "outputMint": output_token,
                "amount": str(amount),
                "slippageBps": JUPITER_CONFIG["slippage_bps"]
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                return TradeParams(
                    amount_in=Decimal(str(data["inAmount"])),
                    amount_out=Decimal(str(data["outAmount"])),
                    price_impact=Decimal(str(data.get("priceImpactPct", "0"))),
                    minimum_out=Decimal(str(data["otherAmountThreshold"])),
                    route=data["route"]
                )
        except Exception as e:
            logger.error(f"Error getting quote: {str(e)}")
            return None

    async def execute_swap(self, trade: Trade) -> bool:
        """Execute token swap transaction."""
        if not self.session or not trade.params:
            raise RuntimeError("Session not initialized or trade params missing")
            
        try:
            # Get swap transaction
            url = f"{JUPITER_CONFIG['base_url']}/swap"
            payload = {
                "route": trade.params.route,
                "userPublicKey": str(self.wallet.public_key),
                "wrapUnwrapSOL": True
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to get swap transaction: {await response.text()}")
                    
                swap_data = await response.json()
                
            # Sign and send transaction
            transaction = Transaction.deserialize(bytes.fromhex(swap_data["swapTransaction"]))
            transaction.sign(self.wallet)
            
            tx_hash = await self.client.send_transaction(
                transaction,
                self.wallet,
                opts={"skip_preflight": True}
            )
            
            if "result" not in tx_hash:
                raise ValueError("Failed to send transaction")
                
            trade.transaction_hash = tx_hash["result"]
            trade.status = TradeStatus.EXECUTED
            return True
            
        except Exception as e:
            logger.error(f"Error executing swap: {str(e)}")
            trade.status = TradeStatus.FAILED
            trade.error_message = str(e)
            return False
