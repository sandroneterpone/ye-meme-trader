from solana.rpc.api import Client
import time
from datetime import datetime
from .config import *
from .api_clients import APIClients
from .utils.state_manager import StateManager

class SolanaScanner:
    def __init__(self):
        self.http_client = Client(SOLANA_API_URL)
        self.api = APIClients()
        self.state_manager = StateManager()
        self.last_scan_time = None

    def get_token_balance(self, wallet_address):
        """Ottiene il saldo SOL del wallet"""
        try:
            balance = self.http_client.get_balance(wallet_address)
            balance_sol = balance['result']['value'] / 1e9
            self.state_manager.update_balance(balance_sol)
            return balance_sol
        except Exception as e:
            print(f"Error getting balance: {e}")
            return None

    def get_token_info(self, token_address):
        """Ottiene informazioni dettagliate sul token da multiple fonti"""
        try:
            # Birdeye - Informazioni base e prezzo
            birdeye_info = self.api.birdeye.get(
                f"/token/meta/{token_address}"
            ).json()
            
            birdeye_price = self.api.birdeye.get(
                f"/token/price/{token_address}"
            ).json()

            # Solscan - Informazioni aggiuntive
            solscan_info = self.api.solscan.get(
                f"/token/meta/{token_address}"
            ).json()

            # Raydium - Informazioni sulla liquidità
            raydium_pools = self.api.raydium.get(
                f"/pools"
            ).json()
            
            # Trova il pool Raydium per questo token
            token_pool = next(
                (p for p in raydium_pools if p.get("token_address") == token_address),
                None
            )

            # Combina le informazioni
            token_info = {
                "address": token_address,
                "name": birdeye_info["name"],
                "symbol": birdeye_info["symbol"],
                "price": birdeye_price["value"],
                "market_cap": birdeye_price["marketCap"],
                "volume_24h": birdeye_price["volume24h"],
                "holders": solscan_info["holder"],
                "creation_time": solscan_info["createdTime"],
                "liquidity": token_pool["liquidity"] if token_pool else 0,
                "price_change_24h": birdeye_price.get("priceChange24h", 0),
                "verified": solscan_info.get("verified", False)
            }

            # Social Sentiment Analysis
            try:
                # LunarCrush sentiment
                lunar_data = self.api.lunarcrush.get(
                    "/assets",
                    params={"symbol": token_info["symbol"]}
                ).json()
                
                if lunar_data.get("data"):
                    token_info["social_score"] = lunar_data["data"][0]["social_score"]
                    token_info["social_volume"] = lunar_data["data"][0]["social_volume"]
                
                # CryptoPanic news
                news = self.api.cryptopanic.get(
                    "/posts/",
                    params={"currencies": token_info["symbol"]}
                ).json()
                
                token_info["news_sentiment"] = self._analyze_news_sentiment(news)
                
            except Exception as e:
                print(f"Error getting social data: {e}")
                token_info["social_score"] = 0
                token_info["news_sentiment"] = 0

            return token_info
            
        except Exception as e:
            print(f"Error getting token info: {e}")
            return None

    def _analyze_news_sentiment(self, news_data):
        """Analizza il sentiment delle news"""
        if not news_data.get("results"):
            return 0
            
        sentiment_score = 0
        for news in news_data["results"][:10]:  # Ultimi 10 articoli
            if news["votes"]["positive"] > news["votes"]["negative"]:
                sentiment_score += 1
            elif news["votes"]["negative"] > news["votes"]["positive"]:
                sentiment_score -= 1
                
        return sentiment_score / 10  # Normalizza tra -1 e 1

    def is_ye_token(self, token_info):
        """Verifica se il token è correlato a Ye"""
        name_lower = token_info["name"].lower()
        symbol_lower = token_info["symbol"].lower()
        
        # Controlla le keywords
        for keyword in YE_KEYWORDS:
            if keyword in name_lower or keyword in symbol_lower:
                return True
                
        # Controlla anche le news per riferimenti a Ye
        if token_info.get("news_sentiment"):
            news_text = " ".join([n["title"].lower() for n in token_info.get("news", [])])
            for keyword in YE_KEYWORDS:
                if keyword in news_text:
                    return True
                    
        return False

    def calculate_potential_score(self, token_info):
        """Calcola uno score per il potenziale del token"""
        score = 0
        
        # Età del token (max 20 punti)
        age_minutes = (datetime.now() - datetime.fromtimestamp(token_info["creation_time"])).total_seconds() / 60
        if age_minutes <= 5:
            score += 20
        elif age_minutes <= 30:
            score += 10
        
        # Market Cap (max 20 punti)
        if token_info["market_cap"] < 100000:  # < $100k
            score += 20
        elif token_info["market_cap"] < 500000:  # < $500k
            score += 15
        elif token_info["market_cap"] < 1000000:  # < $1M
            score += 10
            
        # Liquidità (max 15 punti)
        if token_info["liquidity"] >= MIN_LIQUIDITY_USD:
            score += 15
            
        # Holders (max 15 punti)
        if token_info["holders"] >= MIN_HOLDERS:
            score += 15
            
        # Social Score (max 15 punti)
        if token_info.get("social_score", 0) > 0:
            score += min(15, token_info["social_score"] / 100)
            
        # News Sentiment (max 15 punti)
        if token_info.get("news_sentiment", 0) > 0:
            score += token_info["news_sentiment"] * 15
            
        return score

    def is_potential_moonshot(self, token_info):
        """Verifica se il token ha potenziale di crescita esplosiva"""
        try:
            # Calcola l'età in minuti
            creation_time = datetime.fromtimestamp(token_info["creation_time"])
            age_minutes = (datetime.now() - creation_time).total_seconds() / 60
            
            # Deve essere nuovo (< 5 minuti)
            if age_minutes > 5:
                return False
                
            # Verifica liquidità minima
            if token_info["liquidity"] < MIN_LIQUIDITY_USD:
                return False
                
            # Verifica holders minimi
            if token_info["holders"] < MIN_HOLDERS:
                return False
                
            # Calcola potenziale score
            potential_score = self.calculate_potential_score(token_info)
            if potential_score < 70:  # Richiede almeno 70/100 punti
                return False
                
            # Calcola potenziale moltiplicatore
            market_cap = token_info["market_cap"]
            if market_cap < 100000:  # < $100k
                potential = 1000
            elif market_cap < 500000:  # < $500k
                potential = 500
            elif market_cap < 1000000:  # < $1M
                potential = 100
            else:
                potential = 50
                
            token_info["potential_multiplier"] = potential
            token_info["age_minutes"] = age_minutes
            token_info["potential_score"] = potential_score
            
            return True
            
        except Exception as e:
            print(f"Error in moonshot analysis: {e}")
            return False

    def scan_new_tokens(self):
        """Scansiona per nuovi token"""
        try:
            current_time = time.time()
            
            if not self.last_scan_time or (current_time - self.last_scan_time) >= SCAN_INTERVAL:
                self.last_scan_time = current_time
                
                # Get new tokens from multiple sources
                interesting_tokens = []
                
                # Birdeye - New tokens
                new_tokens = self.api.birdeye.get("/token/list").json()["data"]
                
                for token in new_tokens:
                    token_info = self.get_token_info(token["address"])
                    if not token_info:
                        continue
                        
                    if self.is_ye_token(token_info) and self.is_potential_moonshot(token_info):
                        interesting_tokens.append(token_info)
                        # Notifica opportunità
                        self.state_manager.add_notification("golden_opportunity", token_info)
                
                return interesting_tokens
                
        except Exception as e:
            print(f"Error scanning tokens: {e}")
            return []

    def __del__(self):
        """Cleanup delle risorse"""
        self.api.close_all()