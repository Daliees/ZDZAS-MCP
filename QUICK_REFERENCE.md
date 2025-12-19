# ZAS OOP Quick Reference

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements_new.txt

# 2. Configure .env
cp env-dot .env
# Edit .env with your credentials

# 3. Run MCP server
python3 app_new.py

# 4. Run Chat API (in another terminal)
python3 chat_api_new.py
```

## 📦 Import Cheat Sheet

```python
# Core
from src.zas.core import Config, get_config
from src.zas.core import ZASException, APIException, ConfigurationException
from src.zas.core import BaseAPIClient

# Services
from src.zas.services import ZendeskService, JiraService, ConfluenceService

# Tools
from src.zas.tools import (
    TicketTools, KnowledgeBaseTools, ReportingTools,
    JiraTools, ConfluenceTools, GeneralTools
)
from src.zas.tools.registry import MCPToolRegistry

# Agents
from src.zas.agents import MCPClient, ZASAgent
from src.zas.agents.mcp_client import get_mcp_client

# API
from src.zas.api import ChatAPI, MCPProxy
```

## 🔧 Common Code Patterns

### Initialize Configuration
```python
from src.zas.core import Config

# From environment
config = Config.from_env()

# Or get global instance
from src.zas.core import get_config
config = get_config()
```

### Use Zendesk Service
```python
from src.zas.core import get_config
from src.zas.services import ZendeskService

config = get_config()
zendesk = ZendeskService(config)

# Search tickets
tickets = zendesk.search_tickets("type:ticket status:open", limit=10)

# Get ticket
ticket = zendesk.get_ticket(12345)

# Add note
zendesk.add_internal_note(12345, "Internal note")

# Search articles
articles = zendesk.search_articles("password reset", limit=5)
```

### Use Ticket Tools
```python
from src.zas.tools import TicketTools
from src.zas.services import ZendeskService
from src.zas.core import get_config

config = get_config()
zendesk = ZendeskService(config)
tools = TicketTools(zendesk)

# Search
result = tools.search("status:open", limit=10)
print(result["count"])

# Get details
result = tools.get(12345)
print(result["ticket"]["subject"])

# Add note
result = tools.add_internal_note(12345, "Note text")
```

### Use Agent
```python
from src.zas.agents import ZASAgent
from src.zas.agents.mcp_client import get_mcp_client

# Create agent
mcp_client = get_mcp_client()
agent = ZASAgent(mcp_client)

# Single turn
response = agent.run("Zoek alle open tickets")
print(response)

# With history
history = []
response = agent.run("Hoe kan ik mijn wachtwoord resetten?", history)
print(response)
```

### Create MCP Server
```python
from app_new import create_mcp_server
from src.zas.core import get_config

config = get_config()
mcp = create_mcp_server(config)

# Run server
mcp.run(
    transport="http",
    host="127.0.0.1",
    port=8000,
    path="/mcp",
    stateless_http=True,
)
```

### Create Chat API
```python
from chat_api_new import create_chat_api
import uvicorn

chat_api = create_chat_api()
uvicorn.run(chat_api.app, host="0.0.0.0", port=3000)
```

## 🛠️ Common Tasks

### Add a New Tool

1. **Create the tool class:**
```python
# src/zas/tools/my_tools.py
class MyTools:
    def __init__(self, zendesk: ZendeskService):
        self.zendesk = zendesk
    
    def my_action(self, param: str) -> Dict[str, Any]:
        """Tool description for LLM."""
        try:
            # Use service
            result = self.zendesk.some_method(param)
            return {"ok": True, "result": result}
        except Exception as e:
            return {"error": str(e)}
```

2. **Register the tool:**
```python
# src/zas/tools/registry.py
class MCPToolRegistry:
    def __init__(self, config, mcp):
        # ...
        self.my_tools = MyTools(self.zendesk)
    
    def register_all(self):
        # ...
        self._register_tool("my_action", self.my_tools.my_action)
```

3. **Add to agent:**
```python
# src/zas/agents/zas_agent.py
class ZASAgent:
    def _create_tools(self):
        @function_tool
        def my_action(param: str) -> Any:
            return self.mcp_client.call_tool("my_action", {"param": param})
        
        tools = [..., my_action]
        return tools
```

### Add a New Service

1. **Create service class:**
```python
# src/zas/services/new_service.py
from ..core import BaseAPIClient, Config

class NewService(BaseAPIClient):
    def __init__(self, config: Config):
        # Get config from config.new_service
        super().__init__(
            base_url=config.new_service.base_url,
            auth=config.new_service.auth,
            timeout=config.api_timeout,
            rate_limit_delay=config.rate_limit_delay,
        )
    
    def some_method(self, param: str) -> Dict:
        return self.get(f"/endpoint/{param}")
```

2. **Add config:**
```python
# src/zas/core/config.py
@dataclass
class NewServiceConfig:
    base_url: str
    api_key: str
    
    @property
    def auth(self) -> tuple[str, str]:
        return ("", self.api_key)

@dataclass
class Config:
    # ...
    new_service: Optional[NewServiceConfig] = None
```

### Error Handling

```python
from src.zas.core.exceptions import (
    ZASException,
    ConfigurationException,
    APIException,
    ValidationException,
)

try:
    config = Config.from_env()
except ConfigurationException as e:
    print(f"Config error: {e}")

try:
    zendesk = ZendeskService(config)
    ticket = zendesk.get_ticket(12345)
except APIException as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")

try:
    zendesk.add_internal_note(12345, "")
except ValidationException as e:
    print(f"Validation error: {e}")
```

## 📝 Environment Variables

```bash
# Required
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=your-email@example.com
ZENDESK_API_TOKEN=your-api-token

# Optional - Jira
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# Optional - Confluence
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token

# MCP Server
MCP_HOST=127.0.0.1
MCP_PORT=8000
ZAS_MCP_SERVER_URL=http://127.0.0.1:8000/mcp

# Logging
ZAS_FEEDBACK_LOG=zas_feedback_log.jsonl
```

## 🔌 API Endpoints

### Chat API (Port 3000)

**Chat:**
```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Zoek open tickets", "conversationId": "optional-id"}'
```

**Feedback:**
```bash
curl -X POST http://localhost:3000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "conversationId": "abc-123",
    "agentReply": "Ik heb 5 tickets gevonden",
    "rating": "good",
    "createdAt": "2025-12-19T10:00:00Z"
  }'
```

**Reset:**
```bash
curl -X POST http://localhost:3000/reset \
  -H "Content-Type: application/json" \
  -d '{"conversationId": "abc-123"}'
```

**Health:**
```bash
curl http://localhost:3000/health
```

### MCP Server (Port 8000)

**Call Tool:**
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

## 🧪 Testing Commands

```bash
# Run verification
python3 verify_new_architecture.py

# Test imports
python3 -c "from src.zas.core import Config; print('✓ Imports work')"

# Test config
python3 -c "from src.zas.core import Config; c = Config.from_env(); print(c.zendesk.subdomain)"

# Test service
python3 -c "from src.zas.core import get_config; from src.zas.services import ZendeskService; z = ZendeskService(get_config()); print(z.base_url)"

# Test MCP server creation
python3 -c "from app_new import create_mcp_server; mcp = create_mcp_server(); print(mcp.name)"
```

## 📊 File Locations

```
Main entry points:
  app_new.py              - MCP server
  chat_api_new.py         - Chat API
  mcp_proxy_new.py        - MCP proxy
  server_wrapper_new.py   - Unified wrapper

Core:
  src/zas/core/config.py      - Configuration
  src/zas/core/exceptions.py  - Exceptions
  src/zas/core/base_client.py - Base client

Services:
  src/zas/services/zendesk_service.py
  src/zas/services/jira_service.py
  src/zas/services/confluence_service.py

Tools:
  src/zas/tools/ticket_tools.py
  src/zas/tools/kb_tools.py
  src/zas/tools/jira_tools.py
  src/zas/tools/confluence_tools.py
  src/zas/tools/reporting_tools.py
  src/zas/tools/general_tools.py
  src/zas/tools/registry.py

Agents:
  src/zas/agents/mcp_client.py
  src/zas/agents/zas_agent.py

API:
  src/zas/api/chat_api.py
  src/zas/api/mcp_proxy.py

Docs:
  README_NEW.md           - Main documentation
  ARCHITECTURE.md         - Architecture details
  MIGRATION_GUIDE.md      - Migration steps
  REFACTORING_SUMMARY.md  - Complete summary
  QUICK_REFERENCE.md      - This file
```

## 🐛 Troubleshooting

**Import Error:**
```bash
# Add to PYTHONPATH
export PYTHONPATH=/home/ryan/code/ZDZAS-MCP:$PYTHONPATH
```

**Config Error:**
```bash
# Check .env exists and is loaded
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('ZENDESK_SUBDOMAIN'))"
```

**Module Not Found:**
```bash
# Install dependencies
pip install -r requirements_new.txt
```

**Port Already in Use:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
```

## 📚 Further Reading

- [README_NEW.md](README_NEW.md) - Complete guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture details
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Migration guide
- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - Summary

## 💡 Tips

1. **Always use `get_config()`** instead of creating Config directly
2. **Services are stateless** - create once, reuse
3. **Tools wrap services** - always use dependency injection
4. **Type hints are your friend** - IDE will help you
5. **Check exceptions** - use custom exception types
6. **Test each layer** - core → services → tools → agents
7. **Read the docstrings** - all methods are documented

## ✅ Quick Checklist

- [ ] Dependencies installed (`pip install -r requirements_new.txt`)
- [ ] `.env` configured with required variables
- [ ] Verification passed (`python3 verify_new_architecture.py`)
- [ ] MCP server runs (`python3 app_new.py`)
- [ ] Chat API runs (`python3 chat_api_new.py`)
- [ ] Can import all modules
- [ ] Services connect to APIs
- [ ] Tools work correctly
- [ ] Agent responds to queries

---

**Need help?** Check the full documentation in README_NEW.md or MIGRATION_GUIDE.md
