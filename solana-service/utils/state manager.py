import json
import os
from datetime import datetime

class StateManager:
    def __init__(self):
        self.state_file = "shared_state/bot_state.json"
        os.makedirs("shared_state", exist_ok=True)
        self.ensure_state_file()
    
    def ensure_state_file(self):
        if not os.path.exists(self.state_file):
            initial_state = {
                "notifications": [],
                "active_trades": [],
                "balance": 0,
                "last_update": "",
                "bot_status": "stopped"
            }
            self.save_state(initial_state)
    
    def save_state(self, state):
        with open(self.state_file, 'w') as f:
            json.dump(state, f)
    
    def load_state(self):
        with open(self.state_file, 'r') as f:
            return json.load(f)
    
    def add_notification(self, notification_type, data):
        state = self.load_state()
        notification = {
            "type": notification_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        state["notifications"].append(notification)
        self.save_state(state)
    
    def update_bot_status(self, status):
        state = self.load_state()
        state["bot_status"] = status
        state["last_update"] = datetime.now().isoformat()
        self.save_state(state)
    
    def update_balance(self, balance):
        state = self.load_state()
        state["balance"] = balance
        self.save_state(state)
    
    def update_active_trades(self, trades):
        state = self.load_state()
        state["active_trades"] = trades
        self.save_state(state)