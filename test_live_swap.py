import os
import asyncio
from dotenv import load_dotenv
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from trading.auto_trader import AutoTrader
import base58

async def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize Solana client
    client = AsyncClient("https://api.mainnet-beta.solana.com")
    
    try:
        # Load private key from env
        private_key_base58 = os.getenv("PHANTOM_BASE58_KEY")
        if not private_key_base58:
            raise ValueError("Missing PHANTOM_BASE58_KEY in .env file")
            
        # Initialize wallet
        wallet = Keypair.from_bytes(base58.b58decode(private_key_base58))
        
        # Initialize trader
        trader = AutoTrader(wallet, client, test_mode=False)
        
        # USDC -> BONK
        BONK_MINT = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # BONK token
        USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC token
        amount_usdc = 0.1
        
        print(f"\nGetting quote for {amount_usdc} USDC to BONK...")
        quote = await trader.jupiter_client.get_quote(
            input_mint=USDC_MINT,
            output_mint=BONK_MINT,
            amount=amount_usdc
        )
        
        if quote:
            output_amount = float(quote['outAmount']) / 1e9  # BONK has 9 decimals
            price_impact = float(quote.get('priceImpactPct', 0))
            
            print(f"You will receive: {output_amount:.2f} BONK")
            print(f"Price Impact: {price_impact:.2f}%")
            
            if price_impact > 1.0:
                print("⚠️  WARNING: Price impact is high!")
                proceed = input("Do you want to proceed? (y/n): ")
                if proceed.lower() != 'y':
                    print("Swap cancelled")
                    return
            
            print(f"\nExecuting swap...")
            tx_hash = await trader.jupiter_client.swap(quote)
            
            if tx_hash:
                print(f"\n✅ Swap completed!")
                print(f"Transaction hash: {tx_hash}")
                print(f"View on Solscan: https://solscan.io/tx/{tx_hash}")
            else:
                print("\n❌ Swap failed")
        else:
            print("❌ Failed to get quote")
            
    except Exception as e:
        print(f"\n❌ Error during swap: {str(e)}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
