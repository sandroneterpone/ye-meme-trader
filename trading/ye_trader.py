import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class YeMemeTrader:
    def __init__(self):
        load_dotenv()
        self.wallet_address = os.getenv("WALLET_ADDRESS")
        self.max_concurrent_trades = int(os.getenv("MAX_CONCURRENT_TRADES", "3"))
        self.stop_loss_percentage = float(os.getenv("STOP_LOSS_PERCENTAGE", "15"))
        self.take_profit_percentage = float(os.getenv("TAKE_PROFIT_PERCENTAGE", "50"))
        self.initial_investment = float(os.getenv("INITIAL_INVESTMENT", "0.1"))  # in SOL
        
        # Load shared state
        self.shared_state_file = "shared_data/shared_state.json"
        self.load_shared_state()
        
    def load_shared_state(self):
        """Load shared state from file"""
        try:
            if os.path.exists(self.shared_state_file):
                with open(self.shared_state_file, 'r') as f:
                    self.shared_state = json.load(f)
            else:
                self.shared_state = {
                    "memecoin_trovate": [],
                    "saldo_wallet": {"sol": 0.0, "usd": 0.0},
                    "trade": {
                        "active_trades": [],
                        "pending_trades": []
                    },
                    "prof_e_perd": {
                        "total_profit_sol": 0.0,
                        "total_profit_usd": 0.0,
                        "trades_history": []
                    }
                }
                self.save_shared_state()
        except Exception as e:
            logger.error(f"Error loading shared state: {str(e)}")
            raise
            
    def save_shared_state(self):
        """Save shared state to file"""
        try:
            os.makedirs(os.path.dirname(self.shared_state_file), exist_ok=True)
            with open(self.shared_state_file, 'w') as f:
                json.dump(self.shared_state, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving shared state: {str(e)}")
            
    async def place_trade(self, token_info):
        """Place a trade for a token"""
        if len(self.shared_state["trade"]["active_trades"]) >= self.max_concurrent_trades:
            logger.info("Maximum concurrent trades reached")
            return False
            
        trade = {
            "token_address": token_info["address"],
            "token_symbol": token_info["symbol"],
            "entry_price": token_info["price"],
            "amount_sol": self.initial_investment,
            "stop_loss": token_info["price"] * (1 - self.stop_loss_percentage/100),
            "take_profit": token_info["price"] * (1 + self.take_profit_percentage/100),
            "timestamp": datetime.now().isoformat()
        }
        
        self.shared_state["trade"]["active_trades"].append(trade)
        self.save_shared_state()
        
        logger.info(f"Placed trade for {token_info['symbol']} at {token_info['price']}")
        return True
        
    async def update_trades(self, current_prices):
        """Update active trades based on current prices"""
        for trade in self.shared_state["trade"]["active_trades"][:]:  # Copy list to avoid modification during iteration
            current_price = current_prices.get(trade["token_address"])
            if not current_price:
                continue
                
            # Check stop loss
            if current_price <= trade["stop_loss"]:
                await self.close_trade(trade, current_price, "stop_loss")
                continue
                
            # Check take profit
            if current_price >= trade["take_profit"]:
                await self.close_trade(trade, current_price, "take_profit")
                
    async def close_trade(self, trade, current_price, reason):
        """Close a trade and update profit/loss"""
        profit_sol = (current_price - trade["entry_price"]) * trade["amount_sol"]
        
        trade_result = {
            **trade,
            "exit_price": current_price,
            "profit_sol": profit_sol,
            "reason": reason,
            "close_timestamp": datetime.now().isoformat()
        }
        
        # Update totals
        self.shared_state["prof_e_perd"]["total_profit_sol"] += profit_sol
        self.shared_state["prof_e_perd"]["trades_history"].append(trade_result)
        
        # Remove from active trades
        self.shared_state["trade"]["active_trades"].remove(trade)
        
        self.save_shared_state()
        
        logger.info(f"Closed trade for {trade['token_symbol']} with profit {profit_sol:.4f} SOL")
