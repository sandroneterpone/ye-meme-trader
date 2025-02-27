def get_ghetto_message(message_type, data=None):
    """Get ghetto-style message templates"""
    
    messages = {
        'start': """
Yo {user}! 🔥 
Welcome to YE MEME TRADER BOT! 
I'm here to help you find dem fresh Ye coins on Solana! 
Use /help to see what I can do for you! 
Let's get this bread fam! 💰
""",

        'help': """
YO FAM! Here's what I can do for you:

/scan - Scout for fresh Ye coins 🔍
/wallet - Check your wallet status 💼
/trades - View your active trades 📊
/stats - View trading stats 📈
/auto - Toggle auto-trading mode 🤖

Remember:
🔥 = Ultra fresh (< 30min)
⚡️ = Fresh (< 1h)
""",

        'wallet_info': """
💼 WALLET STATUS 💼

Balance: {balance} SOL
Active Trades: {active_trades}
Wallet: {wallet_address}

📊 PERFORMANCE:
Total Trades: {total_trades}
Win Rate: {win_rate}%
Best Trade: ${best_trade}
Total Profit: ${total_profit}

Mode: {auto_mode}
""",

        'new_opportunity': """
{age_emoji} NEW YE COIN ALERT! {age_emoji}

Name: {name}
Age: {age_text}
Risk Score: {risk_score}/10

📊 METRICS:
Volume (1h): ${volume_1h:,.2f}
Holders: {holders}
Liquidity: ${liquidity:,.2f}
Price Change (1h): {price_change_1h}%

{risk_emoji} Risk Level: {risk_text}
""",

        'trade_opened': """
🚀 NEW TRADE OPENED! 🚀

Coin: {coin_name}
Entry Price: ${entry_price:.6f}
Position Size: {position_size} SOL
Risk Score: {risk_score}/10

⏰ {timestamp}
""",

        'trade_closed': """
💫 TRADE CLOSED! 💫

Coin: {coin_name}
Entry: ${entry_price:.6f}
Exit: ${exit_price:.6f}
Profit: ${profit:.2f} (ROI: {return_percent:.1f}%)

{profit_emoji} {profit_text}
""",

        'trade_status': """
📊 ACTIVE TRADES STATUS 📊

{trades_list}

Total P/L: ${total_pl:.2f}
""",

        'bot_start': """
🚀 YE MEME TRADER BOT ONLINE! 🚀

Wallet Connected: {wallet}
Auto-Trading: ENABLED 🤖
Scanning for fresh Ye coins... 👀
""",

        'bot_shutdown': """
😴 BOT SHUTTING DOWN 😴

Session Summary:
Trades Closed: {trades_closed}
Total Profit: ${total_profit:.2f}

Stay wavy fam! 🌊
"""
    }

    if message_type not in messages:
        return "Message type not found!"

    if data:
        # Format age text based on minutes
        if 'age_minutes' in data:
            minutes = data['age_minutes']
            if minutes < 60:
                data['age_text'] = f"{int(minutes)}min old"
            else:
                hours = minutes / 60
                data['age_text'] = f"{hours:.1f}h old"

        # Format risk text and emoji
        if 'risk_score' in data:
            risk_score = float(data['risk_score'])
            if risk_score < 3:
                data['risk_text'] = "Low Risk 🟢"
                data['risk_emoji'] = "🟢"
            elif risk_score < 7:
                data['risk_text'] = "Medium Risk 🟡"
                data['risk_emoji'] = "🟡"
            else:
                data['risk_text'] = "High Risk 🔴"
                data['risk_emoji'] = "🔴"

        # Format profit text and emoji
        if 'profit' in data:
            profit = float(data['profit'])
            if profit > 0:
                data['profit_text'] = "PROFIT! 🎯"
                data['profit_emoji'] = "💰"
            else:
                data['profit_text'] = "LOSS! 📉"
                data['profit_emoji'] = "😢"

        return messages[message_type].format(**data)
    
    return messages[message_type]
