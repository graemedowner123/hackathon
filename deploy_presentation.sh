#!/bin/bash

# P2P Lending Platform - Presentation Deployment Script
# This script will help you publish your presentation to GitHub Pages

echo "🚀 P2P Lending Platform - Presentation Deployment"
echo "=================================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Initializing..."
    git init
    echo "✅ Git repository initialized"
fi

# Create a gh-pages branch if it doesn't exist
echo "📝 Setting up GitHub Pages branch..."

# Check if gh-pages branch exists
if git show-ref --verify --quiet refs/heads/gh-pages; then
    echo "✅ gh-pages branch already exists"
else
    echo "📝 Creating gh-pages branch..."
    git checkout --orphan gh-pages
    git rm -rf . 2>/dev/null || true
    echo "✅ gh-pages branch created"
fi

# Switch to gh-pages branch
git checkout gh-pages

# Copy presentation files
echo "📋 Copying presentation files..."
cp presentation.html index.html
echo "✅ Presentation copied as index.html"

# Create a simple README for the gh-pages branch
cat > README.md << 'EOF'
# P2P Lending Platform - Live Presentation

This is the live presentation for the P2P Lending Platform.

## View the Presentation

The presentation is automatically deployed to GitHub Pages and can be viewed at:
`https://[your-username].github.io/[repository-name]/`

## Features Showcased

- AI-Powered Bot Lending System
- Competitive Bidding Marketplace
- AWS Cloud Architecture
- Real-time Performance Metrics
- Comprehensive Testing Results

## Last Updated

Generated automatically on deployment.
EOF

# Add all files
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Deploy P2P Lending Platform presentation to GitHub Pages - $(date)"

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo "1. Push this branch to GitHub:"
echo "   git remote add origin https://github.com/[your-username]/[repository-name].git"
echo "   git push -u origin gh-pages"
echo ""
echo "2. Enable GitHub Pages in your repository settings:"
echo "   - Go to Settings > Pages"
echo "   - Select 'Deploy from a branch'"
echo "   - Choose 'gh-pages' branch"
echo "   - Click Save"
echo ""
echo "3. Your presentation will be available at:"
echo "   https://[your-username].github.io/[repository-name]/"
echo ""
echo "✅ Deployment preparation complete!"
