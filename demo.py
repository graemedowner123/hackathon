#!/usr/bin/env python3
"""
Demo script for P2P Lending Platform
This script creates sample users and loan requests to demonstrate the platform
"""

from app import app, db, User, LoanRequest, Bid
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def create_demo_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        print("Creating demo users...")
        
        # Create borrowers
        borrower1 = User(
            email='john.borrower@example.com',
            password_hash=generate_password_hash('password123'),
            first_name='John',
            last_name='Smith',
            phone='555-0101',
            user_type='borrower',
            credit_score=720,
            annual_income=65000
        )
        
        borrower2 = User(
            email='sarah.borrower@example.com',
            password_hash=generate_password_hash('password123'),
            first_name='Sarah',
            last_name='Johnson',
            phone='555-0102',
            user_type='borrower',
            credit_score=680,
            annual_income=55000
        )
        
        # Create lenders
        lender1 = User(
            email='mike.lender@example.com',
            password_hash=generate_password_hash('password123'),
            first_name='Mike',
            last_name='Wilson',
            phone='555-0201',
            user_type='lender',
            annual_income=120000
        )
        
        lender2 = User(
            email='lisa.lender@example.com',
            password_hash=generate_password_hash('password123'),
            first_name='Lisa',
            last_name='Davis',
            phone='555-0202',
            user_type='lender',
            annual_income=95000
        )
        
        lender3 = User(
            email='david.lender@example.com',
            password_hash=generate_password_hash('password123'),
            first_name='David',
            last_name='Brown',
            phone='555-0203',
            user_type='lender',
            annual_income=150000
        )
        
        # Add users to database
        users = [borrower1, borrower2, lender1, lender2, lender3]
        for user in users:
            db.session.add(user)
        
        db.session.commit()
        print(f"Created {len(users)} demo users")
        
        # Create loan requests
        print("Creating demo loan requests...")
        
        loan1 = LoanRequest(
            borrower_id=borrower1.id,
            amount=15000,
            purpose='Debt Consolidation',
            term_months=36,
            max_interest_rate=12.5,
            description='Looking to consolidate high-interest credit card debt. Stable employment for 5+ years.',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        loan2 = LoanRequest(
            borrower_id=borrower1.id,
            amount=8000,
            purpose='Home Improvement',
            term_months=24,
            max_interest_rate=10.0,
            description='Kitchen renovation project. Have contractor quotes and permits ready.',
            expires_at=datetime.utcnow() + timedelta(days=6)
        )
        
        loan3 = LoanRequest(
            borrower_id=borrower2.id,
            amount=25000,
            purpose='Business',
            term_months=48,
            max_interest_rate=15.0,
            description='Expanding my online retail business. Need inventory and marketing budget.',
            expires_at=datetime.utcnow() + timedelta(days=5)
        )
        
        loan4 = LoanRequest(
            borrower_id=borrower2.id,
            amount=5000,
            purpose='Education',
            term_months=12,
            max_interest_rate=8.0,
            description='Professional certification course to advance my career.',
            expires_at=datetime.utcnow() + timedelta(days=4)
        )
        
        # Add loan requests to database
        loans = [loan1, loan2, loan3, loan4]
        for loan in loans:
            db.session.add(loan)
        
        db.session.commit()
        print(f"Created {len(loans)} demo loan requests")
        
        # Create bids
        print("Creating demo bids...")
        
        # Bids for loan1 ($15,000 debt consolidation)
        bid1 = Bid(
            loan_request_id=loan1.id,
            lender_id=lender1.id,
            amount=15000,
            interest_rate=11.5,
            message='Excellent credit score! I can offer you a competitive rate.'
        )
        
        bid2 = Bid(
            loan_request_id=loan1.id,
            lender_id=lender2.id,
            amount=15000,
            interest_rate=12.0,
            message='Stable income and good credit. Happy to fund this loan.'
        )
        
        bid3 = Bid(
            loan_request_id=loan1.id,
            lender_id=lender3.id,
            amount=15000,
            interest_rate=10.8,
            message='Best rate available! Long-term lender with excellent track record.'
        )
        
        # Bids for loan2 ($8,000 home improvement)
        bid4 = Bid(
            loan_request_id=loan2.id,
            lender_id=lender1.id,
            amount=8000,
            interest_rate=9.5,
            message='Home improvements are great investments. Competitive rate offered.'
        )
        
        bid5 = Bid(
            loan_request_id=loan2.id,
            lender_id=lender3.id,
            amount=8000,
            interest_rate=9.2,
            message='Love funding home improvement projects. Quick approval process.'
        )
        
        # Bids for loan3 ($25,000 business)
        bid6 = Bid(
            loan_request_id=loan3.id,
            lender_id=lender2.id,
            amount=25000,
            interest_rate=14.5,
            message='Supporting small business growth. Flexible terms available.'
        )
        
        bid7 = Bid(
            loan_request_id=loan3.id,
            lender_id=lender3.id,
            amount=25000,
            interest_rate=13.8,
            message='Business expansion loans are my specialty. Let\'s grow together!'
        )
        
        # Bids for loan4 ($5,000 education)
        bid8 = Bid(
            loan_request_id=loan4.id,
            lender_id=lender1.id,
            amount=5000,
            interest_rate=7.5,
            message='Education is the best investment. Great rate for career advancement.'
        )
        
        # Add bids to database
        bids = [bid1, bid2, bid3, bid4, bid5, bid6, bid7, bid8]
        for bid in bids:
            db.session.add(bid)
        
        db.session.commit()
        print(f"Created {len(bids)} demo bids")
        
        print("\n" + "="*50)
        print("DEMO DATA CREATED SUCCESSFULLY!")
        print("="*50)
        print("\nDemo Users Created:")
        print("\nBORROWERS:")
        print("- john.borrower@example.com (password: password123)")
        print("  Credit Score: 720, Income: $65,000")
        print("- sarah.borrower@example.com (password: password123)")
        print("  Credit Score: 680, Income: $55,000")
        
        print("\nLENDERS:")
        print("- mike.lender@example.com (password: password123)")
        print("- lisa.lender@example.com (password: password123)")
        print("- david.lender@example.com (password: password123)")
        
        print("\nLoan Requests Created:")
        for loan in loans:
            print(f"- ${loan.amount:,.0f} for {loan.purpose} ({len([b for b in bids if b.loan_request_id == loan.id])} bids)")
        
        print("\nTo test the application:")
        print("1. Run: python3 app.py")
        print("2. Open: http://localhost:5000")
        print("3. Login with any of the demo accounts above")
        print("4. Explore borrower and lender dashboards")
        print("5. Place bids, accept offers, and see the competition!")

if __name__ == '__main__':
    create_demo_data()
