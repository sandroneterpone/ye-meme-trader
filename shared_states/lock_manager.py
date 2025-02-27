import fcntl
import json
import time
from pathlib import Path

class FileLockManager:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.lock_file = self.file_path.with_suffix('.lock')
        self.fd = None

    def __enter__(self):
        """Acquisisce il lock sul file"""
        self.fd = open(self.lock_file, 'w')
        while True:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except IOError:
                time.sleep(0.1)  # Aspetta 100ms prima di riprovare
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Rilascia il lock"""
        if self.fd:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            self.fd.close()

class StateManager:
    def __init__(self, state_file="bot_state.json"):
        self.state_file = Path(__file__).parent / state_file
        self.ensure_state_file()

    def ensure_state_file(self):
        """Crea il file di stato se non esiste"""
        if not self.state_file.exists():
            initial_state = {
                "notifications": [],
                "active_trades": [],
                "balance": 0,
                "last_update": "",
                "bot_status": "stopped"
            }
            self.save_state(initial_state)

    def save_state(self, state):
        """Salva lo stato con lock"""
        with FileLockManager(self.state_file):
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

    def load_state(self):
        """Carica lo stato con lock"""
        with FileLockManager(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)