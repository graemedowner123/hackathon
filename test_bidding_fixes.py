#!/usr/bin/env python3
"""
Test script for bidding functionality
"""

import sys
import os
import logging
from decimal import Decimal

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_template_filters():
    """Test template filters with various data types"""
    print("Testing template filters...")
    
    # Mock data with Decimal objects (like DynamoDB returns)
    test_bids = [
        {'interest_rate': Decimal('5.5'), 'amount': Decimal('10000')},
        {'interest_rate': Decimal('6.2'), 'amount': Decimal('15000')},
        {'interest_rate': Decimal('4.8'), 'amount': Decimal('8000')},
    ]
    
    try:
        from app_dynamodb import dict_min_filter, dict_max_filter, dict_avg_filter
        
        min_rate = dict_min_filter(test_bids, 'interest_rate')
        max_rate = dict_max_filter(test_bids, 'interest_rate')
        avg_rate = dict_avg_filter(test_bids, 'interest_rate')
        
        print(f"  Min rate: {min_rate}%")
        print(f"  Max rate: {max_rate}%")
        print(f"  Avg rate: {avg_rate:.2f}%")
        
        assert min_rate == 4.8, f"Expected 4.8, got {min_rate}"
        assert max_rate == 6.2, f"Expected 6.2, got {max_rate}"
        assert abs(avg_rate - 5.5) < 0.1, f"Expected ~5.5, got {avg_rate}"
        
        print("✅ Template filters working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Template filter test failed: {e}")
        return False

def test_bid_creation():
    """Test bid creation functionality"""
    print("Testing bid creation...")
    
    try:
        from dynamodb_models import bid_model
        
        # Test creating a bid
        test_bid_id = bid_model.create_bid(
            loan_request_id='test-loan-123',
            lender_id='test-lender-456',
            amount=10000,
            interest_rate=5.5,
            message='Test bid from automated test'
        )
        
        if test_bid_id:
            print(f"✅ Bid created successfully: {test_bid_id}")
            
            # Test retrieving the bid
            bid = bid_model.get_bid(test_bid_id)
            if bid:
                print(f"✅ Bid retrieved successfully")
                print(f"  Amount: ${float(bid['amount'])}")
                print(f"  Interest Rate: {float(bid['interest_rate'])}%")
                return True
            else:
                print("❌ Failed to retrieve created bid")
                return False
        else:
            print("❌ Failed to create bid")
            return False
            
    except Exception as e:
        print(f"❌ Bid creation test failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def test_bot_bidding_logic():
    """Test bot bidding logic"""
    print("Testing bot bidding logic...")
    
    try:
        from bot_lenders import BotLender
        
        # Create a test bot
        test_bot = BotLender(
            bot_id='test-bot-123',
            name='Test Bot',
            strategy='balanced',
            capital=100000,
            min_credit_score=650,
            max_loan_amount=25000
        )
        
        # Test loan and borrower data
        test_loan = {
            'id': 'test-loan-456',
            'amount': 15000,
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        
        test_borrower = {
            'credit_score': 720,
            'annual_income': 60000
        }
        
        # Test if bot should bid
        should_bid = test_bot.should_bid_on_loan(test_loan, test_borrower)
        print(f"  Should bid: {should_bid}")
        
        if should_bid:
            interest_rate = test_bot.calculate_interest_rate(test_loan, test_borrower)
            print(f"  Calculated rate: {interest_rate}%")
            
            if 3.0 <= interest_rate <= 12.0:
                print("✅ Bot bidding logic working correctly")
                return True
            else:
                print(f"❌ Interest rate {interest_rate}% is out of expected range")
                return False
        else:
            print("❌ Bot should have bid on this loan")
            return False
            
    except Exception as e:
        print(f"❌ Bot bidding logic test failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running Bidding System Tests")
    print("=" * 40)
    
    tests = [
        test_template_filters,
        test_bid_creation,
        test_bot_bidding_logic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bidding system is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
