#!/bin/bash

# Legal AI Document Processing System - Startup Script

set -e

echo "================================"
echo "Legal AI System Startup"
echo "================================"

# Check if in backend directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found. Please run this script from the backend directory."
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Create data directories
mkdir -p data/uploads data/db data/vector_db data/logs

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Copying .env.example..."
    cp .env.example .env
    echo "Please edit .env with your OpenAI API key and other settings."
    echo ""
    read -p "Press Enter to continue..."
fi

# Initialize database
echo "Initializing database..."
python3 -c "from app.models import init_db; init_db(); print('Database initialized.')"

# Start server
echo ""
echo "Starting server on http://localhost:8000"
echo "API documentation: http://localhost:8000/docs"
echo "Frontend: Open frontend/public/index.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn app.main:app --reload --port 8000
