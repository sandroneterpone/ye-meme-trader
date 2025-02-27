import os
import logging
import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client

logger = logging.getLogger(__name__)

class WalletManager:
    def __init__(self):
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        # Verifica se l'indirizzo è in formato base58 o stringa normale
        try:
            if len(self.wallet_address) > 44:  # Probabile chiave privata
                secret_key = base58.b58decode(self.wallet_address)
                self.keypair = Keypair.from_bytes(secret_key)
                self.public_key = str(self.keypair.pubkey())
                logger.info(f"Initialized wallet from private key")
            else:
                self.public_key = str(Pubkey.from_string(self.wallet_address))
                logger.info(f"Initialized wallet from public key")
        except Exception as e:
            logger.error(f"Error initializing wallet: {str(e)}")
            self.public_key = None
            
        try:
            self.client = Client(endpoint="https://api.mainnet-beta.solana.com", timeout=30)
            logger.info("Connected to Solana RPC endpoint")
        except Exception as e:
            logger.error(f"Error connecting to Solana RPC: {str(e)}")
            self.client = None
        
    def get_balance(self):
        """Get wallet balance in SOL"""
        try:
            if not self.public_key or not self.client:
                logger.error("Wallet or RPC client not properly initialized")
                return 0.0
                
            logger.info(f"Fetching balance for address: {self.public_key}")
            response = self.client.get_balance(self.public_key)
            
            if response and 'result' in response:
                # Convert lamports to SOL (1 SOL = 1e9 lamports)
                balance_sol = float(response['result']['value']) / 1e9
                logger.info(f"Balance fetched successfully: {balance_sol} SOL")
                return balance_sol
            else:
                logger.error(f"Invalid response from RPC: {response}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting wallet balance: {str(e)}")
            return 0.0
            
    def check_allowance(self, token_address):
        """Check if we have enough allowance to trade a token"""
        try:
            # Per Solana non serve l'allowance come su EVM
            return True
        except Exception as e:
            logger.error(f"Error checking allowance: {str(e)}")
            return False
            
    def approve_token(self, token_address, amount):
        """Approve token for trading"""
        try:
            # Per Solana non serve l'approve come su EVM
            return True
        except Exception as e:
            logger.error(f"Error approving token: {str(e)}")
            return False
