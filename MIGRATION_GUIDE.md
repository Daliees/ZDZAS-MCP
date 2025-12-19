# ZAS Migration Guide: Functional to OOP

## Overview

This guide explains the migration from the functional architecture to the new OOP architecture.

## Architecture Changes

### Before (Functional)
```
├── app.py              # Loads all tool modules, starts MCP
├── core.py             # Global helpers and config
├── tools_ticket.py     # Ticket functions
├── tools_kb.py         # KB functions
├── tools_jira.py       # Jira functions
├── tools_confluence.py # Confluence functions
├── tools_reporting.py  # Reporting functions
├── tools_general.py    # General functions
├── chat_api.py         # Chat API with inline logic
├── mcp_proxy.py        # MCP proxy
└── zas_agent.py        # Agent with inline MCP calls
```

### After (OOP)
```
src/zas/
├── core/                    # Infrastructure layer
│   ├── config.py           # Config classes with validation
│   ├── exceptions.py       # Custom exception hierarchy
│   └── base_client.py      # Abstract API client
├── services/               # Business logic layer
│   ├── zendesk_service.py  # ZendeskService class
│   ├── jira_service.py     # JiraService class
│   └── confluence_service.py # ConfluenceService class
├── tools/                  # MCP integration layer
│   ├── ticket_tools.py     # TicketTools class
│   ├── kb_tools.py         # KnowledgeBaseTools class
│   ├── jira_tools.py       # JiraTools class
│   ├── confluence_tools.py # ConfluenceTools class
│   ├── reporting_tools.py  # ReportingTools class
│   ├── general_tools.py    # GeneralTools class
│   └── registry.py         # MCPToolRegistry
├── agents/                 # Agent layer
│   ├── mcp_client.py       # MCPClient class
│   └── zas_agent.py        # ZASAgent class
└── api/                    # API layer
    ├── chat_api.py         # ChatAPI class
    └── mcp_proxy.py        # MCPProxy class

# Entry points
├── app_new.py              # MCP server entry point
├── chat_api_new.py         # Chat API entry point
├── mcp_proxy_new.py        # Proxy entry point
└── server_wrapper_new.py   # Unified entry point
```

## Key Improvements

### 1. Configuration Management

**Before:**
```python
# core.py
ZD_SUB = os.getenv("ZENDESK_SUBDOMAIN")
ZD_EMAIL = os.getenv("ZENDESK_EMAIL")
ZD_TOKEN = os.getenv("ZENDESK_API_TOKEN")
AUTH = (f"{ZD_EMAIL}/token", ZD_TOKEN)
BASE = f"https://{ZD_SUB}.zendesk.com/api/v2"
```

**After:**
```python
# src/zas/core/config.py
from src.zas.core import Config

config = Config.from_env()
print(config.zendesk.base_url)  # https://subdomain.zendesk.com/api/v2
print(config.zendesk.auth)       # ('email/token', 'token')
```

### 2. API Clients

**Before:**
```python
# core.py
def _get(url_path, params=None, timeout=20):
    url = f"{BASE}{url_path}"
    r = requests.get(url, params=params, auth=AUTH, timeout=timeout)
    r.raise_for_status()
    return r.json()
```

**After:**
```python
# src/zas/services/zendesk_service.py
class ZendeskService(BaseAPIClient):
    def get_ticket(self, ticket_id: int) -> Dict[str, Any]:
        data = self.get(f"/tickets/{ticket_id}.json")
        return data.get("ticket", {})
```

### 3. Tool Organization

**Before:**
```python
# tools_ticket.py
from core import mcp, _get, _put

@mcp.tool
def ticket_get(ticket_id: int):
    data = _get(f"/tickets/{ticket_id}.json")
    return {"ok": True, "ticket": data.get("ticket")}
```

**After:**
```python
# src/zas/tools/ticket_tools.py
class TicketTools:
    def __init__(self, zendesk: ZendeskService):
        self.zendesk = zendesk
    
    def get(self, ticket_id: int) -> Dict[str, Any]:
        try:
            ticket = self.zendesk.get_ticket(ticket_id)
            return {"ok": True, "ticket": ticket}
        except Exception as e:
            return {"error": str(e)}

# src/zas/tools/registry.py
class MCPToolRegistry:
    def __init__(self, config: Config, mcp: FastMCP):
        self.zendesk = ZendeskService(config)
        self.ticket_tools = TicketTools(self.zendesk)
    
    def register_all(self):
        self.mcp.tool(self.ticket_tools.get)
```

### 4. Agent Architecture

**Before:**
```python
# zas_agent.py
def _mcp_call(tool_name: str, arguments: Dict) -> Any:
    # Direct HTTP call
    resp = requests.post(MCP_SERVER_URL, json=payload)
    return _parse_mcp_response(tool_name, resp)

@function_tool
def ticket_get(ticket_id: int) -> Any:
    return _mcp_call("ticket_get", {"ticket_id": ticket_id})
```

**After:**
```python
# src/zas/agents/mcp_client.py
class MCPClient:
    def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        # Encapsulated HTTP logic with proper error handling
        ...

# src/zas/agents/zas_agent.py
class ZASAgent:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.tools = self._create_tools()
        self.agent = Agent(tools=self.tools, ...)
    
    def run(self, message: str, history: List) -> str:
        # Managed conversation flow
        ...
```

## Migration Steps

### 1. Install Dependencies
```bash
pip install -r requirements_new.txt
```

### 2. Test Imports
```bash
python3 -c "from src.zas.core import Config; print('OK')"
```

### 3. Configure Environment
Ensure your `.env` file has all required variables:
```bash
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=your-email
ZENDESK_API_TOKEN=your-token
```

### 4. Run Verification
```bash
python3 verify_new_architecture.py
```

### 5. Start Services

**MCP Server:**
```bash
python3 app_new.py
```

**Chat API:**
```bash
python3 chat_api_new.py
```

**MCP Proxy:**
```bash
python3 mcp_proxy_new.py
```

### 6. Test Endpoints

**Test MCP:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"ping","arguments":{}}}'
```

**Test Chat API:**
```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"ping"}'
```

### 7. Switch Over

Once everything works:
```bash
# Backup old files
mkdir -p backup_old
mv app.py core.py chat_api.py backup_old/

# Activate new files
mv app_new.py app.py
mv chat_api_new.py chat_api.py
mv mcp_proxy_new.py mcp_proxy.py
mv server_wrapper_new.py server_wrapper.py
```

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Architecture** | Functional, procedural | OOP, layered |
| **Testability** | Hard to mock | Easy with DI |
| **Configuration** | Global variables | Config classes |
| **Error Handling** | Generic exceptions | Custom hierarchy |
| **Type Safety** | Minimal | Full type hints |
| **Reusability** | Tool-specific | Service layer |
| **Extensibility** | Add functions | Add classes |
| **Separation** | Mixed concerns | Clear layers |

## Code Comparison Examples

### Example 1: Searching Tickets

**Before:**
```python
# tools_ticket.py
@mcp.tool
def tickets_search(query: str, limit: int = 50):
    raw = _paginate_search(query=query, limit=limit)
    items = []
    for hit in raw:
        items.append({
            "id": hit.get("id"),
            "subject": hit.get("subject"),
            # ... more fields
        })
    return {"count": len(items), "tickets": items}
```

**After:**
```python
# Service layer
class ZendeskService:
    def search_tickets(self, query: str, limit: int) -> List[Dict]:
        return self._paginate_search(query, limit)

# Tool layer
class TicketTools:
    def search(self, query: str, limit: int = 50) -> Dict:
        raw = self.zendesk.search_tickets(query, limit)
        items = [self._format_ticket(t) for t in raw]
        return {"count": len(items), "tickets": items}
```

### Example 2: Adding Internal Notes

**Before:**
```python
# tools_ticket.py
@mcp.tool
def ticket_add_internal_note(ticket_id: int, body: str):
    payload = {
        "ticket": {
            "comment": {"body": body, "public": False}
        }
    }
    data = _put(f"/tickets/{ticket_id}.json", payload)
    return {"ok": True, "ticket": data.get("ticket")}
```

**After:**
```python
# Service layer
class ZendeskService:
    def add_internal_note(self, ticket_id: int, body: str) -> Dict:
        if not body.strip():
            raise ValidationException("Body cannot be empty")
        payload = {"ticket": {"comment": {"body": body, "public": False}}}
        return self.put(f"/tickets/{ticket_id}.json", json=payload)

# Tool layer
class TicketTools:
    def add_internal_note(self, ticket_id: int, body: str) -> Dict:
        try:
            ticket = self.zendesk.add_internal_note(ticket_id, body)
            return {"ok": True, "ticket": ticket}
        except ValidationException as e:
            return {"ok": False, "error": str(e)}
```

## Testing

### Unit Test Example

```python
# test_ticket_tools.py
from unittest.mock import Mock
from src.zas.tools import TicketTools

def test_ticket_get():
    # Mock service
    mock_zendesk = Mock()
    mock_zendesk.get_ticket.return_value = {"id": 123, "subject": "Test"}
    
    # Create tools
    tools = TicketTools(mock_zendesk)
    
    # Test
    result = tools.get(123)
    
    # Assert
    assert result["ok"] is True
    assert result["ticket"]["id"] == 123
    mock_zendesk.get_ticket.assert_called_once_with(123)
```

## Troubleshooting

### Import Errors

If you get import errors:
```bash
# Ensure src/zas/ has __init__.py files
find src/zas -type d -exec touch {}/__init__.py \;

# Or add to PYTHONPATH
export PYTHONPATH=/home/ryan/code/ZDZAS-MCP:$PYTHONPATH
```

### Configuration Errors

If configuration fails:
```bash
# Check .env file exists
ls -la .env

# Test config loading
python3 -c "from src.zas.core import Config; c = Config.from_env(); print(c.zendesk.subdomain)"
```

### Service Connection Errors

Test services individually:
```python
from src.zas.core import Config
from src.zas.services import ZendeskService

config = Config.from_env()
zendesk = ZendeskService(config)
print(zendesk.base_url)  # Should print your Zendesk URL
```

## Rollback Plan

If you need to rollback:
```bash
# Restore old files
cp backup_old/*.py .

# Or use git
git checkout HEAD -- app.py core.py chat_api.py tools_*.py
```

## Support

For issues or questions:
1. Check verify_new_architecture.py output
2. Review logs in terminal
3. Test each layer independently (core → services → tools → agents)
