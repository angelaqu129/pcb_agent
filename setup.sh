#!/bin/bash

# Quick setup script for Cursor PCB

echo "🔧 Cursor PCB Setup"
echo "==================="
echo ""

cd frontend

echo "📦 Installing frontend dependencies..."
npm install --legacy-peer-deps

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "🚀 To start the app, run:"
    echo "   ./start.sh"
    echo ""
    echo "   OR"
    echo ""
    echo "   cd frontend && npm run dev"
else
    echo ""
    echo "❌ Setup failed. Please check the errors above."
    exit 1
fi
