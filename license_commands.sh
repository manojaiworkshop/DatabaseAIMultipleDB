#!/bin/bash

# Quick Commands for License Portal Integration

echo "======================================================================"
echo "  PGAIView License Portal - Quick Commands"
echo "======================================================================"
echo ""

# Function to run commands
run_command() {
    echo "→ $1"
    echo ""
}

echo "📋 START SERVICES"
echo "----------------------------------------------------------------------"
run_command "cd license-portal && ./start.sh"
echo "  - License Portal UI: http://localhost:3000"
echo "  - License API: http://localhost:8000"
echo ""
run_command "cd /media/crl/Extra\\ Disk31/PYTHON_CODE/DATABASEAI/DatabaseAI && ./start.sh"
echo "  - DatabaseAI: http://localhost:3000"
echo ""

echo "📋 TEST LICENSE PORTAL"
echo "----------------------------------------------------------------------"
run_command "curl http://localhost:8000/api/health"
echo ""
run_command "cd license-portal && python3 test_email.py"
echo ""

echo "📋 GENERATE LICENSE (via API)"
echo "----------------------------------------------------------------------"
cat << 'EOF'
curl -X POST http://localhost:8000/api/license/generate \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "deployment_id": "deploy-20251102-TEST",
    "license_type": "trial"
  }'
EOF
echo ""

echo "📋 ACTIVATE LICENSE IN DATABASEAI"
echo "----------------------------------------------------------------------"
cat << 'EOF'
curl -X POST http://localhost:8000/license/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "YOUR-LICENSE-KEY"}'
EOF
echo ""

echo "📋 CHECK LICENSE STATUS"
echo "----------------------------------------------------------------------"
run_command "curl http://localhost:8000/license/info"
run_command "curl http://localhost:8000/license/check"
run_command "curl http://localhost:8000/license/server-config"
echo ""

echo "📋 UPDATE LICENSE SERVER URL"
echo "----------------------------------------------------------------------"
cat << 'EOF'
curl -X PUT http://localhost:8000/license/server-config \
  -H "Content-Type: application/json" \
  -d '{"server_url": "http://localhost:8000"}'
EOF
echo ""

echo "📋 VALIDATE LICENSE DIRECTLY"
echo "----------------------------------------------------------------------"
cat << 'EOF'
curl -X POST http://localhost:8000/api/license/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "YOUR-LICENSE-KEY"}'
EOF
echo ""

echo "📋 STOP/RESTART SERVICES"
echo "----------------------------------------------------------------------"
run_command "# Kill processes on specific ports"
run_command "lsof -ti:8000 | xargs kill -9"
run_command "lsof -ti:3000 | xargs kill -9"
echo ""

echo "📋 CHECK RUNNING SERVICES"
echo "----------------------------------------------------------------------"
run_command "lsof -i:8000"
run_command "lsof -i:3000"
run_command "ps aux | grep 'uvicorn\\|node\\|react'"
echo ""

echo "📋 VIEW LOGS"
echo "----------------------------------------------------------------------"
run_command "# License Portal logs"
run_command "cd license-portal/backend && tail -f license_portal.log"
echo ""
run_command "# DatabaseAI logs"
run_command "cd /media/crl/Extra\\ Disk31/PYTHON_CODE/DATABASEAI/DatabaseAI && tail -f backend.log"
echo ""

echo "📋 DOCKER COMMANDS"
echo "----------------------------------------------------------------------"
run_command "# Build DatabaseAI with new license integration"
run_command "docker build -f Dockerfile.combined -t opendockerai/pgaiview:latest ."
echo ""
run_command "# Run DatabaseAI container"
run_command "docker stop pgaiview 2>/dev/null; docker rm pgaiview 2>/dev/null"
run_command "docker run -d --name pgaiview -p 80:80 \\"
echo "  -e LICENSE_SERVER_URL=http://host.docker.internal:8000 \\"
echo "  opendockerai/pgaiview:latest"
echo ""

echo "======================================================================"
echo "  Quick Links"
echo "======================================================================"
echo ""
echo "🌐 Web Interfaces:"
echo "   License Portal:  http://localhost:3000"
echo "   DatabaseAI App:  http://localhost:3000"
echo ""
echo "📚 API Documentation:"
echo "   License API:     http://localhost:8000/api/docs"
echo "   License Redoc:   http://localhost:8000/api/redoc"
echo ""
echo "📖 Documentation:"
echo "   Integration Guide:  LICENSE_PORTAL_INTEGRATION.md"
echo "   Update Summary:     LICENSE_PORTAL_UPDATE_SUMMARY.md"
echo "   Email Setup:        license-portal/EMAIL_SETUP_GUIDE.md"
echo "   Changelog:          license-portal/CHANGELOG.md"
echo ""
echo "======================================================================"
