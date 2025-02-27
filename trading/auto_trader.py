import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from solders.keypair import Keypair
from solana.rpc.api import Client
from .solana_client import SolanaClient
from .jupiter_client import JupiterClient

logger = logging.getLogger(__name__)

@dataclass
class TradeConfig:
    max_concurrent_trades: int = 3
    min_holders: int = 100
    stop_loss: float = -15.0
    take_profit: float = 50.0

class AutoTrader:
    def __init__(self, keypair: Keypair, client: Client, test_mode: bool = True):
        self.keypair = keypair
        self.client = client
        self.test_mode = test_mode
        self.solana_client = SolanaClient(keypair, client)
        self.jupiter_client = JupiterClient(keypair, client, test_mode)
        self.logger = logging.getLogger(__name__)
        self.active_trades: Dict[str, dict] = {}
        self.trade_history: List[dict] = []
        self.config = TradeConfig()
        self.last_scan_time = datetime.min
        self.scan_interval = int(os.getenv('TRADE_INTERVAL', 300))  # 5 minuti
        self.logger.info(f"AutoTrader initialized in {'TEST' if test_mode else 'LIVE'} mode")
        
    async def start_auto_trading(self):
        """Avvia il trading automatico"""
        try:
            while True:
                await self.scan_and_trade()
                await asyncio.sleep(self.scan_interval)
        except Exception as e:
            logger.error(f"Error in auto trading loop: {str(e)}")
            
    async def scan_and_trade(self):
        """Scansiona per nuove opportunità e esegue trades"""
        try:
            logger.info("Starting scan for new trading opportunities...")
            
            # Cerca nuovi token
            tokens = await self.scan_tokens("ye")
            logger.info(f"Found {len(tokens)} potential tokens")
            
            valid_tokens = []
            for token in tokens:
                # Verifica i criteri base
                if not await self._validate_token(token):
                    continue
                    
                price = await self.check_token_price(token["address"])
                if price > 0:
                    token["price"] = price
                    valid_tokens.append(token)
                    logger.info(f"Found valid token: {token['symbol']} at price {price}")
                
            # Ordina i token per volume decrescente
            valid_tokens.sort(key=lambda x: x.get("volume", 0), reverse=True)
            
            # Controlla se possiamo fare nuovi trade
            if len(self.active_trades) >= self.config.max_concurrent_trades:
                logger.info("Maximum concurrent trades reached")
                return
                
            # Prendi i migliori token
            for token in valid_tokens[:3]:  # Prova con i top 3 token
                if token["address"] not in self.active_trades:
                    logger.info(f"Attempting to place trade for {token['symbol']}")
                    if await self.open_position(token["address"], 100.0):
                        self.active_trades[token["address"]] = token
                        logger.info(f"Successfully placed trade for {token['symbol']}")
                    
            # Aggiorna i trade esistenti
            await self._update_active_trades()
            
        except Exception as e:
            logger.error(f"Error in scan and trade: {str(e)}")
            
    async def _validate_token(self, token):
        """Valida un token per il trading"""
        try:
            address = token.get("address")
            if not address:
                return False
                
            # Controlla il numero di holders
            holders = await self.solana_client.get_token_holders(address)
            logger.info(f"Token {token.get('symbol')}: {holders} holders")
            
            if holders < self.config.min_holders:
                logger.info(f"Token {token.get('symbol')} rejected: insufficient holders ({holders})")
                return False
                
            # Controlla se il token è già in un trade attivo
            if address in self.active_trades:
                logger.info(f"Token {token.get('symbol')} rejected: already in active trade")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error validating token {token.get('symbol')}: {str(e)}")
            return False
            
    async def _update_active_trades(self):
        """Aggiorna lo stato dei trade attivi"""
        try:
            current_prices = {}
            for address in self.active_trades.keys():
                price = await self.check_token_price(address)
                current_prices[address] = price
                
            # Aggiorna la lista dei trade attivi
            self.active_trades = {
                address: trade for address, trade in self.active_trades.items()
                if address in current_prices
            }
            
            # Monitora le posizioni aperte
            for address, trade in self.active_trades.items():
                await self.monitor_position(
                    address,
                    trade['price'],
                    trade['price'] * (1 + self.config.stop_loss/100),
                    trade['price'] * (1 + self.config.take_profit/100)
                )
                
        except Exception as e:
            logger.error(f"Error updating active trades: {str(e)}")
            
    async def check_token_price(self, token_mint: str) -> float:
        """Get current token price in USDC"""
        try:
            USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            quote = await self.jupiter_client.get_quote(
                input_mint=token_mint,
                output_mint=USDC_MINT,
                amount=1.0  # 1 token
            )
            return float(quote['outAmount']) / 1e6  # Convert from USDC decimals
        except Exception as e:
            self.logger.error(f"Error checking token price: {str(e)}")
            return 0.0

    async def open_position(self, token_mint: str, amount_usdc: float) -> bool:
        """Open a new position by swapping USDC for token"""
        try:
            USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            
            # Check price impact
            price_impact = await self.jupiter_client.get_price_impact(
                input_mint=USDC_MINT,
                output_mint=token_mint,
                amount=amount_usdc
            )
            
            if price_impact > 5.0:  # 5% threshold
                raise Exception(f"Price impact too high: {price_impact}%")
            
            # Execute swap USDC -> Token
            tx_hash = await self.jupiter_client.swap(
                input_mint=USDC_MINT,
                output_mint=token_mint,
                amount=amount_usdc
            )
            
            self.logger.info(f"Opened position with tx: {tx_hash}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening position: {str(e)}")
            return False

    async def close_position(self, token_mint: str, amount: float) -> str:
        """Close an existing position by swapping token back to USDC"""
        try:
            USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            
            # Check price impact before swap
            price_impact = await self.jupiter_client.get_price_impact(
                input_mint=token_mint,
                output_mint=USDC_MINT,
                amount=amount
            )
            
            if price_impact > 5.0:  # 5% threshold
                raise Exception(f"Price impact too high: {price_impact}%")
            
            # Execute swap Token -> USDC
            tx_hash = await self.jupiter_client.swap(
                input_mint=token_mint,
                output_mint=USDC_MINT,
                amount=amount
            )
            
            self.logger.info(f"Closed position with tx: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            self.logger.error(f"Error closing position: {str(e)}")
            raise

    async def monitor_position(self, 
                             token_mint: str,
                             entry_price: float,
                             stop_loss: float,
                             take_profit: float) -> None:
        """Monitor an open position for stop loss or take profit"""
        try:
            while True:
                current_price = await self.check_token_price(token_mint)
                
                # Check stop loss
                if current_price <= stop_loss:
                    self.logger.info(f"Stop loss triggered at {current_price}")
                    await self.close_position(token_mint, 1.0)  # Close entire position
                    break
                    
                # Check take profit    
                if current_price >= take_profit:
                    self.logger.info(f"Take profit triggered at {current_price}")
                    await self.close_position(token_mint, 1.0)  # Close entire position
                    break
                    
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except Exception as e:
            self.logger.error(f"Error monitoring position: {str(e)}")
            raise

    async def scan_tokens(self, prefix: str) -> List[dict]:
        """Scansiona per nuovi token"""
        try:
            # Implementazione della scansione dei token
            # Questa è solo una stub, sostituire con la logica di scansione reale
            return [
                {"address": "token1", "symbol": "TOKEN1"},
                {"address": "token2", "symbol": "TOKEN2"},
                {"address": "token3", "symbol": "TOKEN3"},
            ]
        except Exception as e:
            self.logger.error(f"Error scanning tokens: {str(e)}")
            return []