import asyncio
import json
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SHARED_STATE_PATH = Path("../shared_data/shared_state.json")
CHECK_INTERVAL = 60  # secondi per il check del saldo

class YeMemeBotTelegram:
    def __init__(self):
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        self.setup_handlers()
        self.chat_ids = set()

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("check", self.check_command))
        self.app.add_handler(CommandHandler("balance", self.balance_command))
        self.app.add_handler(CommandHandler("profits", self.profits_command))

    def load_shared_state(self):
        if SHARED_STATE_PATH.exists():
            with open(SHARED_STATE_PATH, 'r') as f:
                return json.load(f)
        return None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.chat_ids.add(update.effective_chat.id)
        await self.send_ghetto_message(update.effective_chat.id, 
            "YO FAM! 🔥 Ya boi's bot is now ACTIVATED! Boutta keep u updated wit all dem MOVES! 💯")
        await self.send_initial_status(update.effective_chat.id)

    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        state = self.load_shared_state()
        if not state:
            await self.send_ghetto_message(update.effective_chat.id, 
                "AYO something ain't right wit the data fam! 😤 Can't check rn!")
            return

        active_trades = state["trade"]["active_trades"]
        if active_trades:
            msg = "CURRENT MOVES IN DA GAME:\n"
            for trade in active_trades:
                msg += f"• {trade['symbol']} - {trade['amount']} SOL 💰\n"
        else:
            msg = "NO ACTIVE TRADES RN FAM! We steady watching tho! 👀"
        
        await self.send_ghetto_message(update.effective_chat.id, msg)

    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.send_balance_update(update.effective_chat.id)

    async def profits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        state = self.load_shared_state()
        if not state:
            await self.send_ghetto_message(update.effective_chat.id, 
                "DATA AIN'T LOADING RN FAM! 😤 Try again later!")
            return

        profits = state["prof_e_perd"]
        msg = f"PROFIT CHECK 💸:\n"
        msg += f"Total Profit: {profits['total_profit_sol']:.3f} SOL (${profits['total_profit_usd']:.2f}) 💰\n"
        
        if profits["trades_history"]:
            msg += "\nLAST FEW MOVES:\n"
            for trade in profits["trades_history"][-5:]:
                msg += f"• {trade['symbol']}: {trade['profit_sol']:.3f} SOL 💎\n"
        
        await self.send_ghetto_message(update.effective_chat.id, msg)

    async def send_initial_status(self, chat_id):
        state = self.load_shared_state()
        if not state:
            await self.send_ghetto_message(chat_id, 
                "YO! Can't get the initial status rn! 😤 But we still WATCHING! 👀")
            return

        # Send balance
        await self.send_balance_update(chat_id)
        
        # Send active trades
        active_trades = state["trade"]["active_trades"]
        if active_trades:
            msg = "CURRENT ACTIVE TRADES:\n"
            for trade in active_trades:
                msg += f"• {trade['symbol']} - {trade['amount']} SOL 💰\n"
            await self.send_ghetto_message(chat_id, msg)

        # Send recent findings
        memecoin_trovate = state["memecoin_trovate"]
        if memecoin_trovate:
            msg = "RECENT FIRE FINDS 🔥:\n"
            for coin in memecoin_trovate[-5:]:
                msg += f"• {coin['symbol']} - Potential {coin['potential_multiplier']}x 🚀\n"
            await self.send_ghetto_message(chat_id, msg)

    async def send_balance_update(self, chat_id):
        state = self.load_shared_state()
        if not state or "saldo_wallet" not in state:
            await self.send_ghetto_message(chat_id, 
                "YO! Can't check the bag rn! 😤 System trippin!")
            return

        balance = state["saldo_wallet"]
        msg = f"CURRENT BAG STATUS 💰:\n"
        msg += f"{balance['sol']:.3f} SOL (${balance['usd']:.2f}) 💎"
        await self.send_ghetto_message(chat_id, msg)

    async def send_ghetto_message(self, chat_id, message):
        try:
            await self.app.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            print(f"Error sending message: {str(e)}")

    async def periodic_balance_check(self):
        while True:
            try:
                for chat_id in self.chat_ids:
                    await self.send_balance_update(chat_id)
                await asyncio.sleep(CHECK_INTERVAL)
            except Exception as e:
                print(f"Error in periodic balance check: {str(e)}")
                await asyncio.sleep(5)

    async def run(self):
        async with self.app:
            await self.app.start()
            await self.periodic_balance_check()
            await self.app.run_polling()

if __name__ == '__main__':
    bot = YeMemeBotTelegram()
    asyncio.run(bot.run())
