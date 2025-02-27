import os
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers import TelegramHandler
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Configurazione logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def main():
    """Main function del bot"""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN non trovato nelle variabili d'ambiente")

    # Inizializza handler
    handler = TelegramHandler()

    # Crea l'applicazione
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Salva chat_id nei dati del bot
    application.bot_data["chat_id"] = TELEGRAM_CHAT_ID

    # Aggiungi gli handlers
    application.add_handler(CommandHandler("start", handler.start))
    application.add_handler(CommandHandler("help", handler.help_command))
    application.add_handler(CommandHandler("status", handler.status))
    application.add_handler(CommandHandler("balance", handler.balance))
    application.add_handler(CommandHandler("trades", handler.trades))

    # Avvia il task di controllo notifiche
    application.create_task(handler.check_notifications(application))

    # Avvia il bot
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())