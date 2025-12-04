#!/bin/bash

# Quick Start Script for VodafoneZiggo AI Assistant
# This script helps get the system up and running quickly

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════╗"
echo "║  VodafoneZiggo AI Assistant - Quick Start         ║"
echo "╚════════════════════════════════════════════════════╝"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✓ Docker found"

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker Compose found"

# Change to project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "📦 Building Docker image..."
docker-compose build

echo ""
echo "🚀 Starting containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for service to be ready (this may take 2-3 minutes on first run)..."
echo "   - Downloading embedding model (~350MB)"
echo "   - Scraping VodafoneZiggo website"
echo "   - Creating vector embeddings"

# Wait for health check to pass
RETRIES=30
while [ $RETRIES -gt 0 ]; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✓ Service is ready!"
        break
    fi
    echo "   Waiting... ($RETRIES attempts remaining)"
    sleep 5
    RETRIES=$((RETRIES - 1))
done

if [ $RETRIES -eq 0 ]; then
    echo "❌ Service did not start. Check logs with: docker-compose logs -f"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║           ✨ READY TO USE! ✨                     ║"
echo "╠════════════════════════════════════════════════════╣"
echo "║ API Endpoint:  http://localhost:8000               ║"
echo "║ API Docs:      http://localhost:8000/docs          ║"
echo "║ Health Check:  http://localhost:8000/api/health    ║"
echo "╚════════════════════════════════════════════════════╝"

echo ""
echo "📚 Example Requests:"
echo ""
echo "1. Check health:"
echo "   curl http://localhost:8000/api/health"
echo ""
echo "2. Ask a question:"
echo "   curl -X POST http://localhost:8000/api/ask \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"question\": \"What internet packages do you offer?\"}'"
echo ""
echo "3. Get statistics:"
echo "   curl http://localhost:8000/api/stats"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f ai-assistant"
echo ""
echo "5. Stop the service:"
echo "   docker-compose down"
echo ""
echo "✅ Setup complete! Visit http://localhost:8000/docs for interactive API docs"
