import asyncio
import os
from dotenv import load_dotenv
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from spl.token.instructions import create_associated_token_account, get_associated_token_address
from solana.transaction import Transaction
import base58

async def main():
    # Load environment variables
    load_dotenv()
    
    # Setup Solana client
    client = AsyncClient("https://api.mainnet-beta.solana.com")
    
    # Load private key from env
    private_key_base58 = os.getenv("PHANTOM_BASE58_KEY")
    private_key_bytes = base58.b58decode(private_key_base58)
    keypair = Keypair.from_bytes(private_key_bytes)
    
    try:
        # USDC mint address
        USDC_MINT = Pubkey.from_string("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
        
        # Get ATA address
        ata = get_associated_token_address(keypair.pubkey(), USDC_MINT)
        print(f"\nCreating USDC account at: {ata}")
        
        # Create instruction
        create_ata_ix = create_associated_token_account(
            payer=keypair.pubkey(),
            owner=keypair.pubkey(),
            mint=USDC_MINT
        )
        
        # Create transaction
        transaction = Transaction()
        transaction.add(create_ata_ix)
        
        # Get recent blockhash
        recent_blockhash = await client.get_latest_blockhash()
        transaction.recent_blockhash = recent_blockhash.value.blockhash
        
        # Sign transaction
        transaction.sign(keypair)
        
        # Send transaction
        print("\nSending transaction...")
        result = await client.send_transaction(transaction)
        
        print(f"\n✅ USDC account created successfully!")
        print(f"Transaction signature: {result.value}")
        print("\nYou can now receive and hold USDC in your wallet.")
        
    except Exception as e:
        print(f"\n❌ Error creating USDC account: {str(e)}")
        if "0x0" in str(e):
            print("\nSembra che l'account USDC sia già stato creato.")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
