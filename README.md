# P2P Lending Platform

A peer-to-peer lending application built with Python Flask backend and HTML/Bootstrap frontend. The platform connects borrowers with lenders through a competitive bidding system.

## Features

### For Borrowers
- Create loan requests with amount, purpose, term, and maximum interest rate
- View competitive bids from multiple lenders
- Accept the best offer from available bids
- Track loan status and history

### For Lenders
- Browse available loan requests
- Place competitive bids with custom interest rates
- View borrower profiles and credit information
- Track bid status and lending portfolio

### Platform Features
- User registration and authentication
- Secure password hashing
- Responsive web interface
- Real-time bid competition
- Loan calculation tools
- Dashboard for both user types

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Authentication**: Flask-Login
- **Security**: Werkzeug password hashing

## Setup Instructions

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python app.py
   ```

3. **Access the application**:
   Open your browser and go to `http://localhost:5000`

## Usage

### Getting Started
1. Register as either a borrower or lender
2. Complete your profile with financial information
3. For borrowers: Create loan requests
4. For lenders: Browse and bid on available loans

### Borrower Workflow
1. Click "Request Loan" from dashboard
2. Fill in loan details (amount, purpose, term, max rate)
3. Submit request and wait for bids
4. Review competing bids and accept the best offer

### Lender Workflow
1. Browse available loan requests from dashboard
2. Review borrower profiles and loan details
3. Place competitive bids with your desired interest rate
4. Wait for borrower to accept or reject your bid

## Database Schema

### Users Table
- User authentication and profile information
- Separate fields for borrowers and lenders
- Credit score and income tracking

### Loan Requests Table
- Loan details and requirements
- Status tracking (open/funded/closed)
- Expiration dates for bidding

### Bids Table
- Lender bids on loan requests
- Interest rates and amounts
- Status tracking (pending/accepted/rejected)

## Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Input validation and sanitization
- SQL injection prevention with SQLAlchemy
- CSRF protection with Flask-WTF tokens

## API Endpoints

- `GET /` - Home page with recent loans
- `POST /register` - User registration
- `POST /login` - User authentication
- `GET /dashboard` - User dashboard (role-specific)
- `POST /request_loan` - Create loan request
- `GET /loan/<id>` - Loan details and bids
- `POST /place_bid/<id>` - Submit bid on loan
- `GET /accept_bid/<id>` - Accept a bid
- `GET /api/loans` - JSON API for loan data

## Future Enhancements

- Payment processing integration
- Credit score verification
- Automated loan matching
- Email notifications
- Mobile app development
- Advanced analytics and reporting
- Risk assessment algorithms
- Secondary market for loan trading

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.
