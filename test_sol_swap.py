import asyncio
import logging
from dotenv import load_dotenv
from trading.auto_trader import AutoTrader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_swap():
    # Initialize trader in test mode
    trader = AutoTrader(test_mode=True)
    
    # Use a minimal amount for testing
    trader.trade_amount = 0.001  # 0.001 SOL
    
    # Check SOL balance
    balance = await trader.trading_client.get_sol_balance()
    logger.info(f"Current SOL balance: {balance} SOL")
    
    if balance < trader.trade_amount:
        logger.error(f"Insufficient SOL balance. Need at least {trader.trade_amount} SOL")
        return
        
    # Test token (BONK has good liquidity)
    test_token = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    
    try:
        logger.info("Testing SOL -> BONK swap...")
        # Get quote first
        quote = await trader.trading_client.get_quote(
            input_mint=trader.sol_mint,
            output_mint=test_token,
            amount=trader.trade_amount,
            slippage=trader.slippage,
            use_sol=True
        )
        
        if quote:
            logger.info(f"Quote received:")
            logger.info(f"Input: {trader.trade_amount} SOL")
            logger.info(f"Output: {float(quote['outAmount'])/1e5:.6f} BONK")
            logger.info(f"Price impact: {float(quote.get('priceImpactPct', 0)) * 100:.4f}%")
            
            # Execute swap
            logger.info("\nExecuting swap...")
            result = await trader.trading_client.buy_token(
                test_token,
                trader.trade_amount,
                trader.slippage,
                use_sol=True
            )
            
            if result:
                logger.info("✅ Test swap successful!")
                logger.info(f"Transaction: https://solscan.io/tx/{result['signature']}")
                
                # Check balances after swap
                sol_balance = await trader.trading_client.get_sol_balance()
                bonk_balance = await trader.trading_client.get_token_balance(test_token)
                logger.info(f"\nBalances after swap:")
                logger.info(f"SOL: {sol_balance} SOL")
                logger.info(f"BONK: {bonk_balance} BONK")
            else:
                logger.error("❌ Swap failed")
        else:
            logger.error("❌ Failed to get quote")
            
    except Exception as e:
        logger.error(f"Error during test: {e}")
    finally:
        # Cleanup
        await trader.trading_client.close()

if __name__ == "__main__":
    asyncio.run(test_swap())
