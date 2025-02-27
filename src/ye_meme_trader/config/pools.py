"""
Known DEX pools and token addresses.
"""
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Pool:
    name: str
    address: str
    token_address: str
    description: Optional[str] = None
    tags: List[str] = None

# Popular Meme Token Pools
MEME_POOLS = {
    "PUMPFUN": Pool(
        name="PUMPFUN",
        address="PUMPFuNE1syYPr6eqPe3FNqV4gEXrVFCrD5WEXVS6K",
        token_address="PUMPFuNE1syYPr6eqPe3FNqV4gEXrVFCrD5WEXVS6K",
        description="PumpFun - The Ultimate Meme Token",
        tags=["meme", "pump", "fun"]
    ),
    "MEMEFAST": Pool(
        name="MEMEFAST",
        address="MEMEFASTjjjkkk1111111111111111111111111111",  # Replace with actual address
        token_address="MEMEFASTjjjkkk1111111111111111111111111111",  # Replace with actual address
        description="MemeFast - Speed of Memes",
        tags=["meme", "fast"]
    ),
    "MGMN": Pool(
        name="MGMN",
        address="MGMNmgmn22222222222222222222222222222222222",  # Replace with actual address
        token_address="MGMNmgmn22222222222222222222222222222222222",  # Replace with actual address
        description="MGMN Token",
        tags=["meme", "mgmn"]
    ),
    "AI": Pool(
        name="AI",
        address="AIaiaiaiaia33333333333333333333333333333333",  # Replace with actual address
        token_address="AIaiaiaiaia33333333333333333333333333333333",  # Replace with actual address
        description="AI Pool",
        tags=["ai", "tech"]
    )
}

# Ye/Kanye Related Token Keywords
YE_KEYWORDS = [
    "ye",
    "kanye",
    "west",
    "yeezy",
    "pablo",
    "donda",
    "graduation",
    "808s",
    "dropout",
    "kardashian"
]

# Blacklisted Tokens
BLACKLISTED_TOKENS = [
    # Add any tokens you want to avoid
]

# Minimum Pool Requirements
MIN_POOL_REQUIREMENTS = {
    "liquidity_usd": 50000,  # $50k minimum liquidity
    "holders": 100,          # Minimum number of holders
    "age_hours": 1,         # Minimum pool age in hours
    "max_price_impact": 2.0  # Maximum price impact in percentage
}
