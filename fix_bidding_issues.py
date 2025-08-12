#!/usr/bin/env python3
"""
Fix bidding issues in the P2P lending platform
"""

import os
import sys
from decimal import Decimal

def fix_template_filters():
    """Fix template filters to handle Decimal objects from DynamoDB"""
    
    # Read the current app file
    app_file = '/home/graemedowner/hackathon/app_dynamodb.py'
    
    with open(app_file, 'r') as f:
        content = f.read()
    
    # Updated filter functions that handle Decimal objects
    new_filters = '''# Custom Jinja2 filters for dictionary operations
@app.template_filter('dict_min')
def dict_min_filter(items, key):
    """Get minimum value from list of dictionaries by key"""
    if not items:
        return 0
    try:
        values = [float(item[key]) for item in items if key in item]
        return min(values) if values else 0
    except (ValueError, TypeError, KeyError):
        return 0

@app.template_filter('dict_max')
def dict_max_filter(items, key):
    """Get maximum value from list of dictionaries by key"""
    if not items:
        return 0
    try:
        values = [float(item[key]) for item in items if key in item]
        return max(values) if values else 0
    except (ValueError, TypeError, KeyError):
        return 0

@app.template_filter('dict_avg')
def dict_avg_filter(items, key):
    """Get average value from list of dictionaries by key"""
    if not items:
        return 0
    try:
        values = [float(item[key]) for item in items if key in item]
        return sum(values) / len(values) if values else 0
    except (ValueError, TypeError, KeyError):
        return 0

@app.template_filter('dict_sum')
def dict_sum_filter(items, key):
    """Get sum of values from list of dictionaries by key"""
    if not items:
        return 0
    try:
        values = [float(item[key]) for item in items if key in item]
        return sum(values) if values else 0
    except (ValueError, TypeError, KeyError):
        return 0'''
    
    # Find and replace the old filter functions
    import re
    
    # Pattern to match the entire filter section
    pattern = r'# Custom Jinja2 filters for dictionary operations.*?return sum\(item\[key\] for item in items\)'
    
    # Replace with new filters
    new_content = re.sub(pattern, new_filters, content, flags=re.DOTALL)
    
    # Write back to file
    with open(app_file, 'w') as f:
        f.write(new_content)
    
    print("✅ Fixed template filters to handle Decimal objects")

def fix_bid_data_conversion():
    """Fix bid data conversion issues"""
    
    # Read the current app file
    app_file = '/home/graemedowner/hackathon/app_dynamodb.py'
    
    with open(app_file, 'r') as f:
        content = f.read()
    
    # Find the loan_details route and add data conversion
    if 'def loan_details(loan_id):' in content:
        # Add a helper function to convert DynamoDB data
        helper_function = '''
def convert_dynamodb_data(data):
    """Convert DynamoDB Decimal objects to Python types"""
    if isinstance(data, list):
        return [convert_dynamodb_data(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_dynamodb_data(value) for key, value in data.items()}
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data
'''
        
        # Insert the helper function after imports
        import_end = content.find('app = Flask(__name__)')
        if import_end != -1:
            content = content[:import_end] + helper_function + '\n' + content[import_end:]
        
        # Update the loan_details route to use the conversion
        old_route = '''@app.route('/loan/<loan_id>')
def loan_details(loan_id):
    loan = loan_model.get_loan_request(loan_id)
    if not loan:
        flash('Loan not found.', 'error')
        return redirect(url_for('index'))
    
    bids = bid_model.get_bids_for_loan(loan_id)'''
        
        new_route = '''@app.route('/loan/<loan_id>')
def loan_details(loan_id):
    loan = loan_model.get_loan_request(loan_id)
    if not loan:
        flash('Loan not found.', 'error')
        return redirect(url_for('index'))
    
    bids = bid_model.get_bids_for_loan(loan_id)
    
    # Convert DynamoDB Decimal objects to Python types
    loan = convert_dynamodb_data(loan)
    bids = convert_dynamodb_data(bids)'''
        
        content = content.replace(old_route, new_route)
        
        # Write back to file
        with open(app_file, 'w') as f:
            f.write(content)
        
        print("✅ Added DynamoDB data conversion to loan_details route")

def fix_bot_bidding_errors():
    """Fix potential errors in bot bidding system"""
    
    bot_file = '/home/graemedowner/hackathon/bot_lenders.py'
    
    with open(bot_file, 'r') as f:
        content = f.read()
    
    # Add better error handling to the place_bid method
    old_place_bid = '''        try:
            bid_id = bid_model.create_bid(
                loan_request_id=loan['id'],
                lender_id=self.bot_id,
                amount=loan_amount,
                interest_rate=interest_rate,
                message=message
            )
            
            if bid_id:
                self.available_capital -= Decimal(str(loan_amount))
                self.active_bids.append(bid_id)
                logger.info(f"{self.name}: Placed bid ${loan_amount} at {interest_rate}% on loan {loan['id']}")
                return bid_id
            
        except Exception as e:
            logger.error(f"{self.name}: Error placing bid - {e}")'''
    
    new_place_bid = '''        try:
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
            logger.error(f"Full traceback: {traceback.format_exc()}")'''
    
    content = content.replace(old_place_bid, new_place_bid)
    
    # Add better error handling to the bidding loop
    old_process = '''    def _process_new_loans(self):
        """Process new loan requests and place bids"""
        try:
            # Get all open loans
            open_loans = loan_model.get_all_open_loans()'''
    
    new_process = '''    def _process_new_loans(self):
        """Process new loan requests and place bids"""
        try:
            # Get all open loans
            open_loans = loan_model.get_all_open_loans()
            
            if not open_loans:
                logger.debug("No open loans found")
                return'''
    
    content = content.replace(old_process, new_process)
    
    # Write back to file
    with open(bot_file, 'w') as f:
        f.write(content)
    
    print("✅ Enhanced error handling in bot bidding system")

def create_bidding_test_script():
    """Create a comprehensive test script for bidding functionality"""
    
    test_script = '''#!/usr/bin/env python3
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
'''
    
    with open('/home/graemedowner/hackathon/test_bidding_fixes.py', 'w') as f:
        f.write(test_script)
    
    os.chmod('/home/graemedowner/hackathon/test_bidding_fixes.py', 0o755)
    print("✅ Created comprehensive bidding test script")

def main():
    """Main function to fix all bidding issues"""
    print("🔧 Fixing Bidding System Issues")
    print("=" * 40)
    
    try:
        # Fix template filters
        fix_template_filters()
        
        # Fix data conversion
        fix_bid_data_conversion()
        
        # Fix bot bidding errors
        fix_bot_bidding_errors()
        
        # Create test script
        create_bidding_test_script()
        
        print("\n✅ All fixes applied successfully!")
        print("\n📋 Next Steps:")
        print("1. Run: python3 test_bidding_fixes.py")
        print("2. Start the app: python3 app_dynamodb.py")
        print("3. Test bidding functionality")
        print("4. Start bots: python3 start_bots.py")
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
