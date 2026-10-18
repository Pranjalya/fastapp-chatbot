#!/bin/bash
set -e

# Base directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=== AuraChat Multi-Turn AI Intelligence ==="

# Ensure directories
mkdir -p data/uploads

# Activate Python Virtualenv
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Export Python path
export PYTHONPATH="$DIR/backend:$PYTHONPATH"

# Function to run backend
start_backend() {
    echo "Starting FastAPI backend on http://0.0.0.0:8000 ..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Function to run frontend
start_frontend() {
    echo "Starting React Vite frontend on http://localhost:5173 ..."
    cd "$DIR/frontend"
    exec npm run dev
}

case "$1" in
    frontend)
        start_frontend
        ;;
    backend)
        start_backend
        ;;
    *)
        echo "Usage: ./run.sh [backend|frontend]"
        echo "Starting backend by default..."
        start_backend
        ;;
esac
