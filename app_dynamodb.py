from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from decimal import Decimal
import os
import threading
import atexit
import uuid

# Import DynamoDB models
from dynamodb_models import user_model, loan_model, bid_model, User

# Import Cognito authentication
from cognito_auth import CognitoAuth

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Cognito
cognito_auth = CognitoAuth()

# Import bot manager after app creation
bot_manager = None

def initialize_bots():
    """Initialize bot lenders"""
    global bot_manager
    try:
        from bot_lenders import BotLenderManager
        bot_manager = BotLenderManager()
        
        # Create bot lenders if they don't exist
        if not bot_manager.bots:
            bot_manager.create_bot_lenders()
        
        # Start automated bidding
        bot_manager.start_automated_bidding(check_interval=60)
        app.logger.info("Bot lenders initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize bots: {e}")

def cleanup_bots():
    """Cleanup function to stop bots on app shutdown"""
    global bot_manager
    if bot_manager:
        bot_manager.stop_automated_bidding()

# Register cleanup function
atexit.register(cleanup_bots)

# Custom Jinja2 filters for dictionary operations
@app.template_filter('dict_min')
def dict_min_filter(items, key):
    """Get minimum value from list of dictionaries by key"""
    if not items:
        return 0
    return min(item[key] for item in items)

@app.template_filter('dict_max')
def dict_max_filter(items, key):
    """Get maximum value from list of dictionaries by key"""
    if not items:
        return 0
    return max(item[key] for item in items)

@app.template_filter('dict_avg')
def dict_avg_filter(items, key):
    """Get average value from list of dictionaries by key"""
    if not items:
        return 0
    return sum(item[key] for item in items) / len(items)

@app.template_filter('dict_sum')
def dict_sum_filter(items, key):
    """Get sum of values from list of dictionaries by key"""
    if not items:
        return 0
    return sum(item[key] for item in items)

@login_manager.user_loader
def load_user(user_id):
    user_data = user_model.get_user_by_id(user_id)
    if user_data:
        return User(user_data)
    return None

# Routes
@app.route('/')
def index():
    # Get recent loan requests for the homepage
    recent_loans = loan_model.get_all_open_loans()
    
    # Sort by created_at and limit to 5 most recent
    recent_loans.sort(key=lambda x: x['created_at'], reverse=True)
    recent_loans = recent_loans[:5]
    
    # Get borrower info for each loan and format data
    for loan in recent_loans:
        borrower_data = user_model.get_user_by_id(loan['borrower_id'])
        if borrower_data:
            loan['borrower_name'] = f"{borrower_data['first_name']} {borrower_data['last_name'][0]}."
        else:
            loan['borrower_name'] = "Unknown"
        
        # Get bid count
        bids = bid_model.get_bids_for_loan(loan['id'])
        loan['bid_count'] = len(bids)
        
        # Convert Decimal to float for template
        loan['amount'] = float(loan['amount'])
        loan['max_interest_rate'] = float(loan['max_interest_rate'])
        
        # Convert ISO string to datetime object
        from datetime import datetime
        loan['created_at'] = datetime.fromisoformat(loan['created_at'].replace('Z', '+00:00'))
    
    return render_template('index.html', recent_loans=recent_loans)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form.get('phone', '')
        user_type = request.form['user_type']
        credit_score = request.form.get('credit_score')
        annual_income = request.form.get('annual_income')
        
        # Convert to appropriate types
        credit_score = int(credit_score) if credit_score else None
        annual_income = float(annual_income) if annual_income else None
        
        # Check if user already exists
        existing_user = user_model.get_user_by_email(email)
        if existing_user:
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('register.html')
        
        # Create new user
        user_id = user_model.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            user_type=user_type,
            credit_score=credit_score,
            annual_income=annual_income
        )
        
        if user_id:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user_data = user_model.get_user_by_email(email)
        
        if user_data and user_model.verify_password(user_data, password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    # Generate social login URLs
    social_login_urls = {}
    try:
        social_login_urls = {
            'google': cognito_auth.get_social_login_url('Google', state='google'),
            'facebook': cognito_auth.get_social_login_url('Facebook', state='facebook'),
            'amazon': cognito_auth.get_social_login_url('LoginWithAmazon', state='amazon'),
            'cognito': cognito_auth.get_authorization_url(state='cognito')
        }
    except Exception as e:
        app.logger.error(f"Error generating social login URLs: {e}")
    
    return render_template('login.html', social_login_urls=social_login_urls)

# Cognito Authentication Routes
@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Cognito"""
    try:
        # Get authorization code from callback
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            flash(f'Authentication error: {error}', 'error')
            return redirect(url_for('login'))
        
        if not code:
            flash('No authorization code received', 'error')
            return redirect(url_for('login'))
        
        # Exchange code for tokens
        tokens = cognito_auth.exchange_code_for_tokens(code)
        
        # Verify and decode ID token
        id_token = tokens.get('id_token')
        access_token = tokens.get('access_token')
        
        if not id_token:
            flash('No ID token received', 'error')
            return redirect(url_for('login'))
        
        # Verify token and get user info
        user_info = cognito_auth.verify_token(id_token)
        
        # Get additional user info if needed
        if access_token:
            try:
                additional_info = cognito_auth.get_user_info(access_token)
                user_info.update(additional_info)
            except:
                pass  # Additional info is optional
        
        # Determine provider from state or token
        provider = state if state in ['google', 'facebook', 'amazon'] else 'cognito'
        
        # Create or get user from social login
        user_data = handle_social_login(user_info, provider)
        
        if user_data:
            user = User(user_data)
            login_user(user)
            flash(f'Successfully logged in with {provider.title()}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Check if we need to complete registration
            if session.get('pending_social_registration'):
                return redirect(url_for('complete_social_registration'))
            else:
                flash('Failed to create or retrieve user account', 'error')
                return redirect(url_for('login'))
            
    except Exception as e:
        app.logger.error(f"OAuth callback error: {e}")
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('login'))

def handle_social_login(user_info, provider):
    """Handle social login user creation/retrieval"""
    try:
        email = user_info.get('email', '')
        
        if not email:
            flash('No email provided by social provider', 'error')
            return None
        
        # Check if user already exists
        existing_user = user_model.get_user_by_email(email)
        
        if existing_user:
            # Update social login info if needed
            if not existing_user.get('social_login'):
                user_model.update_user(existing_user['id'], {
                    'social_login': True,
                    'provider': provider,
                    'provider_id': user_info.get('sub', ''),
                    'last_login': datetime.utcnow().isoformat()
                })
            return existing_user
        
        # Create new user from social login
        social_user_data = cognito_auth.create_user_from_social(user_info, provider)
        
        # Store in session for registration completion
        session['social_user_data'] = social_user_data
        session['pending_social_registration'] = True
        
        # Redirect to complete registration
        flash('Please complete your registration to continue', 'info')
        return None  # Will redirect to registration completion
        
    except Exception as e:
        app.logger.error(f"Social login handling error: {e}")
        return None

@app.route('/auth/complete-registration', methods=['GET', 'POST'])
def complete_social_registration():
    """Complete registration for social login users"""
    if 'pending_social_registration' not in session:
        return redirect(url_for('login'))
    
    social_data = session.get('social_user_data', {})
    
    if request.method == 'POST':
        try:
            # Get additional required fields
            user_type = request.form['user_type']
            phone = request.form.get('phone', '')
            credit_score = int(request.form.get('credit_score', 0)) if request.form.get('credit_score') else None
            annual_income = float(request.form.get('annual_income', 0)) if request.form.get('annual_income') else None
            
            # Create user with social and form data
            user_id = user_model.create_user(
                email=social_data['email'],
                password=None,  # No password for social login
                first_name=social_data['first_name'],
                last_name=social_data['last_name'],
                phone=phone,
                user_type=user_type,
                credit_score=credit_score,
                annual_income=annual_income,
                social_login=True,
                provider=social_data['provider'],
                provider_id=social_data['provider_id'],
                email_verified=social_data.get('email_verified', False),
                picture=social_data.get('picture', '')
            )
            
            if user_id:
                # Clear session data
                session.pop('social_user_data', None)
                session.pop('pending_social_registration', None)
                
                # Login user
                user_data = user_model.get_user_by_id(user_id)
                user = User(user_data)
                login_user(user)
                
                flash('Registration completed successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Registration failed. Please try again.', 'error')
                
        except Exception as e:
            app.logger.error(f"Social registration completion error: {e}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('complete_social_registration.html', social_data=social_data)

@app.route('/logout/complete')
def logout_complete():
    """Handle logout completion from Cognito"""
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    # Check if user logged in via social/Cognito
    if hasattr(current_user, 'social_login') and current_user.social_login:
        logout_user()
        # Redirect to Cognito logout
        cognito_logout_url = cognito_auth.logout_url()
        return redirect(cognito_logout_url)
    else:
        # Regular logout
        logout_user()
        return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type == 'borrower':
        # Get borrower's loan requests
        loan_requests = loan_model.get_loans_by_borrower(current_user.id)
        
        # Get bids for each loan request and format data
        for loan in loan_requests:
            bids = bid_model.get_bids_for_loan(loan['id'])
            loan['bids'] = bids
            loan['bid_count'] = len(bids)
            
            # Convert Decimal to float
            loan['amount'] = float(loan['amount'])
            loan['max_interest_rate'] = float(loan['max_interest_rate'])
            
            # Convert ISO string to datetime object for template formatting
            from datetime import datetime
            loan['created_at'] = datetime.fromisoformat(loan['created_at'].replace('Z', '+00:00'))
            
            for bid in bids:
                bid['amount'] = float(bid['amount'])
                bid['interest_rate'] = float(bid['interest_rate'])
                # Convert bid created_at too
                bid['created_at'] = datetime.fromisoformat(bid['created_at'].replace('Z', '+00:00'))
                
                # Get lender info
                lender_data = user_model.get_user_by_id(bid['lender_id'])
                if lender_data:
                    bid['lender_name'] = f"{lender_data['first_name']} {lender_data['last_name']}"
        
        return render_template('borrower_dashboard.html', loan_requests=loan_requests)
    
    else:  # lender
        # Get available loan requests
        available_loans = loan_model.get_all_open_loans()
        
        # Get lender's bids
        my_bids = bid_model.get_bids_by_lender(current_user.id)
        
        # Add borrower info to loans and format data
        for loan in available_loans:
            borrower_data = user_model.get_user_by_id(loan['borrower_id'])
            if borrower_data:
                loan['borrower_name'] = f"{borrower_data['first_name']} {borrower_data['last_name']}"
                loan['borrower_credit_score'] = borrower_data.get('credit_score', 0)
                
                # Create borrower object for template compatibility
                from datetime import datetime
                borrower_created_at = datetime.fromisoformat(borrower_data['created_at'].replace('Z', '+00:00'))
                
                loan['borrower'] = {
                    'first_name': borrower_data['first_name'],
                    'last_name': borrower_data['last_name'],
                    'credit_score': borrower_data.get('credit_score', 0),
                    'annual_income': float(borrower_data.get('annual_income', 0)),
                    'created_at': borrower_created_at
                }
            
            # Convert Decimal to float
            loan['amount'] = float(loan['amount'])
            loan['max_interest_rate'] = float(loan['max_interest_rate'])
            
            # Convert ISO string to datetime object
            from datetime import datetime
            loan['created_at'] = datetime.fromisoformat(loan['created_at'].replace('Z', '+00:00'))
            
            # Get bid count
            bids = bid_model.get_bids_for_loan(loan['id'])
            loan['bid_count'] = len(bids)
        
        # Add loan info to bids and format data
        for bid in my_bids:
            loan_data = loan_model.get_loan_request(bid['loan_request_id'])
            if loan_data:
                bid['loan_amount'] = float(loan_data['amount'])
                bid['loan_purpose'] = loan_data['purpose']
            
            bid['amount'] = float(bid['amount'])
            bid['interest_rate'] = float(bid['interest_rate'])
            # Convert bid created_at
            from datetime import datetime
            bid['created_at'] = datetime.fromisoformat(bid['created_at'].replace('Z', '+00:00'))
        
        return render_template('lender_dashboard.html', 
                             available_loans=available_loans, 
                             my_bids=my_bids)

@app.route('/request_loan', methods=['GET', 'POST'])
@login_required
def request_loan():
    if current_user.user_type != 'borrower':
        flash('Only borrowers can request loans.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        purpose = request.form['purpose']
        term_months = int(request.form['term_months'])
        max_interest_rate = float(request.form['max_interest_rate'])
        description = request.form.get('description', '')
        
        loan_id = loan_model.create_loan_request(
            borrower_id=current_user.id,
            amount=amount,
            purpose=purpose,
            term_months=term_months,
            max_interest_rate=max_interest_rate,
            description=description
        )
        
        if loan_id:
            flash('Loan request created successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Failed to create loan request. Please try again.', 'error')
    
    return render_template('request_loan.html')

@app.route('/loan/<loan_id>')
def loan_details(loan_id):
    loan = loan_model.get_loan_request(loan_id)
    if not loan:
        flash('Loan not found.', 'error')
        return redirect(url_for('index'))
    
    # Get borrower info and add to loan object
    borrower_data = user_model.get_user_by_id(loan['borrower_id'])
    if borrower_data:
        loan['borrower_name'] = f"{borrower_data['first_name']} {borrower_data['last_name']}"
        loan['borrower_credit_score'] = borrower_data.get('credit_score', 0)
        
        # Create a borrower object for template compatibility
        from datetime import datetime
        borrower_created_at = datetime.fromisoformat(borrower_data['created_at'].replace('Z', '+00:00'))
        
        loan['borrower'] = {
            'first_name': borrower_data['first_name'],
            'last_name': borrower_data['last_name'],
            'credit_score': borrower_data.get('credit_score', 0),
            'annual_income': float(borrower_data.get('annual_income', 0)),
            'created_at': borrower_created_at
        }
    
    # Get bids
    bids = bid_model.get_bids_for_loan(loan_id)
    
    # Add lender info to bids and convert Decimals
    for bid in bids:
        lender_data = user_model.get_user_by_id(bid['lender_id'])
        if lender_data:
            bid['lender_name'] = f"{lender_data['first_name']} {lender_data['last_name']}"
        
        bid['amount'] = float(bid['amount'])
        bid['interest_rate'] = float(bid['interest_rate'])
        
        # Convert bid created_at
        from datetime import datetime
        bid['created_at'] = datetime.fromisoformat(bid['created_at'].replace('Z', '+00:00'))
    
    # Convert loan Decimals and dates
    loan['amount'] = float(loan['amount'])
    loan['max_interest_rate'] = float(loan['max_interest_rate'])
    
    # Convert ISO string to datetime object
    from datetime import datetime
    loan['created_at'] = datetime.fromisoformat(loan['created_at'].replace('Z', '+00:00'))
    if 'expires_at' in loan:
        loan['expires_at'] = datetime.fromisoformat(loan['expires_at'].replace('Z', '+00:00'))
    
    # Sort bids by interest rate (lowest first)
    bids.sort(key=lambda x: x['interest_rate'])
    
    return render_template('loan_details.html', loan=loan, bids=bids)

@app.route('/place_bid/<loan_id>', methods=['GET'])
@login_required
def place_bid_form(loan_id):
    """Show the bid placement form"""
    if current_user.user_type != 'lender':
        flash('Only lenders can place bids.', 'error')
        return redirect(url_for('loan_details', loan_id=loan_id))
    
    loan = loan_model.get_loan_request(loan_id)
    if not loan or loan['status'] != 'open':
        flash('This loan is no longer available for bidding.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get borrower info and add to loan object
    borrower_data = user_model.get_user_by_id(loan['borrower_id'])
    if borrower_data:
        loan['borrower_name'] = f"{borrower_data['first_name']} {borrower_data['last_name']}"
        loan['borrower_credit_score'] = borrower_data.get('credit_score', 0)
        
        # Create a borrower object for template compatibility
        from datetime import datetime
        borrower_created_at = datetime.fromisoformat(borrower_data['created_at'].replace('Z', '+00:00'))
        
        loan['borrower'] = {
            'first_name': borrower_data['first_name'],
            'last_name': borrower_data['last_name'],
            'credit_score': borrower_data.get('credit_score', 0),
            'annual_income': float(borrower_data.get('annual_income', 0)),
            'created_at': borrower_created_at
        }
    
    # Get existing bids for reference
    bids = bid_model.get_bids_for_loan(loan_id)
    loan['bids'] = bids
    
    # Convert loan data
    loan['amount'] = float(loan['amount'])
    loan['max_interest_rate'] = float(loan['max_interest_rate'])
    
    # Convert ISO string to datetime object
    from datetime import datetime
    loan['created_at'] = datetime.fromisoformat(loan['created_at'].replace('Z', '+00:00'))
    
    return render_template('place_bid.html', loan=loan)

@app.route('/place_bid/<loan_id>', methods=['POST'])
@login_required
def place_bid(loan_id):
    if current_user.user_type != 'lender':
        flash('Only lenders can place bids.', 'error')
        return redirect(url_for('loan_details', loan_id=loan_id))
    
    loan = loan_model.get_loan_request(loan_id)
    if not loan or loan['status'] != 'open':
        flash('This loan is no longer available for bidding.', 'error')
        return redirect(url_for('dashboard'))
    
    amount = float(request.form['amount'])
    interest_rate = float(request.form['interest_rate'])
    message = request.form.get('message', '')
    
    # Validate bid
    if amount > float(loan['amount']):
        flash('Bid amount cannot exceed loan amount.', 'error')
        return redirect(url_for('loan_details', loan_id=loan_id))
    
    if interest_rate > float(loan['max_interest_rate']):
        flash('Interest rate cannot exceed maximum rate.', 'error')
        return redirect(url_for('loan_details', loan_id=loan_id))
    
    bid_id = bid_model.create_bid(
        loan_request_id=loan_id,
        lender_id=current_user.id,
        amount=amount,
        interest_rate=interest_rate,
        message=message
    )
    
    if bid_id:
        flash('Bid placed successfully!', 'success')
    else:
        flash('Failed to place bid. Please try again.', 'error')
    
    return redirect(url_for('loan_details', loan_id=loan_id))

@app.route('/accept_bid/<bid_id>')
@login_required
def accept_bid(bid_id):
    bid = bid_model.get_bid(bid_id)
    if not bid:
        flash('Bid not found.', 'error')
        return redirect(url_for('dashboard'))
    
    loan = loan_model.get_loan_request(bid['loan_request_id'])
    if not loan or loan['borrower_id'] != current_user.id:
        flash('You can only accept bids on your own loans.', 'error')
        return redirect(url_for('dashboard'))
    
    # Update bid status to accepted
    bid_model.update_bid_status(bid_id, 'accepted')
    
    # Update loan status to funded
    loan_model.update_loan_status(bid['loan_request_id'], 'funded')
    
    # Reject all other bids for this loan
    all_bids = bid_model.get_bids_for_loan(bid['loan_request_id'])
    for other_bid in all_bids:
        if other_bid['id'] != bid_id and other_bid['status'] == 'pending':
            bid_model.update_bid_status(other_bid['id'], 'rejected')
    
    flash('Bid accepted successfully! Your loan has been funded.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/loans')
def api_loans():
    """API endpoint for loan data"""
    loans = loan_model.get_all_open_loans()
    
    loans_data = []
    for loan in loans:
        borrower_data = user_model.get_user_by_id(loan['borrower_id'])
        bids = bid_model.get_bids_for_loan(loan['id'])
        
        loans_data.append({
            'id': loan['id'],
            'amount': float(loan['amount']),
            'purpose': loan['purpose'],
            'term_months': loan['term_months'],
            'max_interest_rate': float(loan['max_interest_rate']),
            'created_at': loan['created_at'],  # Keep as ISO string for API
            'borrower_name': f"{borrower_data['first_name']} {borrower_data['last_name'][0]}." if borrower_data else "Unknown",
            'bid_count': len(bids)
        })
    
    return jsonify(loans_data)

# Bot Management Routes
@app.route('/admin/bots')
@login_required
def bot_admin():
    """Admin page for managing bot lenders"""
    # Simple admin check - in production, implement proper admin roles
    if not current_user.email.endswith('@admin.com'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    global bot_manager
    if not bot_manager:
        initialize_bots()
    
    stats = bot_manager.get_bot_stats() if bot_manager else {'total_bots': 0, 'bots': []}
    return render_template('bot_admin.html', stats=stats)

@app.route('/admin/bots/start', methods=['POST'])
@login_required
def start_bots():
    """Start automated bot bidding"""
    if not current_user.email.endswith('@admin.com'):
        return jsonify({'error': 'Access denied'}), 403
    
    global bot_manager
    try:
        if not bot_manager:
            initialize_bots()
        
        if bot_manager:
            bot_manager.start_automated_bidding()
            return jsonify({'success': True, 'message': 'Bot bidding started'})
        else:
            return jsonify({'error': 'Failed to initialize bot manager'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/bots/stop', methods=['POST'])
@login_required
def stop_bots():
    """Stop automated bot bidding"""
    if not current_user.email.endswith('@admin.com'):
        return jsonify({'error': 'Access denied'}), 403
    
    global bot_manager
    try:
        if bot_manager:
            bot_manager.stop_automated_bidding()
            return jsonify({'success': True, 'message': 'Bot bidding stopped'})
        else:
            return jsonify({'error': 'Bot manager not initialized'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/bots/stats')
@login_required
def bot_stats_api():
    """API endpoint for bot statistics"""
    if not current_user.email.endswith('@admin.com'):
        return jsonify({'error': 'Access denied'}), 403
    
    global bot_manager
    if not bot_manager:
        return jsonify({'total_bots': 0, 'bots': []})
    
    stats = bot_manager.get_bot_stats()
    return jsonify(stats)

@app.route('/admin/bots/reset', methods=['POST'])
@login_required
def reset_bots():
    """Reset bot lenders (recreate them)"""
    if not current_user.email.endswith('@admin.com'):
        return jsonify({'error': 'Access denied'}), 403
    
    global bot_manager
    try:
        if bot_manager:
            bot_manager.stop_automated_bidding()
            bot_manager.bots.clear()
            bot_manager.create_bot_lenders()
            bot_manager.start_automated_bidding()
        else:
            initialize_bots()
        
        return jsonify({'success': True, 'message': 'Bots reset successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/bots/initialize', methods=['POST'])
@login_required
def initialize_bots_route():
    """Initialize bot lenders manually"""
    if not current_user.email.endswith('@admin.com'):
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        initialize_bots()
        return jsonify({'success': True, 'message': 'Bots initialized successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
