# ZAS Architecture Overview

## System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        Client Layer                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐        │
│  │   VS Code   │  │ Web Frontend │  │  OpenAI GPT     │        │
│  │  Extension  │  │   (React)    │  │  w/ MCP Tools   │        │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘        │
└─────────┼────────────────┼───────────────────┼─────────────────┘
          │                │                   │
          │ HTTP           │ HTTP              │ HTTP
          │                │                   │
┌─────────▼────────────────▼───────────────────▼─────────────────┐
│                        API Layer                               │
│  ┌──────────────────┐            ┌──────────────────┐          │
│  │    Chat API      │            │    MCP Proxy     │          │
│  │  (Port 3000)     │            │   (Port 8080)    │          │
│  │                  │            │                  │          │
│  │  - /chat         │            │  - /mcp          │          │
│  │  - /feedback     │            │                  │          │
│  │  - /reset        │            │  Proxies to →    │          │
│  └────────┬─────────┘            └────────┬─────────┘          │
└───────────┼───────────────────────────────┼────────────────────┘
            │                               │
            │ Uses Agent                    │
            │                               │
┌───────────▼───────────────────────────────▼─────────────────────┐
│                      Agent Layer                                │
│  ┌───────────────────────────────────────────────────────┐      │
│  │                    ZASAgent                           │      │
│  │  ┌─────────────────────────────────────────────────┐  │      │
│  │  │  Claude 3.5 Sonnet (Anthropic Agents SDK)       │  │      │
│  │  └─────────────────────────────────────────────────┘  │      │
│  │                                                       │      │
│  │  Tools: tickets_search, ticket_get, kb_search, ...    │      │
│  └───────────────────────┬───────────────────────────────┘      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           │ MCP HTTP Client
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    MCP Server Layer                             │
│  ┌──────────────────────────────────────────────────────┐       │
│  │         FastMCP Server (Port 8000)                   │       │
│  │                                                      │       │
│  │  ┌──────────────────────────────────────────────┐    │       │
│  │  │         MCPToolRegistry                      │    │       │
│  │  │  - Initializes all services                  │    │       │
│  │  │  - Registers all tools with MCP              │    │       │
│  │  └─────────────────┬────────────────────────────┘    │       │
│  └────────────────────┼─────────────────────────────────┘       │
└───────────────────────┼─────────────────────────────────────────┘
                        │
                        │ Dependency Injection
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                     Tool Layer                                  │
│  ┌──────────────┐ ┌────────────┐ ┌──────────────┐               │
│  │ TicketTools  │ │  KBTools   │ │  JiraTools   │  ...          │
│  │              │ │            │ │              │               │
│  │ - search()   │ │ - search() │ │ - get_issue()│               │
│  │ - get()      │ │ - create() │ └──────┬───────┘               │
│  │ - comment()  │ └─────┬──────┘        │                       │
│  └──────┬───────┘       │               │                       │
└─────────┼───────────────┼───────────────┼───────────────────────┘
          │               │               │
          │ Uses Service  │               │
          │               │               │
┌─────────▼───────────────▼───────────────▼─────────────────────┐
│                    Service Layer                              │
│  ┌─────────────────┐ ┌──────────────────┐ ┌──────────────┐    │
│  │ ZendeskService  │ │  JiraService     │ │ Confluence   │    │
│  │ (Required)      │ │  (Optional)      │ │   Service    │    │
│  │                 │ │                  │ │  (Optional)  │    │
│  │ - get_ticket()  │ │ - get_issue()    │ │ - search()   │    │
│  │ - search()      │ │                  │ │ - get_page() │    │
│  │ - update()      │ │                  │ │              │    │
│  └────────┬────────┘ └────────┬─────────┘ └──────┬───────┘    │
└───────────┼───────────────────┼──────────────────┼────────────┘
            │                   │                  │
            │ Extends           │                  │
            │                   │                  │
┌───────────▼───────────────────▼──────────────────▼──────────┐
│                      Core Layer                             │
│  ┌─────────────────────────────────────────────────┐        │
│  │             BaseAPIClient                       │        │
│  │  - HTTP methods (get, post, put, delete)        │        │
│  │  - Rate limiting                                │        │
│  │  - Error handling                               │        │
│  │  - Authentication                               │        │
│  └─────────────────────────────────────────────────┘        │
│                                                             │
│  ┌─────────────────────────────────────────────────┐        │
│  │                   Config                        │        │
│  │  - ZendeskConfig (required)                     │        │
│  │  - JiraConfig (optional)                        │        │
│  │  - ConfluenceConfig (optional)                  │        │
│  │  - Loads from environment                       │        │
│  └─────────────────────────────────────────────────┘        │
│                                                             │
│  ┌─────────────────────────────────────────────────┐        │
│  │             Custom Exceptions                   │        │
│  │  - ZASException (base)                          │        │
│  │  - ConfigurationException                       │        │
│  │  - APIException                                 │        │
│  │  - ValidationException                          │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Makes API calls to
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                    External APIs                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Zendesk    │  │     Jira     │  │  Confluence  │          │
│  │     API      │  │     API      │  │     API      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────────────────────────────────────────┘
```

## Data Flow Example: "Search for tickets"

```
1. User → Chat API
   POST /chat {"message": "Zoek tickets van deze week"}

2. Chat API → ZASAgent
   agent.run("Zoek tickets van deze week", history)

3. ZASAgent (LLM) → Decides to use tool
   tickets_search(query="type:ticket created>2024-12-12", limit=50)

4. ZASAgent → MCPClient
   mcp_client.call_tool("tickets_search", {...})

5. MCPClient → FastMCP Server (HTTP)
   POST http://localhost:8000/mcp
   {"method": "tools/call", "params": {"name": "tickets_search", ...}}

6. FastMCP → MCPToolRegistry → TicketTools
   ticket_tools.search(query=..., limit=...)

7. TicketTools → ZendeskService
   zendesk.search_tickets(query=..., limit=...)

8. ZendeskService → BaseAPIClient
   self.get("/search.json", params={...})

9. BaseAPIClient → Zendesk API
   GET https://subdomain.zendesk.com/api/v2/search.json

10. Response flows back up:
    Zendesk → BaseAPIClient → ZendeskService → TicketTools 
    → FastMCP → MCPClient → ZASAgent

11. ZASAgent (LLM) → Formats response
    "Ik heb 15 tickets gevonden van deze week: ..."

12. Response → Chat API → User
    {"reply": "Ik heb 15 tickets gevonden...", "conversationId": "..."}
```

## Design Patterns Used

### 1. **Layered Architecture**
- Core → Services → Tools → Agents → API
- Each layer only depends on layers below it
- Clear separation of concerns

### 2. **Dependency Injection**
```python
# Services injected into tools
class TicketTools:
    def __init__(self, zendesk: ZendeskService):
        self.zendesk = zendesk

# MCP client injected into agent
class ZASAgent:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
```

### 3. **Template Method Pattern**
```python
class BaseAPIClient:
    def _make_request(self, method, path, ...):
        self._rate_limit()
        # Common logic
        ...
    
    def get(self, path, params):
        return self._make_request("GET", path, params=params)
```

### 4. **Factory Pattern**
```python
def create_mcp_server(config: Config) -> FastMCP:
    mcp = FastMCP(name="zendesk_mcp_http")
    registry = MCPToolRegistry(config, mcp)
    registry.register_all()
    return mcp
```

### 5. **Singleton Pattern**
```python
_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
```

### 6. **Strategy Pattern**
```python
# Different auth strategies per service
class ZendeskConfig:
    @property
    def auth(self) -> tuple[str, str]:
        return (f"{self.email}/token", self.api_token)

class JiraConfig:
    @property
    def auth(self) -> tuple[str, str]:
        return (self.email, self.api_token)
```

## Directory Structure

```
/home/ryan/code/ZDZAS-MCP/
├── src/zas/                      # Main package
│   ├── __init__.py
│   ├── core/                     # Core infrastructure
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration classes
│   │   ├── exceptions.py        # Custom exceptions
│   │   └── base_client.py       # Base API client
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   ├── zendesk_service.py   # Zendesk API wrapper
│   │   ├── jira_service.py      # Jira API wrapper
│   │   └── confluence_service.py # Confluence API wrapper
│   ├── tools/                   # MCP tools
│   │   ├── __init__.py
│   │   ├── ticket_tools.py      # Ticket operations
│   │   ├── kb_tools.py          # Knowledge base
│   │   ├── jira_tools.py        # Jira operations
│   │   ├── confluence_tools.py  # Confluence operations
│   │   ├── reporting_tools.py   # Reporting & export
│   │   ├── general_tools.py     # Utilities
│   │   └── registry.py          # Tool registration
│   ├── agents/                  # Agent layer
│   │   ├── __init__.py
│   │   ├── mcp_client.py        # MCP HTTP client
│   │   └── zas_agent.py         # Main agent
│   └── api/                     # API endpoints
│       ├── __init__.py
│       ├── chat_api.py          # Chat API
│       └── mcp_proxy.py         # MCP proxy
├── app_new.py                   # MCP server entry point
├── chat_api_new.py              # Chat API entry point
├── mcp_proxy_new.py             # Proxy entry point
├── server_wrapper_new.py        # Unified entry point
├── verify_new_architecture.py   # Verification script
├── migrate_to_oop.sh            # Migration script
├── requirements_new.txt         # Dependencies
├── README_NEW.md                # New documentation
└── MIGRATION_GUIDE.md           # This guide
```

## Component Responsibilities

### Core Layer
- **Config**: Load and validate configuration from environment
- **BaseAPIClient**: Handle HTTP requests, rate limiting, auth
- **Exceptions**: Define custom error types

### Service Layer
- **ZendeskService**: Zendesk API operations (tickets, KB, users, orgs)
- **JiraService**: Jira API operations (issues, comments)
- **ConfluenceService**: Confluence API operations (pages, search)

### Tool Layer
- **TicketTools**: MCP tools for ticket operations
- **KnowledgeBaseTools**: MCP tools for KB operations
- **JiraTools**: MCP tools for Jira operations
- **ConfluenceTools**: MCP tools for Confluence operations
- **ReportingTools**: MCP tools for reporting/export
- **GeneralTools**: Utility tools (ping, etc.)
- **MCPToolRegistry**: Register all tools with FastMCP

### Agent Layer
- **MCPClient**: HTTP client for calling MCP tools
- **ZASAgent**: Conversational agent with Claude + MCP tools

### API Layer
- **ChatAPI**: FastAPI app for chat interactions
- **MCPProxy**: Proxy for OpenAI integration

## Key Classes

### BaseAPIClient
```python
class BaseAPIClient(ABC):
    def __init__(self, base_url, auth, timeout, rate_limit_delay)
    def get(path, params) -> Dict
    def post(path, json) -> Dict
    def put(path, json) -> Dict
    def delete(path) -> Dict
    def _make_request(method, path, ...) -> Dict
    def _rate_limit() -> None
```

### ZendeskService
```python
class ZendeskService(BaseAPIClient):
    # Ticket operations
    def get_ticket(ticket_id) -> Dict
    def search_tickets(query, limit) -> List[Dict]
    def update_ticket(ticket_id, update_data) -> Dict
    def add_internal_note(ticket_id, body) -> Dict
    def get_ticket_comments(ticket_id, public_only) -> List[Dict]
    
    # User operations
    def get_user(user_id) -> Dict
    def search_users(query) -> List[Dict]
    
    # Organization operations
    def get_organization(org_id) -> Dict
    
    # Knowledge base operations
    def search_articles(query, ...) -> List[Dict]
    def get_article(article_id) -> Dict
    def create_article(section_id, title, body, ...) -> Dict
```

### MCPToolRegistry
```python
class MCPToolRegistry:
    def __init__(config: Config, mcp: FastMCP)
    def register_all() -> None
    def _register_tool(name: str, func: Callable) -> None
```

### ZASAgent
```python
class ZASAgent:
    def __init__(mcp_client: MCPClient, model: str)
    def run(message: str, history: List) -> str
    def _get_instructions() -> str
    def _create_tools() -> List
```

## Configuration

### Environment Variables

**Required:**
- `ZENDESK_SUBDOMAIN`
- `ZENDESK_EMAIL`
- `ZENDESK_API_TOKEN`

**Optional:**
- `JIRA_BASE_URL`
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`
- `CONFLUENCE_BASE_URL`
- `CONFLUENCE_EMAIL`
- `CONFLUENCE_API_TOKEN`

**Server Settings:**
- `MCP_HOST` (default: 127.0.0.1)
- `MCP_PORT` (default: 8000)
- `ZAS_MCP_SERVER_URL` (for agent)
- `ZAS_FEEDBACK_LOG` (default: zas_feedback_log.jsonl)

## Testing Strategy

### Unit Tests
```python
# Test services with mocked HTTP
def test_zendesk_get_ticket(mock_requests):
    config = Config.from_env()
    zendesk = ZendeskService(config)
    ticket = zendesk.get_ticket(123)
    assert ticket["id"] == 123

# Test tools with mocked services
def test_ticket_tools_get():
    mock_zendesk = Mock()
    tools = TicketTools(mock_zendesk)
    result = tools.get(123)
    assert result["ok"]
```

### Integration Tests
```python
# Test full stack
def test_end_to_end():
    config = Config.from_env()
    mcp = create_mcp_server(config)
    # Test MCP calls
```

## Performance Considerations

1. **Rate Limiting**: Built into BaseAPIClient
2. **Connection Pooling**: Handled by requests library
3. **Caching**: Can be added at service layer
4. **Pagination**: Implemented in ZendeskService
5. **Timeouts**: Configurable per request

## Security

1. **Credentials**: Loaded from environment, never hardcoded
2. **API Tokens**: Used instead of passwords
3. **HTTPS**: All external API calls use HTTPS
4. **Input Validation**: Done at service layer
5. **Error Messages**: Don't expose sensitive data

## Extensibility

### Adding a New Service

1. Create `src/zas/services/new_service.py`:
```python
class NewService(BaseAPIClient):
    def __init__(self, config: Config):
        super().__init__(...)
```

2. Add config in `src/zas/core/config.py`:
```python
@dataclass
class NewServiceConfig:
    base_url: str
    api_key: str
```

3. Update `Config` class to include it

### Adding a New Tool

1. Create `src/zas/tools/new_tools.py`:
```python
class NewTools:
    def __init__(self, service: NewService):
        self.service = service
```

2. Register in `MCPToolRegistry`:
```python
self.new_tools = NewTools(new_service)
self._register_tool("new_tool", self.new_tools.some_method)
```

3. Add to agent in `ZASAgent._create_tools()`

## Monitoring & Logging

- Use Python's `logging` module
- Log at service layer for API calls
- Log at tool layer for MCP operations
- Feedback logging in Chat API

## Deployment

### Docker
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements_new.txt .
RUN pip install -r requirements_new.txt
COPY . .
CMD ["python3", "app_new.py"]
```

### Heroku/Railway
Use `Procfile`:
```
web: python3 server_wrapper_new.py
mcp: python3 app_new.py
chat: python3 chat_api_new.py
```

## Summary

The new OOP architecture provides:

✅ **Clear structure** - Layered architecture with well-defined responsibilities
✅ **Type safety** - Full type hints throughout
✅ **Testability** - Easy to mock and test each layer
✅ **Maintainability** - Code is organized and easy to understand
✅ **Extensibility** - Easy to add new services and tools
✅ **Reusability** - Services can be used independently
✅ **Configuration** - Centralized and validated
✅ **Error handling** - Custom exception hierarchy
✅ **Documentation** - Comprehensive docs and examples

The migration preserves all existing functionality while providing a solid foundation for future development.
