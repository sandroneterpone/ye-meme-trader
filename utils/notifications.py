import os
import logging
import random
import asyncio
from datetime import datetime
from typing import Dict, Optional, List, Any
from .ghetto_messages import get_ghetto_message

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, app=None):
        self.app = app
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.notification_queue = asyncio.Queue()
        self.retries = 3
        self.retry_delay = 2  # seconds
        self.last_notification = None
        self.notification_history: List[Dict[str, Any]] = []
        
    async def _send_message_with_retry(self, message: str) -> bool:
        """Send a message to Telegram with retry logic"""
        if not self.app or not self.chat_id:
            logger.error("Telegram app or chat_id not configured")
            return False
            
        for attempt in range(self.retries):
            try:
                await self.app.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='HTML'  # Enable HTML formatting
                )
                self._log_notification(message)
                return True
            except Exception as e:
                logger.error(f"Error sending Telegram message (attempt {attempt + 1}/{self.retries}): {e}")
                if attempt < self.retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
        return False
        
    def _log_notification(self, message: str) -> None:
        """Log notification for history and analytics"""
        self.notification_history.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'type': self._get_notification_type(message)
        })
        self.last_notification = message
        
    def _get_notification_type(self, message: str) -> str:
        """Determine notification type from message content"""
        if '🚀 YE BOT ONLINE!' in message:
            return 'startup'
        elif 'OPENING NEW TRADE!' in message:
            return 'trade_open'
        elif 'CLOSING TRADE!' in message:
            return 'trade_close'
        elif 'NEW YE COIN ALERT!' in message:
            return 'opportunity'
        return 'other'

    async def send_message(self, message: str) -> None:
        """Queue a message for sending"""
        await self.notification_queue.put(message)
        await self._process_queue()
        
    async def _process_queue(self) -> None:
        """Process queued notifications"""
        while not self.notification_queue.empty():
            message = await self.notification_queue.get()
            success = await self._send_message_with_retry(message)
            if not success:
                logger.error(f"Failed to send message after {self.retries} attempts")

    async def bot_start(self, wallet_address: str) -> None:
        """Send enhanced bot startup notification"""
        msg = get_ghetto_message('bot_start', {
            'wallet': wallet_address[:8] + '...',
            'time': datetime.now().strftime('%H:%M:%S'),
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        await self.send_message(msg)
        
    async def bot_shutdown(self, trades_closed: int, total_profit: float) -> None:
        """Send enhanced bot shutdown notification"""
        session_stats = self._get_session_stats()
        msg = get_ghetto_message('bot_shutdown', {
            'trades_closed': trades_closed,
            'total_profit': round(total_profit, 2),
            'win_rate': session_stats['win_rate'],
            'best_trade': session_stats['best_trade']
        })
        await self.send_message(msg)
        
    def _get_session_stats(self) -> Dict[str, Any]:
        """Calculate session statistics"""
        trades = [n for n in self.notification_history if n['type'] in ['trade_open', 'trade_close']]
        if not trades:
            return {'win_rate': 0, 'best_trade': 0}
            
        wins = len([t for t in trades if t['type'] == 'trade_close' and 'profit' in t['message']])
        total_trades = len([t for t in trades if t['type'] == 'trade_close'])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'win_rate': round(win_rate, 2),
            'best_trade': self._get_best_trade()
        }
        
    def _get_best_trade(self) -> float:
        """Get the best trade profit from history"""
        trade_profits = []
        for n in self.notification_history:
            if n['type'] == 'trade_close' and 'profit' in n['message']:
                try:
                    profit_str = n['message'].split('Profit: $')[1].split('\n')[0]
                    trade_profits.append(float(profit_str))
                except:
                    continue
        return max(trade_profits) if trade_profits else 0
        
    async def new_opportunity(self, token_name: str, risk_score: float, trade_size: float) -> None:
        """Send enhanced opportunity notification"""
        potential = self._calculate_potential(risk_score)
        msg = get_ghetto_message('opportunity', {
            'coin': token_name,
            'risk': round(risk_score, 2),
            'trade_size': round(trade_size, 2),
            'potential': potential,
            'confidence': self._get_confidence_emoji(risk_score)
        })
        await self.send_message(msg)
        
    def _calculate_potential(self, risk_score: float) -> int:
        """Calculate potential return based on risk score"""
        base_potential = random.randint(2, 10)
        risk_multiplier = max(1, (10 - risk_score) / 2)
        return int(base_potential * risk_multiplier)
        
    def _get_confidence_emoji(self, risk_score: float) -> str:
        """Get confidence emoji based on risk score"""
        if risk_score <= 3:
            return "💎 ULTRA BULLISH"
        elif risk_score <= 5:
            return "🚀 BULLISH"
        elif risk_score <= 7:
            return "⚠️ CAREFUL"
        return "💀 RISKY"
        
    async def trade_opened(self, token_name: str, entry_price: float, size: float, risk: float) -> None:
        """Send enhanced trade opened notification"""
        msg = get_ghetto_message('trade_open', {
            'coin': token_name,
            'entry': round(entry_price, 6),
            'size': round(size, 2),
            'risk': round(risk, 2),
            'time': datetime.now().strftime('%H:%M:%S'),
            'confidence': self._get_confidence_emoji(risk)
        })
        await self.send_message(msg)
        
    async def trade_closed(self, token_name: str, entry: float, exit_price: float, 
                          profit: float, return_percent: float) -> None:
        """Send enhanced trade closed notification"""
        hold_time = self._calculate_hold_time(token_name)
        msg = get_ghetto_message('trade_close', {
            'coin': token_name,
            'entry': round(entry, 6),
            'exit': round(exit_price, 6),
            'profit': round(profit, 2),
            'return_percent': round(return_percent, 2),
            'hold_time': hold_time,
            'performance': self._get_performance_emoji(return_percent)
        })
        await self.send_message(msg)
        
    def _calculate_hold_time(self, token_name: str) -> str:
        """Calculate how long we held the trade"""
        open_time = None
        close_time = datetime.now()
        
        for n in reversed(self.notification_history):
            if n['type'] == 'trade_open' and token_name in n['message']:
                open_time = datetime.fromisoformat(n['timestamp'])
                break
                
        if not open_time:
            return "unknown"
            
        delta = close_time - open_time
        minutes = delta.total_seconds() / 60
        
        if minutes < 60:
            return f"{int(minutes)}m"
        else:
            hours = minutes / 60
            return f"{int(hours)}h {int(minutes % 60)}m"
            
    def _get_performance_emoji(self, return_percent: float) -> str:
        """Get performance emoji based on return percentage"""
        if return_percent >= 100:
            return "🌟 LEGENDARY"
        elif return_percent >= 50:
            return "🔥 FIRE"
        elif return_percent >= 20:
            return "💪 SOLID"
        elif return_percent > 0:
            return "✅ PROFIT"
        else:
            return "❌ LOSS"
        
    async def trade_status(self, trades: Dict[str, Any]) -> None:
        """Send enhanced active trades status"""
        if not trades:
            await self.send_message("🚫 No active trades rn fam! We stay ready tho! 💯")
            return
            
        trades_msg = "🔥 CURRENT TRADES IN DA HOOD 🔥\n\n"
        for trade_id, trade in trades.items():
            trade['hold_time'] = self._calculate_hold_time(trade['coin'])
            trade['performance'] = self._get_performance_emoji(trade.get('pl', 0))
            trades_msg += get_ghetto_message('trade_status', trade)
            
        await self.send_message(trades_msg)
        
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics for analytics"""
        return {
            'total_notifications': len(self.notification_history),
            'by_type': self._count_by_type(),
            'last_notification': self.last_notification,
            'session_stats': self._get_session_stats()
        }
        
    def _count_by_type(self) -> Dict[str, int]:
        """Count notifications by type"""
        counts = {}
        for n in self.notification_history:
            n_type = n['type']
            counts[n_type] = counts.get(n_type, 0) + 1
        return counts
