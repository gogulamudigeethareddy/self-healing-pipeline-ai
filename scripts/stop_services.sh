#!/bin/bash

# AI-Powered Self-Healing Data Pipeline - Service Stop Script

echo "🛑 Stopping AI-Powered Self-Healing Data Pipeline Services"
echo "=========================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Stop Docker services
print_status "Stopping Docker services..."
docker-compose down

# Stop Flask backend if PID file exists
if [ -f ".flask_pid" ]; then
    FLASK_PID=$(cat .flask_pid)
    if ps -p $FLASK_PID > /dev/null; then
        print_status "Stopping Flask backend (PID: $FLASK_PID)..."
        kill $FLASK_PID
    fi
    rm .flask_pid
fi

# Stop React frontend if PID file exists
if [ -f ".react_pid" ]; then
    REACT_PID=$(cat .react_pid)
    if ps -p $REACT_PID > /dev/null; then
        print_status "Stopping React frontend (PID: $REACT_PID)..."
        kill $REACT_PID
    fi
    rm .react_pid
fi

# Kill any remaining processes on the ports
print_status "Cleaning up port processes..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true

print_status "✅ All services stopped successfully!" 