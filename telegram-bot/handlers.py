async def notify_opportunity(self, context, data):
    message = "🔥 YOOOOO WASSUP GANG!! NUOVO TOKEN DI YE DROPPATO COME UNA BOMBA!! 🔥\n\n"
    message += f"💎 NOME DELLA SHITCOIN: {data['name']} ({data['symbol']})\n"
    message += f"💰 PREZZO: ${data['price']:.8f} (ANCORA UN CAZZO)\n"
    message += f"💸 MARKET CAP: ${data['market_cap']:,.0f} (PICCOLA AF)\n"
    message += f"👥 QUANTI DENTRO: {data['holders']:,} PAZZI\n"
    message += f"⏰ FRESH COME LA MERDA: {data['age_minutes']:.1f} min\n"
    message += f"🚀 POTENZIALE DI PUMP: {data['potential_multiplier']}x SHEEEEEESH!\n\n"
    message += "YOOO SVEGLIAAAA!! 🗣️ METTI LE NOTIFICHE CAZZO!! APE TIME!! 🦍🦍"

async def notify_trade_opened(self, context, data):
    message = "💰 AYOOO GANG GANG!! SIAMO DENTRO COME I LUPI!! 🐺\n\n"
    message += f"🎯 SHITCOIN: {data['symbol']}\n"
    message += f"📈 SIAMO ENTRATI A: ${data['entry_price']:.8f} (EARLY AF)\n"
    message += f"💵 QUANTO ABBIAMO YOLATO: {data['amount_sol']:.2f} SOL\n"
    message += f"🛑 SE SCENDE QUA SIAMO FOTTUTI: ${data['stop_loss']:.8f}\n"
    message += f"🎆 TARGET DA RICCHI: ${data['take_profit']:.8f}\n\n"
    message += "DIAMOND HANDS GANG!! 💎🙌 NO PAPER HANDS O SEI BANNATO!! PUMPAAAAA!! 🚀"

async def notify_trade_closed(self, context, data):
    profit_emoji = "🤑" if data['pnl_percentage'] > 0 else "💀"
    message = f"{profit_emoji} YOOO TRADE CHIUSO!! DRUM ROLL... {profit_emoji}\n\n"
    message += f"🎯 SHITCOIN: {data['symbol']}\n"
    message += f"📈 ENTRY DA GOAT: ${data['entry_price']:.8f}\n"
    message += f"📉 USCITI A: ${data['exit_price']:.8f}\n"
    message += f"💰 GAINS/REKT: {data['pnl_percentage']:.2f}%\n"
    message += f"💵 SOLANA FATTE: {data['pnl_sol']:.4f} SOL\n\n"
    
    if data['pnl_percentage'] > 0:
        message += "SHEEEEEESH!! 🔥 MANGIAMO BENE STASERA FAM!! WAGMI!! 💸🤑💸"
    else:
        message += "BRUH... 💀 CI HANNO RUGGATO!! NGMI MA TOMORROW WE FEAST!! 🌙"

async def notify_bot_start(self, context):
    message = "😤 YURRR!! BOT ACCESO COME UN RAZZO!! 😤\n\n"
    message += "🎯 PRONTI A RUGGARE TUTTE LE SHITCOIN DI YE!\n"
    message += "🚀 TEMPO DI FARE IL PAPEETE CON STI TOKEN!\n"
    message += "💰 ANDIAMO A PRENDERCI STA BREAD FAM!!\n\n"
    message += f"⏰ INIZIAMO A FARE CASINO ALLE {datetime.now().strftime('%H:%M:%S')}"

async def notify_balance(self, context):
    balance = self.state_reader.get_balance()
    message = "💰 YOOO GANG!! ECCO QUANTO SIAMO RICCHI!! 💰\n\n"
    message += f"🪙 SOLANA NEL WALLET: {balance:.4f}\n"
    message += f"💵 DOLLARI PER FLEXARE: ${balance * 20:.2f}\n\n"
    message += "STILL EATING GOOD FAM!! 🍗 NO RAMEN TODAY!! 🤑"

async def notify_important_movements(self, context, movements):
    message = "👀 YOOO FAM!! MOVIMENTO ASSURDO!! GUARDATE STA ROBA!! 👀\n\n"
    for mov in movements:
        if mov['change'] > 0:
            message += f"🚀 {mov['symbol']}: +{mov['change']}% in {mov['timeframe']} PUMPANDO COME UN PAZZO!!\n"
        else:
            message += f"💀 {mov['symbol']}: {mov['change']}% in {mov['timeframe']} BRUH MOMENT FR FR!\n"
    message += "\nSTAY WOKE FAM!! NON DORMITE SU STA ROBA!! 👁️ NGMI CHI DORME!!"