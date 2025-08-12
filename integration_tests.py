#!/usr/bin/env python3
"""
Integration Test Suite for P2P Lending Platform
Tests end-to-end workflows and system integration
"""

import unittest
import sys
import os
import json
import time
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestLoanBiddingWorkflow(unittest.TestCase):
    """Test complete loan bidding workflow"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        try:
            from bot_lenders import BotLender, BotLenderManager
            from app_dynamodb import convert_dynamodb_data, dict_min_filter, dict_avg_filter
            
            self.BotLender = BotLender
            self.BotLenderManager = BotLenderManager
            self.convert_dynamodb_data = convert_dynamodb_data
            self.dict_min_filter = dict_min_filter
            self.dict_avg_filter = dict_avg_filter
        except ImportError:
            self.skipTest("Required modules not available")
    
    def test_complete_bidding_workflow(self):
        """Test complete workflow from loan creation to bid evaluation"""
        
        # Step 1: Create a loan request (simulated DynamoDB data)
        loan_request = {
            'id': 'integration-loan-001',
            'borrower_id': 'borrower-123',
            'amount': Decimal('25000'),
            'purpose': 'debt_consolidation',
            'term_months': 48,
            'max_interest_rate': Decimal('12.0'),
            'description': 'Consolidating credit card debt',
            'status': 'open',
            'created_at': '2023-08-12T10:00:00Z'
        }
        
        # Step 2: Create borrower profile
        borrower_profile = {
            'id': 'borrower-123',
            'credit_score': 740,
            'annual_income': Decimal('75000'),
            'employment_status': 'employed',
            'debt_to_income_ratio': Decimal('0.25')
        }
        
        # Step 3: Convert DynamoDB data
        converted_loan = self.convert_dynamodb_data(loan_request)
        converted_borrower = self.convert_dynamodb_data(borrower_profile)
        
        # Step 4: Create bot lenders
        bots = [
            self.BotLender('bot-conservative-1', 'SafetyFirst Capital', 'conservative', 500000, min_credit_score=720),
            self.BotLender('bot-aggressive-1', 'GrowthMax Lending', 'aggressive', 300000, min_credit_score=650),
            self.BotLender('bot-balanced-1', 'BalancedChoice Finance', 'balanced', 400000, min_credit_score=700),
            self.BotLender('bot-aggressive-2', 'QuickCash Solutions', 'aggressive', 200000, min_credit_score=600, max_loan_amount=20000)
        ]
        
        # Step 5: Simulate bidding process
        bids = []
        for bot in bots:
            if bot.should_bid_on_loan(converted_loan, converted_borrower):
                interest_rate = bot.calculate_interest_rate(converted_loan, converted_borrower)
                
                bid = {
                    'id': f'bid-{bot.bot_id}-{int(time.time())}',
                    'loan_request_id': converted_loan['id'],
                    'lender_id': bot.bot_id,
                    'lender_name': bot.name,
                    'amount': Decimal(str(converted_loan['amount'])),
                    'interest_rate': Decimal(str(interest_rate)),
                    'message': f'Competitive rate from {bot.name}',
                    'status': 'pending',
                    'created_at': '2023-08-12T10:05:00Z'
                }
                bids.append(bid)
        
        # Step 6: Verify bidding results
        self.assertGreater(len(bids), 0, "At least one bot should have placed a bid")
        self.assertLessEqual(len(bids), 4, "No more than 4 bids should be placed")
        
        # Step 7: Convert bids for template processing
        converted_bids = self.convert_dynamodb_data(bids)
        
        # Step 8: Test template filter functionality
        if converted_bids:
            min_rate = self.dict_min_filter(converted_bids, 'interest_rate')
            avg_rate = self.dict_avg_filter(converted_bids, 'interest_rate')
            
            self.assertGreater(min_rate, 0, "Minimum rate should be positive")
            self.assertLess(min_rate, 15, "Minimum rate should be reasonable")
            self.assertGreater(avg_rate, 0, "Average rate should be positive")
            self.assertLess(avg_rate, 15, "Average rate should be reasonable")
            self.assertGreaterEqual(avg_rate, min_rate, "Average should be >= minimum")
        
        # Step 9: Verify bid competition
        if len(converted_bids) > 1:
            rates = [bid['interest_rate'] for bid in converted_bids]
            rate_spread = max(rates) - min(rates)
            self.assertGreater(rate_spread, 0, "There should be rate competition between bots")
        
        print(f"✅ Workflow test completed: {len(bids)} bids placed for ${converted_loan['amount']} loan")
        for bid in converted_bids:
            print(f"   • {bid['lender_name']}: {bid['interest_rate']:.2f}% APR")
    
    def test_multi_loan_scenario(self):
        """Test bots handling multiple loans simultaneously"""
        
        # Create multiple loan scenarios
        loan_scenarios = [
            {
                'loan': {
                    'id': 'loan-small',
                    'amount': Decimal('8000'),
                    'term_months': 24,
                    'max_interest_rate': Decimal('15.0'),
                    'purpose': 'emergency'
                },
                'borrower': {'credit_score': 680, 'annual_income': Decimal('45000')}
            },
            {
                'loan': {
                    'id': 'loan-medium',
                    'amount': Decimal('20000'),
                    'term_months': 36,
                    'max_interest_rate': Decimal('10.0'),
                    'purpose': 'home_improvement'
                },
                'borrower': {'credit_score': 750, 'annual_income': Decimal('70000')}
            },
            {
                'loan': {
                    'id': 'loan-large',
                    'amount': Decimal('40000'),
                    'term_months': 60,
                    'max_interest_rate': Decimal('8.0'),
                    'purpose': 'business'
                },
                'borrower': {'credit_score': 800, 'annual_income': Decimal('120000')}
            }
        ]
        
        # Create bot manager
        manager = self.BotLenderManager()
        
        # Add test bots
        test_bots = [
            self.BotLender('multi-bot-1', 'Conservative Multi', 'conservative', 200000, min_credit_score=720),
            self.BotLender('multi-bot-2', 'Aggressive Multi', 'aggressive', 150000, min_credit_score=650),
            self.BotLender('multi-bot-3', 'Balanced Multi', 'balanced', 175000, min_credit_score=700)
        ]
        manager.bots = test_bots
        
        # Process each loan
        total_bids = 0
        loan_results = []
        
        for scenario in loan_scenarios:
            loan = self.convert_dynamodb_data(scenario['loan'])
            borrower = self.convert_dynamodb_data(scenario['borrower'])
            
            scenario_bids = 0
            for bot in manager.bots:
                if bot.should_bid_on_loan(loan, borrower):
                    rate = bot.calculate_interest_rate(loan, borrower)
                    scenario_bids += 1
                    total_bids += 1
            
            loan_results.append({
                'loan_id': loan['id'],
                'amount': loan['amount'],
                'credit_score': borrower['credit_score'],
                'bids_received': scenario_bids
            })
        
        # Verify results
        self.assertGreater(total_bids, 0, "Should have received some bids across all loans")
        
        # Higher credit scores should generally receive more bids
        high_credit_loans = [r for r in loan_results if r['credit_score'] >= 750]
        low_credit_loans = [r for r in loan_results if r['credit_score'] < 700]
        
        if high_credit_loans and low_credit_loans:
            avg_bids_high = sum(r['bids_received'] for r in high_credit_loans) / len(high_credit_loans)
            avg_bids_low = sum(r['bids_received'] for r in low_credit_loans) / len(low_credit_loans)
            self.assertGreaterEqual(avg_bids_high, avg_bids_low, "High credit borrowers should get more bids")
        
        print(f"✅ Multi-loan test: {total_bids} total bids across {len(loan_scenarios)} loans")
        for result in loan_results:
            print(f"   • {result['loan_id']}: {result['bids_received']} bids (Credit: {result['credit_score']})")


class TestBotCompetition(unittest.TestCase):
    """Test bot competition and market dynamics"""
    
    def setUp(self):
        """Set up competition test fixtures"""
        try:
            from bot_lenders import BotLender
            self.BotLender = BotLender
        except ImportError:
            self.skipTest("Bot lenders module not available")
    
    def test_rate_competition(self):
        """Test that bots compete on interest rates"""
        
        # Create competitive scenario
        loan = {
            'id': 'competitive-loan',
            'amount': 15000,
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        }
        borrower = {'credit_score': 720, 'annual_income': 65000}
        
        # Create multiple bots with same strategy but different parameters
        competitive_bots = [
            self.BotLender('comp-1', 'Competitor 1', 'balanced', 100000, min_credit_score=700),
            self.BotLender('comp-2', 'Competitor 2', 'balanced', 150000, min_credit_score=700),
            self.BotLender('comp-3', 'Competitor 3', 'balanced', 200000, min_credit_score=700),
            self.BotLender('comp-4', 'Competitor 4', 'balanced', 120000, min_credit_score=700)
        ]
        
        # Get rates from all bots
        rates = []
        for bot in competitive_bots:
            if bot.should_bid_on_loan(loan, borrower):
                rate = bot.calculate_interest_rate(loan, borrower)
                rates.append(rate)
        
        # Verify competition
        self.assertGreater(len(rates), 1, "Multiple bots should compete")
        
        # Rates should vary due to randomness in calculation
        if len(rates) > 1:
            rate_spread = max(rates) - min(rates)
            self.assertGreater(rate_spread, 0, "Rates should vary between competitors")
            self.assertLess(rate_spread, 3.0, "Rate spread should be reasonable")
        
        print(f"✅ Competition test: {len(rates)} competing rates, spread: {max(rates) - min(rates):.2f}%")
    
    def test_strategy_differentiation(self):
        """Test that different strategies produce different behaviors"""
        
        # Test with medium-risk borrower
        loan = {
            'id': 'strategy-test',
            'amount': 20000,
            'term_months': 48,
            'max_interest_rate': 14.0,
            'purpose': 'business'
        }
        borrower = {'credit_score': 690, 'annual_income': 55000}
        
        # Create bots with different strategies
        conservative_bot = self.BotLender('strat-cons', 'Conservative', 'conservative', 100000, min_credit_score=750)
        aggressive_bot = self.BotLender('strat-aggr', 'Aggressive', 'aggressive', 100000, min_credit_score=650)
        balanced_bot = self.BotLender('strat-bal', 'Balanced', 'balanced', 100000, min_credit_score=700)
        
        # Test bidding decisions
        conservative_bids = conservative_bot.should_bid_on_loan(loan, borrower)
        aggressive_bids = aggressive_bot.should_bid_on_loan(loan, borrower)
        balanced_bids = balanced_bot.should_bid_on_loan(loan, borrower)
        
        # Conservative should be most restrictive
        self.assertFalse(conservative_bids, "Conservative bot should not bid on medium-risk loan")
        self.assertTrue(aggressive_bids, "Aggressive bot should bid on medium-risk loan")
        
        # Test rate differences for qualifying bots
        if aggressive_bids and balanced_bids:
            aggressive_rate = aggressive_bot.calculate_interest_rate(loan, borrower)
            balanced_rate = balanced_bot.calculate_interest_rate(loan, borrower)
            
            # Aggressive should generally charge higher rates for higher risk
            self.assertGreaterEqual(aggressive_rate, balanced_rate - 1.0, "Aggressive should charge competitive rates")
        
        print(f"✅ Strategy test: Conservative={conservative_bids}, Aggressive={aggressive_bids}, Balanced={balanced_bids}")
    
    def test_capital_constraints(self):
        """Test bot behavior under capital constraints"""
        
        # Create bot with limited capital
        limited_bot = self.BotLender('limited', 'Limited Capital Bot', 'aggressive', 50000, min_credit_score=600)
        
        # Create multiple large loans
        large_loans = [
            {'id': f'large-{i}', 'amount': 25000, 'term_months': 36, 'max_interest_rate': 12.0, 'purpose': 'business'}
            for i in range(5)
        ]
        borrower = {'credit_score': 700, 'annual_income': 80000}
        
        # Bot should only bid on loans it can afford
        successful_bids = 0
        for loan in large_loans:
            if limited_bot.should_bid_on_loan(loan, borrower):
                # Simulate placing the bid
                limited_bot.available_capital -= Decimal(str(loan['amount']))
                limited_bot.active_bids.append(f"bid-{loan['id']}")
                successful_bids += 1
        
        # Should have placed exactly 2 bids (50000 / 25000 = 2)
        self.assertEqual(successful_bids, 2, "Bot should place exactly 2 bids given capital constraints")
        self.assertEqual(limited_bot.available_capital, 0, "All capital should be deployed")
        
        print(f"✅ Capital constraint test: {successful_bids} bids placed, ${limited_bot.available_capital} remaining")


class TestSystemIntegration(unittest.TestCase):
    """Test system-wide integration scenarios"""
    
    def setUp(self):
        """Set up system integration fixtures"""
        try:
            from bot_lenders import BotLenderManager
            from app_dynamodb import convert_dynamodb_data
            
            self.BotLenderManager = BotLenderManager
            self.convert_dynamodb_data = convert_dynamodb_data
        except ImportError:
            self.skipTest("Required modules not available")
    
    @patch('bot_lenders.user_model')
    @patch('bot_lenders.loan_model')
    @patch('bot_lenders.bid_model')
    def test_automated_bidding_simulation(self, mock_bid_model, mock_loan_model, mock_user_model):
        """Test automated bidding system simulation"""
        
        # Mock user creation for bots
        mock_user_model.create_user.return_value = 'mock-bot-user-id'
        
        # Mock open loans
        mock_open_loans = [
            {
                'id': 'auto-loan-1',
                'borrower_id': 'borrower-1',
                'amount': Decimal('15000'),
                'term_months': 36,
                'max_interest_rate': Decimal('12.0'),
                'purpose': 'debt_consolidation'
            },
            {
                'id': 'auto-loan-2',
                'borrower_id': 'borrower-2',
                'amount': Decimal('8000'),
                'term_months': 24,
                'max_interest_rate': Decimal('15.0'),
                'purpose': 'emergency'
            }
        ]
        mock_loan_model.get_all_open_loans.return_value = mock_open_loans
        
        # Mock borrower data
        mock_borrower_data = {
            'borrower-1': {'credit_score': 740, 'annual_income': Decimal('65000')},
            'borrower-2': {'credit_score': 660, 'annual_income': Decimal('45000')}
        }
        mock_user_model.get_user_by_id.side_effect = lambda user_id: mock_borrower_data.get(user_id)
        
        # Mock existing bids (empty)
        mock_bid_model.get_bids_for_loan.return_value = []
        
        # Mock successful bid creation
        mock_bid_model.create_bid.return_value = 'mock-bid-id'
        
        # Create and initialize bot manager
        manager = self.BotLenderManager()
        manager.create_bot_lenders()
        
        # Simulate processing new loans
        manager._process_new_loans()
        
        # Verify bids were attempted
        self.assertGreater(mock_bid_model.create_bid.call_count, 0, "Bids should have been placed")
        
        # Verify loan and borrower data was fetched
        mock_loan_model.get_all_open_loans.assert_called_once()
        self.assertGreater(mock_user_model.get_user_by_id.call_count, 0, "Borrower data should have been fetched")
        
        print(f"✅ Automated bidding simulation: {mock_bid_model.create_bid.call_count} bids attempted")
    
    def test_data_flow_integrity(self):
        """Test data integrity through the complete flow"""
        
        # Start with DynamoDB-style data
        original_data = {
            'loan': {
                'id': 'data-flow-loan',
                'amount': Decimal('22500.75'),
                'interest_rate': Decimal('7.25'),
                'term_months': 42
            },
            'bids': [
                {'id': 'bid-1', 'amount': Decimal('22500.75'), 'rate': Decimal('6.8')},
                {'id': 'bid-2', 'amount': Decimal('22500.75'), 'rate': Decimal('7.1')},
                {'id': 'bid-3', 'amount': Decimal('22500.75'), 'rate': Decimal('6.95')}
            ]
        }
        
        # Convert data
        converted_data = self.convert_dynamodb_data(original_data)
        
        # Verify conversion integrity
        self.assertEqual(converted_data['loan']['amount'], 22500.75)
        self.assertEqual(converted_data['loan']['interest_rate'], 7.25)
        self.assertEqual(converted_data['loan']['term_months'], 42)
        
        # Verify bid data integrity
        self.assertEqual(len(converted_data['bids']), 3)
        for i, bid in enumerate(converted_data['bids']):
            self.assertIsInstance(bid['amount'], float)
            self.assertIsInstance(bid['rate'], float)
            self.assertEqual(bid['amount'], 22500.75)
        
        # Test template filters with converted data
        from app_dynamodb import dict_min_filter, dict_avg_filter
        
        min_rate = dict_min_filter(converted_data['bids'], 'rate')
        avg_rate = dict_avg_filter(converted_data['bids'], 'rate')
        
        self.assertEqual(min_rate, 6.8)
        self.assertAlmostEqual(avg_rate, 6.95, places=2)
        
        print(f"✅ Data flow integrity: ${converted_data['loan']['amount']} loan, {len(converted_data['bids'])} bids")


def run_integration_tests():
    """Run integration tests with detailed reporting"""
    
    print("🔗 P2P Lending Platform - Integration Test Suite")
    print("=" * 55)
    
    # Create test suite
    test_classes = [
        TestLoanBiddingWorkflow,
        TestBotCompetition,
        TestSystemIntegration
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
    
    print(f"\nRunning {suite.countTestCases()} integration tests...\n")
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 55)
    print("📊 Integration Test Summary")
    print("=" * 55)
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
        print("🎉 All integration tests passed!")
        return True
    else:
        print("❌ Some integration tests failed.")
        return False


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
