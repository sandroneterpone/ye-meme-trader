"""
Trade-related models and data structures.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any

class TradeType(Enum):
    """Type of trade."""
    BUY = "buy"
    SELL = "sell"

class TradeStatus(Enum):
    """Status of a trade."""
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TradeParams:
    """Parameters for a trade."""
    amount_in: Decimal
    amount_out: Decimal
    price_impact: Decimal
    minimum_out: Decimal
    route: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeParams":
        """Create TradeParams from dictionary data."""
        return cls(
            amount_in=Decimal(str(data["amount_in"])),
            amount_out=Decimal(str(data["amount_out"])),
            price_impact=Decimal(str(data["price_impact"])),
            minimum_out=Decimal(str(data["minimum_out"])),
            route=data["route"]
        )

@dataclass
class Trade:
    """Represents a trade transaction."""
    id: str
    token_address: str
    type: TradeType
    amount_sol: Decimal
    timestamp: datetime
    status: TradeStatus
    params: Optional[TradeParams] = None
    transaction_hash: Optional[str] = None
    error_message: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trade":
        """Create Trade from dictionary data."""
        params_data = data.get("params")
        params = TradeParams.from_dict(params_data) if params_data else None
        
        return cls(
            id=data["id"],
            token_address=data["token_address"],
            type=TradeType(data["type"]),
            amount_sol=Decimal(str(data["amount_sol"])),
            timestamp=datetime.fromtimestamp(data["timestamp"]),
            status=TradeStatus(data["status"]),
            params=params,
            transaction_hash=data.get("transaction_hash"),
            error_message=data.get("error_message")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Trade to dictionary."""
        result = {
            "id": self.id,
            "token_address": self.token_address,
            "type": self.type.value,
            "amount_sol": str(self.amount_sol),
            "timestamp": int(self.timestamp.timestamp()),
            "status": self.status.value,
        }
        
        if self.params:
            result["params"] = {
                "amount_in": str(self.params.amount_in),
                "amount_out": str(self.params.amount_out),
                "price_impact": str(self.params.price_impact),
                "minimum_out": str(self.params.minimum_out),
                "route": self.params.route
            }
            
        if self.transaction_hash:
            result["transaction_hash"] = self.transaction_hash
            
        if self.error_message:
            result["error_message"] = self.error_message
            
        return result
