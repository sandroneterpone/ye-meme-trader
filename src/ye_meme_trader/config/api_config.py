"""
API configuration and endpoints.
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class APIConfig:
    """Base API configuration."""
    api_key: str
    base_url: str
    headers: Optional[dict] = None

# Birdeye API Config
BIRDEYE_CONFIG = APIConfig(
    api_key=os.getenv("BIRDEYE_API_KEY"),
    base_url="https://public-api.birdeye.so/v1",
    headers={
        "x-api-key": os.getenv("BIRDEYE_API_KEY")
    }
)

# Solscan API Config
SOLSCAN_CONFIG = APIConfig(
    api_key=os.getenv("SOLSCAN_API_KEY"),
    base_url="https://public-api.solscan.io",
    headers={
        "token": os.getenv("SOLSCAN_API_KEY")
    }
)

# Jupiter API Config
JUPITER_CONFIG = APIConfig(
    api_key=None,  # No API key needed
    base_url="https://quote-api.jup.ag/v6"
)

# Social Media APIs
TWITTER_CONFIG = APIConfig(
    api_key=os.getenv("TWITTER_BEARER_TOKEN"),
    base_url="https://api.twitter.com/2",
    headers={
        "Authorization": f"Bearer {os.getenv('TWITTER_BEARER_TOKEN')}"
    }
)

REDDIT_CONFIG = APIConfig(
    api_key=os.getenv("REDDIT_CLIENT_SECRET"),
    base_url="https://oauth.reddit.com",
    headers={
        "User-Agent": os.getenv("REDDIT_USER_AGENT")
    }
)

# Market Data APIs
COINMARKETCAP_CONFIG = APIConfig(
    api_key=os.getenv("COINMARKETCAP_API_KEY"),
    base_url="https://pro-api.coinmarketcap.com/v1",
    headers={
        "X-CMC_PRO_API_KEY": os.getenv("COINMARKETCAP_API_KEY")
    }
)

CRYPTOCOMPARE_CONFIG = APIConfig(
    api_key=os.getenv("CRYPTOCOMPARE_API_KEY"),
    base_url="https://min-api.cryptocompare.com/data",
    headers={
        "authorization": f"Apikey {os.getenv('CRYPTOCOMPARE_API_KEY')}"
    }
)

# Sentiment Analysis APIs
LUNARCRUSH_CONFIG = APIConfig(
    api_key=os.getenv("LUNARCRUSH_API_KEY"),
    base_url="https://lunarcrush.com/api/v2",
    headers={
        "Authorization": f"Bearer {os.getenv('LUNARCRUSH_API_KEY')}"
    }
)

CRYPTOPANIC_CONFIG = APIConfig(
    api_key=os.getenv("CRYPTOPANIC_API_KEY"),
    base_url="https://cryptopanic.com/api/v1",
    headers={
        "Authorization": f"Bearer {os.getenv('CRYPTOPANIC_API_KEY')}"
    }
)

# API Endpoints
class BirdeyeEndpoints:
    """Birdeye API endpoints."""
    TOKEN_PRICE = "/defi/price"
    TOKEN_INFO = "/defi/token_info"
    TOKEN_HOLDERS = "/defi/token_holders"
    TOKEN_POOLS = "/defi/token_pools"
    MULTI_PRICE = "/defi/multi_price"

class SolscanEndpoints:
    """Solscan API endpoints."""
    TOKEN_HOLDERS = "/token/holders"
    TOKEN_META = "/token/meta"
    TOKEN_PRICE = "/token/price"
    ACCOUNT_TOKENS = "/account/tokens"
    TRANSACTION = "/transaction"

class JupiterEndpoints:
    """Jupiter API endpoints."""
    QUOTE = "/quote"
    SWAP = "/swap"
    PRICE = "/price"
    TOKENS = "/tokens"

class TwitterEndpoints:
    """Twitter API endpoints."""
    SEARCH_TWEETS = "/tweets/search/recent"
    USER_TWEETS = "/tweets"
    USER_BY_USERNAME = "/users/by/username"

class RedditEndpoints:
    """Reddit API endpoints."""
    SEARCH = "/search"
    SUBREDDIT = "/r/{subreddit}"
    HOT = "/hot"
    NEW = "/new"
