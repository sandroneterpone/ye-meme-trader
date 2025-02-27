import os
import logging
import base58
from typing import Optional, Dict, List, Any
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
import aiohttp
import json
from spl.token.instructions import get_associated_token_address
from solders.pubkey import Pubkey

logger = logging.getLogger(__name__)

class SolanaClient:
    def __init__(self, keypair: Keypair, client: AsyncClient):
        self.birdeye_api_key = os.getenv('BIRDEYE_API_KEY')
        self.solscan_api_key = os.getenv('SOLSCAN_API_KEY')
        self.wallet_address = str(keypair.pubkey())
        
        # API endpoints
        self.jupiter_api = "https://quote-api.jup.ag/v6"
        self.raydium_api = os.getenv('RAYDIUM_API_URL')
        self.birdeye_api = os.getenv('BIRDEYE_API_URL')
        
        self.keypair = keypair
        self.client = client
        
    async def get_token_price(self, token_address):
        """Get token price from Birdeye"""
        url = f"https://public-api.birdeye.so/v1/token/price?address={token_address}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'x-api-key': self.birdeye_api_key}) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data.get('data', {}).get('value', 0))
                return 0
                
    async def get_token_info(self, token_address):
        """Get detailed token info from Solscan"""
        url = f"https://public-api.solscan.io/token/meta?tokenAddress={token_address}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'token': self.solscan_api_key}) as response:
                if response.status == 200:
                    return await response.json()
                return None
                
    async def get_jupiter_quote(self, input_mint, output_mint, amount):
        """Get quote from Jupiter"""
        url = f"{self.jupiter_api}/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": 50
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return None
                
    async def get_raydium_pools(self):
        """Get all Raydium pools"""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.raydium_api) as response:
                if response.status == 200:
                    return await response.json()
                return []
                
    async def analyze_token_metrics(self, token_address):
        """Analyze token metrics from Birdeye"""
        url = f"https://public-api.birdeye.so/v1/token/metrics?address={token_address}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'x-api-key': self.birdeye_api_key}) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'liquidity': data.get('data', {}).get('liquidity', 0),
                        'volume_24h': data.get('data', {}).get('volume24h', 0),
                        'price_change_24h': data.get('data', {}).get('priceChange24h', 0),
                        'holders': data.get('data', {}).get('holders', 0)
                    }
                return None
                
    async def check_token_safety(self, token_address):
        """Check token safety metrics"""
        metrics = await self.analyze_token_metrics(token_address)
        if not metrics:
            return False, "Couldn't fetch token metrics"
            
        # Check minimum requirements
        if metrics['liquidity'] < float(os.getenv('MIN_LIQUIDITY', 1000.0)):
            return False, "Insufficient liquidity"
            
        if metrics['holders'] < int(os.getenv('MIN_HOLDERS', 50)):
            return False, "Too few holders"
            
        if abs(metrics['price_change_24h']) > float(os.getenv('MAX_PRICE_CHANGE', 0.50)):
            return False, "Price change too volatile"
            
        return True, "Token passed safety checks"

    async def is_valid_token(self, token_address: str) -> bool:
        """Verify if an address is a valid Solana token"""
        try:
            # Check token metadata
            token_info = await self.get_token_info(token_address)
            if not token_info:
                return False
                
            # Verify basic token properties
            if not all(key in token_info for key in ['name', 'symbol', 'decimals']):
                return False
                
            # Check if token has any transactions
            url = f"https://public-api.solscan.io/token/txs?tokenAddress={token_address}&limit=1"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'token': self.solscan_api_key}) as response:
                    if response.status != 200:
                        return False
                    txs = await response.json()
                    if not txs or len(txs) == 0:
                        return False
                        
            return True
            
        except Exception as e:
            logger.error(f"Error validating token {token_address}: {str(e)}")
            return False
            
    async def get_token_liquidity(self, token_address: str) -> dict:
        """Get token liquidity information from various DEXes"""
        liquidity_info = {
            'total_liquidity_usd': 0,
            'dexes': {}
        }
        
        try:
            # Get Raydium liquidity
            if self.raydium_api:
                url = f"{self.raydium_api}/pools?token={token_address}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            pools = await response.json()
                            raydium_liquidity = sum(float(pool.get('liquidity', 0)) for pool in pools)
                            liquidity_info['dexes']['raydium'] = raydium_liquidity
                            liquidity_info['total_liquidity_usd'] += raydium_liquidity
                            
            # Get Jupiter liquidity
            url = f"{self.jupiter_api}/pools?tokens={token_address}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        pools = await response.json()
                        jupiter_liquidity = sum(float(pool.get('liquidity', 0)) for pool in pools)
                        liquidity_info['dexes']['jupiter'] = jupiter_liquidity
                        liquidity_info['total_liquidity_usd'] += jupiter_liquidity
                        
            # Get Birdeye liquidity data
            url = f"https://public-api.birdeye.so/v1/token/pools?address={token_address}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'x-api-key': self.birdeye_api_key}) as response:
                    if response.status == 200:
                        data = await response.json()
                        pools = data.get('data', {}).get('items', [])
                        birdeye_liquidity = sum(float(pool.get('liquidity', 0)) for pool in pools)
                        liquidity_info['dexes']['birdeye'] = birdeye_liquidity
                        liquidity_info['total_liquidity_usd'] += birdeye_liquidity
                        
        except Exception as e:
            logger.error(f"Error getting liquidity for token {token_address}: {str(e)}")
            
        return liquidity_info

    async def execute_jupiter_swap(self, route: dict) -> dict:
        """Esegue uno swap su Jupiter"""
        try:
            # Prepara i dati della transazione
            tx_data = {
                'route': route,
                'userPublicKey': self.wallet_address,
                'slippageBps': int(os.getenv('SLIPPAGE_BPS', 50)),
                'prioritizationFeeLamports': 0,  # Opzionale
                'asLegacyTransaction': False  # Usa le transazioni versioned
            }
            
            # Ottieni la transazione da Jupiter
            url = f"{self.jupiter_api}/swap"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=tx_data) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to get swap transaction: {await response.text()}")
                    swap_tx = await response.json()
                    
            # Firma e invia la transazione
            signed_tx = await self.sign_and_send_transaction(Transaction.deserialize(base64.b64decode(swap_tx['swapTransaction'])))
            
            # Attendi la conferma
            tx_hash = signed_tx
            confirmed = await self._wait_for_confirmation(tx_hash)
            
            if not confirmed:
                raise ValueError("Transaction failed to confirm")
                
            return {
                'success': True,
                'txHash': tx_hash
            }
            
        except Exception as e:
            logger.error(f"Error executing Jupiter swap: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def sign_and_send_transaction(self, transaction: Transaction) -> Optional[str]:
        """Firma e invia una transazione"""
        try:
            # Firma transazione
            transaction.sign(self.keypair)
            
            # Invia transazione
            result = await self.client.send_transaction(transaction)
            
            if "result" in result:
                tx_hash = result["result"]
                logger.info(f"Transaction sent: {tx_hash}")
                return tx_hash
                
            logger.error(f"Error sending transaction: {result}")
            return None
            
        except Exception as e:
            logger.error(f"Error signing/sending transaction: {str(e)}")
            return None
            
    async def get_balance(self) -> Optional[float]:
        """Ottiene il bilancio del wallet in SOL"""
        try:
            result = await self.client.get_balance(self.keypair.pubkey())
            if "result" in result:
                balance_lamports = result["result"]["value"]
                balance_sol = balance_lamports / 1e9
                return balance_sol
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return None
            
    async def get_token_holders(self, token_address: str) -> dict:
        """Ottiene informazioni dettagliate sui holders del token"""
        try:
            url = f"{self.birdeye_api}/token/holders?address={token_address}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'x-api-key': self.birdeye_api_key}) as response:
                    if response.status == 200:
                        data = await response.json()
                        holders_data = data.get('data', {}).get('items', [])
                        
                        # Analizza la distribuzione dei holders
                        total_holders = len(holders_data)
                        total_supply = sum(float(h.get('amount', 0)) for h in holders_data)
                        
                        # Calcola la concentrazione
                        top_10_holdings = sum(float(h.get('amount', 0)) for h in holders_data[:10])
                        concentration_ratio = (top_10_holdings / total_supply) if total_supply > 0 else 1
                        
                        return {
                            'total_holders': total_holders,
                            'total_supply': total_supply,
                            'concentration_ratio': concentration_ratio,
                            'holders_distribution': holders_data[:50]  # Top 50 holders
                        }
                        
            return {
                'total_holders': 0,
                'total_supply': 0,
                'concentration_ratio': 1,
                'holders_distribution': []
            }
            
        except Exception as e:
            logger.error(f"Error getting token holders: {str(e)}")
            return {
                'total_holders': 0,
                'total_supply': 0,
                'concentration_ratio': 1,
                'holders_distribution': []
            }
            
    async def get_token_trades(self, token_address: str, limit: int = 100) -> list:
        """Ottiene le ultime trades del token"""
        try:
            url = f"{self.birdeye_api}/token/trades?address={token_address}&limit={limit}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'x-api-key': self.birdeye_api_key}) as response:
                    if response.status == 200:
                        data = await response.json()
                        trades = data.get('data', {}).get('items', [])
                        
                        return [{
                            'time': trade.get('time'),
                            'side': trade.get('side'),
                            'price': float(trade.get('price', 0)),
                            'amount': float(trade.get('amount', 0)),
                            'value': float(trade.get('value', 0)),
                            'maker': trade.get('maker'),
                            'taker': trade.get('taker')
                        } for trade in trades]
                        
            return []
            
        except Exception as e:
            logger.error(f"Error getting token trades: {str(e)}")
            return []
            
    async def get_token_social_data(self, token_address: str) -> dict:
        """Ottiene dati social del token da varie fonti"""
        try:
            social_data = {
                'twitter': {
                    'followers': 0,
                    'engagement': 0,
                    'sentiment': 0
                },
                'discord': {
                    'members': 0,
                    'active_users': 0,
                    'message_frequency': 0
                },
                'telegram': {
                    'members': 0,
                    'active_users': 0,
                    'message_frequency': 0
                }
            }
            
            # Implementa la raccolta dati da Twitter
            if self.twitter_api_key:
                # TODO: Implementa l'integrazione con Twitter
                pass
                
            # Implementa la raccolta dati da Discord
            if self.discord_token:
                # TODO: Implementa l'integrazione con Discord
                pass
                
            # Implementa la raccolta dati da Telegram
            if self.telegram_bot_token:
                # TODO: Implementa l'integrazione con Telegram
                pass
                
            return social_data
            
        except Exception as e:
            logger.error(f"Error getting social data: {str(e)}")
            return {
                'twitter': {'followers': 0, 'engagement': 0, 'sentiment': 0},
                'discord': {'members': 0, 'active_users': 0, 'message_frequency': 0},
                'telegram': {'members': 0, 'active_users': 0, 'message_frequency': 0}
            }
            
    async def _wait_for_confirmation(self, tx_hash: str, max_retries: int = 30) -> bool:
        """Attende la conferma di una transazione"""
        try:
            url = "https://api.mainnet-beta.solana.com"
            retries = 0
            
            while retries < max_retries:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getSignatureStatuses",
                        "params": [[tx_hash]]
                    }) as response:
                        if response.status == 200:
                            result = await response.json()
                            status = result['result']['value'][0]
                            
                            if status is not None and status.get('confirmationStatus') == 'confirmed':
                                return True
                                
                await asyncio.sleep(1)
                retries += 1
                
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for confirmation: {str(e)}")
            return False
            
    async def analyze_token_metrics(self, token_address: str) -> dict:
        """Analizza le metriche di un token"""
        try:
            metrics = {
                'liquidity': 0,
                'holders': 0,
                'price_change_24h': 0,
                'volume_24h': 0,
                'market_cap': 0
            }
            
            # Ottieni dati da Birdeye
            url = f"{self.birdeye_api}/token/meta?address={token_address}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'x-api-key': self.birdeye_api_key}) as response:
                    if response.status == 200:
                        data = await response.json()
                        token_data = data.get('data', {})
                        
                        metrics.update({
                            'liquidity': float(token_data.get('liquidity', 0)),
                            'holders': int(token_data.get('holders', 0)),
                            'price_change_24h': float(token_data.get('priceChange24h', 0)),
                            'volume_24h': float(token_data.get('volume24h', 0)),
                            'market_cap': float(token_data.get('marketCap', 0))
                        })
                        
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing token metrics: {str(e)}")
            return {
                'liquidity': 0,
                'holders': 0,
                'price_change_24h': 0,
                'volume_24h': 0,
                'market_cap': 0
            }

    async def create_and_sign_transaction(self, instructions: list) -> Optional[Transaction]:
        """Crea e firma una transazione"""
        try:
            # Crea la transazione
            transaction = Transaction()
            for ix in instructions:
                transaction.add(ix)
                
            # Firma la transazione
            transaction.sign(self.keypair)
            return transaction
            
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}")
            return None
            
    async def send_transaction(self, transaction: Dict[str, Any]) -> Optional[str]:
        """Invia una transazione alla blockchain"""
        try:
            # Implementare la logica per inviare la transazione
            # Per ora è un placeholder
            return "transaction_signature"
        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            return None

    async def get_token_accounts(self) -> List[Dict[str, Any]]:
        try:
            response = await self.client.get_token_accounts_by_owner(
                self.keypair.pubkey(),
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}
            )
            return response.value if response.value else []
        except Exception as e:
            logger.error(f"Error getting token accounts: {str(e)}")
            return []

    async def get_sol_balance(self) -> float:
        """Get SOL balance for the wallet"""
        try:
            response = await self.client.get_balance(self.keypair.pubkey())
            balance_lamports = response.value
            return balance_lamports / 1e9  # Convert lamports to SOL
        except Exception as e:
            logger.error(f"Error getting SOL balance: {str(e)}")
            return 0.0

    async def get_token_balance(self, token_mint: str) -> float:
        """Get token balance for a specific mint"""
        try:
            # Convert string to Pubkey
            mint_pubkey = Pubkey.from_string(token_mint)
            owner_pubkey = self.keypair.pubkey()
            
            # Get ATA address
            ata = get_associated_token_address(owner_pubkey, mint_pubkey)
            
            # Get account info
            response = await self.client.get_token_account_balance(str(ata))
            
            if response.value is None:
                return 0.0
                
            amount = float(response.value.amount)
            decimals = response.value.decimals
            
            return amount / (10 ** decimals)
            
        except Exception as e:
            self.logger.error(f"Error getting token balance: {str(e)}")
            return 0.0

    async def execute_raydium_swap(self, 
                                input_token: str,
                                output_token: str,
                                amount: float,
                                slippage: float = 1.0) -> Optional[str]:
        """Esegue uno swap su Raydium"""
        try:
            # Ottieni la quotazione
            quote = await self.raydium.get_swap_quote(
                input_token,
                output_token,
                amount,
                slippage
            )
            
            if not quote:
                logger.error("Failed to get swap quote")
                return None
                
            # Crea la transazione di swap
            swap_tx = await self.raydium.create_swap_transaction(
                self.wallet_address,
                input_token,
                output_token,
                amount,
                slippage
            )
            
            if not swap_tx:
                logger.error("Failed to create swap transaction")
                return None
                
            # Firma la transazione
            transaction = await self.create_and_sign_transaction(swap_tx["instructions"])
            if not transaction:
                return None
                
            # Invia la transazione
            tx_hash = await self.send_transaction(transaction)
            return tx_hash
            
        except Exception as e:
            logger.error(f"Error executing Raydium swap: {str(e)}")
            return None

    async def get_token_balance(self, token_address: str) -> float:
        try:
            response = await self.client.get_token_account_balance(token_address)
            if response.value:
                return float(response.value.amount) / (10 ** response.value.decimals)
            return 0.0
        except Exception as e:
            logger.error(f"Error getting token balance: {str(e)}")
            return 0.0

    async def get_sol_balance(self) -> float:
        try:
            response = await self.client.get_balance(self.keypair.pubkey())
            if response.value:
                return float(response.value) / 1e9  # Convert lamports to SOL
            return 0.0
        except Exception as e:
            logger.error(f"Error getting SOL balance: {str(e)}")
            return 0.0

    async def send_transaction(self, transaction: Dict[str, Any]) -> Optional[str]:
        try:
            # Implementare la logica per inviare la transazione
            # Per ora è un placeholder
            return "transaction_signature"
        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            return None

    async def get_token_accounts(self) -> List[Dict[str, Any]]:
        try:
            response = await self.client.get_token_accounts_by_owner(
                self.keypair.pubkey(),
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}
            )
            return response.value if response.value else []
        except Exception as e:
            logger.error(f"Error getting token accounts: {str(e)}")
            return []

    async def check_token_account_exists(self, token_mint: str) -> bool:
        """Check if ATA exists for a token"""
        try:
            mint_pubkey = Pubkey.from_string(token_mint)
            owner_pubkey = self.keypair.pubkey()
            ata = get_associated_token_address(owner_pubkey, mint_pubkey)
            
            response = await self.client.get_account_info(ata)
            return response.value is not None
            
        except Exception as e:
            logger.error(f"Error checking token account: {str(e)}")
            return False
