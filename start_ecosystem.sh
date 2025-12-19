#!/bin/bash
# ZAS Ecosystem Starter
# Starts all necessary services for the ZAS system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ZAS Ecosystem Starter${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo -e "${YELLOW}Please create a .env file with your configuration.${NC}"
    echo "Example:"
    echo "  cp env-dot .env"
    echo "  nano .env"
    exit 1
fi

echo -e "${GREEN}✓ Configuration file found${NC}"
# Load environment variables
set -a
source .env
set +a

# Set defaults if not specified
MCP_HOST=${MCP_HOST:-127.0.0.1}
MCP_PORT=${MCP_PORT:-8000}
CHAT_API_HOST=${CHAT_API_HOST:-0.0.0.0}
CHAT_API_PORT=${CHAT_API_PORT:-3000}
MCP_PROXY_HOST=${MCP_PROXY_HOST:-0.0.0.0}
MCP_PROXY_PORT=${MCP_PROXY_PORT:-8080}
# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"
python3 -c "import fastmcp" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Dependencies not installed${NC}"
    echo -e "${BLUE}Installing dependencies...${NC}"
    pip install -r requirements.txt
}

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Create logs directory
mkdir -p logs

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Starting Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Start MCP Server
if check_port $MCP_PORT; then
    echo -e "${BLUE}Starting MCP Server on $MCP_HOST:$MCP_PORT...${NC}"
    nohup python3 app.py > logs/mcp_server.log 2>&1 &
    MCP_PID=$!
    echo $MCP_PID > logs/mcp_server.pid
    echo -e "${GREEN}✓ MCP Server started (PID: $MCP_PID)${NC}"
    echo -e "  Log: logs/mcp_server.log"
    echo -e "  URL: http://$MCP_HOST:$MCP_PORT/mcp"
else
    echo -e "${YELLOW}⚠️  Skipping MCP Server (port $MCP_PORT in use)${NC}"
    MCP_PID=""
fi

sleep 2

# Start Chat API
if check_port $CHAT_API_PORT; then
    echo -e "${BLUE}Starting Chat API on $CHAT_API_HOST:$CHAT_API_PORT...${NC}"
    nohup python3 chat_api.py > logs/chat_api.log 2>&1 &
    CHAT_PID=$!
    echo $CHAT_PID > logs/chat_api.pid
    echo -e "${GREEN}✓ Chat API started (PID: $CHAT_PID)${NC}"
    echo -e "  Log: logs/chat_api.log"
    echo -e "  URL: http://$CHAT_API_HOST:$CHAT_API_PORT"
else
    echo -e "${YELLOW}⚠️  Skipping Chat API (port $CHAT_API_PORT in use)${NC}"
    CHAT_PID=""
fi

sleep 2

# Start MCP Proxy
if check_port $MCP_PROXY_PORT; then
    echo -e "${BLUE}Starting MCP Proxy on $MCP_PROXY_HOST:$MCP_PROXY_PORT...${NC}"
    nohup python3 mcp_proxy.py > logs/mcp_proxy.log 2>&1 &
    PROXY_PID=$!
    echo $PROXY_PID > logs/mcp_proxy.pid
    echo -e "${GREEN}✓ MCP Proxy started (PID: $PROXY_PID)${NC}"
    echo -e "  Log: logs/mcp_proxy.log"
    echo -e "  URL: http://$MCP_PROXY_HOST:$MCP_PROXY_PORT/mcp"
else
    echo -e "${YELLOW}⚠️  Skipping MCP Proxy (port $MCP_PROXY_PORT in use)${NC}"
    PROXY_PID=""
fi

sleep 2

# Start Telegram Bot if configured
TELEGRAM_PID=""
if [ "${TELEGRAM_ENABLED:-false}" = "true" ] && [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
    echo -e "${BLUE}Starting Telegram Bot...${NC}"
    nohup python3 telegram_bot.py > logs/telegram_bot.log 2>&1 &
    TELEGRAM_PID=$!
    echo $TELEGRAM_PID > logs/telegram_bot.pid
    echo -e "${GREEN}✓ Telegram Bot started (PID: $TELEGRAM_PID)${NC}"
    echo -e "  Log: logs/telegram_bot.log"
    echo -e "  Commands: /status, /help"
else
    echo -e "${YELLOW}⚠️  Telegram Bot not configured (skipping)${NC}"
fi

sleep 2

# Start Dashboard
DASHBOARD_HOST=${DASHBOARD_HOST:-0.0.0.0}
DASHBOARD_PORT=${DASHBOARD_PORT:-5000}

if check_port $DASHBOARD_PORT; then
    echo -e "${BLUE}Starting Dashboard on $DASHBOARD_HOST:$DASHBOARD_PORT...${NC}"
    nohup python3 dashboard.py > logs/dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    echo $DASHBOARD_PID > logs/dashboard.pid
    echo -e "${GREEN}✓ Dashboard started (PID: $DASHBOARD_PID)${NC}"
    echo -e "  Log: logs/dashboard.log"
    echo -e "  URL: http://$DASHBOARD_HOST:$DASHBOARD_PORT"
    echo -e "  Default credentials: admin / admin123"
else
    echo -e "${YELLOW}⚠️  Skipping Dashboard (port $DASHBOARD_PORT in use)${NC}"
    DASHBOARD_PID=""
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  System Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Wait a bit for services to start
sleep 3

# Check if services are running
echo -e "${GREEN}Active Services:${NC}"
[ -n "$MCP_PID" ] && ps -p $MCP_PID > /dev/null 2>&1 && echo -e "  ✓ MCP Server    (PID: $MCP_PID) - http://$MCP_HOST:$MCP_PORT/mcp"
[ -n "$CHAT_PID" ] && ps -p $CHAT_PID > /dev/null 2>&1 && echo -e "  ✓ Chat API      (PID: $CHAT_PID) - http://$CHAT_API_HOST:$CHAT_API_PORT"
[ -n "$PROXY_PID" ] && ps -p $PROXY_PID > /dev/null 2>&1 && echo -e "  ✓ MCP Proxy     (PID: $PROXY_PID) - http://$MCP_PROXY_HOST:$MCP_PROXY_PORT/mcp"
[ -n "$TELEGRAM_PID" ] && ps -p $TELEGRAM_PID > /dev/null 2>&1 && echo -e "  ✓ Telegram Bot  (PID: $TELEGRAM_PID) - Commands: /status, /help"
[ -n "$DASHBOARD_PID" ] && ps -p $DASHBOARD_PID > /dev/null 2>&1 && echo -e "  ✓ Dashboard     (PID: $DASHBOARD_PID) - http://$DASHBOARD_HOST:$DASHBOARD_PORT"

echo ""
echo -e "${BLUE}Management Commands:${NC}"
echo -e "  Stop all:    ./stop_ecosystem.sh"
echo -e "  View logs:   tail -f logs/mcp_server.log"
echo -e "  Check status: ps aux | grep python3"
echo ""

# Test MCP server
echo -e "${BLUE}Testing MCP Server...${NC}"
sleep 2
if curl -s -X POST http://$MCP_HOST:$MCP_PORT/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"ping","arguments":{}}}' \
  | grep -q "pong" 2>/dev/null; then
    echo -e "${GREEN}✓ MCP Server is responding${NC}"
else
    echo -e "${YELLOW}⚠️  MCP Server might still be starting up${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ZAS Ecosystem Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop monitoring (services will continue running)${NC}"
echo ""

# Tail logs (can be interrupted with Ctrl+C)
tail -f logs/*.log 2>/dev/null || true
