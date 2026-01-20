#!/bin/bash
# Start script for ZDZAS-MCP servers

cd "$(dirname "$0")" || exit 1

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
  echo "❌ Virtual environment not found!"
  echo "Creating .venv..."
  python3 -m venv .venv
  source .venv/bin/activate
  echo "📦 Installing dependencies..."
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
  echo "❌ .env file not found!"
  echo "Copy .env.example to .env and configure it:"
  echo "  cp .env.example .env"
  exit 1
fi

echo "🚀 Starting ZDZAS-MCP servers..."
echo ""
echo "  📍 MCP Server:  http://127.0.0.1:8000/mcp"
echo "  📍 Chat API:    http://0.0.0.0:9000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start both servers
python3 start_all.py
