import os
import asyncio
from dotenv import load_dotenv
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from trading.jupiter_client import JupiterClient
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
        
        # Initialize Jupiter client
        jupiter = JupiterClient(wallet, client, test_mode=False)
        
        # USDC -> BONK
        print(f"\nGetting quote for 0.1 USDC to BONK...")
        quote = await jupiter.get_quote(
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC mint
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK mint
            0.1  # Amount in USDC
        )
        
        if quote:
            out_amount = float(quote['outAmount'])
            price_impact = float(quote.get('priceImpactPct', 0))
            print(f"You will receive: {out_amount / 1e9:.2f} BONK")
            print(f"Price Impact: {price_impact:.2f}%")
            
            print("\nExecuting swap...")
            signature = await jupiter.swap(quote)
            
            if signature:
                print(f"\n✅ Swap completed!")
                print(f"Transaction hash: {signature}")
                print(f"View on Solscan: https://solscan.io/tx/{signature}")
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
