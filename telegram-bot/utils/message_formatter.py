from datetime import datetime

class MessageFormatter:
    @staticmethod
    def format_price(price):
        """Formatta il prezzo con il numero giusto di decimali"""
        if price < 0.00000001:
            return f"${price:.10f}"
        elif price < 0.0000001:
            return f"${price:.9f}"
        elif price < 0.000001:
            return f"${price:.8f}"
        else:
            return f"${price:.7f}"

    @staticmethod
    def format_large_number(number):
        """Formatta numeri grandi con K, M, B"""
        if number >= 1_000_000_000:
            return f"{number/1_000_000_000:.1f}B"
        elif number >= 1_000_000:
            return f"{number/1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number/1_000:.1f}K"
        return str(number)

    @staticmethod
    def format_time_ago(timestamp):
        """Formatta il tempo trascorso in stile ghetto"""
        diff = datetime.now() - datetime.fromisoformat(timestamp)
        minutes = diff.total_seconds() / 60
        
        if minutes < 1:
            return "PROPRIO ORA FAM! 🔥"
        elif minutes < 60:
            return f"{int(minutes)}min FA"
        elif minutes < 1440:
            hours = int(minutes / 60)
            return f"{hours}h FA"
        else:
            days = int(minutes / 1440)
            return f"{days}d FA"