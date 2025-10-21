#!/bin/bash
# Alternative frontend build using Yarn

echo "🧪 Testing frontend build with Yarn (alternative approach)..."

cd frontend

# Clean everything
echo "🧹 Cleaning previous build..."
rm -rf node_modules yarn.lock build .yarn

# Install Yarn if not available
if ! command -v yarn &> /dev/null; then
    echo "📦 Installing Yarn..."
    npm install -g yarn
fi

# Install dependencies with Yarn
echo "📦 Installing dependencies with Yarn..."
yarn install

# Test build
echo "🏗️ Testing build with Yarn..."
yarn build

if [ $? -eq 0 ]; then
    echo "✅ Frontend build with Yarn successful!"
    echo "You can now run the full deployment with: ./deploy.sh"
else
    echo "❌ Frontend build with Yarn also failed!"
    echo "Falling back to npm approach..."
    exit 1
fi
