#!/usr/bin/env python3
"""
Demo script showing how the bot bidding system works
This runs without requiring AWS credentials
"""

import random
import time
from datetime import datetime
from decimal import Decimal

class MockBotLender:
    """Mock version of BotLender for demonstration"""
    
    def __init__(self, name, strategy, capital, min_credit_score=600, 
                 max_loan_amount=50000, preferred_terms=None, risk_tolerance='medium'):
        self.name = name
        self.strategy = strategy
        self.capital = Decimal(str(capital))
        self.available_capital = Decimal(str(capital))
        self.min_credit_score = min_credit_score
        self.max_loan_amount = max_loan_amount
        self.preferred_terms = preferred_terms or [12, 24, 36, 48, 60]
        self.risk_tolerance = risk_tolerance
        self.active_bids = []
        self.funded_loans = []
        
    def should_bid_on_loan(self, loan, borrower):
        """Determine if this bot should bid on a given loan"""
        
        # Check available capital
        loan_amount = float(loan['amount'])
        if self.available_capital < loan_amount:
            print(f"  {self.name}: ❌ Insufficient capital for loan {loan['id']}")
            return False
        
        # Check credit score requirement
        borrower_credit_score = borrower.get('credit_score', 0)
        if borrower_credit_score < self.min_credit_score:
            print(f"  {self.name}: ❌ Credit score {borrower_credit_score} below minimum {self.min_credit_score}")
            return False
        
        # Check loan amount limits
        if loan_amount > self.max_loan_amount:
            print(f"  {self.name}: ❌ Loan amount ${loan_amount} exceeds maximum ${self.max_loan_amount}")
            return False
        
        # Check preferred terms
        if loan['term_months'] not in self.preferred_terms:
            print(f"  {self.name}: ❌ Term {loan['term_months']} months not in preferred terms")
            return False
        
        # Strategy-specific checks
        if self.strategy == 'conservative':
            return self._conservative_check(loan, borrower)
        elif self.strategy == 'aggressive':
            return self._aggressive_check(loan, borrower)
        elif self.strategy == 'balanced':
            return self._balanced_check(loan, borrower)
        
        return True
    
    def _conservative_check(self, loan, borrower):
        """Conservative lending strategy"""
        credit_score = borrower.get('credit_score', 0)
        annual_income = float(borrower.get('annual_income', 0))
        loan_amount = float(loan['amount'])
        
        if credit_score < 750:
            print(f"  {self.name}: ❌ Conservative strategy requires credit score ≥750 (got {credit_score})")
            return False
        
        if annual_income > 0 and (loan_amount / annual_income) > 0.2:
            print(f"  {self.name}: ❌ Debt-to-income ratio too high for conservative strategy")
            return False
        
        safe_purposes = ['debt_consolidation', 'home_improvement', 'medical']
        if loan.get('purpose', '').lower().replace(' ', '_') not in safe_purposes:
            print(f"  {self.name}: ❌ Loan purpose not suitable for conservative strategy")
            return False
        
        print(f"  {self.name}: ✅ Conservative criteria met")
        return True
    
    def _aggressive_check(self, loan, borrower):
        """Aggressive lending strategy"""
        credit_score = borrower.get('credit_score', 0)
        
        if credit_score < 650:
            print(f"  {self.name}: ❌ Even aggressive strategy requires credit score ≥650 (got {credit_score})")
            return False
        
        print(f"  {self.name}: ✅ Aggressive criteria met")
        return True
    
    def _balanced_check(self, loan, borrower):
        """Balanced lending strategy"""
        credit_score = borrower.get('credit_score', 0)
        annual_income = float(borrower.get('annual_income', 0))
        loan_amount = float(loan['amount'])
        
        if credit_score < 700:
            print(f"  {self.name}: ❌ Balanced strategy requires credit score ≥700 (got {credit_score})")
            return False
        
        if annual_income > 0 and (loan_amount / annual_income) > 0.3:
            print(f"  {self.name}: ❌ Debt-to-income ratio too high for balanced strategy")
            return False
        
        print(f"  {self.name}: ✅ Balanced criteria met")
        return True
    
    def calculate_interest_rate(self, loan, borrower):
        """Calculate competitive interest rate based on risk assessment"""
        base_rate = 5.0
        credit_score = borrower.get('credit_score', 600)
        loan_amount = float(loan['amount'])
        term_months = loan['term_months']
        max_rate = float(loan['max_interest_rate'])
        
        # Credit score adjustment
        if credit_score >= 800:
            credit_adjustment = -1.0
        elif credit_score >= 750:
            credit_adjustment = -0.5
        elif credit_score >= 700:
            credit_adjustment = 0.0
        elif credit_score >= 650:
            credit_adjustment = 1.0
        else:
            credit_adjustment = 2.0
        
        # Loan amount adjustment
        if loan_amount > 25000:
            amount_adjustment = 0.5
        elif loan_amount > 10000:
            amount_adjustment = 0.0
        else:
            amount_adjustment = -0.25
        
        # Term adjustment
        if term_months > 48:
            term_adjustment = 0.5
        elif term_months > 24:
            term_adjustment = 0.0
        else:
            term_adjustment = -0.25
        
        # Strategy adjustment
        if self.strategy == 'conservative':
            strategy_adjustment = -0.5
        elif self.strategy == 'aggressive':
            strategy_adjustment = 1.0
        else:
            strategy_adjustment = 0.0
        
        # Calculate final rate
        calculated_rate = base_rate + credit_adjustment + amount_adjustment + term_adjustment + strategy_adjustment
        
        # Add some randomness for competitive bidding
        randomness = random.uniform(-0.3, 0.3)
        calculated_rate += randomness
        
        # Ensure rate is within bounds
        calculated_rate = max(3.0, min(calculated_rate, max_rate - 0.1))
        
        return round(calculated_rate, 2)
    
    def place_bid(self, loan, borrower):
        """Simulate placing a bid on a loan"""
        if not self.should_bid_on_loan(loan, borrower):
            return None
        
        loan_amount = float(loan['amount'])
        interest_rate = self.calculate_interest_rate(loan, borrower)
        
        messages = [
            f"Competitive rate offered by {self.name}. Quick approval process.",
            f"Automated lending with favorable terms. {self.name} at your service.",
            f"Fast funding available. {self.name} offers reliable lending solutions.",
            f"Excellent rate for qualified borrowers. {self.name} - trusted lending partner.",
            f"Quick decision and funding. {self.name} specializes in {loan.get('purpose', 'personal')} loans."
        ]
        message = random.choice(messages)
        
        # Simulate successful bid
        bid_id = f"bid_{random.randint(1000, 9999)}"
        self.available_capital -= Decimal(str(loan_amount))
        self.active_bids.append(bid_id)
        
        print(f"  {self.name}: 🎯 PLACED BID - ${loan_amount:,.2f} at {interest_rate}% APR")
        print(f"    Message: {message}")
        
        return bid_id

def demo_bot_bidding():
    """Demonstrate the bot bidding system"""
    print("🤖 P2P Lending Bot Bidding System Demo")
    print("=" * 50)
    
    # Create demo bot lenders
    bots = [
        MockBotLender(
            name='SafetyFirst Capital',
            strategy='conservative',
            capital=500000,
            min_credit_score=750,
            max_loan_amount=25000,
            preferred_terms=[24, 36, 48]
        ),
        MockBotLender(
            name='GrowthMax Lending',
            strategy='aggressive',
            capital=300000,
            min_credit_score=650,
            max_loan_amount=50000,
            preferred_terms=[12, 24, 36, 48, 60]
        ),
        MockBotLender(
            name='BalancedChoice Finance',
            strategy='balanced',
            capital=400000,
            min_credit_score=700,
            max_loan_amount=35000,
            preferred_terms=[24, 36, 48]
        ),
        MockBotLender(
            name='QuickCash Solutions',
            strategy='aggressive',
            capital=200000,
            min_credit_score=600,
            max_loan_amount=15000,
            preferred_terms=[12, 24, 36]
        )
    ]
    
    print(f"\n📊 Created {len(bots)} Bot Lenders:")
    for bot in bots:
        print(f"  • {bot.name}: {bot.strategy.title()} strategy, ${bot.capital:,} capital")
    
    # Create sample loan requests
    sample_loans = [
        {
            'id': 'loan_001',
            'amount': 15000,
            'term_months': 36,
            'max_interest_rate': 12.0,
            'purpose': 'debt_consolidation'
        },
        {
            'id': 'loan_002',
            'amount': 8000,
            'term_months': 24,
            'max_interest_rate': 15.0,
            'purpose': 'home_improvement'
        },
        {
            'id': 'loan_003',
            'amount': 25000,
            'term_months': 60,
            'max_interest_rate': 10.0,
            'purpose': 'business'
        },
        {
            'id': 'loan_004',
            'amount': 5000,
            'term_months': 12,
            'max_interest_rate': 18.0,
            'purpose': 'emergency'
        }
    ]
    
    # Create sample borrowers
    sample_borrowers = [
        {'credit_score': 780, 'annual_income': 75000},  # Excellent credit
        {'credit_score': 720, 'annual_income': 55000},  # Good credit
        {'credit_score': 680, 'annual_income': 45000},  # Fair credit
        {'credit_score': 620, 'annual_income': 35000}   # Poor credit
    ]
    
    print(f"\n💰 Processing {len(sample_loans)} Loan Requests:")
    print("-" * 50)
    
    total_bids = 0
    
    for i, loan in enumerate(sample_loans):
        borrower = sample_borrowers[i]
        
        print(f"\n📋 Loan Request #{i+1} (ID: {loan['id']})")
        print(f"   Amount: ${loan['amount']:,}")
        print(f"   Term: {loan['term_months']} months")
        print(f"   Max Rate: {loan['max_interest_rate']}%")
        print(f"   Purpose: {loan['purpose'].replace('_', ' ').title()}")
        print(f"   Borrower: Credit Score {borrower['credit_score']}, Income ${borrower['annual_income']:,}")
        
        print(f"\n🤖 Bot Evaluation:")
        
        loan_bids = 0
        for bot in bots:
            bid_result = bot.place_bid(loan, borrower)
            if bid_result:
                loan_bids += 1
                total_bids += 1
            
            # Add small delay for realism
            time.sleep(0.5)
        
        if loan_bids == 0:
            print(f"  ❌ No bots placed bids on this loan")
        else:
            print(f"  ✅ {loan_bids} bot(s) placed bids on this loan")
    
    print(f"\n📈 Bidding Summary:")
    print(f"   Total Bids Placed: {total_bids}")
    print(f"   Average Bids per Loan: {total_bids/len(sample_loans):.1f}")
    
    print(f"\n💼 Bot Capital Status:")
    for bot in bots:
        utilization = float((bot.capital - bot.available_capital) / bot.capital * 100)
        print(f"   {bot.name}: ${bot.available_capital:,.2f} available ({utilization:.1f}% utilized)")
    
    print(f"\n🎉 Demo completed! The bot system is working correctly.")
    print(f"   In the real system, bots would continuously monitor for new loans")
    print(f"   and place competitive bids automatically every 30-60 seconds.")

if __name__ == "__main__":
    demo_bot_bidding()
