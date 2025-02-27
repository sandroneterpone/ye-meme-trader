import os
from dotenv import load_dotenv
from datetime import timedelta

# Carica le variabili d'ambiente
load_dotenv()

# Environment
ENV = os.getenv("ENV", "dev")
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"

# Wallet Settings
PHANTOM_BASE58_KEY = os.getenv("PHANTOM_BASE58_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
TRADE_BUDGET = float(os.getenv("TRADE_BUDGET", 20.0))

# API Keys
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
CRYPTOCOMPARE_API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
DEXSCREENER_API_KEY = os.getenv("DEXSCREENER_API_KEY")

# Trading Settings
TRADE_INTERVAL = int(os.getenv("TRADE_INTERVAL", 300))  # 5 minuti
MAX_CONCURRENT_TRADES = int(os.getenv("MAX_CONCURRENT_TRADES", 3))
STOP_LOSS_PERCENTAGE = float(os.getenv("STOP_LOSS_PERCENTAGE", 15))
TAKE_PROFIT_PERCENTAGE = float(os.getenv("TAKE_PROFIT_PERCENTAGE", 50))
MIN_LIQUIDITY_USD = float(os.getenv("MIN_LIQUIDITY_USD", 50000))
MAX_PRICE_IMPACT = float(os.getenv("MAX_PRICE_IMPACT", 2.0))
MIN_HOLDERS = int(os.getenv("MIN_HOLDERS", 100))
MAX_WALLET_EXPOSURE = float(os.getenv("MAX_WALLET_EXPOSURE", 0.15))

# API Endpoints
JUPITER_API_URL = os.getenv("JUPITER_API_URL", "https://quote-api.jup.ag/v6")
RAYDIUM_API_URL = os.getenv("RAYDIUM_API_URL", "https://api.raydium.io/v2")
BIRDEYE_API_URL = os.getenv("BIRDEYE_API_URL", "https://public-api.birdeye.so/v1")
SOLSCAN_API_URL = os.getenv("SOLSCAN_API_URL", "https://public-api.solscan.io")

# DEX Settings
SLIPPAGE_BPS = int(os.getenv("SLIPPAGE_BPS", 50))  # 0.5%
GAS_ADJUSTMENT = float(os.getenv("GAS_ADJUSTMENT", 1.3))  # 30% extra per gas

# Token Analysis Settings
MIN_TOKEN_AGE_MINUTES = 0  # Token appena creati
MAX_TOKEN_AGE_MINUTES = 5  # Non più vecchi di 5 minuti
MIN_PRICE_CHANGE = 5.0  # 5% minimo di movimento
MIN_VOLUME_24H = 10000  # $10k minimo di volume
MAX_OWNER_PERCENTAGE = 20  # Max 20% in mano a un singolo wallet
MIN_SOCIAL_SCORE = 50  # Score minimo per sentiment social

# Risk Management
PORTFOLIO_STOP_LOSS = -25  # Stop loss del -25% sul portfolio totale
MAX_DRAWDOWN = -35  # Drawdown massimo consentito
RISK_PER_TRADE = 0.1  # 10% del budget per trade
MAX_DAILY_TRADES = 10  # Numero massimo di trade al giorno

# Scanning Settings
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", 300))
YE_KEYWORDS = ["ye", "yeezy", "kanye", "west", "pablo", "donda"]
VIRAL_KEYWORDS = ["pepe", "doge", "shib", "elon", "moon", "wojak", "chad", "meme"]

# Token Safety Checks
REQUIRED_LIQUIDITY_PAIRS = ["SOL", "USDC", "USDT"]
MIN_LP_AGE_HOURS = 1
MAX_TAX_PERCENTAGE = 10
MIN_VERIFIED_PAIRS = 2

# Position Sizing
POSITION_SIZES = {
    "MICRO": 0.05,  # 5% del budget
    "SMALL": 0.10,  # 10% del budget
    "MEDIUM": 0.15, # 15% del budget
    "LARGE": 0.20   # 20% del budget
}

# Take Profit Levels
TAKE_PROFIT_LEVELS = {
    "LEVEL_1": {"percentage": 25, "size": 0.25},  # Vendi 25% a +25%
    "LEVEL_2": {"percentage": 50, "size": 0.25},  # Vendi 25% a +50%
    "LEVEL_3": {"percentage": 100, "size": 0.25}, # Vendi 25% a +100%
    "MOON": {"percentage": 1000, "size": 0.25}    # Tieni 25% per 1000x
}

# Stop Loss Strategy
STOP_LOSS_STRATEGY = {
    "INITIAL": -15,           # Stop loss iniziale
    "BREAKEVEN": 25,         # Muovi a breakeven a +25%
    "TRAILING_ACTIVATION": 35, # Attiva trailing stop a +35%
    "TRAILING_DISTANCE": 20   # Distanza trailing stop 20%
}

# Time Windows
TIME_WINDOWS = {
    "PRICE_CHECK": timedelta(minutes=5),
    "VOLUME_CHECK": timedelta(hours=24),
    "HOLDER_CHECK": timedelta(hours=1),
    "SOCIAL_CHECK": timedelta(hours=12)
}

# Error Handling
MAX_RETRIES = 3  # Numero massimo di tentativi per le API calls
RETRY_DELAY = 1  # Secondi di attesa tra i tentativi

# Monitoring
SENTRY_DSN = os.getenv("SENTRY_DSN")

# Redis Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Social Media Monitoring
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Discord Settings
DISCORD_CHANNELS = [
    "573903561680248842", "892397103311761408", "845378638728355840",
    "597638925346930704", "758764017189797902", "784642064400556052",
    "428295358100013068", "813876321033297974", "899995315323494434",
    "858510655570198571"
]

# Telegram Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
