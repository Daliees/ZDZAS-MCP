# Architecture

## Project Structure

```
ZDZAS-MCP/
│
├── app.py                     # MCP server entry point
├── core.py                    # Core functionality
├── mcp_proxy.py               # MCP proxy implementation
├── chat_api.py                # Chat API interface
├── server_wrapper.py          # Server wrapper
├── zas_agent.py               # ZAS agent implementation
│
├── tools_general.py           # General tools
├── tools_ticket.py            # Ticket-related tools
├── tools_kb.py                # Knowledge base tools
├── tools_jira.py              # Jira integration tools
├── tools_confluence.py        # Confluence integration tools
├── tools_reporting.py         # Reporting tools
│
├── src/
│   └── zendesk_mcp_server/    # Zendesk MCP server module
│       ├── __init__.py
│       ├── server.py
│       └── zendesk_client.py
│
├── docs/                      # Documentation
├── .env.example               # Environment configuration template
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project metadata
└── README.md                  # Project overview
```

## Component Overview

### MCP Server (`app.py`)
Main entry point for the MCP server, exposing all tools to the Zendesk AI Agent.

### Tool Modules
- **tools_general.py**: General-purpose utilities (ping, export, search)
- **tools_ticket.py**: Ticket operations and analysis
- **tools_kb.py**: Knowledge base article management
- **tools_jira.py**: Jira issue integration
- **tools_confluence.py**: Confluence documentation access
- **tools_reporting.py**: Analytics and reporting functions

### Integration Layer
- **core.py**: Core business logic
- **mcp_proxy.py**: MCP protocol implementation
- **chat_api.py**: API for chat interactions

## Data Flow

1. Zendesk AI Agent → MCP Server (via HTTP/WebSocket)
2. MCP Server → Tool Modules (function calls)
3. Tool Modules → External APIs (Zendesk, Jira, Confluence)
4. Response flows back through the chain

## Security

- All credentials stored in environment variables
- No secrets in source code
- API tokens used for authentication
- HTTPS for external API communication
