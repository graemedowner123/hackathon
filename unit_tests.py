#!/usr/bin/env python3
"""
Unit Tests for P2P Lending Platform Core Functionality
Focused tests that can run without external dependencies
"""

import unittest
import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestBotLenderLogic(unittest.TestCase):
    """Test bot lender business logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from bot_lenders import BotLender
            self.BotLender = BotLender
        except ImportError:
            self.skipTest("Bot lenders module not available")
        
        # Create test bots
        self.conservative_bot = self.BotLender(
            bot_id='test-conservative',
            name='Conservative Test Bot',
            strategy='conservative',
            capital=100000,
            min_credit_score=750,
            max_loan_amount=25000,
            preferred_terms=[24, 36, 48]
        )
        
        self.aggressive_bot = self.BotLender(
            bot_id='test-aggressive',
            name='Aggressive Test Bot',
            strategy='aggressive',
            capital=100000,
            min_credit_score=650,
            max_loan_amount=50000,
            preferred_terms=[12, 24, 36, 48, 60]
        )
        
        self.balanced_bot = self.BotLender(
            bot_id='test-balanced',
            name='Balanced Test Bot',
            strategy='balanced',
            capital=100000,
            min_credit_score=700,
            max_loan_amount=35000,
            preferred_terms=[24, 36, 48]
        )
    
    def test_credit_score_filtering(self):
        """Test bots filter loans based on credit score requirements"""
        loan = {
            'id': 'test-loan-1',
            'amount': 15000,
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        
        # Test with high credit score (should pass all bots)
        high_credit_borrower = {'credit_score': 800, 'annual_income': 80000}
        self.assertTrue(self.conservative_bot.should_bid_on_loan(loan, high_credit_borrower))
        self.assertTrue(self.aggressive_bot.should_bid_on_loan(loan, high_credit_borrower))
        self.assertTrue(self.balanced_bot.should_bid_on_loan(loan, high_credit_borrower))
        
        # Test with medium credit score (should pass aggressive and balanced)
        medium_credit_borrower = {'credit_score': 720, 'annual_income': 60000}
        self.assertFalse(self.conservative_bot.should_bid_on_loan(loan, medium_credit_borrower))
        self.assertTrue(self.aggressive_bot.should_bid_on_loan(loan, medium_credit_borrower))
        self.assertTrue(self.balanced_bot.should_bid_on_loan(loan, medium_credit_borrower))
        
        # Test with low credit score (should pass only aggressive)
        low_credit_borrower = {'credit_score': 680, 'annual_income': 50000}
        self.assertFalse(self.conservative_bot.should_bid_on_loan(loan, low_credit_borrower))
        self.assertTrue(self.aggressive_bot.should_bid_on_loan(loan, low_credit_borrower))
        self.assertFalse(self.balanced_bot.should_bid_on_loan(loan, low_credit_borrower))
    
    def test_loan_amount_limits(self):
        """Test bots respect loan amount limits"""
        borrower = {'credit_score': 800, 'annual_income': 100000}
        
        # Small loan (should pass all bots)
        small_loan = {
            'id': 'small-loan',
            'amount': 10000,
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        self.assertTrue(self.conservative_bot.should_bid_on_loan(small_loan, borrower))
        self.assertTrue(self.aggressive_bot.should_bid_on_loan(small_loan, borrower))
        self.assertTrue(self.balanced_bot.should_bid_on_loan(small_loan, borrower))
        
        # Medium loan (should pass aggressive and balanced)
        medium_loan = {
            'id': 'medium-loan',
            'amount': 30000,
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        self.assertFalse(self.conservative_bot.should_bid_on_loan(medium_loan, borrower))
        self.assertTrue(self.aggressive_bot.should_bid_on_loan(medium_loan, borrower))
        self.assertTrue(self.balanced_bot.should_bid_on_loan(medium_loan, borrower))
        
        # Large loan (should pass only aggressive)
        large_loan = {
            'id': 'large-loan',
            'amount': 45000,
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        self.assertFalse(self.conservative_bot.should_bid_on_loan(large_loan, borrower))
        self.assertTrue(self.aggressive_bot.should_bid_on_loan(large_loan, borrower))
        self.assertFalse(self.balanced_bot.should_bid_on_loan(large_loan, borrower))
    
    def test_term_preferences(self):
        """Test bots respect term preferences"""
        borrower = {'credit_score': 800, 'annual_income': 80000}
        
        # Preferred term (36 months - all bots should accept)
        preferred_term_loan = {
            'id': 'preferred-term',
            'amount': 15000,
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        self.assertTrue(self.conservative_bot.should_bid_on_loan(preferred_term_loan, borrower))
        self.assertTrue(self.aggressive_bot.should_bid_on_loan(preferred_term_loan, borrower))
        self.assertTrue(self.balanced_bot.should_bid_on_loan(preferred_term_loan, borrower))
        
        # Non-preferred term (60 months - only aggressive should accept)
        long_term_loan = {
            'id': 'long-term',
            'amount': 15000,
            'term_months': 60,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        self.assertFalse(self.conservative_bot.should_bid_on_loan(long_term_loan, borrower))
        self.assertTrue(self.aggressive_bot.should_bid_on_loan(long_term_loan, borrower))
        self.assertFalse(self.balanced_bot.should_bid_on_loan(long_term_loan, borrower))
    
    def test_interest_rate_calculation(self):
        """Test interest rate calculation logic"""
        loan = {
            'id': 'rate-test',
            'amount': 15000,
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        
        # Test with different credit scores
        high_credit = {'credit_score': 800, 'annual_income': 80000}
        medium_credit = {'credit_score': 720, 'annual_income': 60000}
        
        # Calculate rates
        conservative_rate_high = self.conservative_bot.calculate_interest_rate(loan, high_credit)
        aggressive_rate_high = self.aggressive_bot.calculate_interest_rate(loan, high_credit)
        aggressive_rate_medium = self.aggressive_bot.calculate_interest_rate(loan, medium_credit)
        
        # Rates should be within bounds
        self.assertGreaterEqual(conservative_rate_high, 3.0)
        self.assertLessEqual(conservative_rate_high, 12.0)
        self.assertGreaterEqual(aggressive_rate_high, 3.0)
        self.assertLessEqual(aggressive_rate_high, 12.0)
        
        # Higher credit score should generally get better rate
        self.assertLessEqual(aggressive_rate_high, aggressive_rate_medium + 0.5)
        
        # Conservative strategy should generally offer competitive rates
        self.assertLessEqual(conservative_rate_high, aggressive_rate_high + 1.0)
    
    def test_capital_management(self):
        """Test bot capital tracking"""
        initial_capital = self.conservative_bot.capital
        initial_available = self.conservative_bot.available_capital
        
        # Initially, all capital should be available
        self.assertEqual(initial_capital, initial_available)
        self.assertEqual(len(self.conservative_bot.active_bids), 0)
        
        # Simulate placing bids
        bid_amount_1 = Decimal('10000')
        bid_amount_2 = Decimal('15000')
        
        self.conservative_bot.available_capital -= bid_amount_1
        self.conservative_bot.active_bids.append('bid-1')
        
        self.conservative_bot.available_capital -= bid_amount_2
        self.conservative_bot.active_bids.append('bid-2')
        
        # Check capital tracking
        expected_available = initial_available - bid_amount_1 - bid_amount_2
        self.assertEqual(self.conservative_bot.available_capital, expected_available)
        self.assertEqual(len(self.conservative_bot.active_bids), 2)
        
        # Check utilization
        utilization = (initial_capital - self.conservative_bot.available_capital) / initial_capital
        self.assertEqual(utilization, Decimal('0.25'))  # 25% utilization
    
    def test_insufficient_capital(self):
        """Test bot behavior with insufficient capital"""
        # Reduce bot's available capital
        self.conservative_bot.available_capital = Decimal('5000')
        
        # Try to bid on a loan requiring more capital
        large_loan = {
            'id': 'large-loan',
            'amount': 10000,  # More than available capital
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        borrower = {'credit_score': 800, 'annual_income': 80000}
        
        # Should not bid due to insufficient capital
        self.assertFalse(self.conservative_bot.should_bid_on_loan(large_loan, borrower))


class TestTemplateFiltersUnit(unittest.TestCase):
    """Unit tests for template filters"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from app_dynamodb import dict_min_filter, dict_max_filter, dict_avg_filter, dict_sum_filter
            self.dict_min_filter = dict_min_filter
            self.dict_max_filter = dict_max_filter
            self.dict_avg_filter = dict_avg_filter
            self.dict_sum_filter = dict_sum_filter
        except ImportError:
            self.skipTest("App module not available")
    
    def test_basic_functionality(self):
        """Test basic filter functionality with normal data"""
        data = [
            {'rate': 5.5, 'amount': 10000},
            {'rate': 6.2, 'amount': 15000},
            {'rate': 4.8, 'amount': 8000}
        ]
        
        self.assertEqual(self.dict_min_filter(data, 'rate'), 4.8)
        self.assertEqual(self.dict_max_filter(data, 'rate'), 6.2)
        self.assertAlmostEqual(self.dict_avg_filter(data, 'rate'), 5.5, places=1)
        self.assertEqual(self.dict_sum_filter(data, 'amount'), 33000)
    
    def test_decimal_handling(self):
        """Test filters handle Decimal objects correctly"""
        data = [
            {'rate': Decimal('5.5'), 'amount': Decimal('10000')},
            {'rate': Decimal('6.2'), 'amount': Decimal('15000')},
            {'rate': Decimal('4.8'), 'amount': Decimal('8000')}
        ]
        
        self.assertEqual(self.dict_min_filter(data, 'rate'), 4.8)
        self.assertEqual(self.dict_max_filter(data, 'rate'), 6.2)
        self.assertAlmostEqual(self.dict_avg_filter(data, 'rate'), 5.5, places=1)
        self.assertEqual(self.dict_sum_filter(data, 'amount'), 33000)
    
    def test_edge_cases(self):
        """Test filters handle edge cases gracefully"""
        # Empty list
        self.assertEqual(self.dict_min_filter([], 'rate'), 0)
        self.assertEqual(self.dict_max_filter([], 'rate'), 0)
        self.assertEqual(self.dict_avg_filter([], 'rate'), 0)
        self.assertEqual(self.dict_sum_filter([], 'amount'), 0)
        
        # Missing keys
        data_missing_keys = [{'other': 5}, {'different': 10}]
        self.assertEqual(self.dict_min_filter(data_missing_keys, 'rate'), 0)
        self.assertEqual(self.dict_max_filter(data_missing_keys, 'rate'), 0)
        self.assertEqual(self.dict_avg_filter(data_missing_keys, 'rate'), 0)
        self.assertEqual(self.dict_sum_filter(data_missing_keys, 'amount'), 0)
        
        # Invalid data types
        data_invalid = [{'rate': 'invalid'}, {'rate': None}]
        self.assertEqual(self.dict_min_filter(data_invalid, 'rate'), 0)
        self.assertEqual(self.dict_max_filter(data_invalid, 'rate'), 0)
        self.assertEqual(self.dict_avg_filter(data_invalid, 'rate'), 0)
        self.assertEqual(self.dict_sum_filter(data_invalid, 'rate'), 0)
    
    def test_mixed_data_types(self):
        """Test filters handle mixed valid and invalid data"""
        data = [
            {'rate': 5.5, 'amount': 10000},
            {'rate': 'invalid', 'amount': 'invalid'},
            {'rate': Decimal('4.8'), 'amount': Decimal('8000')},
            {'other_field': 'value'}  # Missing required keys
        ]
        
        # Should process only valid entries
        self.assertEqual(self.dict_min_filter(data, 'rate'), 4.8)
        self.assertEqual(self.dict_max_filter(data, 'rate'), 5.5)
        self.assertAlmostEqual(self.dict_avg_filter(data, 'rate'), 5.15, places=1)
        self.assertEqual(self.dict_sum_filter(data, 'amount'), 18000)


class TestDataConversionUnit(unittest.TestCase):
    """Unit tests for data conversion functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from app_dynamodb import convert_dynamodb_data
            self.convert_dynamodb_data = convert_dynamodb_data
        except ImportError:
            self.skipTest("App module not available")
    
    def test_decimal_conversion(self):
        """Test Decimal objects are converted to float"""
        data = {
            'amount': Decimal('15000.50'),
            'rate': Decimal('5.5'),
            'score': Decimal('720')
        }
        
        converted = self.convert_dynamodb_data(data)
        
        self.assertIsInstance(converted['amount'], float)
        self.assertIsInstance(converted['rate'], float)
        self.assertIsInstance(converted['score'], float)
        self.assertEqual(converted['amount'], 15000.50)
        self.assertEqual(converted['rate'], 5.5)
        self.assertEqual(converted['score'], 720.0)
    
    def test_nested_structure_conversion(self):
        """Test nested data structures are converted properly"""
        data = {
            'loan': {
                'amount': Decimal('10000'),
                'details': {
                    'rate': Decimal('4.5'),
                    'term': 36
                }
            },
            'bids': [
                {'amount': Decimal('10000'), 'rate': Decimal('4.2')},
                {'amount': Decimal('10000'), 'rate': Decimal('4.8')}
            ],
            'metadata': {
                'created': '2023-01-01',
                'stats': {
                    'min_rate': Decimal('4.2'),
                    'max_rate': Decimal('4.8')
                }
            }
        }
        
        converted = self.convert_dynamodb_data(data)
        
        # Check loan conversion
        self.assertIsInstance(converted['loan']['amount'], float)
        self.assertIsInstance(converted['loan']['details']['rate'], float)
        self.assertEqual(converted['loan']['details']['term'], 36)  # Non-Decimal preserved
        
        # Check bids array conversion
        self.assertIsInstance(converted['bids'][0]['amount'], float)
        self.assertIsInstance(converted['bids'][0]['rate'], float)
        self.assertIsInstance(converted['bids'][1]['amount'], float)
        self.assertIsInstance(converted['bids'][1]['rate'], float)
        
        # Check nested metadata conversion
        self.assertEqual(converted['metadata']['created'], '2023-01-01')  # String preserved
        self.assertIsInstance(converted['metadata']['stats']['min_rate'], float)
        self.assertIsInstance(converted['metadata']['stats']['max_rate'], float)
    
    def test_non_decimal_preservation(self):
        """Test non-Decimal data types are preserved"""
        data = {
            'string': 'test string',
            'integer': 42,
            'float': 3.14159,
            'boolean': True,
            'none_value': None,
            'list': [1, 2, 3, 'four'],
            'empty_dict': {},
            'empty_list': []
        }
        
        converted = self.convert_dynamodb_data(data)
        
        self.assertEqual(converted['string'], 'test string')
        self.assertEqual(converted['integer'], 42)
        self.assertEqual(converted['float'], 3.14159)
        self.assertEqual(converted['boolean'], True)
        self.assertIsNone(converted['none_value'])
        self.assertEqual(converted['list'], [1, 2, 3, 'four'])
        self.assertEqual(converted['empty_dict'], {})
        self.assertEqual(converted['empty_list'], [])
    
    def test_edge_cases(self):
        """Test edge cases in data conversion"""
        # None input
        self.assertIsNone(self.convert_dynamodb_data(None))
        
        # Empty structures
        self.assertEqual(self.convert_dynamodb_data({}), {})
        self.assertEqual(self.convert_dynamodb_data([]), [])
        
        # Single Decimal
        self.assertEqual(self.convert_dynamodb_data(Decimal('123.45')), 123.45)
        
        # Mixed list
        mixed_list = [Decimal('1.5'), 'string', 42, None]
        converted_list = self.convert_dynamodb_data(mixed_list)
        self.assertEqual(converted_list, [1.5, 'string', 42, None])


def run_unit_tests():
    """Run unit tests with detailed reporting"""
    
    print("🧪 P2P Lending Platform - Unit Test Suite")
    print("=" * 50)
    
    # Create test suite
    test_classes = [
        TestBotLenderLogic,
        TestTemplateFiltersUnit,
        TestDataConversionUnit
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True
    )
    
    print(f"\nRunning {suite.countTestCases()} unit tests...\n")
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Unit Test Summary")
    print("=" * 50)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print(f"\n❌ Failed Tests:")
        for test, traceback in result.failures:
            print(f"  • {test}")
    
    if result.errors:
        print(f"\n💥 Error Tests:")
        for test, traceback in result.errors:
            print(f"  • {test}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("🎉 All unit tests passed!")
        return True
    else:
        print("❌ Some unit tests failed.")
        return False


if __name__ == '__main__':
    success = run_unit_tests()
    sys.exit(0 if success else 1)
