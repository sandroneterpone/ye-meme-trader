import asyncio
import os
import base58
from dotenv import load_dotenv
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from jupiter_python_sdk.jupiter import Jupiter

# Carica variabili d'ambiente
load_dotenv()

async def test_swap():
    async_client = None
    try:
        # Inizializza client RPC e keypair
        private_key = os.getenv("PHANTOM_BASE58_KEY")
        keypair = Keypair.from_bytes(base58.b58decode(private_key))
        async_client = AsyncClient("https://api.mainnet-beta.solana.com", commitment=Confirmed)
        
        # Inizializza Jupiter client
        jupiter = Jupiter(
            async_client=async_client,
            keypair=keypair
        )
        
        # Token da scambiare (SOL -> USDC per test)
        SOL_MINT = "So11111111111111111111111111111111111111112"
        USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        # Test swap quote
        amount = str(int(0.1 * 1e9))  # 0.1 SOL in lamports
        quote = await jupiter.quote(
            input_mint=SOL_MINT,
            output_mint=USDC_MINT,
            amount=amount,
            slippage_bps=100  # 1% slippage
        )
        
        if quote:
            print(f"Swap Quote: {quote}")
            
            # Test swap transaction
            tx = await jupiter.swap(
                input_mint=SOL_MINT,
                output_mint=USDC_MINT,
                amount=amount,
                slippage_bps=100
            )
            
            if tx:
                print(f"Swap Transaction: {tx}")
                # Non firmiamo/inviamo la transazione per test
                
        else:
            print("Failed to get swap quote")
            
    except Exception as e:
        print(f"Error in test: {str(e)}")
    finally:
        if async_client:
            await async_client.close()

if __name__ == "__main__":
    asyncio.run(test_swap())
