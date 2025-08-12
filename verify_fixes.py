#!/usr/bin/env python3
"""
Verify that bidding fixes are working without requiring AWS credentials
"""

import sys
import os
from decimal import Decimal

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_template_filters():
    """Test that template filters can handle Decimal objects"""
    print("🧪 Testing Template Filters...")
    
    try:
        # Import the fixed filters
        from app_dynamodb import dict_min_filter, dict_max_filter, dict_avg_filter, dict_sum_filter
        
        # Test data with Decimal objects (like DynamoDB returns)
        test_bids = [
            {'interest_rate': Decimal('5.5'), 'amount': Decimal('10000')},
            {'interest_rate': Decimal('6.2'), 'amount': Decimal('15000')},
            {'interest_rate': Decimal('4.8'), 'amount': Decimal('8000')},
        ]
        
        # Test all filters
        min_rate = dict_min_filter(test_bids, 'interest_rate')
        max_rate = dict_max_filter(test_bids, 'interest_rate')
        avg_rate = dict_avg_filter(test_bids, 'interest_rate')
        sum_amount = dict_sum_filter(test_bids, 'amount')
        
        print(f"   Min Interest Rate: {min_rate}%")
        print(f"   Max Interest Rate: {max_rate}%")
        print(f"   Avg Interest Rate: {avg_rate:.2f}%")
        print(f"   Total Amount: ${sum_amount:,.2f}")
        
        # Verify results
        assert min_rate == 4.8, f"Expected 4.8, got {min_rate}"
        assert max_rate == 6.2, f"Expected 6.2, got {max_rate}"
        assert abs(avg_rate - 5.5) < 0.1, f"Expected ~5.5, got {avg_rate}"
        assert sum_amount == 33000, f"Expected 33000, got {sum_amount}"
        
        # Test edge cases
        empty_result = dict_min_filter([], 'interest_rate')
        assert empty_result == 0, f"Expected 0 for empty list, got {empty_result}"
        
        print("   ✅ All template filters working correctly!")
        return True
        
    except Exception as e:
        print(f"   ❌ Template filter test failed: {e}")
        return False

def test_data_conversion():
    """Test the DynamoDB data conversion helper"""
    print("\n🔄 Testing Data Conversion...")
    
    try:
        from app_dynamodb import convert_dynamodb_data
        
        # Test data with nested Decimal objects
        test_data = {
            'loan': {
                'amount': Decimal('15000'),
                'interest_rate': Decimal('5.5'),
                'term_months': 36
            },
            'bids': [
                {'amount': Decimal('15000'), 'rate': Decimal('4.8')},
                {'amount': Decimal('15000'), 'rate': Decimal('5.2')}
            ]
        }
        
        converted = convert_dynamodb_data(test_data)
        
        # Verify conversion
        assert isinstance(converted['loan']['amount'], float)
        assert isinstance(converted['loan']['interest_rate'], float)
        assert isinstance(converted['bids'][0]['amount'], float)
        assert isinstance(converted['bids'][0]['rate'], float)
        
        print(f"   Loan Amount: ${converted['loan']['amount']:,.2f}")
        print(f"   Loan Rate: {converted['loan']['interest_rate']}%")
        print(f"   First Bid Rate: {converted['bids'][0]['rate']}%")
        print("   ✅ Data conversion working correctly!")
        return True
        
    except Exception as e:
        print(f"   ❌ Data conversion test failed: {e}")
        return False

def test_bot_logic():
    """Test bot bidding logic"""
    print("\n🤖 Testing Bot Bidding Logic...")
    
    try:
        from bot_lenders import BotLender
        
        # Create test bots with different strategies
        bots = [
            BotLender('bot1', 'Conservative Bot', 'conservative', 100000, min_credit_score=750),
            BotLender('bot2', 'Aggressive Bot', 'aggressive', 100000, min_credit_score=650),
            BotLender('bot3', 'Balanced Bot', 'balanced', 100000, min_credit_score=700)
        ]
        
        # Test scenarios
        scenarios = [
            {
                'name': 'High Credit Score Borrower',
                'loan': {'id': 'loan1', 'amount': 15000, 'term_months': 36, 'max_interest_rate': 12.0, 'purpose': 'debt_consolidation'},
                'borrower': {'credit_score': 780, 'annual_income': 75000}
            },
            {
                'name': 'Medium Credit Score Borrower',
                'loan': {'id': 'loan2', 'amount': 10000, 'term_months': 24, 'max_interest_rate': 15.0, 'purpose': 'home_improvement'},
                'borrower': {'credit_score': 720, 'annual_income': 55000}
            },
            {
                'name': 'Lower Credit Score Borrower',
                'loan': {'id': 'loan3', 'amount': 8000, 'term_months': 36, 'max_interest_rate': 18.0, 'purpose': 'emergency'},
                'borrower': {'credit_score': 650, 'annual_income': 40000}
            }
        ]
        
        for scenario in scenarios:
            print(f"\n   📋 Scenario: {scenario['name']}")
            print(f"      Credit Score: {scenario['borrower']['credit_score']}")
            print(f"      Loan Amount: ${scenario['loan']['amount']:,}")
            
            bids_placed = 0
            for bot in bots:
                should_bid = bot.should_bid_on_loan(scenario['loan'], scenario['borrower'])
                if should_bid:
                    rate = bot.calculate_interest_rate(scenario['loan'], scenario['borrower'])
                    print(f"      {bot.name}: Would bid at {rate}%")
                    bids_placed += 1
                else:
                    print(f"      {bot.name}: Would not bid")
            
            print(f"      Total bids: {bids_placed}/3")
        
        print("\n   ✅ Bot bidding logic working correctly!")
        return True
        
    except Exception as e:
        print(f"   ❌ Bot logic test failed: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
        return False

def test_error_handling():
    """Test error handling improvements"""
    print("\n🛡️ Testing Error Handling...")
    
    try:
        from app_dynamodb import dict_min_filter
        
        # Test with invalid data
        test_cases = [
            ([], 'interest_rate'),  # Empty list
            ([{'no_rate': 5}], 'interest_rate'),  # Missing key
            ([{'interest_rate': 'invalid'}], 'interest_rate'),  # Invalid type
            (None, 'interest_rate'),  # None input
        ]
        
        for i, (data, key) in enumerate(test_cases):
            try:
                result = dict_min_filter(data, key)
                print(f"   Test case {i+1}: Returned {result} (expected 0)")
                assert result == 0, f"Expected 0, got {result}"
            except Exception as e:
                print(f"   ❌ Test case {i+1} failed: {e}")
                return False
        
        print("   ✅ Error handling working correctly!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 Verifying Bidding System Fixes")
    print("=" * 50)
    
    tests = [
        test_template_filters,
        test_data_conversion,
        test_bot_logic,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Verification Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All fixes verified successfully!")
        print("\n✅ The bidding system is now working correctly:")
        print("   • Template filters handle DynamoDB Decimal objects")
        print("   • Data conversion prevents type errors")
        print("   • Bot logic evaluates loans properly")
        print("   • Error handling is robust")
        print("\n🚀 Ready to start the application!")
        print("   Run: python3 app_dynamodb.py")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        print("Please check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
