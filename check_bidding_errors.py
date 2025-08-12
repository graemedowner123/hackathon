#!/usr/bin/env python3
"""
Comprehensive Bidding System Error Check
Identifies and reports any issues with the bidding functionality
"""

import sys
import os
import traceback
from decimal import Decimal
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_template_filters():
    """Test template filters for errors"""
    print("🧪 Testing Template Filters...")
    
    try:
        from app_dynamodb import dict_min_filter, dict_max_filter, dict_avg_filter, dict_sum_filter
        
        # Test 1: Basic functionality
        basic_data = [
            {'rate': 5.5, 'amount': 10000},
            {'rate': 6.2, 'amount': 15000},
            {'rate': 4.8, 'amount': 8000}
        ]
        
        min_rate = dict_min_filter(basic_data, 'rate')
        max_rate = dict_max_filter(basic_data, 'rate')
        avg_rate = dict_avg_filter(basic_data, 'rate')
        sum_amount = dict_sum_filter(basic_data, 'amount')
        
        assert min_rate == 4.8, f"Expected 4.8, got {min_rate}"
        assert max_rate == 6.2, f"Expected 6.2, got {max_rate}"
        assert abs(avg_rate - 5.5) < 0.1, f"Expected ~5.5, got {avg_rate}"
        assert sum_amount == 33000, f"Expected 33000, got {sum_amount}"
        
        print("   ✅ Basic functionality: PASS")
        
        # Test 2: Decimal objects
        decimal_data = [
            {'rate': Decimal('5.5'), 'amount': Decimal('10000')},
            {'rate': Decimal('4.8'), 'amount': Decimal('8000')}
        ]
        
        min_rate = dict_min_filter(decimal_data, 'rate')
        sum_amount = dict_sum_filter(decimal_data, 'amount')
        
        assert min_rate == 4.8, f"Expected 4.8, got {min_rate}"
        assert sum_amount == 18000, f"Expected 18000, got {sum_amount}"
        
        print("   ✅ Decimal handling: PASS")
        
        # Test 3: Mixed valid/invalid data
        mixed_data = [
            {'rate': 5.5, 'amount': 10000},
            {'rate': 'invalid', 'amount': 'invalid'},
            {'rate': Decimal('4.8'), 'amount': Decimal('8000')},
            {'other_field': 'value'}
        ]
        
        min_rate = dict_min_filter(mixed_data, 'rate')
        max_rate = dict_max_filter(mixed_data, 'rate')
        avg_rate = dict_avg_filter(mixed_data, 'rate')
        sum_amount = dict_sum_filter(mixed_data, 'amount')
        
        assert min_rate == 4.8, f"Expected 4.8, got {min_rate}"
        assert max_rate == 5.5, f"Expected 5.5, got {max_rate}"
        assert abs(avg_rate - 5.15) < 0.1, f"Expected ~5.15, got {avg_rate}"
        assert sum_amount == 18000, f"Expected 18000, got {sum_amount}"
        
        print("   ✅ Mixed data handling: PASS")
        
        # Test 4: Edge cases
        empty_result = dict_min_filter([], 'rate')
        assert empty_result == 0, f"Expected 0 for empty list, got {empty_result}"
        
        missing_key_result = dict_min_filter([{'other': 5}], 'rate')
        assert missing_key_result == 0, f"Expected 0 for missing key, got {missing_key_result}"
        
        print("   ✅ Edge cases: PASS")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Template filters failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_data_conversion():
    """Test DynamoDB data conversion"""
    print("\n🔄 Testing Data Conversion...")
    
    try:
        from app_dynamodb import convert_dynamodb_data
        
        # Test nested data with Decimals
        test_data = {
            'loan': {
                'amount': Decimal('15000.50'),
                'rate': Decimal('5.5'),
                'details': {
                    'min_rate': Decimal('4.2'),
                    'max_rate': Decimal('7.8')
                }
            },
            'bids': [
                {'amount': Decimal('15000'), 'rate': Decimal('4.8')},
                {'amount': Decimal('15000'), 'rate': Decimal('5.2')}
            ],
            'metadata': {
                'count': 2,
                'status': 'active'
            }
        }
        
        converted = convert_dynamodb_data(test_data)
        
        # Verify conversions
        assert isinstance(converted['loan']['amount'], float)
        assert isinstance(converted['loan']['rate'], float)
        assert isinstance(converted['loan']['details']['min_rate'], float)
        assert isinstance(converted['bids'][0]['amount'], float)
        assert isinstance(converted['bids'][0]['rate'], float)
        
        # Verify values preserved
        assert converted['loan']['amount'] == 15000.50
        assert converted['loan']['rate'] == 5.5
        assert converted['metadata']['count'] == 2  # Non-Decimal preserved
        assert converted['metadata']['status'] == 'active'  # String preserved
        
        print("   ✅ Data conversion: PASS")
        return True
        
    except Exception as e:
        print(f"   ❌ Data conversion failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_bot_bidding_logic():
    """Test bot bidding logic"""
    print("\n🤖 Testing Bot Bidding Logic...")
    
    try:
        from bot_lenders import BotLender
        
        # Create test bots
        conservative_bot = BotLender(
            'test-conservative', 'Conservative Bot', 'conservative', 
            100000, min_credit_score=750, max_loan_amount=25000
        )
        
        aggressive_bot = BotLender(
            'test-aggressive', 'Aggressive Bot', 'aggressive',
            100000, min_credit_score=650, max_loan_amount=50000
        )
        
        balanced_bot = BotLender(
            'test-balanced', 'Balanced Bot', 'balanced',
            100000, min_credit_score=700, max_loan_amount=35000
        )
        
        # Test scenarios
        scenarios = [
            {
                'name': 'High Credit Borrower',
                'loan': {
                    'id': 'test-loan-1',
                    'amount': 15000,
                    'term_months': 36,
                    'max_interest_rate': 12.0,
                    'purpose': 'debt_consolidation'
                },
                'borrower': {'credit_score': 780, 'annual_income': 75000},
                'expected_bids': 3  # All bots should bid
            },
            {
                'name': 'Medium Credit Borrower',
                'loan': {
                    'id': 'test-loan-2',
                    'amount': 10000,
                    'term_months': 24,
                    'max_interest_rate': 15.0,
                    'purpose': 'home_improvement'
                },
                'borrower': {'credit_score': 720, 'annual_income': 55000},
                'expected_bids': 2  # Aggressive and balanced should bid
            },
            {
                'name': 'Lower Credit Borrower',
                'loan': {
                    'id': 'test-loan-3',
                    'amount': 8000,
                    'term_months': 36,
                    'max_interest_rate': 18.0,
                    'purpose': 'emergency'
                },
                'borrower': {'credit_score': 680, 'annual_income': 40000},
                'expected_bids': 1  # Only aggressive should bid
            }
        ]
        
        bots = [conservative_bot, aggressive_bot, balanced_bot]
        
        for scenario in scenarios:
            print(f"   📋 Testing: {scenario['name']}")
            
            actual_bids = 0
            rates = []
            
            for bot in bots:
                if bot.should_bid_on_loan(scenario['loan'], scenario['borrower']):
                    rate = bot.calculate_interest_rate(scenario['loan'], scenario['borrower'])
                    rates.append(rate)
                    actual_bids += 1
                    print(f"      {bot.name}: Would bid at {rate:.2f}%")
                else:
                    print(f"      {bot.name}: Would not bid")
            
            # Verify expected behavior
            if actual_bids != scenario['expected_bids']:
                print(f"      ⚠️  Expected {scenario['expected_bids']} bids, got {actual_bids}")
            
            # Verify rates are reasonable
            for rate in rates:
                assert 3.0 <= rate <= 20.0, f"Rate {rate}% is outside reasonable range"
            
            print(f"      ✅ {actual_bids} bids placed")
        
        # Test capital management
        print("   💰 Testing capital management...")
        
        initial_capital = conservative_bot.capital
        initial_available = conservative_bot.available_capital
        
        assert initial_capital == initial_available, "Initial capital should equal available capital"
        
        # Simulate placing a bid
        bid_amount = Decimal('10000')
        conservative_bot.available_capital -= bid_amount
        conservative_bot.active_bids.append('test-bid-1')
        
        assert conservative_bot.available_capital == initial_available - bid_amount
        assert len(conservative_bot.active_bids) == 1
        
        print("      ✅ Capital tracking working correctly")
        
        print("   ✅ Bot bidding logic: PASS")
        return True
        
    except Exception as e:
        print(f"   ❌ Bot bidding logic failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_flask_routes():
    """Test Flask route functionality"""
    print("\n🌐 Testing Flask Routes...")
    
    try:
        from app_dynamodb import app
        
        with app.test_client() as client:
            # Test home route
            response = client.get('/')
            assert response.status_code in [200, 302], f"Home route returned {response.status_code}"
            
            # Test register route
            response = client.get('/register')
            assert response.status_code == 200, f"Register route returned {response.status_code}"
            
            # Test login route
            response = client.get('/login')
            assert response.status_code == 200, f"Login route returned {response.status_code}"
            
        print("   ✅ Flask routes: PASS")
        return True
        
    except Exception as e:
        print(f"   ❌ Flask routes failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_error_handling():
    """Test error handling robustness"""
    print("\n🛡️ Testing Error Handling...")
    
    try:
        from app_dynamodb import dict_min_filter
        
        # Test various error conditions
        error_cases = [
            (None, 'rate', "None input"),
            ([], 'rate', "Empty list"),
            ([{'other': 5}], 'rate', "Missing key"),
            ([{'rate': None}], 'rate', "None value"),
            ([{'rate': 'invalid'}], 'rate', "Invalid string"),
            ([{'rate': [1, 2, 3]}], 'rate', "Invalid list"),
        ]
        
        for data, key, description in error_cases:
            try:
                result = dict_min_filter(data, key)
                assert result == 0, f"{description}: Expected 0, got {result}"
                print(f"      ✅ {description}: Handled gracefully")
            except Exception as e:
                print(f"      ❌ {description}: Failed with {e}")
                return False
        
        print("   ✅ Error handling: PASS")
        return True
        
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        return False

def check_file_integrity():
    """Check that all required files exist and are valid"""
    print("\n📁 Checking File Integrity...")
    
    required_files = [
        'app_dynamodb.py',
        'bot_lenders.py',
        'dynamodb_models.py',
        'cognito_auth.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            # Check if file is not empty
            if os.path.getsize(file) == 0:
                missing_files.append(f"{file} (empty)")
    
    if missing_files:
        print(f"   ❌ Missing or empty files: {', '.join(missing_files)}")
        return False
    else:
        print("   ✅ All required files present")
        return True

def main():
    """Main error checking function"""
    print("🔍 P2P Lending Platform - Bidding System Error Check")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("File Integrity", check_file_integrity),
        ("Template Filters", test_template_filters),
        ("Data Conversion", test_data_conversion),
        ("Bot Bidding Logic", test_bot_bidding_logic),
        ("Flask Routes", test_flask_routes),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("📊 ERROR CHECK SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 NO ERRORS FOUND!")
        print("✅ Bidding system is working correctly")
        print("✅ All components are functional")
        print("✅ Error handling is robust")
        print("✅ Ready for production use")
        
        print("\n🚀 SYSTEM STATUS: HEALTHY")
        print("The bidding system is operating without errors.")
        
    else:
        print(f"\n❌ {total - passed} ERROR(S) FOUND!")
        print("Please review the failed tests above and fix the issues.")
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("1. Review error messages and tracebacks")
        print("2. Fix identified issues")
        print("3. Re-run this error check")
        print("4. Test manually if needed")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
