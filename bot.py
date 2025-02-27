import os
import logging
import asyncio
import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler
import fcntl
import sys
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

from trading.solana_scanner import SolanaScanner
from trading.auto_trader import AutoTrader
from trading.ye_meme_trader import YeMemeTrader

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Constants
LOCK_FILE = "/tmp/yebot.lock"

# Set timezone
timezone = pytz.timezone('Europe/Rome')

class YeBot:
    def __init__(self, scanner, auto_trader):
        logger.info("Initializing YeBot...")
        try:
            self.scanner = scanner
            self.auto_trader = auto_trader
            self.start_time = datetime.now()
            self.telegram_app = None
            logger.info("YeBot initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing YeBot: {e}")
            raise

    async def send_notification(self, message):
        """Send notification via Telegram"""
        if self.telegram_app and TELEGRAM_CHAT_ID:
            try:
                await self.telegram_app.bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=message
                )
            except Exception as e:
                logger.error(f"Failed to send notification: {str(e)}")

    async def notify_trade_opportunity(self, token_info):
        """Notify about a new trade opportunity"""
        message = (
            f"🚨 NEW YE TOKEN ALERT! 🚨\n\n"
            f"Token: {token_info['name']}\n"
            f"Symbol: {token_info['symbol']}\n"
            f"Price: ${token_info['price']:.6f}\n"
            f"24h Volume: ${token_info['volume_24h']:,.2f}\n"
            f"Market Cap: ${token_info['market_cap']:,.2f}\n"
            f"Holders: {token_info['holders']}\n\n"
            f"Contract: {token_info['address']}"
        )
        await self.send_notification(message)

    async def start_auto_trading(self):
        """Start the auto trading process"""
        try:
            logger.info("Starting auto trading...")
            await self.auto_trader.start_auto_trading()
        except Exception as e:
            logger.error(f"Error in auto trading: {str(e)}")
            raise

def acquire_lock():
    """Try to acquire a lock file to prevent multiple instances"""
    try:
        lock_fp = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fp
    except IOError:
        return None

async def get_wallet_balance():
    try:
        wallet_address = os.getenv("WALLET_ADDRESS")
        pubkey = Pubkey.from_string(wallet_address)
        async with AsyncClient("https://api.mainnet-beta.solana.com") as client:
            response = await client.get_balance(pubkey)
            balance = float(response.value) / 1_000_000_000  # Convert lamports to SOL
            return balance
    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}")
        return 0.0

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send current wallet balance"""
    balance = await get_wallet_balance()
    await update.message.reply_text(
        f"💰 Cash nel Wallet rn: {balance:.4f} SOL\n"
        f"🏦 Il tuo indirizzo zio: {os.getenv('WALLET_ADDRESS')}\n\n"
        "Siamo pronti per shoppare token no cap 🔥"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    await update.message.reply_text(
        "Yo fratm, ecco i comandi:\n\n"
        "/balance - Vedi quanto cash hai nel wallet\n"
        "/help - Ti spiego come funziona sta roba\n\n"
        "Sto sempre a cercare nuovi token di Ye che pompano, trust 💯"
    )

async def test_swap_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test uno swap con un piccolo importo"""
    try:
        # Token di test: BONK (uno dei token meme più liquidi)
        test_token = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
        amount = 0.01  # 0.01 SOL
        
        msg = await update.message.reply_text("🧪 Testing swap...\n\n0.01 SOL ➡️ BONK")
        
        # Esegui lo swap
        result = await context.bot_data['bot'].auto_trader.trader.execute_order(
            token_address=test_token,
            side="buy",
            amount=amount
        )
        
        if result["success"]:
            await msg.edit_text(
                f"✅ Test swap completato!\n\n"
                f"TX: https://solscan.io/tx/{result['tx_hash']}\n"
                f"Amount: {amount} SOL\n"
                f"Price: ${result['price']:.6f}\n"
            )
        else:
            await msg.edit_text(f"❌ Test swap fallito:\n{result['error']}")
            
    except Exception as e:
        logger.error(f"Error in test swap: {str(e)}")
        await update.message.reply_text(f"❌ Errore: {str(e)}")

def main():
    """Start the bot."""
    try:
        # Try to acquire lock
        lock_fp = acquire_lock()
        if not lock_fp:
            logger.error("Another instance is already running")
            sys.exit(1)
        
        logger.info("Starting bot initialization...")
        
        async def start_bot():
            try:
                # Initialize bot components
                scanner = SolanaScanner()
                trader = YeMemeTrader()
                auto_trader = AutoTrader(trader=trader, scanner=scanner)
                bot = YeBot(scanner, auto_trader)
                
                # Initialize Telegram app
                app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
                
                # Add command handlers
                app.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("🚀 YO FRATM, IL BOT È PARTITO SKRRT!")))
                app.add_handler(CommandHandler("help", help_command))
                app.add_handler(CommandHandler("balance", balance_command))
                app.add_handler(CommandHandler("test_swap", test_swap_command))
                
                bot.telegram_app = app
                
                # Store bot instance in bot_data
                app.bot_data['bot'] = bot
                
                # Start the bot
                await app.initialize()
                await app.start()
                
                # Send startup message
                balance = await get_wallet_balance()
                startup_msg = (
                    "🚀 YO FRATM, IL BOT È PARTITO SKRRT!\n\n"
                    f"💰 Cash nel Wallet: {balance:.4f} SOL\n\n"
                    "A caccia del prossimo token di Ye che pompa 100x no cap fr fr 🔥"
                )
                await app.bot.send_message(chat_id=os.getenv("TELEGRAM_CHAT_ID"), text=startup_msg)
                
                # Start trading
                await bot.start_auto_trading()
            except Exception as e:
                logger.error(f"Error in bot tasks: {e}")
                if 'app' in locals():
                    await app.stop()
                raise
            finally:
                logger.info("Shutting down bot...")
                if 'app' in locals():
                    await app.shutdown()
                # Release lock file
                fcntl.flock(lock_fp, fcntl.LOCK_UN)
                lock_fp.close()

        # Run the bot
        asyncio.run(start_bot())

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error in main: {e}")
        raise

if __name__ == '__main__':
    main()