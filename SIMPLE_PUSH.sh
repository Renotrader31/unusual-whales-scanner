#!/bin/bash
# Simple GitHub Push Script
# Run this from inside the uw_scanner directory

echo "🚀 Setting up GitHub repository..."

# Check if we're in a git repo
if [ ! -d .git ]; then
    echo "❌ Error: Not in a git repository"
    echo "Make sure you're inside the uw_scanner folder"
    exit 1
fi

# Add remote (will fail if already exists, that's OK)
git remote add origin https://github.com/Renotrader31/unusual-whales-scanner.git 2>/dev/null || true

# Show current status
echo ""
echo "📊 Repository Status:"
git log --oneline -5
echo ""
echo "📁 Files ready to push:"
git ls-files | wc -l
echo ""

# Push to GitHub
echo "🔄 Pushing to GitHub..."
echo "You'll be prompted for credentials:"
echo "  Username: Renotrader31"
echo "  Password: Use your Personal Access Token"
echo ""

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Your code is now on GitHub!"
    echo "🔗 View it at: https://github.com/Renotrader31/unusual-whales-scanner"
else
    echo ""
    echo "❌ Push failed. Check your credentials and try again."
fi
