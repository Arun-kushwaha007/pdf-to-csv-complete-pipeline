#!/bin/bash
# Debug frontend dependencies

echo "🔍 Debugging frontend dependencies..."

cd frontend

echo "📋 Environment:"
echo "Node version: $(node --version)"
echo "NPM version: $(npm --version)"
echo ""

echo "📦 Current package.json:"
cat package.json
echo ""

echo "🧹 Cleaning everything..."
rm -rf node_modules package-lock.json build .npm

echo "📦 Installing dependencies..."
npm install --legacy-peer-deps --force

echo "🔍 Checking ajv-related packages:"
npm list ajv ajv-keywords ajv-formats 2>/dev/null || echo "Some packages not found"

echo "🔍 Checking what's in node_modules/ajv:"
ls -la node_modules/ajv/ 2>/dev/null || echo "ajv not found"

echo "🔍 Checking ajv version:"
npm list ajv 2>/dev/null || echo "ajv not found"

echo "🔍 Checking for ajv/dist/compile/codegen:"
find node_modules -name "codegen*" 2>/dev/null || echo "codegen not found"

echo "🔍 Checking ajv-formats dependencies:"
npm list ajv-formats 2>/dev/null || echo "ajv-formats not found"

echo "🔍 Checking what ajv-formats expects:"
cat node_modules/ajv-formats/package.json 2>/dev/null | grep -A5 -B5 ajv || echo "ajv-formats package.json not found"

echo "🏗️ Attempting build..."
npm run build
