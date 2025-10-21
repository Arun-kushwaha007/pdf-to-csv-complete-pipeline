#!/bin/bash
# Quick test for OpenSSL fix

echo "🧪 Testing OpenSSL legacy provider fix..."

cd frontend

# Test build with OpenSSL legacy provider
echo "🏗️ Testing build with OpenSSL legacy provider..."
NODE_OPTIONS='--openssl-legacy-provider' npm run build

if [ $? -eq 0 ]; then
    echo "✅ OpenSSL fix successful!"
    echo "Frontend build works with Node.js 18.20.8"
    echo "You can now run the full deployment with: ./deploy.sh"
else
    echo "❌ OpenSSL fix failed!"
    echo "Error details above"
    exit 1
fi
