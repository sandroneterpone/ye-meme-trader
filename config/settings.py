"""
Configuration settings for the Ye Meme Token Trading Bot.
"""
import os
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Solana configuration
SOLANA_CONFIG: Dict[str, Any] = {
    "network_url": os.getenv("SOLANA_NETWORK_URL", "https://api.mainnet-beta.solana.com"),
    "ws_url": os.getenv("SOLANA_WS_URL", "wss://api.mainnet-beta.solana.com"),
    "wallet_key": os.getenv("PHANTOM_BASE58_KEY"),
}

# Jupiter DEX configuration
JUPITER_CONFIG: Dict[str, Any] = {
    "base_url": "https://quote-api.jup.ag/v6",
    "slippage_bps": 50,  # 0.5%
    "default_token": "So11111111111111111111111111111111111111112",  # SOL
}

# Redis configuration
REDIS_CONFIG: Dict[str, Any] = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
}

# Telegram configuration
TELEGRAM_CONFIG: Dict[str, Any] = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
}

# API configuration
API_CONFIG: Dict[str, Any] = {
    "birdeye": {
        "base_url": "https://public-api.birdeye.so",
        "api_key": os.getenv("BIRDEYE_API_KEY"),
    },
    "solscan": {
        "base_url": "https://public-api.solscan.io",
        "api_key": os.getenv("SOLSCAN_API_KEY"),
    },
    "twitter": {
        "api_key": os.getenv("TWITTER_API_KEY"),
        "api_secret": os.getenv("TWITTER_API_SECRET"),
        "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
        "access_secret": os.getenv("TWITTER_ACCESS_SECRET"),
    },
    "reddit": {
        "client_id": os.getenv("REDDIT_CLIENT_ID"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
        "user_agent": "YeMemeTrader/1.0",
    },
}

# Trading parameters
TRADING_CONFIG: Dict[str, Any] = {
    "min_liquidity_sol": 5.0,  # Minimum pool liquidity in SOL
    "max_price_impact_pct": 2.0,  # Maximum price impact percentage
    "min_age_minutes": 5,  # Minimum token age in minutes
    "max_age_minutes": 60,  # Maximum token age in minutes
    "min_holders": 10,  # Minimum number of token holders
    "min_price_increase_pct": 20.0,  # Minimum price increase percentage
    "trade_amount_sol": 0.1,  # Amount to trade in SOL
    "take_profit_pct": 50.0,  # Take profit percentage
    "stop_loss_pct": -20.0,  # Stop loss percentage
}

# Token filtering
TOKEN_FILTERS: Dict[str, Any] = {
    "name_keywords": ["ye", "yeezy", "kanye", "west"],
    "excluded_keywords": ["scam", "honeypot", "rug"],
    "min_name_length": 3,
    "max_name_length": 32,
}

# Logging configuration
LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "bot.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
}
