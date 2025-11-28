# RAG Feature Quick Start Script (PowerShell)

Write-Host "🚀 DatabaseAI RAG Feature Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "✅ Docker found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Start Qdrant
Write-Host "📦 Starting Qdrant Vector Database..." -ForegroundColor Yellow
docker-compose -f docker-compose.qdrant.yml up -d

# Wait for Qdrant to be ready
Write-Host "⏳ Waiting for Qdrant to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:6333" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Qdrant is ready!" -ForegroundColor Green
            break
        }
    } catch {
        # Continue waiting
    }
    
    $attempt++
    Write-Host "   Waiting... ($attempt/$maxAttempts)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($attempt -eq $maxAttempts) {
    Write-Host "❌ Qdrant failed to start. Check logs with: docker-compose -f docker-compose.qdrant.yml logs" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔧 Installing Python dependencies..." -ForegroundColor Yellow
Set-Location backend
pip install qdrant-client==1.7.0 sentence-transformers==2.2.2 pandas==2.1.4

Write-Host ""
Write-Host "✅ RAG Feature Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Enable RAG in app_config.yml (rag.enabled: true)" -ForegroundColor White
Write-Host "2. Restart backend: python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8088" -ForegroundColor White
Write-Host "3. Open the UI and go to Settings → RAG tab" -ForegroundColor White
Write-Host "4. (Optional) Upload sample data from rag_sample_data.csv" -ForegroundColor White
Write-Host ""
Write-Host "📊 Qdrant Dashboard: http://localhost:6333/dashboard" -ForegroundColor Cyan
Write-Host "📚 Documentation: See RAG_FEATURE_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
