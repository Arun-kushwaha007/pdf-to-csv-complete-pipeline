#!/bin/bash
# Comprehensive frontend build test

echo "🧪 Testing frontend build with comprehensive dependency fixes..."

cd frontend

# Clean everything thoroughly
echo "🧹 Cleaning previous build..."
rm -rf node_modules package-lock.json build .npm .cache

# Clear all caches
echo "🗑️ Clearing all caches..."
npm cache clean --force
yarn cache clean 2>/dev/null || true

# Install dependencies with specific strategy
echo "📦 Installing dependencies..."
npm install --legacy-peer-deps --force

# Fix ajv specifically
echo "🔧 Fixing ajv dependency..."
npm install ajv@^6.12.6 --legacy-peer-deps --force

# Remove problematic packages and reinstall
echo "🔄 Reinstalling problematic packages..."
npm uninstall ajv-formats ajv-keywords 2>/dev/null || true
npm install ajv@^6.12.6 --legacy-peer-deps --force

# Try to install compatible versions
echo "🔧 Installing compatible versions..."
npm install ajv-keywords@^3.5.2 --legacy-peer-deps --force 2>/dev/null || true

# Test build
echo "🏗️ Testing build..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Frontend build test successful!"
    echo "You can now run the full deployment with: ./deploy.sh"
else
    echo "❌ Frontend build test failed!"
    echo ""
    echo "🔍 Debugging information:"
    echo "Node version: $(node --version)"
    echo "NPM version: $(npm --version)"
    echo ""
    echo "📋 Installed ajv packages:"
    npm list ajv ajv-keywords ajv-formats 2>/dev/null || true
    echo ""
    echo "Please check the error messages above"
    exit 1
fi