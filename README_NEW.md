# ZAS (Zendesk Agent System) - Enterprise Edition

A modern, OOP-based Zendesk support agent system with MCP (Model Context Protocol) integration.

## 🏗️ Architecture

The codebase follows a clean, layered OOP architecture:

```
src/zas/
├── core/              # Core infrastructure
│   ├── config.py      # Configuration management
│   ├── exceptions.py  # Custom exceptions
│   └── base_client.py # Base API client
├── services/          # Business logic layer
│   ├── zendesk_service.py
│   ├── jira_service.py
│   └── confluence_service.py
├── tools/             # MCP tool implementations
│   ├── ticket_tools.py
│   ├── kb_tools.py
│   ├── jira_tools.py
│   └── registry.py    # Tool registration
├── agents/            # AI agent layer
│   ├── mcp_client.py  # MCP HTTP client
│   └── zas_agent.py   # Main conversational agent
└── api/               # API endpoints
    ├── chat_api.py    # Chat API
    └── mcp_proxy.py   # MCP proxy
```

## 🚀 Key Features

- **Clean OOP Design**: Proper separation of concerns with service, tool, and API layers
- **Dependency Injection**: Services are injected into tools and agents
- **Configuration Management**: Centralized config with environment variable support
- **Error Handling**: Custom exceptions with proper error propagation
- **Type Safety**: Full type hints throughout the codebase
- **Extensibility**: Easy to add new services, tools, or agents

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env-dot .env
# Edit .env with your credentials
```

## 🔧 Configuration

Set the following environment variables in `.env`:

```bash
# Required: Zendesk
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=your-email@example.com
ZENDESK_API_TOKEN=your-api-token

# Optional: Jira
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# Optional: Confluence
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token

# MCP Settings
MCP_HOST=127.0.0.1
MCP_PORT=8000

# Logging
ZAS_FEEDBACK_LOG=zas_feedback_log.jsonl
```

## 🏃 Running the Application

### Start MCP Server (Port 8000)
```bash
python app_new.py
```

### Start Chat API (Port 3000)
```bash
python chat_api_new.py
```

### Start MCP Proxy (Port 8080)
```bash
python mcp_proxy_new.py
```

### All-in-one (for Heroku/Railway)
```bash
python server_wrapper_new.py
```

## 🧪 Usage Examples

### Using the Services Directly

```python
from src.zas.core import Config
from src.zas.services import ZendeskService

config = Config.from_env()
zendesk = ZendeskService(config)

# Search tickets
tickets = zendesk.search_tickets("type:ticket status:open", limit=10)

# Get ticket details
ticket = zendesk.get_ticket(12345)

# Add internal note
zendesk.add_internal_note(12345, "Internal note text")
```

### Using the Agent

```python
from src.zas.agents import ZASAgent
from src.zas.agents.mcp_client import get_mcp_client

mcp_client = get_mcp_client()
agent = ZASAgent(mcp_client)

response = agent.run("Zoek alle open tickets van deze week")
print(response)
```

## 📚 API Documentation

### Chat API Endpoints

- `POST /chat` - Send a message to the agent
- `POST /feedback` - Submit feedback for an agent response
- `POST /reset` - Reset conversation history
- `GET /health` - Health check

### MCP Tools

Available tools registered with the MCP server:

- **Tickets**: `tickets_search`, `ticket_get`, `ticket_comments`, `ticket_add_internal_note`, `ticket_update`
- **Knowledge Base**: `kb_search_articles`, `kb_generate_draft`, `kb_create_draft_article`
- **Reporting**: `tickets_export_csv`
- **Jira**: `jira_get_issue`
- **Confluence**: `confluence_search_pages`, `confluence_get_page`
- **General**: `ping`

## 🔄 Migration from Old Structure

The old files (`app.py`, `core.py`, `tools_*.py`, etc.) are preserved for reference.
New files are suffixed with `_new.py`:

- `app.py` → `app_new.py`
- `chat_api.py` → `chat_api_new.py`
- `mcp_proxy.py` → `mcp_proxy_new.py`
- `server_wrapper.py` → `server_wrapper_new.py`

Once tested, you can remove the old files and rename the new ones.

## 🧩 Design Patterns Used

- **Factory Pattern**: Service and API creation
- **Dependency Injection**: Services injected into tools
- **Repository Pattern**: Services abstract API details
- **Strategy Pattern**: Different authentication strategies per service
- **Singleton Pattern**: Global configuration instance

## 🛡️ Error Handling

Custom exceptions for different error types:

- `ConfigurationException` - Missing or invalid configuration
- `APIException` - API call failures
- `ValidationException` - Input validation errors
- `ZASException` - Base exception for all ZAS errors

## 📈 Benefits of New Architecture

1. **Testability**: Easy to mock services for unit tests
2. **Maintainability**: Clear separation of concerns
3. **Scalability**: Easy to add new integrations
4. **Type Safety**: Full type hints for better IDE support
5. **Reusability**: Services can be used independently
6. **Configuration**: Centralized and validated config

## 🤝 Contributing

When adding new features:

1. Add service methods in `src/zas/services/`
2. Create tool wrappers in `src/zas/tools/`
3. Register tools in `src/zas/tools/registry.py`
4. Add agent functions in `src/zas/agents/zas_agent.py`

## 📝 License

See LICENSE file.
