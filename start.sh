#!/bin/bash

echo "Starting P2P Lending Platform..."
echo "=================================="

# Check if demo data exists
if [ ! -f "p2p_lending.db" ]; then
    echo "No database found. Creating demo data..."
    python3 demo.py
    echo ""
fi

echo "Starting Flask application..."
echo "Access the application at: http://localhost:5000"
echo ""
echo "Demo accounts:"
echo "Borrowers: john.borrower@example.com, sarah.borrower@example.com"
echo "Lenders: mike.lender@example.com, lisa.lender@example.com, david.lender@example.com"
echo "Password for all accounts: password123"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

python3 app.py
