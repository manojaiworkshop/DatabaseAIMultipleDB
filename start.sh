#!/bin/bash

# Start both backend and frontend in separate terminal windows

echo "🚀 Starting DatabaseAI..."

# Start backend
gnome-terminal --tab --title="Backend" -- bash -c "
    cd backend
    source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
    pip install -q -r requirements.txt
    echo '✅ Backend starting on http://localhost:8088'
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8088
    exec bash
" &

# Wait a moment for backend to start
sleep 3

# Start frontend
gnome-terminal --tab --title="Frontend" -- bash -c "
    cd frontend
    npm install --silent 2>/dev/null
    echo '✅ Frontend starting on http://localhost:3000'
    npm start
    exec bash
" &

echo "✅ Both services are starting..."
echo "   Backend:  http://localhost:8088"
echo "   Frontend: http://localhost:3000"
echo ""
echo "The application will open automatically in your browser."
