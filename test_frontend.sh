#!/bin/bash

# Quick test script for React frontend build
echo "🧪 Testing React frontend build..."

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found. Please run from project root."
    exit 1
fi

cd frontend

# Check Node.js version
echo "Node.js version: $(node -v)"
echo "npm version: $(npm -v)"

# Clean previous build
echo "Cleaning previous build..."
rm -rf node_modules package-lock.json build

# Install dependencies
echo "Installing dependencies with legacy peer deps..."
npm install --legacy-peer-deps

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Build
echo "Building frontend..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ React build successful!"
    echo "Build output is in frontend/build/"
    ls -la build/
else
    echo "❌ React build failed!"
    exit 1
fi

echo "🎉 Frontend build test completed successfully!"
