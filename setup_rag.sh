#!/bin/bash

# RAG Feature Quick Start Script

echo "🚀 DatabaseAI RAG Feature Setup"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Docker found"
echo ""

# Start Qdrant
echo "📦 Starting Qdrant Vector Database..."
docker-compose -f docker-compose.qdrant.yml up -d

# Wait for Qdrant to be ready
echo "⏳ Waiting for Qdrant to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:6333 > /dev/null 2>&1; then
        echo "✅ Qdrant is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Waiting... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Qdrant failed to start. Check logs with: docker-compose -f docker-compose.qdrant.yml logs"
    exit 1
fi

echo ""
echo "🔧 Installing Python dependencies..."
cd backend
pip install qdrant-client==1.7.0 sentence-transformers==2.2.2 pandas==2.1.4

echo ""
echo "✅ RAG Feature Setup Complete!"
echo ""
echo "📝 Next Steps:"
echo "1. Enable RAG in app_config.yml (rag.enabled: true)"
echo "2. Restart backend: python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8088"
echo "3. Open the UI and go to Settings → RAG tab"
echo "4. (Optional) Upload sample data from rag_sample_data.csv"
echo ""
echo "📊 Qdrant Dashboard: http://localhost:6333/dashboard"
echo "📚 Documentation: See RAG_FEATURE_GUIDE.md"
echo ""
