"""
Telegram bot service for notifications and commands.
"""
import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config.settings import TELEGRAM_CONFIG
import shared_data.constants as constants
from shared_data.redis_manager import RedisManager

logger = logging.getLogger(__name__)

class TelegramService:
    """Service for Telegram bot interactions."""
    
    def __init__(self):
        """Initialize the Telegram service."""
        self.bot = Application.builder().token(TELEGRAM_CONFIG["bot_token"]).build()
        self.chat_id = TELEGRAM_CONFIG["chat_id"]
        self.redis = RedisManager()
        
    async def setup(self):
        """Setup bot commands and handlers."""
        # Command handlers
        self.bot.add_handler(CommandHandler("status", self.cmd_status))
        self.bot.add_handler(CommandHandler("balance", self.cmd_balance))
        self.bot.add_handler(CommandHandler("trades", self.cmd_trades))
        self.bot.add_handler(CommandHandler("settings", self.cmd_settings))
        
        # Callback handlers
        self.bot.add_handler(CallbackQueryHandler(self.handle_callback))
        
    async def start(self):
        """Start the Telegram bot."""
        await self.setup()
        await self.bot.initialize()
        await self.bot.start()
        
        # Get initial balance
        balance = await self.redis.get_balance_info()
        sol_balance = balance.get('sol_balance', 0)
        usd_value = balance.get('usd_value', 0)
        
        startup_msg = f"""
🔥 YO YO YO, YE BOT IN DA HOUSE! 🔥

Wassup fam! Ya boi Ye Bot is up n' runnin' 🚀
Ready to make it rain on dem tokens! 💸

Current Stash:
💰 {sol_balance} SOL (${usd_value})

YEEZY SEASON APPROACHIN' 
WE BOUT TO GO CRAZY! 
LET'S GET THIS BREAD! 🍞

Type /help to see what ya boi can do for ya!
        """
        
        await self.bot.bot.send_message(
            chat_id=self.chat_id,
            text=startup_msg
        )
        
        logger.info("Telegram bot started")

    async def stop(self):
        """Stop the Telegram bot."""
        await self.bot.stop()
        await self.bot.shutdown()
        await self.redis.close()
        
    async def send_trade_notification(self, trade_data: Dict[str, Any]):
        """Send notification about new trade."""
        try:
            trade_type = trade_data["type"]
            token_address = trade_data["token_address"]
            amount_sol = trade_data["amount_sol"]
            
            token_info = await self.redis.get_token_info(token_address)
            token_name = token_info.get("name", "Unknown")
            token_symbol = token_info.get("symbol", "???")
            
            message = f"""
🚨 YO CHECK IT OUT FAM! NEW {trade_type.upper()} ALERT! 🚨

We bout to {trade_type.lower()} dis fire token:
🎯 {token_name} ({token_symbol})
💸 Droppin {amount_sol} SOL on it!
⚡ Confidence: {trade_data.get('confidence_score', 0):.2f}

STRAIGHT UP! NO CAP! 💯
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("Peep Token 👀", url=f"https://solscan.io/token/{token_address}"),
                    InlineKeyboardButton("Nah, Skip This ❌", callback_data=f"cancel_trade:{trade_data['id']}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error sending trade notification: {str(e)}")
            
    async def send_position_update(self, position_data: Dict[str, Any]):
        """Send update about position status."""
        try:
            token_address = position_data["token_address"]
            token_info = await self.redis.get_token_info(token_address)
            
            profit_loss = position_data.get("profit_loss_pct", 0)
            emoji = "📈🔥" if profit_loss >= 0 else "📉💀"
            
            status = "BUSSIN FR FR" if profit_loss >= 0 else "DOWN BAD"
            
            message = f"""
{emoji} YO CHECK THE MOVES {emoji}

Token: {token_info.get('name')} ({token_info.get('symbol')})
Status: {status}
P/L: {profit_loss:.2f}% {'SHEEEESH!' if profit_loss >= 20 else ''}

Entry: {position_data.get('entry_price')} SOL
Now: {position_data.get('current_price')} SOL

{'WE EATIN GOOD! 🍗' if profit_loss >= 0 else 'STAY STRONG FAM 💪'}
            """
            
            await self.bot.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
            
        except Exception as e:
            logger.error(f"Error sending position update: {str(e)}")
            
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        try:
            status = await self.redis.get_trading_status()
            budget_sol = await self.redis.get("trading_budget_sol")
            budget_usd = await self.redis.get("trading_budget_usd")
            
            message = f"""
👑 YE BOT STATUS CHECK 👑

Bot Status: {'🟢 BUSSIN' if status.get('is_active') else '🔴 DOWN BAD'}
Da Bag: ${budget_usd} (≈ {budget_sol} SOL)
Active Plays: {status.get('active_trades', 0)}
Total Moves: {status.get('total_trades', 0)}

{'WE GOING PLATINUM! 💿' if status.get('is_active') else 'WE NEED A COMEBACK! 🔄'}
            """
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error handling status command: {str(e)}")
            await update.message.reply_text("Ay fam, something ain't right 😤")
            
    async def cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command."""
        try:
            balance = await self.redis.get_balance_info()
            
            message = f"""
💰 STACKS ON DECK 💰

SOL: {balance.get('sol_balance', 0)} 
USD: ${balance.get('usd_value', 0)}
Ready to Deploy: {balance.get('available_sol', 0)} SOL
In da Game: {balance.get('in_trades_sol', 0)} SOL

{'BALLIN! 🏀' if float(balance.get('sol_balance', 0)) > 10 else 'STILL HUSTLIN! 💪'}
            """
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error handling balance command: {str(e)}")
            await update.message.reply_text("Can't check the bag rn fam 😤")

    async def cmd_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trades command."""
        try:
            # Get active trades from Redis
            trades = await self.redis.get_active_trades()
            
            if not trades:
                await update.message.reply_text("No active trades")
                return
                
            message = "🔄 Active Trades 🔄\n\n"
            for trade in trades:
                token_info = await self.redis.get_token_info(trade["token_address"])
                message += f"Token: {token_info.get('name')} ({token_info.get('symbol')})\n"
                message += f"Amount: {trade['amount_sol']} SOL\n"
                message += f"P/L: {trade.get('profit_loss_pct', 0):.2f}%\n\n"
                
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error handling trades command: {str(e)}")
            await update.message.reply_text("Error getting trades")
            
    async def cmd_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command."""
        try:
            # Get current settings from Redis
            settings = await self.redis.get_trading_settings()
            
            message = "⚙️ Trading Settings ⚙️\n\n"
            message += f"Min Trade: {settings.get('min_trade_amount_sol')} SOL\n"
            message += f"Max Trade: {settings.get('max_trade_amount_sol')} SOL\n"
            message += f"Take Profit: {settings.get('take_profit_pct')}%\n"
            message += f"Stop Loss: {settings.get('stop_loss_pct')}%\n"
            
            keyboard = [
                [InlineKeyboardButton("Edit Settings", callback_data="edit_settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error handling settings command: {str(e)}")
            await update.message.reply_text("Error getting settings")
            
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards."""
        try:
            query = update.callback_query
            data = query.data
            
            if data.startswith("cancel_trade:"):
                trade_id = data.split(":")[1]
                # Signal trade cancellation through Redis
                await self.redis.set_trade_action(trade_id, "cancel")
                await query.answer("Trade cancellation requested")
                await query.edit_message_text("Cancelling trade...")
                
            elif data == "edit_settings":
                # Show settings edit menu
                keyboard = [
                    [InlineKeyboardButton("Take Profit", callback_data="edit:take_profit")],
                    [InlineKeyboardButton("Stop Loss", callback_data="edit:stop_loss")],
                    [InlineKeyboardButton("Back", callback_data="settings_back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("Select setting to edit:", reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error handling callback: {str(e)}")
            await query.answer("Error processing request")
