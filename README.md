# ZAS - Zendesk Agent System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: OOP](https://img.shields.io/badge/code%20style-OOP-brightgreen.svg)](https://en.wikipedia.org/wiki/Object-oriented_programming)
[![Architecture: Clean](https://img.shields.io/badge/architecture-clean-blue.svg)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

A modern, enterprise-grade AI assistant for Zendesk support teams, built with clean OOP architecture and Claude AI integration via Model Context Protocol (MCP).

## 🌟 Features

- 🎯 **Intelligent Ticket Management** - Search, view, and update Zendesk tickets with natural language
- 📚 **Knowledge Base Integration** - Search articles and generate KB content from solved tickets
- 🔗 **Multi-Platform Support** - Integrate with Jira and Confluence
- 💬 **Conversational AI** - Powered by Claude 3.5 Sonnet with context-aware responses
- 🔌 **MCP Integration** - Model Context Protocol for seamless tool integration
- 🏗️ **Clean Architecture** - 5-layer OOP design with SOLID principles
- 🧪 **Type Safe** - Full type hints for better IDE support and fewer bugs
- 📊 **Export & Reporting** - Generate reports and export data to CSV

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│   VS Code Extension | Web UI | OpenAI GPT with MCP          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    API Layer                                 │
│   Chat API (3000) | MCP Proxy (8080) | MCP Server (8000)   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   Agent Layer                                │
│   ZASAgent with Claude 3.5 Sonnet + MCP Tools               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   Tool Layer                                 │
│   TicketTools | KBTools | JiraTools | ConfluenceTools      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Service Layer                               │
│   ZendeskService | JiraService | ConfluenceService          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   Core Layer                                 │
│   Config | BaseAPIClient | Custom Exceptions                │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd ZDZAS-MCP

# Install dependencies
pip install -r requirements_new.txt
```

### Configuration

Create a `.env` file in the root directory:

```bash
# Required - Zendesk
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

# MCP Settings
MCP_HOST=127.0.0.1
MCP_PORT=8000
ZAS_MCP_SERVER_URL=http://127.0.0.1:8000/mcp
```

### Running the Application

**Start MCP Server:**
```bash
python3 app_new.py
# Runs on http://127.0.0.1:8000/mcp
```

**Start Chat API:**
```bash
python3 chat_api_new.py
# Runs on http://0.0.0.0:3000
```

**Start MCP Proxy (for OpenAI integration):**
```bash
python3 mcp_proxy_new.py
# Runs on http://0.0.0.0:8080
```

### Verify Installation

```bash
python3 verify_new_architecture.py
```

## 💡 Usage Examples

### Using the Chat API

```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Zoek alle open tickets van deze week",
    "conversationId": "session-123"
  }'
```

### Using Services Directly

```python
from src.zas.core import Config
from src.zas.services import ZendeskService

# Initialize
config = Config.from_env()
zendesk = ZendeskService(config)

# Search tickets
tickets = zendesk.search_tickets("type:ticket status:open", limit=10)
for ticket in tickets:
    print(f"#{ticket['id']}: {ticket['subject']}")

# Get ticket details
ticket = zendesk.get_ticket(12345)
print(f"Status: {ticket['status']}")
print(f"Priority: {ticket['priority']}")

# Add internal note
zendesk.add_internal_note(12345, "Working on this issue")

# Search knowledge base
articles = zendesk.search_articles("password reset", limit=5)
for article in articles:
    print(f"{article['title']}: {article['url']}")
```

### Using the Agent

```python
from src.zas.agents import ZASAgent
from src.zas.agents.mcp_client import get_mcp_client

# Initialize agent
mcp_client = get_mcp_client()
agent = ZASAgent(mcp_client)

# Single conversation turn
response = agent.run("Hoe kan ik mijn wachtwoord resetten?")
print(response)

# Multi-turn conversation with history
history = []
response1 = agent.run("Zoek ticket 12345", history)
print(response1)

response2 = agent.run("Voeg een interne notitie toe", history)
print(response2)
```

### Using Tools with MCP

```python
from src.zas.core import get_config
from src.zas.services import ZendeskService
from src.zas.tools import TicketTools

# Initialize
config = get_config()
zendesk = ZendeskService(config)
tools = TicketTools(zendesk)

# Use tools (same interface as MCP)
result = tools.search("status:open created>2025-12-12", limit=20)
print(f"Found {result['count']} tickets")

result = tools.get(12345)
print(result['ticket']['subject'])

result = tools.add_internal_note(12345, "Following up on this")
print("Note added!" if result['ok'] else f"Error: {result['error']}")
```

## 🛠️ Available MCP Tools

### Ticket Operations
- `tickets_search(query, limit)` - Search for tickets
- `ticket_get(ticket_id)` - Get ticket details
- `ticket_comments(ticket_id, include_public)` - Get ticket comments
- `ticket_add_internal_note(ticket_id, body)` - Add internal note
- `ticket_update(ticket_id, status, priority, assignee_id, tags)` - Update ticket

### Knowledge Base
- `kb_search_articles(query, limit, label_names, locale)` - Search articles
- `kb_generate_draft(query, limit)` - Generate draft article from tickets
- `kb_create_draft_article(section_id, title, body, locale)` - Create draft article

### Jira Integration
- `jira_get_issue(issue_key, max_comments)` - Get Jira issue details

### Confluence Integration
- `confluence_search_pages(query, limit, space_key)` - Search pages
- `confluence_get_page(page_id, include_body)` - Get page details

### Reporting
- `tickets_export_csv(query, path, limit)` - Export tickets to CSV

### Utilities
- `ping()` - Health check

## 📁 Project Structure

```
/home/ryan/code/ZDZAS-MCP/
├── src/zas/                      # Main package
│   ├── core/                     # Core infrastructure
│   │   ├── config.py            # Configuration management
│   │   ├── exceptions.py        # Custom exceptions
│   │   └── base_client.py       # Base API client
│   ├── services/                # Business logic
│   │   ├── zendesk_service.py   # Zendesk API wrapper
│   │   ├── jira_service.py      # Jira API wrapper
│   │   └── confluence_service.py # Confluence API wrapper
│   ├── tools/                   # MCP tool implementations
│   │   ├── ticket_tools.py      # Ticket operations
│   │   ├── kb_tools.py          # Knowledge base tools
│   │   ├── jira_tools.py        # Jira tools
│   │   ├── confluence_tools.py  # Confluence tools
│   │   ├── reporting_tools.py   # Reporting tools
│   │   ├── general_tools.py     # Utility tools
│   │   └── registry.py          # Tool registration
│   ├── agents/                  # AI agent layer
│   │   ├── mcp_client.py        # MCP HTTP client
│   │   └── zas_agent.py         # Main conversational agent
│   └── api/                     # API endpoints
│       ├── chat_api.py          # Chat API (FastAPI)
│       └── mcp_proxy.py         # MCP proxy
├── app_new.py                   # MCP server entry point
├── chat_api_new.py              # Chat API entry point
├── mcp_proxy_new.py             # Proxy entry point
├── server_wrapper_new.py        # Unified entry point
├── requirements_new.txt         # Python dependencies
└── .env                         # Configuration (create this)
```

## 🧪 Testing

### Run Verification
```bash
python3 verify_new_architecture.py
```

### Manual Testing

**Test MCP Server:**
```bash
# Terminal 1: Start MCP server
python3 app_new.py

# Terminal 2: Test ping
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

**Test Chat API:**
```bash
# Terminal 1: Start chat API
python3 chat_api_new.py

# Terminal 2: Test chat
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "ping"}'
```

## 🎨 Design Patterns

The architecture implements several design patterns:

- **Layered Architecture** - Clear separation between layers
- **Dependency Injection** - Services injected into tools and agents
- **Factory Pattern** - Service and API creation
- **Template Method** - Base API client with common logic
- **Singleton** - Global configuration instance
- **Strategy Pattern** - Different auth strategies per service

## 🔒 Security

- ✅ Credentials loaded from environment variables
- ✅ API tokens used instead of passwords
- ✅ HTTPS for all external API calls
- ✅ Input validation at service layer
- ✅ Error messages don't expose sensitive data

## 📊 Benefits of OOP Architecture

| Aspect | Improvement |
|--------|-------------|
| **Maintainability** | Clear organization, single responsibility |
| **Testability** | Easy to mock with dependency injection |
| **Type Safety** | Full type hints for IDE support |
| **Extensibility** | Add new services/tools easily |
| **Reusability** | Services can be used independently |
| **Error Handling** | Custom exception hierarchy |
| **Documentation** | Comprehensive inline docs |

## 📚 Documentation

- **[README.md](README.md)** - This file (overview and quick start)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture documentation
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migration from old structure
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference guide
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - Refactoring summary

## 🔄 Migration from Old Structure

If you're upgrading from the old functional architecture:

1. Review the [Migration Guide](MIGRATION_GUIDE.md)
2. Run the migration script: `./migrate_to_oop.sh`
3. Test thoroughly with `verify_new_architecture.py`
4. Switch over when ready

Old files are preserved (without `_new` suffix) for reference and gradual migration.

## 🚢 Deployment

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements_new.txt .
RUN pip install --no-cache-dir -r requirements_new.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 8000 3000 8080

# Run MCP server by default
CMD ["python3", "app_new.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    command: python3 app_new.py
    ports:
      - "8000:8000"
    env_file:
      - .env
  
  chat-api:
    build: .
    command: python3 chat_api_new.py
    ports:
      - "3000:3000"
    env_file:
      - .env
    depends_on:
      - mcp-server
  
  mcp-proxy:
    build: .
    command: python3 mcp_proxy_new.py
    ports:
      - "8080:8080"
    env_file:
      - .env
    depends_on:
      - mcp-server
```

### Heroku/Railway

Use `Procfile`:
```
web: python3 server_wrapper_new.py
mcp: python3 app_new.py
chat: python3 chat_api_new.py
proxy: python3 mcp_proxy_new.py
```

## 🤝 Contributing

### Adding a New Service

1. Create service class in `src/zas/services/`
2. Extend `BaseAPIClient`
3. Add configuration in `src/zas/core/config.py`
4. Create corresponding tools in `src/zas/tools/`
5. Register tools in `MCPToolRegistry`
6. Add agent functions in `ZASAgent`

### Adding a New Tool

1. Create tool method in appropriate tools class
2. Register in `MCPToolRegistry`
3. Add function_tool wrapper in `ZASAgent`
4. Update documentation

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed instructions.

## 📝 API Endpoints

### Chat API (Port 3000)

- `POST /chat` - Send message to agent
- `POST /feedback` - Submit feedback
- `POST /reset` - Reset conversation
- `GET /health` - Health check

### MCP Server (Port 8000)

- `POST /mcp` - MCP JSON-RPC endpoint

### MCP Proxy (Port 8080)

- `POST /mcp` - Proxied MCP endpoint

## 🐛 Troubleshooting

**Import Errors:**
```bash
export PYTHONPATH=/home/ryan/code/ZDZAS-MCP:$PYTHONPATH
```

**Configuration Errors:**
```bash
# Verify .env exists and is valid
python3 -c "from src.zas.core import Config; c = Config.from_env(); print('✓ Config OK')"
```

**Connection Errors:**
```bash
# Test service connectivity
python3 -c "from src.zas.core import get_config; from src.zas.services import ZendeskService; z = ZendeskService(get_config()); print(z.base_url)"
```

**Port Already in Use:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

## 📈 Performance

- **Rate Limiting** - Built into BaseAPIClient (configurable delay)
- **Connection Pooling** - Handled by requests library
- **Pagination** - Automatic for large result sets
- **Timeouts** - Configurable per request (default 20s)
- **Caching** - Can be added at service layer if needed

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) for MCP server
- Powered by [Claude 3.5 Sonnet](https://www.anthropic.com/claude) from Anthropic
- Uses [Anthropic Agents SDK](https://github.com/anthropics/anthropic-sdk-python) for agent framework
- API integrations: Zendesk, Jira, Confluence

## 📞 Support

For issues or questions:
1. Check the [Quick Reference](QUICK_REFERENCE.md)
2. Review [Architecture Documentation](ARCHITECTURE.md)
3. Run `python3 verify_new_architecture.py`
4. Check error logs in terminal output

---

**Version:** 2.0.0 (OOP Architecture)  
**Last Updated:** December 19, 2025  
**Python:** 3.10+  
**Architecture:** Clean OOP with 5 layers
