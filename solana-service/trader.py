from solana.rpc.api import Client
import httpx
from datetime import datetime
from .config import *
from .utils.state_manager import StateManager

class SolanaTrader:
    def __init__(self):
        self.http_client = Client(SOLANA_API_URL)
        self.state_manager = StateManager()
        self.jupiter_session = httpx.Client(base_url=JUPITER_API_URL)
        
    def setup_wallet(self, wallet_address=None, private_key=None):
        self.wallet_address = wallet_address or WALLET_ADDRESS
        self.private_key = private_key or PHANTOM_BASE58_KEY
        
    def check_token_safety(self, token_address):
        try:
            # Verifica honeypot
            quote = self.jupiter_session.get(
                "/quote",
                params={
                    "inputMint": token_address,
                    "outputMint": "So11111111111111111111111111111111111111112",  # SOL
                    "amount": "1000000"  # 1 token
                }
            ).json()
            
            if quote.get("error"):
                return False
                
            # Verifica slippage
            price_impact = float(quote["priceImpact"])
            if price_impact > MAX_PRICE_IMPACT:
                return False
                
            return True
            
        except Exception as e:
            print(f"Error checking token safety: {e}")
            return False
            
    def buy_token(self, token_address, amount_sol):
        try:
            # Verifica sicurezza
            if not self.check_token_safety(token_address):
                return False
                
            # Get quote
            quote = self.jupiter_session.get(
                "/quote",
                params={
                    "inputMint": "So11111111111111111111111111111111111111112",  # SOL
                    "outputMint": token_address,
                    "amount": str(int(amount_sol * 1e9))
                }
            ).json()
            
            # Execute trade
            # TODO: Implementare la logica di esecuzione trade con Jupiter
            
            # Notifica trade
            trade_info = {
                "type": "buy",
                "token_address": token_address,
                "amount_sol": amount_sol,
                "price": float(quote["outAmount"]) / float(quote["inAmount"]),
                "timestamp": datetime.now().isoformat()
            }
            self.state_manager.add_notification("trade_opened", trade_info)
            
            return True
            
        except Exception as e:
            print(f"Error buying token: {e}")
            return False
            
    def sell_token(self, token_address, amount):
        try:
            # Get quote
            quote = self.jupiter_session.get(
                "/quote",
                params={
                    "inputMint": token_address,
                    "outputMint": "So11111111111111111111111111111111111111112",  # SOL
                    "amount": str(amount)
                }
            ).json()
            
            # Execute trade
            # TODO: Implementare la logica di esecuzione trade con Jupiter
            
            # Notifica trade
            trade_info = {
                "type": "sell",
                "token_address": token_address,
                "amount": amount,
                "price": float(quote["outAmount"]) / float(quote["inAmount"]),
                "timestamp": datetime.now().isoformat()
            }
            self.state_manager.add_notification("trade_closed", trade_info)
            
            return True
            
        except Exception as e:
            print(f"Error selling token: {e}")
            return False