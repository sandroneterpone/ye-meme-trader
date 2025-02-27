"""
Token models and data structures.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

@dataclass
class TokenMetrics:
    """Token metrics and analytics data."""
    creation_time: int
    age_minutes: int
    initial_price: Decimal
    current_price: Decimal
    price_change_pct: Decimal
    volume_24h: Decimal
    liquidity_sol: Decimal
    holders_count: int
    transactions_count: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenMetrics":
        """Create TokenMetrics from dictionary data."""
        return cls(
            creation_time=int(data["creation_time"]),
            age_minutes=int(data["age_minutes"]),
            initial_price=Decimal(str(data["initial_price"])),
            current_price=Decimal(str(data["current_price"])),
            price_change_pct=Decimal(str(data["price_change_pct"])),
            volume_24h=Decimal(str(data["volume_24h"])),
            liquidity_sol=Decimal(str(data["liquidity_sol"])),
            holders_count=int(data["holders_count"]),
            transactions_count=int(data["transactions_count"])
        )

@dataclass
class Token:
    """Represents a Solana token with its metadata."""
    address: str
    name: str
    symbol: str
    decimals: int
    total_supply: int
    metrics: Optional[TokenMetrics] = None
    
    @property
    def age(self) -> Optional[int]:
        """Get token age in minutes."""
        if self.metrics and self.metrics.creation_time:
            return self.metrics.age_minutes
        return None

    @property
    def price_change(self) -> Optional[Decimal]:
        """Get price change percentage."""
        if self.metrics:
            return self.metrics.price_change_pct
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Token":
        """Create Token from dictionary data."""
        metrics_data = data.get("metrics")
        metrics = TokenMetrics.from_dict(metrics_data) if metrics_data else None
        
        return cls(
            address=data["address"],
            name=data["name"],
            symbol=data["symbol"],
            decimals=int(data["decimals"]),
            total_supply=int(data["total_supply"]),
            metrics=metrics
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Token to dictionary."""
        result = {
            "address": self.address,
            "name": self.name,
            "symbol": self.symbol,
            "decimals": self.decimals,
            "total_supply": self.total_supply,
        }
        
        if self.metrics:
            result["metrics"] = {
                "creation_time": self.metrics.creation_time,
                "age_minutes": self.metrics.age_minutes,
                "initial_price": str(self.metrics.initial_price),
                "current_price": str(self.metrics.current_price),
                "price_change_pct": str(self.metrics.price_change_pct),
                "volume_24h": str(self.metrics.volume_24h),
                "liquidity_sol": str(self.metrics.liquidity_sol),
                "holders_count": self.metrics.holders_count,
                "transactions_count": self.metrics.transactions_count
            }
            
        return result
