import asyncio
import os
from dotenv import load_dotenv
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from trading.solana_client import SolanaClient
from spl.token.instructions import get_associated_token_address
from solders.pubkey import Pubkey
import base58

async def get_token_balance_rpc(client: AsyncClient, wallet_address: str, token_mint: str) -> float:
    """Get token balance using Solana RPC"""
    try:
        # Get ATA
        wallet_pubkey = Pubkey.from_string(wallet_address)
        mint_pubkey = Pubkey.from_string(token_mint)
        ata = get_associated_token_address(wallet_pubkey, mint_pubkey)
        
        # Get balance
        response = await client.get_token_account_balance(str(ata))
        if response.value:
            amount = float(response.value.amount)
            decimals = response.value.decimals
            return amount / (10 ** decimals)
    except Exception as e:
        print(f"Error getting balance: {str(e)}")
    return 0.0

async def main():
    # Load environment variables
    load_dotenv()
    
    # Setup Solana client
    client = AsyncClient("https://api.mainnet-beta.solana.com")
    
    # Load private key from env
    private_key_base58 = os.getenv("PHANTOM_BASE58_KEY")
    private_key_bytes = base58.b58decode(private_key_base58)
    keypair = Keypair.from_bytes(private_key_bytes)
    wallet_address = str(keypair.pubkey())
    
    # Initialize Solana client
    solana_client = SolanaClient(keypair, client)
    
    try:
        # Check SOL balance
        sol_balance = await solana_client.get_sol_balance()
        print(f"\nSOL Balance: {sol_balance} SOL")
        
        if sol_balance < 0.01:
            print("⚠️  WARNING: Low SOL balance. You need at least 0.01 SOL for transaction fees.")
        
        # Check USDC
        USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        # Check if USDC ATA exists
        usdc_ata_exists = await solana_client.check_token_account_exists(USDC_MINT)
        print(f"\nUSDC Account exists: {usdc_ata_exists}")
        
        if not usdc_ata_exists:
            print("⚠️  WARNING: No USDC account found. One will be created with your first USDC transaction.")
        
        # Check USDC balance
        usdc_balance = await get_token_balance_rpc(client, wallet_address, USDC_MINT)
        print(f"USDC Balance: {usdc_balance} USDC")
        
        if usdc_balance < 0.1:
            print("⚠️  WARNING: USDC balance too low for test swap (need at least 0.1 USDC)")
            
        # Summary
        print("\nSummary:")
        print("✓ SOL for fees" if sol_balance >= 0.01 else "✗ Need more SOL for fees")
        print("✓ USDC account exists" if usdc_ata_exists else "✗ USDC account needs to be created")
        print("✓ USDC balance sufficient" if usdc_balance >= 0.1 else "✗ Need more USDC")
        
    except Exception as e:
        print(f"Error checking balances: {str(e)}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
