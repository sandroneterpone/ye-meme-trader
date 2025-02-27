import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional
from .jupiter_client import JupiterClient
from .solana_client import SolanaClient

logger = logging.getLogger(__name__)

class YeMemeTrader:
    def __init__(self):
        self.shared_state = {
            "trade": {
                "active_trades": {},
                "pending_orders": {}
            }
        }
        self.jupiter = JupiterClient()
        self.solana = SolanaClient()
        
    async def place_trade(self, token: dict) -> bool:
        """Piazza un nuovo trade"""
        try:
            address = token["address"]
            symbol = token.get("symbol", "Unknown")
            
            # Ottieni prezzo da Jupiter
            price = await self.jupiter.get_token_price(address)
            if not price:
                logger.error(f"Could not get price for {symbol}")
                return False
                
            # Simula l'acquisto (TODO: implementare l'acquisto reale con Jupiter)
            trade = {
                "symbol": symbol,
                "address": address,
                "entry_price": price,
                "amount": 0.1,  # Test amount
                "amount_usd": 0.1 * price,
                "entry_time": datetime.now(),
                "highest_price": price,
                "stop_loss": price * 0.85,  # -15%
                "trailing_stop": price * 0.85,
                "take_profits": {
                    "tp1": {"price": price * 1.5, "size": 0.5, "executed": False},  # +50%
                    "tp2": {"price": price * 2.0, "size": 0.3, "executed": False},  # +100%
                    "tp3": {"price": price * 3.0, "size": 0.2, "executed": False}   # +200%
                }
            }
            
            self.shared_state["trade"]["active_trades"][address] = trade
            logger.info(f"Successfully placed trade for {symbol} at {price}")
            return True
            
        except Exception as e:
            logger.error(f"Error placing trade: {str(e)}")
            return False
            
    async def update_trades(self, current_prices: Dict[str, float]):
        """Aggiorna lo stato dei trade attivi"""
        try:
            active_trades = self.shared_state["trade"]["active_trades"]
            
            for address in list(active_trades.keys()):
                price = await self.jupiter.get_token_price(address)
                if price:
                    trade = active_trades[address]
                    trade["current_price"] = price
                    trade["pnl_percentage"] = ((price - trade["entry_price"]) / trade["entry_price"]) * 100
                    trade["amount_usd"] = trade["amount"] * price
                    
        except Exception as e:
            logger.error(f"Error updating trades: {str(e)}")
            
    async def get_token_price(self, token_address: str) -> Optional[float]:
        """Ottiene il prezzo corrente di un token"""
        try:
            return await self.jupiter.get_token_price(token_address)
        except Exception as e:
            logger.error(f"Error getting token price: {str(e)}")
            return None
            
    async def execute_order(self, token_address: str, side: str, amount: float) -> dict:
        """Esegue un ordine di trading"""
        try:
            active_trades = self.shared_state["trade"]["active_trades"]
            
            if token_address not in active_trades:
                return {
                    "success": False,
                    "error": "Token not found in active trades"
                }
                
            trade = active_trades[token_address]
            current_price = await self.get_token_price(token_address)
            
            if not current_price:
                return {
                    "success": False,
                    "error": "Could not get current price"
                }
                
            # Configura lo swap
            if side == "buy":
                input_token = "So11111111111111111111111111111111111111112"  # SOL
                output_token = token_address
            else:  # sell
                input_token = token_address
                output_token = "So11111111111111111111111111111111111111112"  # SOL
                
            # Ottieni quotazione
            quote = await self.jupiter.get_swap_quote(
                input_mint=input_token,
                output_mint=output_token,
                amount=amount,
                slippage=1.0  # 1% slippage
            )
            
            if not quote:
                return {
                    "success": False,
                    "error": "Failed to get swap quote"
                }
                
            # Ottieni istruzioni di swap
            swap_ix = await self.jupiter.get_swap_instructions(
                wallet_address=self.solana.wallet_address,
                quote=quote
            )
            
            if not swap_ix:
                return {
                    "success": False,
                    "error": "Failed to get swap instructions"
                }
                
            # Firma e invia la transazione
            transaction = await self.solana.create_and_sign_transaction(swap_ix["instructions"])
            if not transaction:
                return {
                    "success": False,
                    "error": "Failed to create transaction"
                }
                
            # Invia la transazione
            tx_hash = await self.solana.send_transaction(transaction)
            if not tx_hash:
                return {
                    "success": False,
                    "error": "Failed to send transaction"
                }
                
            logger.info(f"Swap executed successfully: {tx_hash}")
            return {
                "success": True,
                "price": current_price,
                "amount": amount,
                "side": side,
                "tx_hash": tx_hash
            }
            
        except Exception as e:
            logger.error(f"Error executing order: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
