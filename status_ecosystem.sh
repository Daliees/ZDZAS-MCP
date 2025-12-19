#!/bin/bash
# ZAS Ecosystem Status Checker
# Checks the status of all ZAS services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ZAS Ecosystem Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Set defaults
MCP_HOST=${MCP_HOST:-127.0.0.1}
MCP_PORT=${MCP_PORT:-8000}
CHAT_API_HOST=${CHAT_API_HOST:-0.0.0.0}
CHAT_API_PORT=${CHAT_API_PORT:-3000}
MCP_PROXY_HOST=${MCP_PROXY_HOST:-0.0.0.0}
MCP_PROXY_PORT=${MCP_PROXY_PORT:-8080}

# Function to check service status
check_service() {
    local name=$1
    local pid_file=$2
    local port=$3
    local url=$4
    
    echo -e "${BLUE}$name:${NC}"
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "  Status: ${GREEN}Running${NC}"
            echo -e "  PID: $PID"
            echo -e "  Port: $port"
            echo -e "  URL: $url"
            
            # Check if port is actually listening
            if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                echo -e "  Port Status: ${GREEN}Listening${NC}"
            else
                echo -e "  Port Status: ${RED}Not Listening${NC}"
            fi
        else
            echo -e "  Status: ${RED}Not Running${NC} (stale PID file)"
        fi
    else
        echo -e "  Status: ${RED}Not Running${NC} (no PID file)"
    fi
    echo ""
}

# Check all services
check_service "MCP Server" "logs/mcp_server.pid" "$MCP_PORT" "http://$MCP_HOST:$MCP_PORT/mcp"
check_service "Chat API" "logs/chat_api.pid" "$CHAT_API_PORT" "http://$CHAT_API_HOST:$CHAT_API_PORT"
check_service "MCP Proxy" "logs/mcp_proxy.pid" "$MCP_PROXY_PORT" "http://$MCP_PROXY_HOST:$MCP_PROXY_PORT/mcp"

# Check Telegram Bot separately (no port)
echo -e "${BLUE}Telegram Bot:${NC}"
if [ -f "logs/telegram_bot.pid" ]; then
    PID=$(cat "logs/telegram_bot.pid")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "  Status: ${GREEN}Running${NC}"
        echo -e "  PID: $PID"
        echo -e "  Commands: /status, /help"
    else
        echo -e "  Status: ${RED}Not Running${NC} (stale PID file)"
    fi
else
    echo -e "  Status: ${RED}Not Running${NC} (no PID file)"
fi
echo ""

# Check Dashboard
DASHBOARD_PORT=${DASHBOARD_PORT:-5000}
check_service "Dashboard" "logs/dashboard.pid" "$DASHBOARD_PORT" "http://0.0.0.0:$DASHBOARD_PORT"

# Show recent log entries
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Recent Logs${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ -d "logs" ]; then
    echo -e "${YELLOW}Last 5 lines of each log:${NC}"
    echo ""
    
    for log in logs/*.log; do
        if [ -f "$log" ]; then
            echo -e "${BLUE}$(basename $log):${NC}"
            tail -n 5 "$log" 2>/dev/null | sed 's/^/  /'
            echo ""
        fi
    done
else
    echo -e "${YELLOW}No logs directory found${NC}"
fi

echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Commands:"
echo -e "  Start:  ./start_ecosystem.sh"
echo -e "  Stop:   ./stop_ecosystem.sh"
echo -e "  Logs:   tail -f logs/mcp_server.log"
echo ""
