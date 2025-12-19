#!/bin/bash
# ZAS Ecosystem Stop Script
# Stops all ZAS services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stopping ZAS Ecosystem${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to stop a service
stop_service() {
    local name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${BLUE}Stopping $name (PID: $PID)...${NC}"
            kill $PID 2>/dev/null || true
            sleep 1
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${YELLOW}Force stopping $name...${NC}"
                kill -9 $PID 2>/dev/null || true
            fi
            echo -e "${GREEN}✓ $name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $name not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  $name PID file not found${NC}"
    fi
}

# Stop all services
stop_service "MCP Server" "logs/mcp_server.pid"
stop_service "Chat API" "logs/chat_api.pid"
stop_service "MCP Proxy" "logs/mcp_proxy.pid"
stop_service "Telegram Bot" "logs/telegram_bot.pid"
stop_service "Dashboard" "logs/dashboard.pid"

echo ""

# Kill any remaining Python processes running ZAS
echo -e "${BLUE}Checking for remaining ZAS processes...${NC}"
pkill -f "python3 app.py" 2>/dev/null && echo -e "${GREEN}✓ Killed remaining MCP Server processes${NC}" || true
pkill -f "python3 chat_api.py" 2>/dev/null && echo -e "${GREEN}✓ Killed remaining Chat API processes${NC}" || true
pkill -f "python3 mcp_proxy.py" 2>/dev/null && echo -e "${GREEN}✓ Killed remaining MCP Proxy processes${NC}" || true
pkill -f "python3 telegram_bot.py" 2>/dev/null && echo -e "${GREEN}✓ Killed remaining Telegram Bot processes${NC}" || true
pkill -f "python3 dashboard.py" 2>/dev/null && echo -e "${GREEN}✓ Killed remaining Dashboard processes${NC}" || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ZAS Ecosystem Stopped${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Logs are preserved in: logs/"
echo ""
