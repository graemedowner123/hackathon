#!/bin/bash

echo "🚀 P2P Lending Platform - Instant Presentation Deployment"
echo "=========================================================="

# Create deployment package
echo "📦 Creating deployment package..."
cd /home/graemedowner/hackathon

# Ensure netlify-deploy directory exists with all files
if [ ! -d "netlify-deploy" ]; then
    mkdir netlify-deploy
fi

cp presentation.html netlify-deploy/index.html
echo "✅ Presentation copied to deployment package"

# Create a zip file for easy upload
echo "📦 Creating deployment archive..."
cd netlify-deploy
zip -r ../p2p-lending-presentation.zip .
cd ..

echo ""
echo "🎯 INSTANT DEPLOYMENT OPTIONS:"
echo "=============================="
echo ""
echo "🌟 OPTION 1: Netlify (Recommended - 2 minutes)"
echo "   1. Go to https://netlify.com"
echo "   2. Sign up/login (free)"
echo "   3. Drag and drop the 'netlify-deploy' folder"
echo "   4. Get instant URL like: https://amazing-name-123456.netlify.app"
echo ""
echo "🌟 OPTION 2: Surge.sh (Fastest - 1 minute)"
echo "   1. Install: npm install -g surge"
echo "   2. Run: cd netlify-deploy && surge"
echo "   3. Choose domain: p2p-lending-demo.surge.sh"
echo "   4. Get instant URL: https://p2p-lending-demo.surge.sh"
echo ""
echo "🌟 OPTION 3: GitHub Pages (Professional - 5 minutes)"
echo "   1. Create new GitHub repository"
echo "   2. Upload files from netlify-deploy folder"
echo "   3. Enable Pages in Settings"
echo "   4. Get URL: https://username.github.io/repository-name"
echo ""
echo "🌟 OPTION 4: Vercel (Developer-friendly - 3 minutes)"
echo "   1. Go to https://vercel.com"
echo "   2. Import from GitHub or upload folder"
echo "   3. Get instant URL: https://project-name.vercel.app"
echo ""

# Check if we can use surge directly
if command -v surge &> /dev/null; then
    echo "🚀 SURGE.SH DETECTED - DEPLOY NOW?"
    echo "=================================="
    echo "Surge is installed. Deploy immediately? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "🚀 Deploying to Surge.sh..."
        cd netlify-deploy
        surge --domain p2p-lending-demo-$(date +%s).surge.sh
        echo "✅ Deployment complete!"
    fi
else
    echo "💡 TIP: Install Surge for instant deployment:"
    echo "   npm install -g surge"
    echo "   cd netlify-deploy && surge"
fi

echo ""
echo "📁 Files ready for deployment:"
echo "   📂 netlify-deploy/ (drag & drop this folder)"
echo "   📦 p2p-lending-presentation.zip (upload this file)"
echo ""
echo "🎯 Your presentation showcases:"
echo "   • AI-powered competitive bidding system"
echo "   • 6 intelligent bot lenders with $2.5M capital"
echo "   • 97.8% system reliability"
echo "   • Production-ready AWS architecture"
echo "   • Comprehensive testing results"
echo ""
echo "✅ Ready for investor demos and stakeholder presentations!"
