import httpx
from config import *

class APIClients:
    def __init__(self):
        # Birdeye API
        self.birdeye = httpx.Client(
            base_url=BIRDEYE_API_URL,
            headers={"x-api-key": BIRDEYE_API_KEY}
        )
        
        # Solscan API
        self.solscan = httpx.Client(
            base_url=SOLSCAN_API_URL,
            headers={"token": SOLSCAN_API_KEY}
        )
        
        # Jupiter API
        self.jupiter = httpx.Client(
            base_url=JUPITER_API_URL
        )
        
        # Raydium API
        self.raydium = httpx.Client(
            base_url=RAYDIUM_API_URL
        )
        
        # CoinMarketCap API
        self.coinmarketcap = httpx.Client(
            base_url="https://pro-api.coinmarketcap.com",
            headers={"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
        )
        
        # CryptoCompare API
        self.cryptocompare = httpx.Client(
            base_url="https://min-api.cryptocompare.com",
            headers={"authorization": f"Apikey {CRYPTOCOMPARE_API_KEY}"}
        )
        
        # LunarCrush API
        self.lunarcrush = httpx.Client(
            base_url="https://lunarcrush.com/api/v2",
            headers={"authorization": LUNARCRUSH_API_KEY}
        )
        
        # CryptoPanic API
        self.cryptopanic = httpx.Client(
            base_url="https://cryptopanic.com/api/v1",
            params={"auth_token": CRYPTOPANIC_API_KEY}
        )

    def close_all(self):
        """Chiude tutte le sessioni HTTP"""
        self.birdeye.close()
        self.solscan.close()
        self.jupiter.close()
        self.raydium.close()
        self.coinmarketcap.close()
        self.cryptocompare.close()
        self.lunarcrush.close()
        self.cryptopanic.close()