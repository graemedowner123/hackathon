import random
import time
from datetime import datetime, timedelta
from decimal import Decimal
import threading
import logging
from dynamodb_models import user_model, loan_model, bid_model, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotLender:
    """Represents an automated bot lender with specific lending criteria"""
    
    def __init__(self, bot_id, name, strategy, capital, min_credit_score=600, 
                 max_loan_amount=50000, preferred_terms=None, risk_tolerance='medium'):
        self.bot_id = bot_id
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
            logger.info(f"{self.name}: Insufficient capital for loan {loan['id']}")
            return False
        
        # Check credit score requirement
        borrower_credit_score = borrower.get('credit_score', 0)
        if borrower_credit_score < self.min_credit_score:
            logger.info(f"{self.name}: Credit score {borrower_credit_score} below minimum {self.min_credit_score}")
            return False
        
        # Check loan amount limits
        if loan_amount > self.max_loan_amount:
            logger.info(f"{self.name}: Loan amount ${loan_amount} exceeds maximum ${self.max_loan_amount}")
            return False
        
        # Check preferred terms
        if loan['term_months'] not in self.preferred_terms:
            logger.info(f"{self.name}: Term {loan['term_months']} months not in preferred terms")
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
        
        # High credit score requirement
        if credit_score < 750:
            return False
        
        # Debt-to-income ratio check (assuming 20% max)
        if annual_income > 0 and (loan_amount / annual_income) > 0.2:
            return False
        
        # Only certain loan purposes
        safe_purposes = ['debt_consolidation', 'home_improvement', 'medical']
        if loan.get('purpose', '').lower().replace(' ', '_') not in safe_purposes:
            return False
        
        return True
    
    def _aggressive_check(self, loan, borrower):
        """Aggressive lending strategy - takes more risks for higher returns"""
        credit_score = borrower.get('credit_score', 0)
        
        # Lower credit score threshold but higher interest rates
        if credit_score < 650:
            return False
        
        # Accept most loan purposes
        return True
    
    def _balanced_check(self, loan, borrower):
        """Balanced lending strategy"""
        credit_score = borrower.get('credit_score', 0)
        annual_income = float(borrower.get('annual_income', 0))
        loan_amount = float(loan['amount'])
        
        # Moderate credit score requirement
        if credit_score < 700:
            return False
        
        # Moderate debt-to-income ratio
        if annual_income > 0 and (loan_amount / annual_income) > 0.3:
            return False
        
        return True
    
    def calculate_interest_rate(self, loan, borrower):
        """Calculate competitive interest rate based on risk assessment"""
        base_rate = 5.0  # Base interest rate
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
        """Place a bid on a loan"""
        if not self.should_bid_on_loan(loan, borrower):
            return None
        
        loan_amount = float(loan['amount'])
        interest_rate = self.calculate_interest_rate(loan, borrower)
        
        # Generate bot message
        messages = [
            f"Competitive rate offered by {self.name}. Quick approval process.",
            f"Automated lending with favorable terms. {self.name} at your service.",
            f"Fast funding available. {self.name} offers reliable lending solutions.",
            f"Excellent rate for qualified borrowers. {self.name} - trusted lending partner.",
            f"Quick decision and funding. {self.name} specializes in {loan.get('purpose', 'personal')} loans."
        ]
        message = random.choice(messages)
        
        try:
            # Ensure all values are properly formatted
            loan_id = str(loan['id'])
            lender_id = str(self.bot_id)
            
            bid_id = bid_model.create_bid(
                loan_request_id=loan_id,
                lender_id=lender_id,
                amount=loan_amount,
                interest_rate=interest_rate,
                message=message
            )
            
            if bid_id:
                self.available_capital -= Decimal(str(loan_amount))
                self.active_bids.append(bid_id)
                logger.info(f"{self.name}: Placed bid ${loan_amount} at {interest_rate}% on loan {loan_id}")
                return bid_id
            else:
                logger.warning(f"{self.name}: Failed to create bid for loan {loan_id}")
            
        except Exception as e:
            logger.error(f"{self.name}: Error placing bid on loan {loan.get('id', 'unknown')} - {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
        
        return None

class BotLenderManager:
    """Manages multiple bot lenders and their automated bidding"""
    
    def __init__(self):
        self.bots = []
        self.running = False
        self.bid_thread = None
        
    def create_bot_lenders(self):
        """Create a diverse set of bot lenders"""
        
        bot_configs = [
            {
                'name': 'SafetyFirst Capital',
                'strategy': 'conservative',
                'capital': 500000,
                'min_credit_score': 750,
                'max_loan_amount': 25000,
                'preferred_terms': [24, 36, 48],
                'risk_tolerance': 'low'
            },
            {
                'name': 'GrowthMax Lending',
                'strategy': 'aggressive',
                'capital': 300000,
                'min_credit_score': 650,
                'max_loan_amount': 50000,
                'preferred_terms': [12, 24, 36, 48, 60],
                'risk_tolerance': 'high'
            },
            {
                'name': 'BalancedChoice Finance',
                'strategy': 'balanced',
                'capital': 400000,
                'min_credit_score': 700,
                'max_loan_amount': 35000,
                'preferred_terms': [24, 36, 48],
                'risk_tolerance': 'medium'
            },
            {
                'name': 'QuickCash Solutions',
                'strategy': 'aggressive',
                'capital': 200000,
                'min_credit_score': 600,
                'max_loan_amount': 15000,
                'preferred_terms': [12, 24, 36],
                'risk_tolerance': 'high'
            },
            {
                'name': 'PremiumRate Investors',
                'strategy': 'conservative',
                'capital': 750000,
                'min_credit_score': 780,
                'max_loan_amount': 100000,
                'preferred_terms': [36, 48, 60],
                'risk_tolerance': 'low'
            },
            {
                'name': 'FlexiLend Partners',
                'strategy': 'balanced',
                'capital': 350000,
                'min_credit_score': 680,
                'max_loan_amount': 30000,
                'preferred_terms': [12, 24, 36, 48],
                'risk_tolerance': 'medium'
            }
        ]
        
        for config in bot_configs:
            # Create bot user account
            bot_id = user_model.create_user(
                email=f"{config['name'].lower().replace(' ', '.')}@botlenders.com",
                password="bot_secure_password_123",
                first_name=config['name'].split()[0],
                last_name="Bot",
                phone="555-BOT-LEND",
                user_type="lender",
                annual_income=1000000  # High income for bots
            )
            
            if bot_id:
                bot = BotLender(
                    bot_id=bot_id,
                    name=config['name'],
                    strategy=config['strategy'],
                    capital=config['capital'],
                    min_credit_score=config['min_credit_score'],
                    max_loan_amount=config['max_loan_amount'],
                    preferred_terms=config['preferred_terms'],
                    risk_tolerance=config['risk_tolerance']
                )
                self.bots.append(bot)
                logger.info(f"Created bot lender: {config['name']} with ${config['capital']} capital")
            else:
                logger.error(f"Failed to create bot user for {config['name']}")
    
    def start_automated_bidding(self, check_interval=30):
        """Start the automated bidding process"""
        if self.running:
            logger.warning("Automated bidding is already running")
            return
        
        self.running = True
        self.bid_thread = threading.Thread(
            target=self._bidding_loop,
            args=(check_interval,),
            daemon=True
        )
        self.bid_thread.start()
        logger.info(f"Started automated bidding with {len(self.bots)} bots")
    
    def stop_automated_bidding(self):
        """Stop the automated bidding process"""
        self.running = False
        if self.bid_thread:
            self.bid_thread.join(timeout=5)
        logger.info("Stopped automated bidding")
    
    def _bidding_loop(self, check_interval):
        """Main bidding loop that runs in a separate thread"""
        while self.running:
            try:
                self._process_new_loans()
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in bidding loop: {e}")
                time.sleep(check_interval)
    
    def _process_new_loans(self):
        """Process new loan requests and place bids"""
        try:
            # Get all open loans
            open_loans = loan_model.get_all_open_loans()
            
            if not open_loans:
                logger.debug("No open loans found")
                return
            
            for loan in open_loans:
                # Get borrower information
                borrower_data = user_model.get_user_by_id(loan['borrower_id'])
                if not borrower_data:
                    continue
                
                # Get existing bids for this loan
                existing_bids = bid_model.get_bids_for_loan(loan['id'])
                
                # Check if any of our bots have already bid
                bot_ids = [bot.bot_id for bot in self.bots]
                existing_bot_bids = [bid for bid in existing_bids if bid['lender_id'] in bot_ids]
                
                # Limit bot bids per loan (max 3 bots can bid on same loan)
                if len(existing_bot_bids) >= 3:
                    continue
                
                # Randomly select bots to bid (not all bots bid on every loan)
                available_bots = [bot for bot in self.bots if bot.bot_id not in [bid['lender_id'] for bid in existing_bot_bids]]
                
                # Each loan gets 1-2 bot bids with some probability
                num_bids = random.choices([0, 1, 2], weights=[0.3, 0.5, 0.2])[0]
                selected_bots = random.sample(available_bots, min(num_bids, len(available_bots)))
                
                for bot in selected_bots:
                    # Add some delay between bids to seem more natural
                    time.sleep(random.uniform(1, 5))
                    bot.place_bid(loan, borrower_data)
                    
        except Exception as e:
            logger.error(f"Error processing new loans: {e}")
    
    def get_bot_stats(self):
        """Get statistics about bot performance"""
        stats = {
            'total_bots': len(self.bots),
            'total_capital': sum(bot.capital for bot in self.bots),
            'available_capital': sum(bot.available_capital for bot in self.bots),
            'active_bids': sum(len(bot.active_bids) for bot in self.bots),
            'funded_loans': sum(len(bot.funded_loans) for bot in self.bots),
            'bots': []
        }
        
        for bot in self.bots:
            bot_stats = {
                'name': bot.name,
                'strategy': bot.strategy,
                'capital': float(bot.capital),
                'available_capital': float(bot.available_capital),
                'utilization': float((bot.capital - bot.available_capital) / bot.capital * 100),
                'active_bids': len(bot.active_bids),
                'funded_loans': len(bot.funded_loans)
            }
            stats['bots'].append(bot_stats)
        
        return stats

# Global bot manager instance
bot_manager = BotLenderManager()
