# 🎵 Ye Meme Trader Bot 🚀

A Telegram bot that trades Kanye West (Ye) related meme coins with style! The bot uses advanced scanning techniques to find potential moon shots while maintaining a ghetto-style communication approach.

## 🔥 Features

- 👀 Automatic scanning for new Ye-related meme coins
- 💹 Smart trade sizing based on risk analysis
- 🤖 Telegram bot with ghetto-style messaging
- 📊 Modern web dashboard for monitoring
- 🔍 Multi-source scanning (Twitter, Reddit, Telegram)
- 🛡️ Advanced scam detection
- 💰 Automatic trade execution
- 📈 Performance tracking

## 🚀 Getting Started

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys and settings (use the provided template)

4. Start the bot:
```bash
python bot.py
```

5. Access the dashboard at `http://localhost:8050`

## 💬 Telegram Commands

- `/start` - Start the bot
- `/wallet` - Check wallet status
- `/trades` - View active trades
- `/scan` - Scan for new opportunities

## 📊 Dashboard Features

- Real-time portfolio tracking
- Active trades monitoring
- Performance metrics
- Trading chart
- Recent opportunities
- Trading log

## 🎯 Trading Strategy

The bot uses a sophisticated strategy to find and trade potential moon shots:

### Token Discovery
- Monitors Jupiter, Magic Eden, and Raydium for new listings
- Scans Discord channels for token mentions
- Analyzes Twitter for trending Ye-related topics
- Tracks holder growth and liquidity changes

### Profit Potential Categories
- 🚀 10000x: Very new tokens (<24h) with high viral potential
- 🌟 1000x: Young tokens (<48h) with good liquidity
- ⭐ 100x: Low market cap with strong community
- 💫 50x: Tokens in positive trend

### Position Management
- Base position size: 20 USD
- Take Profit Levels:
  - TP1: 20% of potential (30% of position)
  - TP2: 50% of potential (40% of position)
  - TP3: 100% of potential (30% of position)
- Stop Loss: -15%
- Trailing Stop: 5%

### Risk Analysis
- Minimum liquidity requirement
- Holder concentration analysis
- Smart contract verification
- Trading volume analysis
- Social sentiment scoring

## 🔧 Configuration

### Required API Keys
```env
# Wallet
PHANTOM_BASE58_KEY="your_phantom_private_key"
WALLET_ADDRESS="your_wallet_address"

# DEX APIs
JUPITER_API_URL="https://quote-api.jup.ag/v6"
RAYDIUM_API_URL="https://api.raydium.io/v2"
BIRDEYE_API_URL="https://public-api.birdeye.so/v1"
SOLSCAN_API_URL="https://public-api.solscan.io"

# Social APIs
TWITTER_API_KEY="your_twitter_key"
DISCORD_TOKEN="your_discord_token"
TELEGRAM_BOT_TOKEN="your_telegram_token"
```

### Trading Parameters
```env
TRADE_INTERVAL=300  # 5 minuti
MAX_CONCURRENT_TRADES=3
MIN_LIQUIDITY_USD=50000
MAX_PRICE_IMPACT=2.0
MIN_HOLDERS=100
MAX_WALLET_EXPOSURE=0.15
```

## 📊 Performance Tracking

The bot tracks and reports:
- P&L per trade
- Win/Loss ratio
- Average holding time
- Best/Worst trades
- Total portfolio value
- ROI percentage

## 🔍 Token Scanning Criteria

The bot looks for tokens with:
1. Growing holder count
2. Increasing liquidity
3. Active social mentions
4. Verified contracts
5. Fair token distribution
6. Reasonable market cap

## ⚠️ Risk Management

Advanced risk controls include:
- Maximum position size limits
- Portfolio exposure limits
- Slippage protection
- Liquidity requirements
- Smart contract analysis
- Holder concentration monitoring

## 🔒 Security

- All API keys are stored in environment variables
- Contract verification checks
- Honeypot detection
- Maximum slippage protection
- Minimum liquidity requirements

## 📝 License

MIT License - Feel free to modify and use as you want!

## 🚀 Ye Meme Token Trading Bot

An automated trading bot for Solana meme tokens, specifically focused on Ye (Kanye West) related tokens.

## 🌟 Features

- Automated trading of Solana meme tokens
- Integration with Jupiter aggregator for best swap rates
- Real-time price monitoring
- Configurable trading strategies
- Test mode for safe simulation

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ye-meme-trader.git
cd ye-meme-trader
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Phantom wallet private key:
```
PHANTOM_BASE58_KEY=your_private_key_here
```

## 🔧 Configuration

The bot can be configured through environment variables:

- `PHANTOM_BASE58_KEY`: Your Phantom wallet private key (base58 encoded)
- `TEST_MODE`: Set to "true" for test mode (no real transactions)

## 🚀 Usage

1. Run the test script to verify everything works:
```bash
python test_live_swap.py
```

2. Start the auto trader:
```bash
python -m trading.auto_trader
```

## 🏗️ Project Structure

```
ye-meme-trader/
├── trading/
│   ├── __init__.py
│   ├── jupiter_client.py    # Jupiter DEX integration
│   └── auto_trader.py       # Main trading logic
├── test_live_swap.py        # Test script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## ⚠️ Disclaimer

This bot is for educational purposes only. Trading cryptocurrency is risky and you should never trade with money you can't afford to lose.

## 📄 License

MIT License. See `LICENSE` file for details.
