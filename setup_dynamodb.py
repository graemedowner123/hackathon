import boto3
import os
from botocore.exceptions import ClientError

def create_dynamodb_tables():
    """Create DynamoDB tables for the P2P lending application"""
    
    dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
    
    # Users table
    try:
        users_table = dynamodb.create_table(
            TableName='p2p-lending-users',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Creating Users table...")
        users_table.wait_until_exists()
        print("Users table created successfully!")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Users table already exists")
        else:
            print(f"Error creating Users table: {e}")
    
    # Loan Requests table
    try:
        loans_table = dynamodb.create_table(
            TableName='p2p-lending-loan-requests',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Creating Loan Requests table...")
        loans_table.wait_until_exists()
        print("Loan Requests table created successfully!")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Loan Requests table already exists")
        else:
            print(f"Error creating Loan Requests table: {e}")
    
    # Bids table
    try:
        bids_table = dynamodb.create_table(
            TableName='p2p-lending-bids',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Creating Bids table...")
        bids_table.wait_until_exists()
        print("Bids table created successfully!")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Bids table already exists")
        else:
            print(f"Error creating Bids table: {e}")
    
    print("All DynamoDB tables are ready!")

if __name__ == '__main__':
    create_dynamodb_tables()
