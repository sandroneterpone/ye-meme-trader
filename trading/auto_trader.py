import os
import json
import asyncio
import logging
import base58
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from .raydium_client import RaydiumClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoTrader:
    def __init__(self, test_mode: bool = True):
        # Load environment variables
        load_dotenv()
        
        # Initialize Solana client
        self.client = AsyncClient("https://api.mainnet-beta.solana.com")
        
        # Load wallet from private key
        private_key = base58.b58decode(os.getenv("PRIVATE_KEY"))
        self.wallet = Keypair.from_bytes(private_key)
        
        # Initialize trading client
        self.trading_client = RaydiumClient(self.wallet, self.client, test_mode)
        
        # Token addresses
        self.sol_mint = "So11111111111111111111111111111111111111112"  # Native SOL mint
        
        # Trading parameters
        self.min_price_change = 0.02  # 2% minimum price change
        self.trade_amount = float(os.getenv("INITIAL_INVESTMENT", "0.1"))  # Trade amount in SOL
        self.slippage = 0.5  # 0.5% slippage
        self.min_holders = int(os.getenv("MIN_HOLDERS", "100"))  # Minimum number of holders
        self.min_liquidity = float(os.getenv("MIN_LIQUIDITY", "1000"))  # Minimum liquidity in SOL
        self.max_token_age = int(os.getenv("MAX_TOKEN_AGE", "600"))  # 10 minutes in seconds
        self.growth_targets = [50, 100, 1000, 10000]  # Potential growth targets (50x, 100x, etc)
        self.min_growth_potential = 50  # Minimum 50x potential
        
        # State
        self.active_trades = {}  # address -> {price, timestamp, etc}
        self.test_mode = test_mode
        self.last_scan = datetime.min
        self.scan_interval = 60  # Check every minute for new tokens
        
        # Circuit Breaker
        self.max_daily_trades = int(os.getenv("MAX_DAILY_TRADES", "10"))
        self.max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", "1.0"))  # Max 1 SOL loss per day
        self.daily_trades = 0
        self.daily_loss = 0.0
        self.last_reset = datetime.now()
        self.trading_enabled = True
        self.error_count = 0
        self.max_errors = 3
        self.last_error_time = datetime.min
        self.error_timeout = 300  # 5 minutes timeout after max errors
        
        # Emergency Stop
        self.emergency_stop = False
        self.stop_loss_triggered = False
        
        logger.info(f"AutoTrader initialized in {'TEST' if test_mode else 'LIVE'} mode")
        
    def reset_daily_limits(self):
        """Reset daily trading limits"""
        now = datetime.now()
        if now - self.last_reset > timedelta(days=1):
            self.daily_trades = 0
            self.daily_loss = 0.0
            self.last_reset = now
            self.error_count = 0
            logger.info("Daily limits reset")
            
    def check_circuit_breaker(self) -> bool:
        """Check if trading should be allowed"""
        try:
            self.reset_daily_limits()
            
            # Check emergency stop
            if self.emergency_stop:
                logger.warning("Emergency stop is active")
                return False
                
            # Check stop loss
            if self.stop_loss_triggered:
                logger.warning("Stop loss has been triggered")
                return False
            
            # Check daily limits
            if self.daily_trades >= self.max_daily_trades:
                logger.warning("Maximum daily trades reached")
                return False
                
            if self.daily_loss >= self.max_daily_loss:
                logger.warning("Maximum daily loss reached")
                self.stop_loss_triggered = True
                return False
                
            # Check error rate
            if self.error_count >= self.max_errors:
                if datetime.now() - self.last_error_time < timedelta(seconds=self.error_timeout):
                    logger.warning("Too many errors, waiting for timeout")
                    return False
                else:
                    self.error_count = 0
                    
            return self.trading_enabled
            
        except Exception as e:
            logger.error(f"Error in circuit breaker: {e}")
            return False
            
    def record_error(self):
        """Record an error occurrence"""
        self.error_count += 1
        self.last_error_time = datetime.now()
        
    def record_trade(self, profit_loss: float):
        """Record a trade and its P/L"""
        self.daily_trades += 1
        if profit_loss < 0:
            self.daily_loss += abs(profit_loss)
            
    def emergency_shutdown(self):
        """Trigger emergency shutdown"""
        self.emergency_stop = True
        self.trading_enabled = False
        logger.critical("EMERGENCY SHUTDOWN TRIGGERED")
        
    async def execute_trade(self, token_address: str, action: str):
        """Execute a trade (buy/sell token)"""
        if not self.check_circuit_breaker():
            logger.warning("Circuit breaker active, skipping trade")
            return
            
        try:
            # Check SOL balance before trading
            balance = await self.trading_client.get_sol_balance()
            if balance < self.trade_amount:
                logger.error(f"Insufficient balance: {balance} SOL")
                return
                
            # Execute trade with safety checks
            if action == "buy":
                # Additional pre-trade validation
                if not await self.validate_token({"address": token_address}):
                    logger.warning(f"Token {token_address} failed final validation")
                    return
                    
                result = await self.trading_client.buy_token(
                    token_address,
                    self.trade_amount,
                    self.slippage,
                    use_sol=True
                )
                
            elif action == "sell":
                result = await self.trading_client.sell_token(
                    token_address,
                    self.trade_amount,
                    self.slippage,
                    use_sol=True
                )
                
            # Record trade result
            if result:
                self.record_trade(result.get("profit_loss", 0))
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            self.record_error()
            
    async def scan_tokens(self) -> List[Dict]:
        """Cerca nuovi token legati a YE"""
        try:
            # TODO: Implementare la ricerca di token usando l'API di Jupiter o Raydium
            # Per ora restituiamo una lista di test
            return [
                {
                    "address": "token1",
                    "symbol": "YE",
                    "name": "Ye Token",
                    "holders": 150,
                    "liquidity": 5000,
                    "supply": 1000000,
                    "price": 0.01,
                    "creation_time": datetime.now().timestamp() - 300
                }
            ]
        except Exception as e:
            logger.error(f"Error scanning tokens: {e}")
            return []

    async def calculate_growth_potential(self, token: Dict) -> float:
        """Calcola il potenziale di crescita del token"""
        try:
            # Calcola il market cap attuale
            current_supply = token.get("supply", 0)
            current_price = token.get("price", 0)
            current_mcap = current_supply * current_price

            # Calcola il market cap massimo potenziale basato su token simili
            # Per ora usiamo un valore di esempio, ma dovremmo prendere dati reali
            max_potential_mcap = 100_000_000  # $100M come esempio

            # Calcola il potenziale di crescita
            growth_potential = max_potential_mcap / current_mcap if current_mcap > 0 else 0
            
            logger.info(f"Token {token['symbol']} growth potential: {growth_potential}x")
            logger.info(f"Current MCap: ${current_mcap:,.2f}")
            logger.info(f"Target MCap: ${max_potential_mcap:,.2f}")
            
            return growth_potential

        except Exception as e:
            logger.error(f"Error calculating growth potential: {e}")
            return 0

    async def validate_token(self, token: Dict) -> bool:
        """Valida un token secondo i nostri criteri"""
        try:
            # Verifica il nome/simbolo
            name = token.get("name", "").lower()
            symbol = token.get("symbol", "").lower()
            if not ("ye" in name or "ye" in symbol or "kanye" in name):
                return False

            # Verifica l'età del token
            creation_time = token.get("creation_time", 0)
            token_age = (datetime.now().timestamp() - creation_time)
            if token_age > self.max_token_age:
                logger.info(f"Token {symbol} rejected: too old ({token_age:.0f} seconds)")
                return False

            # Verifica il numero di holders
            if token.get("holders", 0) < self.min_holders:
                logger.info(f"Token {symbol} rejected: insufficient holders ({token.get('holders')})")
                return False

            # Verifica la liquidità
            if token.get("liquidity", 0) < self.min_liquidity:
                logger.info(f"Token {symbol} rejected: insufficient liquidity (${token.get('liquidity')})")
                return False

            # Verifica se è già in un trade attivo
            if token["address"] in self.active_trades:
                logger.info(f"Token {symbol} rejected: already in active trade")
                return False

            # Verifica il potenziale di crescita
            growth_potential = await self.calculate_growth_potential(token)
            if growth_potential < self.min_growth_potential:
                logger.info(f"Token {symbol} rejected: insufficient growth potential ({growth_potential}x)")
                return False

            logger.info(f"Found valid token: {symbol}")
            logger.info(f"Age: {token_age:.0f} seconds")
            logger.info(f"Growth potential: {growth_potential}x")
            return True

        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return False

    async def monitor_positions(self):
        """Monitora le posizioni aperte"""
        try:
            for token_address, trade in list(self.active_trades.items()):
                # Get current price
                quote = await self.trading_client.get_quote(
                    input_mint=token_address,
                    output_mint=self.sol_mint,
                    amount=trade["amount"],
                    slippage=self.slippage
                )
                
                if quote:
                    current_price = float(quote['outAmount']) / float(quote['inAmount'])
                    price_change = (current_price - trade["entry_price"]) / trade["entry_price"]
                    
                    logger.info(f"Token {token_address}:")
                    logger.info(f"Entry price: {trade['entry_price']:.6f}")
                    logger.info(f"Current price: {current_price:.6f}")
                    logger.info(f"Price change: {price_change*100:.2f}%")
                    
                    # Verifica i target di crescita
                    for target in self.growth_targets:
                        if price_change >= (target - 1):  # -1 perché 50x significa +4900%
                            logger.info(f" {target}x target reached! Selling...")
                            await self.execute_trade(token_address, "sell")
                            break
                    
                    # Sell if price drops significantly
                    if price_change <= -self.min_price_change:
                        logger.info(f"Price dropped by {abs(price_change)*100:.2f}%, selling")
                        await self.execute_trade(token_address, "sell")
                
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")

    async def trading_loop(self):
        """Main trading loop"""
        while True:
            try:
                now = datetime.now()
                
                # Scan for new tokens every minute
                if (now - self.last_scan).total_seconds() >= self.scan_interval:
                    logger.info("Scanning for new tokens...")
                    tokens = await self.scan_tokens()
                    
                    for token in tokens:
                        if await self.validate_token(token):
                            # Try to buy the token
                            await self.execute_trade(token["address"], "buy")
                    
                    self.last_scan = now
                
                # Monitor existing positions
                await self.monitor_positions()
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def start(self):
        """Start the trading bot"""
        logger.info("Starting trading bot...")
        await self.trading_loop()
    
    async def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping trading bot...")
        await self.client.close()