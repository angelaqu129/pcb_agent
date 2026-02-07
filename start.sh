#!/bin/bash

# Cursor PCB - Development Start Script

echo "🚀 Starting Cursor PCB Development Environment"
echo ""

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install --legacy-peer-deps
    cd ..
    echo "✅ Dependencies installed"
    echo ""
fi

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi
echo "✅ Node.js $(node --version)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi
echo "✅ Python $(python3 --version)"

# Check KiCAD (optional)
if command -v kicad-cli &> /dev/null; then
    echo "✅ KiCAD CLI found"
else
    echo "⚠️  KiCAD CLI not found (optional for SVG export)"
fi

echo ""
echo "🎨 Starting Electron + React app..."
echo "   Frontend will open automatically"
echo "   Press Ctrl+C to stop"
echo ""

# Start the app
cd frontend
npm run dev
