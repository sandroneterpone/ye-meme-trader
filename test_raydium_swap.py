import os
import asyncio
import base58
from dotenv import load_dotenv
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from trading.raydium_client import RaydiumClient

# Load environment variables
load_dotenv()

# Token addresses
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
BONK_MINT = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"

async def main():
    # Initialize Solana client
    client = AsyncClient("https://api.mainnet-beta.solana.com")
    
    # Load wallet from private key
    private_key = base58.b58decode(os.getenv("PRIVATE_KEY"))
    wallet = Keypair.from_bytes(private_key)
    
    # Initialize Raydium client
    raydium = RaydiumClient(wallet, client, test_mode=True)
    
    try:
        print("\nGetting quote for 0.1 USDC to BONK...")
        quote = await raydium.get_quote(
            input_mint=USDC_MINT,
            output_mint=BONK_MINT,
            amount=0.1,  # 0.1 USDC
            slippage=0.5  # 0.5% slippage
        )
        
        if quote:
            out_amount = float(quote['outAmount'])
            price_impact = float(quote.get('priceImpact', 0))
            print(f"You will receive: {out_amount / 1e9:.2f} BONK")
            print(f"Price Impact: {price_impact:.2f}%")
            
            print("\nExecuting swap...")
            signature = await raydium.swap(quote)
            
            if signature:
                print(f"\n✅ Swap successful!")
                print(f"Transaction: https://solscan.io/tx/{signature}")
            else:
                print("\n❌ Swap failed")
        else:
            print("\n❌ Failed to get quote")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
