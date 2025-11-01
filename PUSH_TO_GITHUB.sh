#!/bin/bash
# GitHub Push Script
# Run this on your LOCAL machine (not in sandbox)

echo "🚀 Pushing Unusual Whales Scanner to GitHub..."
echo ""

# Add remote
git remote add origin https://github.com/Renotrader31/unusual-whales-scanner.git

# Push to GitHub
git push -u origin main

echo ""
echo "✅ Done! Check your repo at:"
echo "https://github.com/Renotrader31/unusual-whales-scanner"
