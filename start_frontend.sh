#!/bin/bash

# Start DatabaseAI Frontend

echo "🚀 Starting DatabaseAI Frontend..."
echo ""

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found"
    echo "Please run this script from the DATABASEAI root directory"
    exit 1
fi

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    echo "REACT_APP_API_URL=http://localhost:8088/api/v1" > .env
fi

# Start the development server
echo "🌐 Starting frontend server..."
echo "📱 Application will open at http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm start
