"""
Configuration settings for the Ye Meme Token Trading Bot.
"""
import os
from decimal import Decimal

# Solana Configuration
SOLANA_CONFIG = {
    "network_url": os.getenv("SOLANA_NETWORK_URL", "https://api.mainnet-beta.solana.com"),
    "ws_url": os.getenv("SOLANA_WS_URL", "wss://api.mainnet-beta.solana.com"),
    "wallet_key": os.getenv("PHANTOM_BASE58_KEY", ""),
}

# Redis Configuration
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
}

# API Configuration
API_CONFIG = {
    # Birdeye API
    "birdeye_api_url": "https://public-api.birdeye.so/v1",
    "birdeye_api_key": os.getenv("BIRDEYE_API_KEY", ""),
    
    # DexScreener API
    "dexscreener_api_url": "https://api.dexscreener.com/latest/dex",
    
    # Solscan API
    "solscan_api_url": "https://public-api.solscan.io",
    "solscan_api_key": os.getenv("SOLSCAN_API_KEY", ""),
    
    # Jupiter API
    "jupiter_api_url": "https://quote-api.jup.ag/v4",
    "jupiter_slippage_bps": 100,  # 1%
    "default_token": "So11111111111111111111111111111111111111112",  # Wrapped SOL
}

# Token Filtering Configuration
TOKEN_FILTERS = {
    "min_name_length": 3,
    "max_name_length": 32,
    "name_keywords": [
        "ye", "kanye", "west", "yeezy", "pablo", "donda",
        "graduation", "808s", "yeezus", "dropout"
    ],
    "excluded_keywords": [
        "scam", "rug", "fake", "test", "honeypot"
    ],
}

# Trading Configuration
TRADING_CONFIG = {
    # Budget Settings
    "usd_budget": Decimal("20.0"),  # Total budget in USD
    "min_trade_amount_sol": Decimal("0.1"),  # Minimum trade size
    "max_trade_amount_sol": Decimal("5.0"),  # Maximum trade size
    
    # Token Age Requirements
    "min_age_minutes": 30,
    "max_age_minutes": 24 * 60,  # 24 hours
    
    # Liquidity Requirements
    "min_liquidity_sol": Decimal("5.0"),
    "target_liquidity_sol": Decimal("50.0"),
    
    # Price Requirements
    "min_price_increase_pct": Decimal("10.0"),
    "max_price_impact_pct": Decimal("3.0"),
    
    # Trading Parameters
    "min_trade_confidence": 0.7,
    "min_ye_relevance_score": 0.5,
    
    # Position Management
    "take_profit_pct": Decimal("50.0"),
    "stop_loss_pct": Decimal("-15.0"),
    "trailing_stop_pct": Decimal("10.0"),
    
    # Budget Management
    "max_single_trade_pct": Decimal("50.0"),  # Maximum % of budget for single trade
    "min_remaining_budget_pct": Decimal("20.0"),  # Minimum % of budget to keep
}

# Telegram Bot Configuration
TELEGRAM_CONFIG = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}
