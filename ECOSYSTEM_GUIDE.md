# ZAS Ecosystem Management

Quick reference for managing the ZAS system.

## 🚀 Quick Start

```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Add your credentials

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start everything
./start_ecosystem.sh
```

## 🎮 Management Commands

### Start All Services
```bash
./start_ecosystem.sh
```
Starts:
- MCP Server (port 8000)
- Chat API (port 3000)
- MCP Proxy (port 8080)

### Stop All Services
```bash
./stop_ecosystem.sh
```

### Check Status
```bash
./status_ecosystem.sh
```

### View Logs
```bash
# All logs
tail -f logs/*.log

# Specific service
tail -f logs/mcp_server.log
tail -f logs/chat_api.log
tail -f logs/mcp_proxy.log
```

## 🔍 Testing Endpoints

### Test MCP Server
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/call",
    "params": {
      "name": "ping",
      "arguments": {}
    }
  }'
```

### Test Chat API
```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "ping",
    "conversationId": "test-123"
  }'
```

### Test Health
```bash
curl http://localhost:3000/health
```

## 📊 Service URLs

- **MCP Server**: http://127.0.0.1:8000/mcp
- **Chat API**: http://0.0.0.0:3000
- **MCP Proxy**: http://0.0.0.0:8080/mcp
- **Health Check**: http://localhost:3000/health

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process on port
lsof -ti:8000
lsof -ti:3000
lsof -ti:8080

# Kill process
kill $(lsof -ti:8000)
```

### Check Running Services
```bash
ps aux | grep python3
```

### Force Stop Everything
```bash
pkill -f "python3 app.py"
pkill -f "python3 chat_api.py"
pkill -f "python3 mcp_proxy.py"
```

### Clear Logs
```bash
rm -rf logs/*.log
rm -rf logs/*.pid
```

## 📁 File Structure

```
.
├── start_ecosystem.sh      # Start all services
├── stop_ecosystem.sh       # Stop all services
├── status_ecosystem.sh     # Check service status
├── app.py                  # MCP server
├── chat_api.py             # Chat API
├── mcp_proxy.py            # MCP proxy
├── logs/                   # Service logs
│   ├── mcp_server.log
│   ├── chat_api.log
│   └── mcp_proxy.log
└── .env                    # Configuration (create from .env.example)
```

## 🔒 Environment Variables

Required in `.env`:
- `ZENDESK_SUBDOMAIN`
- `ZENDESK_EMAIL`
- `ZENDESK_API_TOKEN`

Optional:
- `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
- `CONFLUENCE_BASE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN`
- `MCP_HOST`, `MCP_PORT`
- `ZAS_MCP_SERVER_URL`

## 💡 Tips

1. **Always check status** before starting to avoid port conflicts
2. **View logs** if services aren't responding
3. **Use .env.example** as a template for configuration
4. **Backup logs** before clearing if you need to debug issues
5. **Run from project root** to ensure correct paths

## 🆘 Getting Help

- Check logs: `./status_ecosystem.sh`
- Verify config: `python3 -c "from src.zas.core import Config; Config.from_env()"`
- Run verification: `python3 verify_new_architecture.py`
- See full docs: [README.md](README.md)
