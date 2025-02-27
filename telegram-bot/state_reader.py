import json
import os
from datetime import datetime

class StateReader:
    def __init__(self):
        self.state_file = "../shared_state/bot_state.json"
        
    def read_state(self):
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading state: {e}")
            return None
            
    def get_new_notifications(self, last_check=None):
        state = self.read_state()
        if not state:
            return []
            
        notifications = state.get("notifications", [])
        if last_check:
            return [n for n in notifications if datetime.fromisoformat(n["timestamp"]) > last_check]
        return notifications
        
    def get_active_trades(self):
        state = self.read_state()
        if not state:
            return []
        return state.get("active_trades", [])
        
    def get_balance(self):
        state = self.read_state()
        if not state:
            return 0
        return state.get("balance", 0)
        
    def get_bot_status(self):
        state = self.read_state()
        if not state:
            return "unknown"
        return state.get("bot_status", "unknown")