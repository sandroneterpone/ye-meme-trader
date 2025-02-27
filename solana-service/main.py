import asyncio
import signal
from datetime import datetime
from solana_scanner import SolanaScanner
from trader import SolanaTrader
from utils.state_manager import StateManager
from config import *

class YeMemeTrader:
    def __init__(self):
        self.scanner = SolanaScanner()
        self.trader = SolanaTrader()
        self.state_manager = StateManager()
        self.running = False
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """Setup handlers per shutdown pulito"""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Gestisce lo shutdown pulito"""
        print("\n🛑 YO FAM! SPENGO TUTTO, ASPETTA UN SECONDO...")
        self.running = False

    async def monitor_wallet(self):
        """Monitora il saldo del wallet"""
        while self.running:
            try:
                balance = self.scanner.get_token_balance(WALLET_ADDRESS)
                self.state_manager.update_balance(balance)
                await asyncio.sleep(60)  # Check ogni minuto
            except Exception as e:
                print(f"💀 BRUH! Errore nel check del wallet: {e}")
                await asyncio.sleep(5)

    async def scan_and_trade(self):
        """Loop principale di scanning e trading"""
        while self.running:
            try:
                # Scan per nuovi token
                print("👀 CERCANDO NUOVE SHITCOIN DI YE...")
                new_tokens = self.scanner.scan_new_tokens()

                for token in new_tokens:
                    print(f"🎯 TROVATO TOKEN POTENZIALE: {token['symbol']}")
                    
                    # Verifica sicurezza
                    if not await self.trader.check_token_safety(token['address']):
                        print(f"❌ NAH FAM, {token['symbol']} PUZZA DI SCAM!")
                        continue

                    # YOLO TIME
                    print(f"🚀 YOLANDO IN {token['symbol']}...")
                    if await self.trader.buy_token(token['address'], token):
                        print(f"💰 SIAMO DENTRO FAM! LFG {token['symbol']}!!")
                    else:
                        print(f"😤 DAMN! NON SIAMO RIUSCITI A COMPRARE {token['symbol']}")

                # Monitor trades attivi
                await self.trader.monitor_trades()
                
                await asyncio.sleep(SCAN_INTERVAL)

            except Exception as e:
                print(f"💀 BRUH! ERRORE NEL MAIN LOOP: {e}")
                await asyncio.sleep(5)

    async def run(self):
        """Avvia il bot"""
        try:
            self.running = True
            print("\n" + "="*50)
            print("🚀 YE MEME TRADER BOT - READY TO MOON 🌙")
            print("="*50 + "\n")
            
            # Aggiorna stato
            self.state_manager.update_bot_status("running")
            
            # Avvia i tasks
            await asyncio.gather(
                self.monitor_wallet(),
                self.scan_and_trade()
            )

        except Exception as e:
            print(f"💀 FATAL ERROR FAM: {e}")
        finally:
            # Cleanup
            self.state_manager.update_bot_status("stopped")
            print("\n" + "="*50)
            print("😴 BOT SPENTO - A DOMANI FAM!")
            print("="*50 + "\n")

def main():
    """Entry point"""
    bot = YeMemeTrader()
    
    # Avvia il loop degli eventi
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(bot.run())
    except KeyboardInterrupt:
        print("\n⛔ CTRL+C DETECTED - SHUTDOWN IN CORSO...")
    finally:
        loop.close()

if __name__ == "__main__":
    main()