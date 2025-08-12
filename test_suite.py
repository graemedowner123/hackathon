#!/usr/bin/env python3
"""
Comprehensive Test Suite for P2P Lending Platform
Tests all major functionality including bidding, user management, loans, and bots
"""

import unittest
import sys
import os
import tempfile
import json
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

class TestTemplateFilters(unittest.TestCase):
    """Test template filters for handling DynamoDB data"""
    
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
    
    def test_filters_with_decimal_objects(self):
        """Test filters handle DynamoDB Decimal objects correctly"""
        test_data = [
            {'interest_rate': Decimal('5.5'), 'amount': Decimal('10000')},
            {'interest_rate': Decimal('6.2'), 'amount': Decimal('15000')},
            {'interest_rate': Decimal('4.8'), 'amount': Decimal('8000')},
        ]
        
        self.assertEqual(self.dict_min_filter(test_data, 'interest_rate'), 4.8)
        self.assertEqual(self.dict_max_filter(test_data, 'interest_rate'), 6.2)
        self.assertAlmostEqual(self.dict_avg_filter(test_data, 'interest_rate'), 5.5, places=1)
        self.assertEqual(self.dict_sum_filter(test_data, 'amount'), 33000)
    
    def test_filters_with_empty_data(self):
        """Test filters handle empty data gracefully"""
        self.assertEqual(self.dict_min_filter([], 'interest_rate'), 0)
        self.assertEqual(self.dict_max_filter([], 'interest_rate'), 0)
        self.assertEqual(self.dict_avg_filter([], 'interest_rate'), 0)
        self.assertEqual(self.dict_sum_filter([], 'amount'), 0)
    
    def test_filters_with_missing_keys(self):
        """Test filters handle missing keys gracefully"""
        test_data = [{'other_field': 5}, {'different_field': 10}]
        
        self.assertEqual(self.dict_min_filter(test_data, 'interest_rate'), 0)
        self.assertEqual(self.dict_max_filter(test_data, 'interest_rate'), 0)
        self.assertEqual(self.dict_avg_filter(test_data, 'interest_rate'), 0)
        self.assertEqual(self.dict_sum_filter(test_data, 'amount'), 0)
    
    def test_filters_with_invalid_data(self):
        """Test filters handle invalid data types gracefully"""
        test_data = [{'interest_rate': 'invalid'}, {'interest_rate': None}]
        
        self.assertEqual(self.dict_min_filter(test_data, 'interest_rate'), 0)
        self.assertEqual(self.dict_max_filter(test_data, 'interest_rate'), 0)
        self.assertEqual(self.dict_avg_filter(test_data, 'interest_rate'), 0)


class TestDataConversion(unittest.TestCase):
    """Test DynamoDB data conversion functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from app_dynamodb import convert_dynamodb_data
            self.convert_dynamodb_data = convert_dynamodb_data
        except ImportError:
            self.skipTest("App module not available")
    
    def test_decimal_conversion(self):
        """Test Decimal objects are converted to float"""
        data = {'amount': Decimal('15000.50'), 'rate': Decimal('5.5')}
        converted = self.convert_dynamodb_data(data)
        
        self.assertIsInstance(converted['amount'], float)
        self.assertIsInstance(converted['rate'], float)
        self.assertEqual(converted['amount'], 15000.50)
        self.assertEqual(converted['rate'], 5.5)
    
    def test_nested_conversion(self):
        """Test nested data structures are converted properly"""
        data = {
            'loan': {
                'amount': Decimal('10000'),
                'details': {'rate': Decimal('4.5')}
            },
            'bids': [
                {'amount': Decimal('10000'), 'rate': Decimal('4.2')},
                {'amount': Decimal('10000'), 'rate': Decimal('4.8')}
            ]
        }
        
        converted = self.convert_dynamodb_data(data)
        
        self.assertIsInstance(converted['loan']['amount'], float)
        self.assertIsInstance(converted['loan']['details']['rate'], float)
        self.assertIsInstance(converted['bids'][0]['amount'], float)
        self.assertIsInstance(converted['bids'][1]['rate'], float)
    
    def test_non_decimal_preservation(self):
        """Test non-Decimal data types are preserved"""
        data = {
            'string': 'test',
            'integer': 42,
            'float': 3.14,
            'boolean': True,
            'none': None
        }
        
        converted = self.convert_dynamodb_data(data)
        
        self.assertEqual(converted['string'], 'test')
        self.assertEqual(converted['integer'], 42)
        self.assertEqual(converted['float'], 3.14)
        self.assertEqual(converted['boolean'], True)
        self.assertIsNone(converted['none'])


class TestBotLender(unittest.TestCase):
    """Test bot lender functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from bot_lenders import BotLender
            self.BotLender = BotLender
        except ImportError:
            self.skipTest("Bot lenders module not available")
        
        self.conservative_bot = self.BotLender(
            bot_id='test-bot-1',
            name='Conservative Test Bot',
            strategy='conservative',
            capital=100000,
            min_credit_score=750,
            max_loan_amount=25000
        )
        
        self.aggressive_bot = self.BotLender(
            bot_id='test-bot-2',
            name='Aggressive Test Bot',
            strategy='aggressive',
            capital=100000,
            min_credit_score=650,
            max_loan_amount=50000
        )
        
        self.balanced_bot = self.BotLender(
            bot_id='test-bot-3',
            name='Balanced Test Bot',
            strategy='balanced',
            capital=100000,
            min_credit_score=700,
            max_loan_amount=35000
        )
    
    def test_conservative_strategy(self):
        """Test conservative bot strategy"""
        # High credit score borrower - should bid
        loan = {
            'id': 'loan-1',
            'amount': 15000,
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        borrower = {'credit_score': 780, 'annual_income': 75000}
        
        self.assertTrue(self.conservative_bot.should_bid_on_loan(loan, borrower))
        
        # Low credit score borrower - should not bid
        borrower_low = {'credit_score': 720, 'annual_income': 75000}
        self.assertFalse(self.conservative_bot.should_bid_on_loan(loan, borrower_low))
    
    def test_aggressive_strategy(self):
        """Test aggressive bot strategy"""
        loan = {
            'id': 'loan-2',
            'amount': 20000,
            'term_months': 48,
            'max_interest_rate': 15.0,
            'purpose': 'business'
        }
        
        # Medium credit score - should bid
        borrower = {'credit_score': 680, 'annual_income': 50000}
        self.assertTrue(self.aggressive_bot.should_bid_on_loan(loan, borrower))
        
        # Very low credit score - should not bid
        borrower_low = {'credit_score': 620, 'annual_income': 50000}
        self.assertFalse(self.aggressive_bot.should_bid_on_loan(loan, borrower_low))
    
    def test_balanced_strategy(self):
        """Test balanced bot strategy"""
        loan = {
            'id': 'loan-3',
            'amount': 12000,
            'term_months': 36,
            'max_interest_rate': 10.0,
            'purpose': 'home_improvement'
        }
        
        # Good credit score - should bid
        borrower = {'credit_score': 720, 'annual_income': 60000}
        self.assertTrue(self.balanced_bot.should_bid_on_loan(loan, borrower))
        
        # Below threshold - should not bid
        borrower_low = {'credit_score': 680, 'annual_income': 60000}
        self.assertFalse(self.balanced_bot.should_bid_on_loan(loan, borrower_low))
    
    def test_interest_rate_calculation(self):
        """Test interest rate calculation logic"""
        loan = {
            'id': 'loan-4',
            'amount': 15000,
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        borrower = {'credit_score': 750, 'annual_income': 70000}
        
        # Test all bot strategies
        conservative_rate = self.conservative_bot.calculate_interest_rate(loan, borrower)
        aggressive_rate = self.aggressive_bot.calculate_interest_rate(loan, borrower)
        balanced_rate = self.balanced_bot.calculate_interest_rate(loan, borrower)
        
        # Rates should be within reasonable bounds
        self.assertGreaterEqual(conservative_rate, 3.0)
        self.assertLessEqual(conservative_rate, 12.0)
        self.assertGreaterEqual(aggressive_rate, 3.0)
        self.assertLessEqual(aggressive_rate, 12.0)
        self.assertGreaterEqual(balanced_rate, 3.0)
        self.assertLessEqual(balanced_rate, 12.0)
        
        # Conservative should generally offer lower rates
        self.assertLessEqual(conservative_rate, aggressive_rate + 1.0)
    
    def test_capital_management(self):
        """Test bot capital management"""
        initial_capital = self.conservative_bot.capital
        initial_available = self.conservative_bot.available_capital
        
        self.assertEqual(initial_capital, initial_available)
        
        # Simulate placing a bid
        loan_amount = Decimal('10000')
        self.conservative_bot.available_capital -= loan_amount
        self.conservative_bot.active_bids.append('bid-123')
        
        self.assertEqual(self.conservative_bot.available_capital, initial_available - loan_amount)
        self.assertEqual(len(self.conservative_bot.active_bids), 1)
    
    def test_loan_amount_limits(self):
        """Test loan amount limits are enforced"""
        # Loan exceeding conservative bot's limit
        large_loan = {
            'id': 'loan-5',
            'amount': 30000,  # Exceeds 25000 limit
            'term_months': 36,
            'max_interest_rate': 10.0,
            'purpose': 'debt_consolidation'
        }
        borrower = {'credit_score': 800, 'annual_income': 100000}
        
        self.assertFalse(self.conservative_bot.should_bid_on_loan(large_loan, borrower))
        self.assertTrue(self.aggressive_bot.should_bid_on_loan(large_loan, borrower))


class TestBotLenderManager(unittest.TestCase):
    """Test bot lender manager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from bot_lenders import BotLenderManager
            self.BotLenderManager = BotLenderManager
        except ImportError:
            self.skipTest("Bot lenders module not available")
    
    @patch('bot_lenders.user_model')
    def test_bot_creation(self, mock_user_model):
        """Test bot lender creation"""
        mock_user_model.create_user.return_value = 'bot-user-123'
        
        manager = self.BotLenderManager()
        manager.create_bot_lenders()
        
        # Should create multiple bots
        self.assertGreater(len(manager.bots), 0)
        
        # Each bot should have required attributes
        for bot in manager.bots:
            self.assertIsNotNone(bot.name)
            self.assertIsNotNone(bot.strategy)
            self.assertGreater(bot.capital, 0)
            self.assertGreaterEqual(bot.min_credit_score, 600)
    
    def test_bot_stats(self):
        """Test bot statistics generation"""
        manager = self.BotLenderManager()
        
        # Add mock bots
        from bot_lenders import BotLender
        bot1 = BotLender('bot1', 'Test Bot 1', 'conservative', 100000)
        bot2 = BotLender('bot2', 'Test Bot 2', 'aggressive', 150000)
        manager.bots = [bot1, bot2]
        
        stats = manager.get_bot_stats()
        
        self.assertEqual(stats['total_bots'], 2)
        self.assertEqual(stats['total_capital'], 250000)
        self.assertEqual(stats['available_capital'], 250000)
        self.assertEqual(len(stats['bots']), 2)


class TestDynamoDBModels(unittest.TestCase):
    """Test DynamoDB model functionality (mocked)"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from dynamodb_models import DynamoDBUser, DynamoDBLoanRequest, DynamoDBBid
            self.DynamoDBUser = DynamoDBUser
            self.DynamoDBLoanRequest = DynamoDBLoanRequest
            self.DynamoDBBid = DynamoDBBid
        except ImportError:
            self.skipTest("DynamoDB models not available")
    
    @patch('dynamodb_models.dynamodb')
    def test_user_creation(self, mock_dynamodb):
        """Test user creation logic"""
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.put_item.return_value = None
        
        user_model = self.DynamoDBUser()
        
        user_id = user_model.create_user(
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            phone='555-1234',
            user_type='borrower',
            credit_score=720,
            annual_income=60000
        )
        
        self.assertIsNotNone(user_id)
        mock_table.put_item.assert_called_once()
    
    @patch('dynamodb_models.dynamodb')
    def test_loan_creation(self, mock_dynamodb):
        """Test loan request creation logic"""
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.put_item.return_value = None
        
        loan_model = self.DynamoDBLoanRequest()
        
        loan_id = loan_model.create_loan_request(
            borrower_id='user-123',
            amount=15000,
            purpose='debt_consolidation',
            term_months=36,
            max_interest_rate=12.0,
            description='Test loan request'
        )
        
        self.assertIsNotNone(loan_id)
        mock_table.put_item.assert_called_once()
    
    @patch('dynamodb_models.dynamodb')
    def test_bid_creation(self, mock_dynamodb):
        """Test bid creation logic"""
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.put_item.return_value = None
        
        bid_model = self.DynamoDBBid()
        
        bid_id = bid_model.create_bid(
            loan_request_id='loan-123',
            lender_id='lender-456',
            amount=15000,
            interest_rate=5.5,
            message='Test bid'
        )
        
        self.assertIsNotNone(bid_id)
        mock_table.put_item.assert_called_once()


class TestFlaskRoutes(unittest.TestCase):
    """Test Flask application routes (mocked)"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from app_dynamodb import app
            self.app = app
            self.client = app.test_client()
            self.app.config['TESTING'] = True
        except ImportError:
            self.skipTest("Flask app not available")
    
    def test_home_route(self):
        """Test home page route"""
        with patch('app_dynamodb.loan_model') as mock_loan_model:
            mock_loan_model.get_all_open_loans.return_value = []
            
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
    
    def test_register_route_get(self):
        """Test registration page GET request"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
    
    def test_login_route_get(self):
        """Test login page GET request"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        try:
            from bot_lenders import BotLender
            from app_dynamodb import convert_dynamodb_data, dict_min_filter
            self.BotLender = BotLender
            self.convert_dynamodb_data = convert_dynamodb_data
            self.dict_min_filter = dict_min_filter
        except ImportError:
            self.skipTest("Required modules not available")
    
    def test_end_to_end_bidding_flow(self):
        """Test complete bidding flow from loan creation to bid evaluation"""
        # Create a loan request (simulated)
        loan_data = {
            'id': 'integration-loan-1',
            'amount': Decimal('15000'),
            'term_months': 36,
            'max_interest_rate': Decimal('12.0'),
            'purpose': 'debt_consolidation',
            'borrower_id': 'borrower-123'
        }
        
        # Create borrower data
        borrower_data = {
            'credit_score': 750,
            'annual_income': Decimal('70000')
        }
        
        # Convert DynamoDB data
        converted_loan = self.convert_dynamodb_data(loan_data)
        converted_borrower = self.convert_dynamodb_data(borrower_data)
        
        # Create bots
        bots = [
            self.BotLender('bot1', 'Conservative Bot', 'conservative', 100000, min_credit_score=750),
            self.BotLender('bot2', 'Aggressive Bot', 'aggressive', 100000, min_credit_score=650),
            self.BotLender('bot3', 'Balanced Bot', 'balanced', 100000, min_credit_score=700)
        ]
        
        # Simulate bidding
        bids = []
        for bot in bots:
            if bot.should_bid_on_loan(converted_loan, converted_borrower):
                interest_rate = bot.calculate_interest_rate(converted_loan, converted_borrower)
                bid = {
                    'lender_id': bot.bot_id,
                    'amount': Decimal(str(converted_loan['amount'])),
                    'interest_rate': Decimal(str(interest_rate)),
                    'lender_name': bot.name
                }
                bids.append(bid)
        
        # Test that bids were placed
        self.assertGreater(len(bids), 0)
        
        # Test template filter with the bids
        converted_bids = self.convert_dynamodb_data(bids)
        min_rate = self.dict_min_filter(converted_bids, 'interest_rate')
        
        # Verify minimum rate is reasonable
        self.assertGreater(min_rate, 0)
        self.assertLess(min_rate, 15)
    
    def test_bot_competition(self):
        """Test that bots compete effectively"""
        loan = {
            'id': 'competition-loan',
            'amount': 20000,
            'term_months': 48,
            'max_interest_rate': 15.0,
            'purpose': 'home_improvement'
        }
        borrower = {'credit_score': 720, 'annual_income': 65000}
        
        # Create multiple bots with different strategies
        bots = [
            self.BotLender('bot1', 'Conservative 1', 'conservative', 200000, min_credit_score=700),
            self.BotLender('bot2', 'Conservative 2', 'conservative', 150000, min_credit_score=720),
            self.BotLender('bot3', 'Aggressive 1', 'aggressive', 100000, min_credit_score=650),
            self.BotLender('bot4', 'Balanced 1', 'balanced', 175000, min_credit_score=700)
        ]
        
        rates = []
        for bot in bots:
            if bot.should_bid_on_loan(loan, borrower):
                rate = bot.calculate_interest_rate(loan, borrower)
                rates.append(rate)
        
        # Should have multiple competitive rates
        self.assertGreater(len(rates), 1)
        
        # Rates should vary (competition)
        self.assertGreater(max(rates) - min(rates), 0.1)


class TestPerformance(unittest.TestCase):
    """Performance tests for the system"""
    
    def setUp(self):
        """Set up performance test fixtures"""
        try:
            from bot_lenders import BotLender
            self.BotLender = BotLender
        except ImportError:
            self.skipTest("Bot lenders module not available")
    
    def test_bot_evaluation_performance(self):
        """Test bot evaluation performance with multiple loans"""
        import time
        
        # Create a bot
        bot = self.BotLender('perf-bot', 'Performance Bot', 'balanced', 1000000)
        
        # Create multiple loan scenarios
        loans = []
        borrowers = []
        for i in range(100):
            loans.append({
                'id': f'loan-{i}',
                'amount': 10000 + (i * 100),
                'term_months': 36,
                'max_interest_rate': 12.0,
                'purpose': 'debt_consolidation'
            })
            borrowers.append({
                'credit_score': 650 + (i % 150),
                'annual_income': 40000 + (i * 500)
            })
        
        # Time the evaluation
        start_time = time.time()
        
        evaluations = 0
        for loan, borrower in zip(loans, borrowers):
            if bot.should_bid_on_loan(loan, borrower):
                bot.calculate_interest_rate(loan, borrower)
                evaluations += 1
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete quickly
        self.assertLess(elapsed, 1.0)  # Less than 1 second for 100 evaluations
        self.assertGreater(evaluations, 0)  # Should evaluate some loans


def run_test_suite():
    """Run the complete test suite with detailed reporting"""
    
    print("🧪 P2P Lending Platform - Comprehensive Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_classes = [
        TestTemplateFilters,
        TestDataConversion,
        TestBotLender,
        TestBotLenderManager,
        TestDynamoDBModels,
        TestFlaskRoutes,
        TestIntegration,
        TestPerformance
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    print(f"\nRunning {suite.countTestCases()} tests across {len(test_classes)} test classes...\n")
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Suite Summary")
    print("=" * 60)
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
    
    if result.skipped:
        print(f"\n⏭️  Skipped Tests:")
        for test, reason in result.skipped:
            print(f"  • {test}: {reason}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("🎉 All tests passed! The system is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return False


if __name__ == '__main__':
    success = run_test_suite()
    sys.exit(0 if success else 1)
