#!/bin/bash

# AI-Powered Self-Healing Data Pipeline - Service Startup Script
# This script starts all services in the correct order

set -e

echo "🚀 Starting AI-Powered Self-Healing Data Pipeline Services"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    cp env.example .env
    print_warning "Please edit .env file with your OpenAI API key and other settings."
    read -p "Press Enter to continue after editing .env file..."
fi

# Step 1: Start Airflow services
print_status "Starting Airflow services..."
docker-compose up -d airflow-webserver airflow-scheduler postgres redis airflow-init

# Wait for Airflow to be ready
print_status "Waiting for Airflow to be ready..."
sleep 30

# Check if Airflow is running
if curl -s http://localhost:8080/health > /dev/null; then
    print_status "✅ Airflow is running at http://localhost:8080"
else
    print_warning "Airflow might still be starting up. Check http://localhost:8080"
fi

# Step 2: Start Flask backend
print_status "Starting Flask backend..."
cd backend
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

print_status "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r ../requirements.txt

print_status "Starting Flask API server..."
python app.py &
FLASK_PID=$!
cd ..

# Wait for Flask to be ready
sleep 5

# Check if Flask is running
if curl -s http://localhost:5000/api/employees > /dev/null; then
    print_status "✅ Flask API is running at http://localhost:5000"
else
    print_warning "Flask API might still be starting up. Check http://localhost:5000"
fi

# Step 3: Start React frontend
print_status "Starting React frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_status "Installing Node.js dependencies..."
    npm install
fi

print_status "Starting React development server..."
npm start &
REACT_PID=$!
cd ..

# Wait for React to be ready
sleep 10

# Check if React is running
if curl -s http://localhost:3000 > /dev/null; then
    print_status "✅ React dashboard is running at http://localhost:3000"
else
    print_warning "React dashboard might still be starting up. Check http://localhost:3000"
fi

echo ""
echo "🎉 All services started successfully!"
echo "====================================="
echo "📊 Airflow UI:     http://localhost:8080 (admin/admin)"
echo "🔧 Flask API:      http://localhost:5000"
echo "📱 React Dashboard: http://localhost:3000"
echo ""
echo "📋 Next steps:"
echo "1. Open the React dashboard to monitor the pipeline"
echo "2. Run the demo script: python scripts/demo.py"
echo "3. Check Airflow UI to see the pipeline DAG"
echo ""
echo "To stop all services, run: ./scripts/stop_services.sh"
echo ""

# Save PIDs for stopping services later
echo $FLASK_PID > .flask_pid
echo $REACT_PID > .react_pid

# Wait for user to stop
echo "Press Ctrl+C to stop all services..."
trap 'echo ""; print_status "Stopping services..."; kill $FLASK_PID $REACT_PID 2>/dev/null; exit 0' INT
wait 