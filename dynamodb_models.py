import boto3
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))

# Table names
USERS_TABLE = 'p2p-lending-users'
LOAN_REQUESTS_TABLE = 'p2p-lending-loan-requests'
BIDS_TABLE = 'p2p-lending-bids'

class DynamoDBUser:
    def __init__(self):
        self.table = dynamodb.Table(USERS_TABLE)
    
    def create_user(self, email, password, first_name, last_name, phone, user_type, 
                   credit_score=None, annual_income=None, social_login=False, provider=None, 
                   provider_id=None, email_verified=False, picture=None):
        user_id = str(uuid.uuid4())
        
        # Hash password only if provided (not for social login)
        password_hash = None
        if password:
            password_hash = generate_password_hash(password)
        
        item = {
            'id': user_id,
            'email': email,
            'password_hash': password_hash,
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone or '',
            'user_type': user_type,
            'credit_score': credit_score or 0,
            'annual_income': Decimal(str(annual_income)) if annual_income else Decimal('0'),
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True,
            'social_login': social_login,
            'email_verified': email_verified
        }
        
        # Add social login specific fields
        if provider:
            item['provider'] = provider
        if provider_id:
            item['provider_id'] = provider_id
        if picture:
            item['picture'] = picture
        
        try:
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(email)'
            )
            return user_id
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            return None  # User already exists
    
    def update_user(self, user_id, updates):
        """Update user with given fields"""
        try:
            # Build update expression
            update_expression = "SET "
            expression_values = {}
            
            for key, value in updates.items():
                update_expression += f"{key} = :{key}, "
                expression_values[f":{key}"] = value
            
            # Remove trailing comma and space
            update_expression = update_expression.rstrip(", ")
            
            self.table.update_item(
                Key={'id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    def get_user_by_id(self, user_id):
        try:
            response = self.table.get_item(Key={'id': user_id})
            return response.get('Item')
        except:
            return None
    
    def get_user_by_email(self, email):
        try:
            response = self.table.scan(
                FilterExpression=Attr('email').eq(email)
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except:
            return None
    
    def verify_password(self, user, password):
        return check_password_hash(user['password_hash'], password)

class DynamoDBLoanRequest:
    def __init__(self):
        self.table = dynamodb.Table(LOAN_REQUESTS_TABLE)
    
    def create_loan_request(self, borrower_id, amount, purpose, term_months, max_interest_rate, description=''):
        loan_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=30)  # 30 days to get bids
        
        item = {
            'id': loan_id,
            'borrower_id': borrower_id,
            'amount': Decimal(str(amount)),
            'purpose': purpose,
            'term_months': term_months,
            'max_interest_rate': Decimal(str(max_interest_rate)),
            'description': description,
            'status': 'open',
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': expires_at.isoformat()
        }
        
        self.table.put_item(Item=item)
        return loan_id
    
    def get_loan_request(self, loan_id):
        try:
            response = self.table.get_item(Key={'id': loan_id})
            return response.get('Item')
        except:
            return None
    
    def get_all_open_loans(self):
        try:
            response = self.table.scan(
                FilterExpression=Attr('status').eq('open')
            )
            return response.get('Items', [])
        except:
            return []
    
    def get_loans_by_borrower(self, borrower_id):
        try:
            response = self.table.scan(
                FilterExpression=Attr('borrower_id').eq(borrower_id)
            )
            return response.get('Items', [])
        except:
            return []
    
    def update_loan_status(self, loan_id, status):
        try:
            self.table.update_item(
                Key={'id': loan_id},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status}
            )
            return True
        except:
            return False

class DynamoDBBid:
    def __init__(self):
        self.table = dynamodb.Table(BIDS_TABLE)
    
    def create_bid(self, loan_request_id, lender_id, amount, interest_rate, message=''):
        bid_id = str(uuid.uuid4())
        
        item = {
            'id': bid_id,
            'loan_request_id': loan_request_id,
            'lender_id': lender_id,
            'amount': Decimal(str(amount)),
            'interest_rate': Decimal(str(interest_rate)),
            'message': message,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        
        self.table.put_item(Item=item)
        return bid_id
    
    def get_bid(self, bid_id):
        try:
            response = self.table.get_item(Key={'id': bid_id})
            return response.get('Item')
        except:
            return None
    
    def get_bids_for_loan(self, loan_request_id):
        try:
            response = self.table.scan(
                FilterExpression=Attr('loan_request_id').eq(loan_request_id)
            )
            return response.get('Items', [])
        except:
            return []
    
    def get_bids_by_lender(self, lender_id):
        try:
            response = self.table.scan(
                FilterExpression=Attr('lender_id').eq(lender_id)
            )
            return response.get('Items', [])
        except:
            return []
    
    def update_bid_status(self, bid_id, status):
        try:
            self.table.update_item(
                Key={'id': bid_id},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status}
            )
            return True
        except:
            return False

# User class for Flask-Login compatibility
class User:
    def __init__(self, user_data):
        self.id = user_data['id']
        self.email = user_data['email']
        self.first_name = user_data['first_name']
        self.last_name = user_data['last_name']
        self.phone = user_data.get('phone', '')
        self.user_type = user_data['user_type']
        self.credit_score = user_data.get('credit_score', 0)
        self.annual_income = float(user_data.get('annual_income', 0))
        self.created_at = user_data['created_at']
        self.is_active = user_data.get('is_active', True)
        
        # Social login attributes
        self.social_login = user_data.get('social_login', False)
        self.provider = user_data.get('provider', '')
        self.provider_id = user_data.get('provider_id', '')
        self.email_verified = user_data.get('email_verified', False)
        self.picture = user_data.get('picture', '')
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return self.is_active
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return self.id

# Initialize model instances
user_model = DynamoDBUser()
loan_model = DynamoDBLoanRequest()
bid_model = DynamoDBBid()
