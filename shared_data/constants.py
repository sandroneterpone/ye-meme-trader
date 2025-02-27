"""
Shared constants between trading bot and Telegram bot.
"""

# Redis key prefixes
REDIS_KEYS = {
    "TRADE_SIGNAL": "trade_signal:",
    "TOKEN_INFO": "token:",
    "TRADE_ACTIVE": "trade:active:",
    "TRADE_ACTION": "trade_action:",
    "TRADING_STATUS": "trading_status",
    "BALANCE_INFO": "balance_info",
    "TRADING_SETTINGS": "trading_settings"
}

# Trade actions
TRADE_ACTIONS = {
    "CANCEL": "cancel",
    "TAKE_PROFIT": "take_profit",
    "STOP_LOSS": "stop_loss"
}

# Trading status
TRADING_STATUS = {
    "ACTIVE": "active",
    "INACTIVE": "inactive",
    "ERROR": "error"
}

# Notification types
NOTIFICATION_TYPES = {
    "NEW_TRADE": "new_trade",
    "TRADE_EXECUTED": "trade_executed",
    "TRADE_FAILED": "trade_failed",
    "POSITION_UPDATE": "position_update",
    "TRADE_CLOSED": "trade_closed",
    "ERROR": "error"
}

# Error codes
ERROR_CODES = {
    "INSUFFICIENT_FUNDS": "insufficient_funds",
    "PRICE_IMPACT_TOO_HIGH": "price_impact_too_high",
    "EXECUTION_FAILED": "execution_failed",
    "INVALID_TOKEN": "invalid_token",
    "API_ERROR": "api_error"
}

# Trade types
TRADE_TYPES = {
    "BUY": "buy",
    "SELL": "sell"
}

# Position status
POSITION_STATUS = {
    "OPEN": "open",
    "CLOSED": "closed",
    "PENDING": "pending",
    "CANCELLED": "cancelled"
}

# Time constants
TIME_CONSTANTS = {
    "TRADE_SIGNAL_EXPIRY": 3600,  # 1 hour
    "TRADE_ACTION_EXPIRY": 300,   # 5 minutes
    "POSITION_UPDATE_INTERVAL": 60,  # 1 minute
    "PRICE_UPDATE_INTERVAL": 5     # 5 seconds
}
