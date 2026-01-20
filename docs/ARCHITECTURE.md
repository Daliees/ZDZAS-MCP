# ZDZAS-MCP Architecture

## Overview

ZDZAS-MCP is a Model Context Protocol (MCP) server that provides AI agents with tools to interact with Zendesk, Jira, Confluence, Salesforce, and knowledge base systems. The system exposes both an MCP interface and a REST Chat API.

## System Components

### 1. MCP Server (`app.py`)
- **Port**: 8000
- **Protocol**: HTTP MCP (FastMCP 2.13.1)
- **Transport**: Stateless HTTP
- **Endpoint**: `http://0.0.0.0:8000/mcp`

The MCP server registers and exposes tools from all modules:
- Admin tools
- Confluence tools
- General tools
- Jira tools
- Knowledge Base tools
- Reporting tools
- Salesforce tools
- Ticket (Zendesk) tools

**Transport Options:**

The system uses **HTTP transport** by default for production deployment. This choice offers several advantages:

**HTTP Transport (Default - Production)**
- ✅ Multi-client support: Multiple agents/users can connect simultaneously
- ✅ Remote access: Accessible from anywhere (Salesforce, webhooks, remote clients)
- ✅ Stateless: Each request is independent, easier to scale horizontally
- ✅ Load balancing: Can be placed behind nginx/load balancer
- ✅ Monitoring: Standard HTTP monitoring tools work out of the box
- ✅ Debugging: Can test with curl, Postman, browser
- ✅ Firewall-friendly: Port 8000 can be opened selectively
- ❌ Slightly higher latency than stdio (negligible for most use cases)

**stdio Transport (Alternative - Development Only)**
- ✅ Lower latency: Direct process communication
- ✅ MCP CLI compatible: Works with official MCP inspector tools
- ✅ Simpler for single-client local development
- ❌ Single client only: One agent process can connect at a time
- ❌ No remote access: Must be on same machine
- ❌ No concurrent requests: Serialized communication
- ❌ Harder to monitor: No HTTP metrics/logs
- ❌ Not suitable for Salesforce integration or webhooks

**Configuration:**

The MCP server can be configured via environment variables:
```bash
# HTTP mode (default)
export MCP_HOST=0.0.0.0
export MCP_PORT=8000

# Start server
python3 app.py
```

For local development with MCP CLI tools, stdio mode could be added:
```python
# app.py with stdio support (not currently implemented)
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--stdio", action="store_true")
args = parser.parse_args()

if args.stdio:
    helpers.mcp.run(transport="stdio")
else:
    helpers.mcp.run(transport="http", host="0.0.0.0", port=8000)
```

**Recommendation:** Keep HTTP as the primary transport. The benefits for production deployment, Salesforce integration, and multi-user support far outweigh the minimal latency difference. stdio mode can be added later if needed for MCP CLI debugging.

### 2. Chat API (`chat_api.py`)
- **Port**: 9000
- **Framework**: FastAPI
- **Features**: Hot-reloading, CORS, streaming responses
- **Endpoints**:
  - `POST /chat` - Chat with the agent
  - `POST /feedback` - Submit feedback
  - `POST /reset` - Reset conversation

### 3. MCP Proxy (`mcp_proxy.py`)
- **Port**: 8080 (configurable)
- **Purpose**: Proxy for MCP requests with metrics and monitoring
- **Features**:
  - Request/response proxying with error handling
  - Metrics tracking (requests, latency, tool usage)
  - Health checks with upstream connectivity test
  - CLI arguments for configuration

**Endpoints:**
- `POST /mcp` - Proxy MCP JSON-RPC requests
- `GET /health` - Health status with upstream check
- `GET /metrics` - Performance metrics and statistics

**Usage:**
```bash
# Start with default settings
python3 mcp_proxy.py

# Custom host/port
python3 mcp_proxy.py --host 127.0.0.1 --port 8100

# Enable hot-reload for development
python3 mcp_proxy.py --reload
```

**Metrics Tracked:**
- Total requests (success/error counts)
- Average latency
- Tool call frequency by tool name
- Uptime and start time
- Success rate percentage

## Directory Structure

```
ZDZAS-MCP/
├── src/zas/              # Main package
│   ├── api/              # Chat API components
│   │   ├── routes.py     # API endpoints
│   │   ├── schemas.py    # Pydantic models
│   │   ├── middleware.py # Auth & logging
│   │   └── logging_utils.py
│   ├── core/             # Core functionality
│   │   ├── config.py     # Configuration management
│   │   ├── database.py   # SQLAlchemy models
│   │   └── helpers.py    # MCP instance & utilities
│   └── tools/            # MCP tool implementations
│       ├── admin.py      # Admin operations
│       ├── confluence.py # Confluence integration
│       ├── general.py    # General utilities
│       ├── jira.py       # Jira integration
│       ├── kb.py         # Knowledge base search
│       ├── reporting.py  # Analytics & reporting
│       ├── salesforce.py # Salesforce integration
│       └── ticket.py     # Zendesk ticket management
├── tests/                # Test suite
│   ├── conftest.py       # Pytest fixtures
│   ├── test_api/         # API tests
│   ├── test_core/        # Core tests
│   ├── test_tools/       # Tool tests
│   └── test_integration/ # Integration tests
├── docs/                 # Documentation
├── salesforce/           # Salesforce LWC components
└── logs/                 # Application logs
```

## Data Flow

### MCP Tool Invocation
```
AI Agent → MCP Server (port 8000) → Tool Module → External API → Response
```

### Chat API Flow
```
Client → Chat API (port 9000) → Agent → MCP Tools → External APIs → Streaming Response
```

## Technology Stack

### Core
- **Python**: 3.12
- **FastMCP**: 2.13.1 (MCP server framework)
- **FastAPI**: Latest (REST API)
- **OpenAI Agents**: 0.6.4 (AI orchestration)

### Integrations
- **Zendesk**: zenpy 2.0.56
- **Database**: SQLAlchemy 2.0.36 + SQLite
- **HTTP**: requests, httpx

### Development Tools
- **Linter/Formatter**: ruff 0.8.0
- **Type Checker**: mypy 1.13.0
- **Testing**: pytest 8.0.0, pytest-asyncio, pytest-cov
- **Pre-commit**: Automated code quality checks
- **Debugger**: debugpy 1.8.0

## Configuration

Configuration is managed through environment variables loaded from `.env`:

### Required Variables
- `ZENDESK_EMAIL` - Zendesk account email
- `ZENDESK_TOKEN` - Zendesk API token
- `ZENDESK_SUBDOMAIN` - Your Zendesk subdomain

### Optional Variables
- `ZAS_CHAT_PORT` - Chat API port (default: 9000)
- `ZAS_CHAT_JSONL` - Chat event log path
- `ZAS_FEEDBACK_LOG` - Feedback log path

See `.env.example` for complete configuration options.

## Database Schema

The system uses SQLite with SQLAlchemy ORM:

- **RequestLog**: Stores chat request logs
- **ResponseLog**: Stores chat response logs
- **Entities**: Entity extraction results (orgs, people, locations, etc.)

## Authentication

### Chat API
Two authentication methods:
1. **Salesforce Headers**: `X-Salesforce-User-Id` and `X-Salesforce-Org-Id`
2. **Basic Auth**: Credentials configured in middleware

### MCP Server
Currently open access on localhost. For production, implement token-based auth.

## Logging

### Structured Logging
- **Format**: JSON Lines (`.jsonl`)
- **Chat Events**: `logs/chat_events.jsonl`
- **Feedback**: `zas_feedback_log.jsonl`

### Application Logs
- Standard Python logging
- Configurable log levels
- Request/response tracking

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run both servers
python3 start_all.py

# Or individually
python3 app.py         # MCP server only
python3 chat_api.py    # Chat API only
```

### Debugging
VS Code debug configurations available in `.vscode/launch.json`:
- MCP Server
- Chat API (with hot-reload)
- Start All
- Current File

### Production Considerations
- Use process manager (PM2, systemd)
- Configure proper CORS origins
- Implement rate limiting
- Add authentication tokens
- Set up proper logging infrastructure
- Use environment-specific configs
- Consider horizontal scaling

## Performance

- **MCP Server**: Handles multiple concurrent tool invocations
- **Chat API**: Streaming responses for better UX
- **Database**: Connection pooling via SQLAlchemy
- **Caching**: Not yet implemented (future enhancement)

## Security

### Current Implementation
- Basic authentication for Chat API
- Environment-based secrets
- No hardcoded credentials
- CORS configured (needs production tightening)

### Future Enhancements
- OAuth2/JWT tokens
- Rate limiting per user
- API key rotation
- Audit logging
- RBAC (Role-Based Access Control)

## Monitoring

### Available Metrics
- Request/response logs
- Error tracking in logs
- Conversation histories (in-memory)

### Future Enhancements
- Prometheus metrics
- Health check endpoints
- Performance monitoring
- Error rate tracking

## Testing Strategy

- **Unit Tests**: Core functionality and utilities
- **Integration Tests**: Tool and API interactions
- **Coverage Target**: >30% (currently 57%)
- **CI/CD**: GitHub Actions workflow

## Future Roadmap

1. **Phase 5**: MCP Architecture Optimization
   - Health check endpoints
   - Graceful shutdown improvements
   - Performance profiling
   
2. **Phase 6**: Admin Dashboard & EU AI Act Compliance
   - React admin interface
   - Conversation management
   - Audit trails
   - Data retention policies
