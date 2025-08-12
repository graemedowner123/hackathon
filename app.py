from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///p2p_lending.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    user_type = db.Column(db.String(20), nullable=False)  # 'borrower' or 'lender'
    credit_score = db.Column(db.Integer)
    annual_income = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    loan_requests = db.relationship('LoanRequest', backref='borrower', lazy=True)
    bids = db.relationship('Bid', backref='lender', lazy=True)

class LoanRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    term_months = db.Column(db.Integer, nullable=False)
    max_interest_rate = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')  # 'open', 'funded', 'closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    bids = db.relationship('Bid', backref='loan_request', lazy=True, cascade='all, delete-orphan')

class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_request_id = db.Column(db.Integer, db.ForeignKey('loan_request.id'), nullable=False)
    lender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    # Get recent loan requests for display
    recent_loans = LoanRequest.query.filter_by(status='open').order_by(LoanRequest.created_at.desc()).limit(5).all()
    return render_template('index.html', recent_loans=recent_loans)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        user_type = request.form['user_type']
        credit_score = request.form.get('credit_score', type=int)
        annual_income = request.form.get('annual_income', type=float)
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            user_type=user_type,
            credit_score=credit_score,
            annual_income=annual_income
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type == 'borrower':
        loan_requests = LoanRequest.query.filter_by(borrower_id=current_user.id).all()
        return render_template('borrower_dashboard.html', loan_requests=loan_requests)
    else:
        # Show available loan requests for lenders
        available_loans = LoanRequest.query.filter_by(status='open').all()
        my_bids = Bid.query.filter_by(lender_id=current_user.id).all()
        return render_template('lender_dashboard.html', available_loans=available_loans, my_bids=my_bids)

@app.route('/request_loan', methods=['GET', 'POST'])
@login_required
def request_loan():
    if current_user.user_type != 'borrower':
        flash('Only borrowers can request loans')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        purpose = request.form['purpose']
        term_months = int(request.form['term_months'])
        max_interest_rate = float(request.form['max_interest_rate'])
        description = request.form['description']
        
        # Set expiration date (7 days from now)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        loan_request = LoanRequest(
            borrower_id=current_user.id,
            amount=amount,
            purpose=purpose,
            term_months=term_months,
            max_interest_rate=max_interest_rate,
            description=description,
            expires_at=expires_at
        )
        
        db.session.add(loan_request)
        db.session.commit()
        
        flash('Loan request submitted successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('request_loan.html')

@app.route('/loan/<int:loan_id>')
def loan_details(loan_id):
    loan = LoanRequest.query.get_or_404(loan_id)
    bids = Bid.query.filter_by(loan_request_id=loan_id).order_by(Bid.interest_rate.asc()).all()
    return render_template('loan_details.html', loan=loan, bids=bids)

@app.route('/place_bid/<int:loan_id>', methods=['GET', 'POST'])
@login_required
def place_bid(loan_id):
    if current_user.user_type != 'lender':
        flash('Only lenders can place bids')
        return redirect(url_for('dashboard'))
    
    loan = LoanRequest.query.get_or_404(loan_id)
    
    if loan.status != 'open':
        flash('This loan is no longer accepting bids')
        return redirect(url_for('loan_details', loan_id=loan_id))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        interest_rate = float(request.form['interest_rate'])
        message = request.form['message']
        
        # Validate bid
        if amount > loan.amount:
            flash('Bid amount cannot exceed loan amount')
            return redirect(url_for('place_bid', loan_id=loan_id))
        
        if interest_rate > loan.max_interest_rate:
            flash('Interest rate exceeds borrower\'s maximum')
            return redirect(url_for('place_bid', loan_id=loan_id))
        
        # Check if lender already has a bid on this loan
        existing_bid = Bid.query.filter_by(loan_request_id=loan_id, lender_id=current_user.id).first()
        if existing_bid:
            flash('You already have a bid on this loan')
            return redirect(url_for('loan_details', loan_id=loan_id))
        
        bid = Bid(
            loan_request_id=loan_id,
            lender_id=current_user.id,
            amount=amount,
            interest_rate=interest_rate,
            message=message
        )
        
        db.session.add(bid)
        db.session.commit()
        
        flash('Bid placed successfully')
        return redirect(url_for('loan_details', loan_id=loan_id))
    
    return render_template('place_bid.html', loan=loan)

@app.route('/accept_bid/<int:bid_id>')
@login_required
def accept_bid(bid_id):
    bid = Bid.query.get_or_404(bid_id)
    loan = bid.loan_request
    
    if loan.borrower_id != current_user.id:
        flash('You can only accept bids on your own loans')
        return redirect(url_for('dashboard'))
    
    if loan.status != 'open':
        flash('This loan is no longer accepting bids')
        return redirect(url_for('dashboard'))
    
    # Accept the bid and close the loan
    bid.status = 'accepted'
    loan.status = 'funded'
    
    # Reject all other bids
    other_bids = Bid.query.filter_by(loan_request_id=loan.id).filter(Bid.id != bid_id).all()
    for other_bid in other_bids:
        other_bid.status = 'rejected'
    
    db.session.commit()
    
    flash('Bid accepted successfully')
    return redirect(url_for('dashboard'))

@app.route('/api/loans')
def api_loans():
    loans = LoanRequest.query.filter_by(status='open').all()
    loans_data = []
    for loan in loans:
        loans_data.append({
            'id': loan.id,
            'amount': loan.amount,
            'purpose': loan.purpose,
            'term_months': loan.term_months,
            'max_interest_rate': loan.max_interest_rate,
            'created_at': loan.created_at.isoformat(),
            'borrower_name': f"{loan.borrower.first_name} {loan.borrower.last_name[0]}.",
            'bid_count': len(loan.bids)
        })
    return jsonify(loans_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
