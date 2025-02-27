import asyncio
import os
import base58
from dotenv import load_dotenv
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from trading.auto_trader import AutoTrader

# Carica variabili d'ambiente
load_dotenv()

async def test_system():
    try:
        # Inizializza client RPC e keypair
        private_key = os.getenv("PHANTOM_BASE58_KEY")
        rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        
        if not private_key:
            raise Exception("PHANTOM_BASE58_KEY non trovata nel file .env")
            
        keypair = Keypair.from_bytes(base58.b58decode(private_key))
        async_client = AsyncClient(rpc_url, commitment=Confirmed)
        
        # Inizializza AutoTrader
        trader = AutoTrader(keypair, async_client)
        
        # Test 1: Check token price
        print("\n1. Test prezzo token...")
        SOL_MINT = "So11111111111111111111111111111111111111112"
        price = await trader.check_token_price(SOL_MINT)
        print(f"Prezzo SOL: ${price}")
        
        if price <= 0:
            raise Exception("Errore nel recupero del prezzo")
            
        # Test 2: Check price impact
        print("\n2. Test price impact...")
        USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        quote = await trader.jupiter_client.get_quote(
            input_mint=SOL_MINT,
            output_mint=USDC_MINT,
            amount=0.1  # 0.1 SOL
        )
        print(f"Price impact: {quote.get('priceImpactPct')}%")
        print(f"Route: {quote.get('routePlan')}")
        
        # Test 3: Monitor position simulation
        print("\n3. Test monitoraggio posizione...")
        current_price = float(quote['outAmount']) / 1e6  # Converte da USDC decimals
        stop_loss = current_price * 0.95  # -5%
        take_profit = current_price * 1.05  # +5%
        
        print(f"Prezzo attuale: ${current_price}")
        print(f"Stop Loss: ${stop_loss}")
        print(f"Take Profit: ${take_profit}")
        
        # Non eseguiamo swap reali per il test
        print("\nTest completati con successo!")
        
    except Exception as e:
        print(f"Errore nei test: {str(e)}")
    finally:
        if async_client:
            await async_client.close()

if __name__ == "__main__":
    asyncio.run(test_system())
