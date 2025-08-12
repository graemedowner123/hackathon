#!/usr/bin/env python3
"""
Test script for the bot bidding system
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bot_system():
    """Test the bot bidding system"""
    logger.info("Testing P2P Lending Bot System")
    
    try:
        # Import required modules
        from bot_lenders import BotLenderManager
        from dynamodb_models import user_model, loan_model, bid_model
        
        # Test 1: Create bot manager
        logger.info("Test 1: Creating bot manager...")
        bot_manager = BotLenderManager()
        
        # Test 2: Create bot lenders
        logger.info("Test 2: Creating bot lenders...")
        bot_manager.create_bot_lenders()
        
        logger.info(f"Created {len(bot_manager.bots)} bot lenders:")
        for bot in bot_manager.bots:
            logger.info(f"  - {bot.name}: {bot.strategy} strategy, ${bot.capital} capital")
        
        # Test 3: Get bot stats
        logger.info("Test 3: Getting bot statistics...")
        stats = bot_manager.get_bot_stats()
        logger.info(f"Bot Stats:")
        logger.info(f"  Total Bots: {stats['total_bots']}")
        logger.info(f"  Total Capital: ${stats['total_capital']:,.2f}")
        logger.info(f"  Available Capital: ${stats['available_capital']:,.2f}")
        
        # Test 4: Check for open loans
        logger.info("Test 4: Checking for open loans...")
        try:
            open_loans = loan_model.get_all_open_loans()
            logger.info(f"Found {len(open_loans)} open loans")
            
            if open_loans:
                for loan in open_loans[:3]:  # Show first 3 loans
                    logger.info(f"  Loan {loan['id']}: ${loan['amount']} for {loan['term_months']} months")
            else:
                logger.info("  No open loans found - bots will wait for new loan requests")
                
        except Exception as e:
            logger.warning(f"Could not fetch open loans: {e}")
        
        # Test 5: Test bot bidding logic (without actually placing bids)
        logger.info("Test 5: Testing bot bidding logic...")
        if bot_manager.bots:
            test_bot = bot_manager.bots[0]
            
            # Create a sample loan and borrower for testing
            sample_loan = {
                'id': 'test-loan-123',
                'amount': 15000,
                'term_months': 36,
                'max_interest_rate': 12.0,
                'purpose': 'debt_consolidation'
            }
            
            sample_borrower = {
                'credit_score': 720,
                'annual_income': 60000
            }
            
            should_bid = test_bot.should_bid_on_loan(sample_loan, sample_borrower)
            if should_bid:
                interest_rate = test_bot.calculate_interest_rate(sample_loan, sample_borrower)
                logger.info(f"  {test_bot.name} would bid at {interest_rate}% for the sample loan")
            else:
                logger.info(f"  {test_bot.name} would not bid on the sample loan")
        
        logger.info("✅ All tests completed successfully!")
        logger.info("Bot system is ready to start automated bidding")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Make sure all dependencies are installed")
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def main():
    """Main function"""
    success = test_bot_system()
    if success:
        print("\n🎉 Bot system test completed successfully!")
        print("You can now run 'python start_bots.py' to start automated bidding")
    else:
        print("\n❌ Bot system test failed!")
        print("Please check the error messages above and fix any issues")
        sys.exit(1)

if __name__ == "__main__":
    main()
