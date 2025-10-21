#!/bin/bash
# Test frontend build before deployment

echo "🧪 Testing frontend build..."

cd frontend

# Clean everything
echo "Cleaning previous build..."
rm -rf node_modules package-lock.json build .npm

# Clear npm cache
echo "Clearing npm cache..."
npm cache clean --force

# Install dependencies
echo "Installing dependencies..."
npm install --legacy-peer-deps --force

# Fix ajv issues
echo "Fixing ajv dependency issues..."
npm install ajv@^6.12.6 ajv-keywords@^3.5.2 --legacy-peer-deps

# Test build
echo "Testing build..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Frontend build test successful!"
    echo "You can now run the full deployment with: ./deploy.sh"
else
    echo "❌ Frontend build test failed!"
    echo "Please check the error messages above"
    exit 1
fi
