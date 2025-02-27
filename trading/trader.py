import os
import logging
from datetime import datetime
from .solana_client import SolanaClient
from .risk_analyzer import RiskAnalyzer
from .price_fetcher import PriceFetcher

logger = logging.getLogger(__name__)

class YeMemeTrader:
    def __init__(self):
        self.risk_analyzer = RiskAnalyzer()
        self.solana_client = SolanaClient()
        self.price_fetcher = PriceFetcher()
        
        # Trading parameters
        self.base_trade_amount = 10.0  # Base trade amount in USD
        self.min_trade_amount = 5.0    # Minimum trade amount in USD
        self.max_trade_amount = 15.0   # Maximum trade amount in USD
        
    def calculate_position_size(self, risk_score):
        """Calculate position size based on risk score (1-10)"""
        if risk_score >= 8:
            return self.min_trade_amount  # High risk, use minimum ($5)
        elif risk_score <= 3:
            return self.max_trade_amount  # Low risk, use maximum ($15)
        return self.base_trade_amount     # Medium risk, use base ($10)
    
    async def analyze_token(self, token_address):
        """Analyze token for potential scam indicators"""
        try:
            # Get token metrics from Birdeye
            metrics = await self.solana_client.analyze_token_metrics(token_address)
            if not metrics:
                return 10, {"error": "Couldn't fetch token metrics"}
            
            # Get token info from Solscan
            token_info = await self.solana_client.get_token_info(token_address)
            
            scam_indicators = {
                'liquidity_analysis': metrics['liquidity'] / float(os.getenv('MIN_LIQUIDITY', 1000.0)),
                'holder_distribution': metrics['holders'] / int(os.getenv('MIN_HOLDERS', 50)),
                'price_volatility': abs(metrics['price_change_24h']) / float(os.getenv('MAX_PRICE_CHANGE', 0.50)),
                'contract_verified': 1 if token_info.get('verified', False) else 0,
                'social_sentiment': await self._analyze_social_sentiment(token_address)
            }
            
            risk_score = self.risk_analyzer.calculate_risk_score(scam_indicators)
            return risk_score, scam_indicators
            
        except Exception as e:
            logger.error(f"Error analyzing token: {str(e)}")
            return 10, {"error": str(e)}
    
    async def execute_trade(self, token_address, amount_usd, side='buy'):
        """Execute a trade with safety checks"""
        try:
            # Get current SOL price
            sol_price = await self.price_fetcher.get_sol_price()
            if not sol_price:
                logger.warning("Using default SOL price")
                sol_price = float(os.getenv('SOL_TO_USD_RATE', 20.0))
            
            # Convert USD amount to SOL
            amount_sol = amount_usd / sol_price
            logger.info(f"Converting ${amount_usd} to {amount_sol} SOL (rate: ${sol_price}/SOL)")

            # Pre-trade checks
            risk_score, indicators = await self.analyze_token(token_address)
            if risk_score > float(os.getenv('RISK_SCORE_THRESHOLD', 7.0)):
                logger.warning(f"Risk score too high ({risk_score}) for {token_address}")
                return False, "Risk too high fam, we ain't gambling like that! 🚫"
            
            # Check minimum trade requirements
            metrics = await self.solana_client.analyze_token_metrics(token_address)
            if metrics:
                if metrics['liquidity'] < float(os.getenv('MIN_LIQUIDITY', 1000.0)):
                    return False, "Liquidity too low fam, we need more juice! 💧"
                    
                if metrics['volume_24h'] < float(os.getenv('MIN_VOLUME_USD', 10000.0)):
                    return False, "Volume too low bruh, we need more action! 📊"
            
            # Get quote from Jupiter
            quote = await self.solana_client.get_jupiter_quote(
                "So11111111111111111111111111111111111111112",  # SOL mint
                token_address,
                int(amount_sol * 1e9)  # Convert to lamports
            )
            
            if not quote:
                return False, "Couldn't get a quote from Jupiter! 😤"
            
            # Check slippage
            if quote.get('slippage', 0) > float(os.getenv('MAX_SLIPPAGE', 30.0)):
                return False, "Slippage too high fam, we ain't getting rekt! 🛑"
            
            # In a real implementation, we would execute the trade here
            # For now, we'll just simulate success
            success = True
            
            if success:
                return True, f"Successfully {'bought' if side == 'buy' else 'sold'} token for {amount_usd}$! 🚀"
            else:
                return False, "Trade failed! 😤"
            
        except Exception as e:
            logger.error(f"Trade execution error: {str(e)}")
            return False, f"Trade failed: {str(e)}"
    
    async def execute_order(self, token_address: str, side: str, amount_usd: float = None, amount: float = None) -> dict:
        """Esegue un ordine di acquisto o vendita"""
        try:
            # Verifica i parametri
            if not amount_usd and not amount:
                raise ValueError("Must specify either amount_usd or amount")
                
            # Ottieni il prezzo corrente
            current_price = await self.solana_client.get_token_price(token_address)
            if not current_price:
                raise ValueError("Could not get current price")
                
            # Se specificato amount_usd, calcola la quantità di token
            if amount_usd:
                amount = amount_usd / current_price
                
            # Ottieni la migliore route da Jupiter
            route = await self.solana_client.get_jupiter_quote(
                input_mint="So11111111111111111111111111111111111111112" if side == "buy" else token_address,
                output_mint=token_address if side == "buy" else "So11111111111111111111111111111111111111112",
                amount=amount
            )
            
            if not route:
                raise ValueError("Could not find a valid route")
                
            # Verifica lo slippage
            price_impact = float(route.get('priceImpactPct', 0)) * 100
            max_impact = float(os.getenv('MAX_PRICE_IMPACT', 2.0))
            if price_impact > max_impact:
                raise ValueError(f"Price impact too high: {price_impact}% > {max_impact}%")
                
            # Esegui la transazione
            tx = await self.solana_client.execute_jupiter_swap(route)
            if not tx['success']:
                raise ValueError(f"Transaction failed: {tx.get('error', 'Unknown error')}")
                
            return {
                'success': True,
                'price': current_price,
                'amount': amount,
                'side': side,
                'impact': price_impact,
                'tx_hash': tx['txHash']
            }
            
        except Exception as e:
            logger.error(f"Error executing {side} order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def calculate_price_impact(self, token_address: str, amount_usd: float) -> float:
        """Calcola l'impatto sul prezzo per un dato ammontare"""
        try:
            # Ottieni il prezzo corrente
            current_price = await self.solana_client.get_token_price(token_address)
            if not current_price:
                raise ValueError("Could not get current price")
                
            # Calcola la quantità di token
            amount = amount_usd / current_price
            
            # Ottieni la route da Jupiter per calcolare l'impatto
            route = await self.solana_client.get_jupiter_quote(
                input_mint="So11111111111111111111111111111111111111112",
                output_mint=token_address,
                amount=amount
            )
            
            if not route:
                raise ValueError("Could not calculate price impact")
                
            return float(route.get('priceImpactPct', 0)) * 100
            
        except Exception as e:
            logger.error(f"Error calculating price impact: {str(e)}")
            return float('inf')  # Ritorna infinito in caso di errore
            
    async def get_token_liquidity(self, token_address: str) -> dict:
        """Ottiene informazioni sulla liquidità del token"""
        try:
            # Ottieni liquidità da vari DEX
            liquidity_info = await self.solana_client.get_token_liquidity(token_address)
            
            # Aggiungi informazioni aggiuntive
            token_info = await self.solana_client.get_token_info(token_address)
            
            return {
                **liquidity_info,
                'holders': token_info.get('holders', 0),
                'market_cap': token_info.get('market_cap', 0),
                'volume_24h': token_info.get('volume24h', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting token liquidity: {str(e)}")
            return {
                'total_liquidity_usd': 0,
                'dexes': {},
                'holders': 0,
                'market_cap': 0,
                'volume_24h': 0
            }
            
    async def _analyze_social_sentiment(self, token_address: str) -> float:
        """Analizza il sentiment sociale per un token"""
        try:
            # Implementa l'analisi del sentiment usando i dati da Twitter e Discord
            # Per ora ritorna un valore casuale tra 0 e 1
            return 0.5
            
        except Exception as e:
            logger.error(f"Error analyzing social sentiment: {str(e)}")
            return 0.0
