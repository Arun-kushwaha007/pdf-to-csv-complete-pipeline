#!/bin/bash

# Test script to verify React frontend build
echo "🧪 Testing React frontend build..."

cd frontend

# Clean install
echo "Cleaning previous install..."
rm -rf node_modules package-lock.json

# Install dependencies
echo "Installing dependencies..."
npm install --legacy-peer-deps

# Build
echo "Building frontend..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ React build successful!"
    echo "Build output is in frontend/build/"
else
    echo "❌ React build failed!"
    exit 1
fi
